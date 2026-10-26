"""Experiment Matrix Runner for CDT in Python.

Loads YAML experiment configurations (single experiment or batches),
executes runs systematically via the CDT bridge, records parameters,
assembles final CF-1.8 compliant 3D NetCDFs, and outputs execution audit reports.
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*GIL.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*global interpreter lock.*")

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import argparse
import datetime
import json
import os
import re
import shutil
import time
from typing import Any, Dict, List, Optional, Union

from launcher.env_checker import check_system_environment, print_environment_report
from launcher.netcdf_assembler import assemble_daily_netcdfs_to_cf18


def check_daily_files_coverage(
    target_dir: Path,
    file_prefix: str,
    start_date: str,
    end_date: str,
    min_size_bytes: int = 1000,
) -> tuple[bool, Optional[str], int, int]:
    """Check daily NetCDF files in target_dir (searching subdirs as well).
    Cleans any 0-byte or corrupted file.
    Returns:
        (is_complete, resume_start_date, valid_count, total_count)
    """
    try:
        s_dt = datetime.datetime.strptime(str(start_date)[:8], "%Y%m%d")
        e_dt = datetime.datetime.strptime(str(end_date)[:8], "%Y%m%d")
    except Exception:
        return False, start_date, 0, 0

    total_count = (e_dt - s_dt).days + 1
    if not target_dir.exists():
        return False, start_date, 0, total_count

    files = list(target_dir.rglob(f"{file_prefix}*.nc"))
    existing_valid_dates = set()

    for f in files:
        try:
            if f.stat().st_size < min_size_bytes:
                try:
                    f.unlink()
                except Exception:
                    pass
                continue
            digits = re.findall(r"\d{8}", f.stem)
            if digits:
                existing_valid_dates.add(digits[-1])
        except Exception:
            continue

    curr = s_dt
    resume_date = None
    while curr <= e_dt:
        d_str = curr.strftime("%Y%m%d")
        if d_str not in existing_valid_dates:
            resume_date = d_str
            break
        curr += datetime.timedelta(days=1)

    valid_count = len(existing_valid_dates)
    is_complete = (resume_date is None and valid_count >= total_count)
    return is_complete, resume_date, valid_count, total_count


def consolidate_daily_files(target_dir: Path, file_prefix: str) -> Path:
    """Consolidate daily netcdfs across subdirectories into a single primary directory."""
    cand_dirs = [
        d for d in [target_dir] + list(target_dir.glob("**/DATA")) + list(target_dir.glob("*_*")) + list(target_dir.glob("MERGED_*"))
        if d.is_dir() and list(d.glob(f"{file_prefix}*.nc"))
    ]
    if not cand_dirs:
        return target_dir
    # Remove duplicates preserving order
    unique_dirs = []
    for cd in cand_dirs:
        if cd not in unique_dirs:
            unique_dirs.append(cd)
    unique_dirs.sort(key=lambda d: len(list(d.glob(f"{file_prefix}*.nc"))), reverse=True)
    primary_dir = unique_dirs[0]
    for d in unique_dirs[1:]:
        if d == primary_dir:
            continue
        for f in d.glob(f"{file_prefix}*.nc"):
            dest = primary_dir / f.name
            try:
                if not dest.exists() or dest.stat().st_size < f.stat().st_size:
                    shutil.move(str(f), str(dest))
            except Exception:
                pass
        try:
            if not list(d.glob("*.nc")):
                shutil.rmtree(str(d), ignore_errors=True)
        except Exception:
            pass
    return primary_dir


def _check_python_requirements() -> bool:
    """Ensure all required Python packages are installed, showing a clean error if not."""
    try:
        import yaml
        import numpy
        import pandas
        import xarray
        import netCDF4
        return True
    except ImportError as e:
        print("\n" + "=" * 75)
        print("  [!] ERROR: FALTAN PAQUETES DE PYTHON REQUERIDOS")
        print("=" * 75)
        print(f"  Detalle del error : {e}")
        print("\n  Para instalar todas las dependencias necesarias en este entorno, ejecuta:")
        print("      pip install -r requirements.txt")
        print("\n  O ejecuta el diagnóstico completo del entorno con:")
        print("      python launcher/experiment_runner.py --check-env")
        print("=" * 75 + "\n")
        return False



def format_duration(seconds: float) -> str:
    """Format elapsed seconds into a human-readable string (e.g. '4h 15m 32s', '12m 45s', or '4.70s')."""
    if seconds is None or seconds < 0:
        return "0.00s"
    if seconds < 60:
        return f"{seconds:.2f}s"
    
    total_sec = int(round(seconds))
    hours = total_sec // 3600
    rem = total_sec % 3600
    minutes = rem // 60
    secs = rem % 60
    
    if hours > 0:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    return f"{minutes}m {secs:02d}s"


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries."""
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


def _probe_netcdf_data_var(nc_path: Union[str, Path], preferred: Optional[str] = None) -> Optional[str]:
    """Inspect a NetCDF file and return its primary climate data variable name."""
    try:
        import netCDF4 as nc
        with nc.Dataset(str(nc_path), "r") as ds:
            coords = ("lon", "lat", "longitude", "latitude", "time", "x", "y")
            data_vars = [
                v for v in ds.variables
                if v.lower() not in coords and len(ds.variables[v].dimensions) >= 2
            ]
            if not data_vars:
                data_vars = [v for v in ds.variables if v.lower() not in coords]
            if not data_vars:
                return None
            if preferred and preferred in data_vars:
                return preferred
            for c in ("precip", "temp", "tmax", "tmin", "precipitation", "tasmax", "tasmin"):
                if c in data_vars:
                    return c
            return data_vars[0]
    except Exception:
        return None


class ExperimentRunner:
    """Orchestrates batches or individual CDT experiments defined via YAML configuration."""

    def __init__(
        self,
        config_target: Union[Path, str],
        base_config_path: Optional[Union[Path, str]] = None,
        region: Optional[str] = "ca",
        nb_cores: Optional[Union[int, str]] = "auto",
        rscript_path: Optional[Path | str] = None,
    ):
        """Initialize runner with path to a YAML configuration file or directory of YAMLs."""
        self.config_target = Path(config_target).resolve()
        if not self.config_target.exists():
            raise FileNotFoundError(f"Target path not found: {self.config_target}")

        self.base_config_path = Path(base_config_path).resolve() if base_config_path else None
        self.region = (region or "ca").lower()
        
        # Parse nb_cores
        parsed_cores: Optional[Union[int, str]] = None
        if nb_cores:
            if isinstance(nb_cores, str) and nb_cores.isdigit():
                parsed_cores = int(nb_cores)
            elif isinstance(nb_cores, int):
                parsed_cores = nb_cores
            elif nb_cores == "auto":
                parsed_cores = "auto"
        
        from launcher.cdt_bridge import CDTBridge
        self.bridge = CDTBridge(rscript_path=rscript_path, nb_cores=parsed_cores)
        self.results_summary: List[Dict[str, Any]] = []

    def _load_yaml_file(self, filepath: Path) -> Dict[str, Any]:
        """Load a YAML file, resolving any 'include' or 'base_config' reference."""
        import yaml
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        # Check for explicit base configuration in runner or inside YAML
        include_ref = data.pop("include", None) or data.pop("base_config", None)
        base_dict = {}

        if self.base_config_path and self.base_config_path.exists():
            with open(self.base_config_path, "r", encoding="utf-8") as bf:
                base_dict = yaml.safe_load(bf) or {}
        elif include_ref:
            # Resolve relative to project root or filepath parent
            cand1 = PROJECT_ROOT / include_ref
            cand2 = filepath.parent / include_ref
            cand_path = cand1 if cand1.exists() else (cand2 if cand2.exists() else Path(include_ref))
            if cand_path.exists():
                with open(cand_path, "r", encoding="utf-8") as bf:
                    base_dict = yaml.safe_load(bf) or {}

        if base_dict:
            return _deep_merge(base_dict, data)
        return data

    def load_configs(self) -> List[Dict[str, Any]]:
        """Load experiment configurations from a single YAML file or directory of YAMLs."""
        configs: List[Dict[str, Any]] = []

        if self.config_target.is_file():
            data = self._load_yaml_file(self.config_target)
            if "experiments" in data:
                global_cfg = data.get("global", {})
                for exp in data["experiments"]:
                    merged_cfg = self._merge_global_and_exp(global_cfg, exp)
                    configs.append(self._normalize_experiment_paths(merged_cfg))
            else:
                configs.append(self._normalize_experiment_paths(data))

        elif self.config_target.is_dir():
            yaml_files = sorted(list(self.config_target.glob("*.yaml")) + list(self.config_target.glob("*.yml")))
            for yf in yaml_files:
                if yf.name.lower().startswith("global_") or yf.name.lower().startswith("hardware_"):
                    continue
                data = self._load_yaml_file(yf)
                if "experiments" in data:
                    global_cfg = data.get("global", {})
                    for exp in data["experiments"]:
                        merged_cfg = self._merge_global_and_exp(global_cfg, exp)
                        configs.append(self._normalize_experiment_paths(merged_cfg))
                else:
                    configs.append(self._normalize_experiment_paths(data))

        return configs

    def _normalize_experiment_paths(self, exp: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize paths depending on variable type (rainfall vs temperature) and region."""
        var_type = exp.get("variable_type", "rainfall").lower()
        exp_id = exp.get("experiment_id", exp.get("id", "EXP"))
        paths = dict(exp.get("paths", {}))

        # Apply regional overrides if present in configuration
        regions_dict = exp.get("regions", {})
        if self.region in regions_dict:
            reg_info = regions_dict[self.region]
            for k, v in reg_info.items():
                if k not in ("name", "benchmark_dir"):
                    paths[k] = v

        # Auto-map generic satellite_dir and stations_file from base_config if not explicitly overridden
        if "satellite_dir" not in paths:
            if var_type in ("rainfall", "rain", "precip"):
                paths["satellite_dir"] = paths.get("satellite_rainfall_dir", "data/chirps_daily")
                paths["satellite_format"] = paths.get("satellite_rainfall_format", "chirps_%s%s%s.nc")
                paths["var_id"] = paths.get("var_id", "precip")
            elif var_type in ("tmax", "tx", "temp_max", "temperature_max"):
                paths["satellite_dir"] = paths.get("satellite_tmax_dir", paths.get("satellite_temperature_dir", "data/chirts_daily/tmax"))
                paths["satellite_format"] = paths.get("satellite_tmax_format", "tmax_%s%s%s.nc")
                paths["var_id"] = "temp" if paths.get("var_id") in (None, "tmax", "") else paths.get("var_id")
            elif var_type in ("tmin", "tn", "temp_min", "temperature_min"):
                paths["satellite_dir"] = paths.get("satellite_tmin_dir", paths.get("satellite_temperature_dir", "data/chirts_daily/tmin"))
                paths["satellite_format"] = paths.get("satellite_tmin_format", "tmin_%s%s%s.nc")
                paths["var_id"] = "temp" if paths.get("var_id") in (None, "tmin", "") else paths.get("var_id")
            else:
                paths["satellite_dir"] = paths.get("satellite_temperature_dir", "data/chirts_daily")
                paths["satellite_format"] = paths.get("satellite_temperature_format", "tmax_%s%s%s.nc")
                paths["var_id"] = paths.get("var_id", "temp")
        else:
            if var_type in ("tmax", "tx", "temp_max", "temperature_max") and paths.get("var_id") in (None, "tmax", ""):
                paths["var_id"] = "temp"
            elif var_type in ("tmin", "tn", "temp_min", "temperature_min") and paths.get("var_id") in (None, "tmin", ""):
                paths["var_id"] = "temp"

        if "stations_file" not in paths:
            reg_suffix = f"_{self.region}" if self.region in ("ca", "rd") else "_all"
            if var_type in ("rainfall", "rain", "precip"):
                paths["stations_file"] = paths.get(
                    "stations_rainfall_file", f"data/stations/precip_stations{reg_suffix}.csv"
                )
            elif var_type in ("tmax", "tx", "temp_max", "temperature_max"):
                paths["stations_file"] = paths.get(
                    "stations_tmax_file",
                    paths.get("stations_temperature_file", f"data/stations/tmax_stations{reg_suffix}.csv"),
                )
            elif var_type in ("tmin", "tn", "temp_min", "temperature_min"):
                paths["stations_file"] = paths.get(
                    "stations_tmin_file",
                    paths.get("stations_temperature_file", f"data/stations/tmin_stations{reg_suffix}.csv"),
                )
            else:
                paths["stations_file"] = paths.get(
                    "stations_temperature_file", f"data/stations/temp_stations{reg_suffix}.csv"
                )

        # Resolve holdout / omitted stations file based on variable type and region
        reg_suffix = f"_{self.region}" if self.region in ("ca", "rd") else ""
        if var_type in ("rainfall", "rain", "precip"):
            cand_candidates = [
                paths.get("holdout_rainfall_file"),
                f"data/stations/validation_holdout_stations_rainfall{reg_suffix}.csv" if reg_suffix else None,
                "data/stations/validation_holdout_stations_rainfall.csv",
                paths.get("holdout_stations_file"),
                "data/stations/validation_holdout_stations.csv",
            ]
        elif var_type in ("tmax", "tx", "temp_max", "temperature_max"):
            cand_candidates = [
                paths.get("holdout_tmax_file"),
                paths.get("holdout_temperature_file"),
                f"data/stations/validation_holdout_stations_temperature{reg_suffix}.csv" if reg_suffix else None,
                f"data/stations/validation_holdout_stations_tmax{reg_suffix}.csv" if reg_suffix else None,
                "data/stations/validation_holdout_stations_temperature.csv",
                "data/stations/validation_holdout_stations_tmax.csv",
                paths.get("holdout_stations_file"),
                "data/stations/validation_holdout_stations.csv",
            ]
        elif var_type in ("tmin", "tn", "temp_min", "temperature_min"):
            cand_candidates = [
                paths.get("holdout_tmin_file"),
                paths.get("holdout_temperature_file"),
                f"data/stations/validation_holdout_stations_temperature{reg_suffix}.csv" if reg_suffix else None,
                f"data/stations/validation_holdout_stations_tmin{reg_suffix}.csv" if reg_suffix else None,
                "data/stations/validation_holdout_stations_temperature.csv",
                "data/stations/validation_holdout_stations_tmin.csv",
                paths.get("holdout_stations_file"),
                "data/stations/validation_holdout_stations.csv",
            ]
        else:
            cand_candidates = [
                paths.get("holdout_temperature_file"),
                paths.get("holdout_rainfall_file"),
                paths.get("holdout_stations_file"),
                "data/stations/validation_holdout_stations.csv",
            ]

        chosen_holdout = None
        for cand in cand_candidates:
            if cand and Path(cand).exists():
                chosen_holdout = cand
                break
        if not chosen_holdout:
            for cand in cand_candidates:
                if cand:
                    chosen_holdout = cand
                    break

        paths["holdout_stations_file"] = chosen_holdout

        # Ensure output_dir and log_dir are set with regional awareness
        def_out_root = f"output/experiments_{self.region}" if self.region in ("ca", "rd") else "output/experiments"
        def_log_root = f"logs/experiments_{self.region}" if self.region in ("ca", "rd") else "logs/experiments"

        out_root = paths.get("output_root", def_out_root)
        log_root = paths.get("log_root", def_log_root)

        if "output_dir" not in paths:
            paths["output_dir"] = f"{out_root}/{exp_id}"
        if "log_dir" not in paths:
            paths["log_dir"] = f"{log_root}/{exp_id}"

        exp["paths"] = paths
        exp["active_region"] = self.region
        return exp

    def _merge_global_and_exp(self, global_cfg: Dict[str, Any], exp_cfg: Dict[str, Any]) -> Dict[str, Any]:
        """Merge global configuration dictionary into a specific experiment dictionary."""
        exp_id = exp_cfg.get("id", exp_cfg.get("experiment_id", "EXP_UNKNOWN"))
        merged = _deep_merge(global_cfg, exp_cfg)
        merged["experiment_id"] = exp_id
        return merged

    def run_all_experiments(self, force: bool = False) -> List[Dict[str, Any]]:
        """Iterate over all loaded experiments and execute them."""
        experiments = self.load_configs()

        if not experiments:
            print(f"[!] No experiments found in: {self.config_target}")
            return []

        print("=" * 80)
        print(f"  CDT EXPERIMENT EXECUTION SUITE: {len(experiments)} EXPERIMENT(S) DETECTED")
        print("=" * 80)

        for i, exp in enumerate(experiments, start=1):
            exp_id = exp.get("experiment_id", exp.get("id", f"EXP_{i:02d}"))
            exp_desc = exp.get("description", "No description provided")
            var_type = exp.get("variable_type", "rainfall").lower()
            paths = exp.get("paths", {})

            print(f"\n[{i}/{len(experiments)}] Running {exp_id}: {exp_desc} ({var_type.upper()})")
            print("-" * 80)

            out_dir = Path(paths.get("output_dir", f"output/experiments/{exp_id}")).resolve()
            log_dir = Path(paths.get("log_dir", f"logs/experiments/{exp_id}")).resolve()
            out_dir.mkdir(parents=True, exist_ok=True)
            log_dir.mkdir(parents=True, exist_ok=True)

            manifest_file = out_dir / "manifest.json"
            post_proc = exp.get("post_processing", {})
            out_nc_name = post_proc.get("output_filename", f"{var_type}_daily_1991_2020_{exp_id}.nc")
            assembled_nc_path = out_dir / out_nc_name

            # Checkpoint: skip experiment if already finished with SUCCESS and valid 3D NetCDF
            if not force and manifest_file.exists() and assembled_nc_path.exists() and assembled_nc_path.stat().st_size > 100000:
                try:
                    with open(manifest_file, "r", encoding="utf-8") as pf:
                        prev_m = json.load(pf)
                    if prev_m.get("status") == "SUCCESS":
                        print(f"[*] Experimento {exp_id} ya completado previamente con exito. Saltando (usar --force para reejecutar).")
                        self.results_summary.append({
                            "id": exp_id,
                            "variable": var_type,
                            "description": exp_desc,
                            "status": "SUCCESS (CACHED)",
                            "time_sec": prev_m.get("execution_time_sec", 0.0),
                            "time_formatted": prev_m.get("execution_time_formatted", "cached"),
                            "output_dir": str(out_dir),
                            "assembled_nc": str(assembled_nc_path),
                            "kge": prev_m.get("validation", {}).get("summary_results", {}).get("mean_kge", "N/A"),
                        })
                        continue
                except Exception:
                    pass

            # Fault Tolerance: If force is requested, wipe previous files to restart clean
            if force:
                for f in out_dir.glob("*.nc"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

            manifest_data = {
                "experiment_id": exp_id,
                "variable_type": var_type,
                "description": exp_desc,
                "timestamp_start": datetime.datetime.now().isoformat(),
                "config": exp,
            }

            # Check for holdout / omitted stations configuration
            validation_cfg = exp.get("validation", {})
            holdout_file = (
                paths.get("holdout_stations_file")
                or paths.get("omitted_stations_file")
                or validation_cfg.get("holdout_stations_file")
                or validation_cfg.get("omitted_stations_file")
            )
            
            orig_station_file = paths.get("stations_file", "")
            training_station_file = orig_station_file
            holdout_station_file = None
            split_info = None

            if holdout_file and Path(holdout_file).exists() and orig_station_file and Path(orig_station_file).exists():
                print(f"  --> Aplicando particion de estaciones con lista de exclusion: {holdout_file}")
                split_dir = out_dir / "station_split"
                try:
                    from launcher.station_manager import split_cdt_station_file
                    split_info = split_cdt_station_file(orig_station_file, holdout_file, split_dir)
                    training_station_file = split_info["training_stations_file"]
                    holdout_station_file = split_info["holdout_stations_file"]
                    print(f"      [Particion] Total: {split_info['total_stations']} | Entrenamiento: {split_info['training_count']} | Validacion (Omitidas): {split_info['holdout_count']}")
                except Exception as e:
                    print(f"      [!] Error al particionar estaciones: {e}. Usando archivo original.")

            # Ensure all 2D daily files exist in satellite_dir; if incomplete or missing, split/resume raw 3D NetCDF
            sat_dir = Path(paths.get("satellite_dir", "")).resolve() if paths.get("satellite_dir") else None
            p_start = str(exp.get("period", {}).get("start_date", "19910101"))
            p_end = str(exp.get("period", {}).get("end_date", "20201231"))
            try:
                dt_s = datetime.datetime.strptime(p_start, "%Y%m%d")
                dt_e = datetime.datetime.strptime(p_end, "%Y%m%d")
                expected_days = (dt_e - dt_s).days + 1
            except Exception:
                expected_days = 10958

            current_nc_count = len(list(sat_dir.glob("*.nc"))) if (sat_dir and sat_dir.exists()) else 0

            if sat_dir and current_nc_count < expected_days:
                raw_key = f"raw_3d_netcdf_{var_type}" if var_type in ("rainfall", "precip") else f"raw_3d_netcdf_{var_type}"
                raw_path_str = paths.get(raw_key) or paths.get("raw_3d_netcdf_rainfall" if var_type in ("rainfall", "precip") else "raw_3d_netcdf_tmax")
                if not raw_path_str or not Path(raw_path_str).exists():
                    cand_3d_files = list(Path("data/raw_netcdf").glob("*.nc")) if Path("data/raw_netcdf").exists() else []
                    for cf in cand_3d_files:
                        if var_type in ("rainfall", "precip") and "chirps" in cf.name.lower():
                            raw_path_str = str(cf)
                            break
                        elif "tmax" in var_type and "tmax" in cf.name.lower():
                            raw_path_str = str(cf)
                            break
                        elif "tmin" in var_type and "tmin" in cf.name.lower():
                            raw_path_str = str(cf)
                            break
                if raw_path_str and Path(raw_path_str).exists():
                    from launcher.data_preprocessor import split_3d_netcdf_to_daily_parallel
                    if current_nc_count > 0:
                        print(f"  --> Grillas diarias incompletas ({current_nc_count:,} de {expected_days:,} días). Reanudando particionado 3D...")
                    else:
                        print(f"  --> Generando {expected_days:,} archivos diarios 2D desde NetCDF 3D: {Path(raw_path_str).name} -> {sat_dir.name}/")
                    
                    split_res = split_3d_netcdf_to_daily_parallel(
                        input_nc_path=raw_path_str,
                        output_dir=sat_dir,
                        filename_format=paths.get("satellite_format", "chirps_%s%s%s.nc" if var_type in ("rainfall", "precip") else f"{var_type}_%s%s%s.nc"),
                        var_id=paths.get("var_id", "precip" if var_type in ("rainfall", "precip") else "temp"),
                        start_date=p_start,
                        end_date=p_end,
                    )
                    if split_res and "var_id" in split_res:
                        paths["var_id"] = split_res["var_id"]

            # Ensure paths["var_id"] accurately reflects the actual variable inside daily NetCDFs
            if sat_dir and sat_dir.exists():
                existing_ncs = list(sat_dir.glob("*.nc"))
                if existing_ncs:
                    probed_var = _probe_netcdf_data_var(existing_ncs[0], preferred=paths.get("var_id"))
                    if probed_var:
                        paths["var_id"] = probed_var

            # Create working copy of exp dict with effective training station path
            exp_exec = dict(exp)
            exp_exec["paths"] = dict(paths)
            exp_exec["paths"]["stations_file"] = training_station_file

            # Sync nb_cores from experiment system config if defined
            exp_sys_cores = exp.get("system", {}).get("nb_cores")
            if exp_sys_cores is not None and self.bridge.nb_cores in (None, "auto"):
                if isinstance(exp_sys_cores, int):
                    self.bridge.nb_cores = exp_sys_cores
                elif isinstance(exp_sys_cores, str) and exp_sys_cores.isdigit():
                    self.bridge.nb_cores = int(exp_sys_cores)

            t0 = time.time()
            if var_type in ("rainfall", "rain", "precip"):
                ret_code, stdout, stderr, elapsed = self._run_rainfall_experiment(exp_exec, out_dir, log_dir)
            elif var_type in ("temperature", "temp", "tmax", "tmin"):
                ret_code, stdout, stderr, elapsed = self._run_temperature_experiment(exp_exec, out_dir, log_dir)
            else:
                print(f"[!] Unknown variable type: {var_type}. Skipping.")
                continue

            status_str = "SUCCESS" if ret_code == 0 else "FAILED"
            if ret_code != 0 and stderr:
                err_lines = [l.strip() for l in stderr.strip().splitlines() if l.strip()]
                for el in err_lines[-4:]:
                    print(f"      [R-stderr] {el}")
            formatted_time = format_duration(elapsed)
            manifest_data["timestamp_end"] = datetime.datetime.now().isoformat()
            manifest_data["execution_time_sec"] = elapsed
            manifest_data["execution_time_formatted"] = formatted_time
            manifest_data["status"] = status_str
            manifest_data["return_code"] = ret_code
            if split_info:
                manifest_data["station_partition"] = {
                    "total": split_info["total_stations"],
                    "training_count": split_info["training_count"],
                    "holdout_count": split_info["holdout_count"],
                    "holdout_ids": split_info["holdout_ids"],
                }

            # Post-processing: Assemble 3D CF-1.8 NetCDF
            post_proc = exp.get("post_processing", {})
            assembled_nc_path = None
            if ret_code == 0 and post_proc.get("assemble_3d_netcdf", True):
                try:
                    eff_prefix = "rr_mrg_" if var_type in ("rainfall", "rain", "precip") else f"{var_type}_mrg_"
                    cand_dirs = [
                        d for d in [out_dir] + list(out_dir.glob("**/DATA")) + list(out_dir.glob("MERGED_*"))
                        if d.is_dir() and list(d.glob(f"{eff_prefix}*.nc"))
                    ]
                    # Select the directory with the maximum number of merged daily netcdf files
                    cand_dirs.sort(key=lambda d: len(list(d.glob(f"{eff_prefix}*.nc"))), reverse=True)
                    daily_nc_dir = cand_dirs[0] if cand_dirs else out_dir
                    
                    if list(daily_nc_dir.glob(f"{eff_prefix}*.nc")):
                        out_nc_name = post_proc.get("output_filename", f"{var_type}_daily_1991_2020_{exp_id}.nc")
                        assembled_nc_path = out_dir / out_nc_name
                        print(f"  --> Ensamblando archivos NetCDF diarios en producto 3D CF-1.8...")
                        eff_cf_var = "precip" if var_type in ("rainfall", "rain", "precip") else ("tmin" if "tmin" in var_type or "tn" in var_type else "tmax")
                        assemble_daily_netcdfs_to_cf18(
                            input_dir=daily_nc_dir,
                            output_netcdf_path=assembled_nc_path,
                            variable_name=eff_cf_var,
                            variable_type=var_type,
                            title=f"Reconstructed Climate Gridded Dataset (1991-2020) - {exp_id}",
                        )
                        manifest_data["assembled_netcdf_cf18"] = str(assembled_nc_path)
                except Exception as e:
                    print(f"  [!] Advertencia al ensamblar NetCDF 3D: {e}")

            # Validation Evaluation Step
            val_target_file = holdout_station_file or (orig_station_file if validation_cfg.get("enabled", False) else None)
            if ret_code == 0 and assembled_nc_path and assembled_nc_path.exists() and val_target_file and Path(val_target_file).exists():
                print(f"  --> Evaluando metricas cuantitativas de validacion contra estaciones independientes...")
                try:
                    from launcher.station_manager import evaluate_netcdf_against_stations
                    wet_thresh = validation_cfg.get("wet_threshold", 1.0)
                    eff_cf_var = "precip" if var_type in ("rainfall", "rain", "precip") else ("tmin" if "tmin" in var_type or "tn" in var_type else "tmax")
                    df_metrics, val_summary = evaluate_netcdf_against_stations(
                        netcdf_path=assembled_nc_path,
                        station_file=val_target_file,
                        var_name=eff_cf_var,
                        var_type=var_type,
                        wet_threshold=wet_thresh,
                    )
                    
                    # Save metrics CSV & JSON
                    metrics_csv_path = out_dir / "validation_metrics_by_station.csv"
                    summary_json_path = out_dir / "validation_summary.json"
                    df_metrics.to_csv(metrics_csv_path, index=False)
                    with open(summary_json_path, "w", encoding="utf-8") as sf:
                        json.dump(val_summary, sf, indent=2)
                    
                    manifest_data["validation"] = {
                        "metrics_by_station_csv": str(metrics_csv_path),
                        "summary_json": str(summary_json_path),
                        "summary_results": val_summary,
                    }
                    
                    # Print summary to console
                    print(f"      [Metricas] Evaluadas {val_summary.get('total_stations_evaluated', 0)} estaciones | KGE Medio: {val_summary.get('mean_kge', 0):.3f} | r: {val_summary.get('mean_r', 0):.3f} | RMSE: {val_summary.get('mean_rmse', 0):.2f}")
                    if "mean_pod" in val_summary:
                        print(f"      [Categoricas] POD: {val_summary.get('mean_pod', 0):.3f} | FAR: {val_summary.get('mean_far', 0):.3f} | ETS: {val_summary.get('mean_ets', 0):.3f} | HSS: {val_summary.get('mean_hss', 0):.3f}")
                except Exception as e:
                    print(f"  [!] Advertencia al computar metricas de validacion: {e}")

            with open(manifest_file, "w", encoding="utf-8") as mf:
                json.dump(manifest_data, mf, indent=2)

            self.results_summary.append({
                "id": exp_id,
                "variable": var_type,
                "description": exp_desc,
                "status": status_str,
                "time_sec": round(elapsed, 2),
                "time_formatted": formatted_time,
                "output_dir": str(out_dir),
                "assembled_nc": str(assembled_nc_path) if assembled_nc_path else "N/A",
                "kge": manifest_data.get("validation", {}).get("summary_results", {}).get("mean_kge", "N/A"),
            })

            icon = "[OK]" if ret_code == 0 else "[FAIL]"
            print(f"  >>> {icon} {exp_id} completado con estado {status_str} en {formatted_time} ({elapsed:.2f}s)")

        self._print_execution_summary()
        return self.results_summary

    def _run_rainfall_experiment(
        self, exp: Dict[str, Any], out_dir: Path, log_dir: Path
    ) -> tuple[int, str, str, float]:
        paths = exp.get("paths", {})
        period = exp.get("period", {})
        start_date = str(period.get("start_date", "19910101"))
        end_date = str(period.get("end_date", "20201231"))
        merging = exp.get("merging", {})
        interp = merging.get("interpolation", {})
        if not interp and "interp_method" in merging:
            interp = {"method": merging["interp_method"]}
        elif not interp and isinstance(merging.get("passes"), list) and len(merging["passes"]) > 0:
            first_pass = merging["passes"][0]
            if isinstance(first_pass, dict) and "interp_method" in first_pass:
                interp = {"method": first_pass["interp_method"]}
        rnor = merging.get("rnor", exp.get("rnor_mask", {}))
        bias_cfg = exp.get("bias_correction", {}) or {}

        # 3-Step Canonical CDT Pipeline for Rainfall:
        # Step 1: Compute Bias Coefficients
        # Step 2: Apply Bias Correction
        # Step 3: Merging Data
        bias_method = str(bias_cfg.get("method", "mbvar")).lower()
        effective_sat_dir = paths.get("satellite_dir", "")
        effective_sat_format = paths.get("satellite_format", "chirps_%s%s%s.nc")
        total_time = 0.0

        if bias_method and bias_method not in ("none", "null", "false"):
            bias_coeffs_dir = out_dir / "bias_coeffs"
            b_interp = bias_cfg.get("interpolation", {})
            if not b_interp and "interp_method" in bias_cfg:
                b_interp = {"method": bias_cfg["interp_method"]}

            cand_rds = [f for f in bias_coeffs_dir.rglob("*.rds") if f.is_file()]
            if cand_rds and cand_rds[0].stat().st_size > 500:
                print(f"  --> [Paso 1/3] [Cache] Coeficientes de sesgo ya calculados previamente.")
                actual_bias_dir = cand_rds[0].parent
            else:
                bias_coeffs_dir.mkdir(parents=True, exist_ok=True)
                print(f"  --> [Paso 1/3] Calculando coeficientes de sesgo ({bias_method})...")
                rc1, out1, err1, t1 = self.bridge.compute_bias_coefficients(
                    variable_type="rainfall",
                    time_step=exp.get("time_step", "daily"),
                    station_file=paths.get("stations_file", ""),
                    netcdf_dir=effective_sat_dir,
                    netcdf_format=effective_sat_format,
                    output_dir=bias_coeffs_dir,
                    bias_method=bias_method,
                    distr_name=bias_cfg.get("distribution") or bias_cfg.get("distr") or "berngamma",
                    interp_method=b_interp.get("method", "okr"),
                    nmin=b_interp.get("nmin", 4),
                    nmax=b_interp.get("nmax", 12),
                    maxdist=b_interp.get("maxdist", 2.0),
                    use_block=b_interp.get("use_block", True),
                    vgm_models=b_interp.get("variogram_models", ["Sph", "Exp", "Gau"]),
                    dem_file=paths.get("dem_file"),
                    var_id=paths.get("var_id", "precip"),
                    start_year=int(str(start_date)[:4]),
                    end_year=int(str(end_date)[:4]),
                    global_bias_opts=(
                        exp.get("biascoeff_options")
                        or exp.get("bias_options")
                        or exp.get("global_bias_options")
                        or exp.get("global_options")
                    ),
                    log_dir=log_dir,
                )
                total_time += t1
                if rc1 != 0:
                    return rc1, out1, err1, total_time

                cand_rds = [f for f in bias_coeffs_dir.rglob("*.rds") if f.is_file()]
                actual_bias_dir = cand_rds[0].parent if cand_rds else bias_coeffs_dir

            # Step 2: Apply bias correction
            adj_dir = out_dir / "bias_adjusted"
            adj_complete, resume_adj_date, adj_count, adj_total = check_daily_files_coverage(
                adj_dir, "rr_adj_", start_date, end_date
            )
            if adj_complete:
                print(f"  --> [Paso 2/3] [Cache] Grillas satelitales ajustadas ya completas ({adj_count}/{adj_total}).")
            else:
                step2_start = resume_adj_date or start_date
                if resume_adj_date and resume_adj_date != start_date:
                    print(f"  --> [Paso 2/3] [Resume] Reanudando ajuste de sesgo desde {step2_start} ({adj_count} dias procesados)...")
                else:
                    print(f"  --> [Paso 2/3] Aplicando ajuste de sesgo a grillas satelitales...")
                rc2, out2, err2, t2 = self.bridge.apply_bias_correction_precip(
                    time_step=exp.get("time_step", "daily"),
                    start_date=step2_start,
                    end_date=end_date,
                    netcdf_dir=effective_sat_dir,
                    netcdf_format=effective_sat_format,
                    bias_dir=actual_bias_dir,
                    bias_format=None,
                    bias_method=bias_method,
                    output_dir=adj_dir,
                    var_id=paths.get("var_id", "precip"),
                    output_format="rr_adj_%s%s%s.nc",
                    log_dir=log_dir,
                )
                total_time += t2
                if rc2 != 0:
                    return rc2, out2, err2, total_time

            effective_sat_dir = consolidate_daily_files(adj_dir, "rr_adj_")
            effective_sat_format = "rr_adj_%s%s%s.nc"

        # Step 3: Merging Data
        consolidate_daily_files(out_dir, "rr_mrg_")
        mrg_complete, resume_mrg_date, mrg_count, mrg_total = check_daily_files_coverage(
            out_dir, "rr_mrg_", start_date, end_date
        )
        if mrg_complete:
            print(f"  --> [Paso 3/3] [Cache] Fusion espacial ya completada previamente ({mrg_count}/{mrg_total}).")
            return 0, "Cached", "", total_time

        if resume_mrg_date and resume_mrg_date != start_date:
            print(f"  --> [Paso 3/3] [Resume] Reanudando fusion espacial ({mrg_count} de {mrg_total} dias ya procesados)...")
        else:
            print(f"  --> [Paso 3/3] Ejecutando fusion espacial final (Merging)...")

        rc3, out3, err3, t3 = self.bridge.merge_rainfall(
            time_step=exp.get("time_step", "daily"),
            start_date=start_date,
            end_date=end_date,
            station_file=paths.get("stations_file", ""),
            netcdf_dir=effective_sat_dir,
            netcdf_format=effective_sat_format,
            output_dir=out_dir,
            var_id=paths.get("var_id", "precip"),
            merge_method=merging.get("method", "SBA"),
            nrun=merging.get("nrun", 3 if isinstance(merging.get("passes"), list) and len(merging.get("passes")) > 1 else 1),
            pass_ratios=merging.get("passes", [1.0, 0.75, 0.5]),
            interp_method=interp.get("method", "idw"),
            nmin=interp.get("nmin", 6),
            nmax=interp.get("nmax", 16),
            maxdist=interp.get("maxdist", 1.5),
            use_block=interp.get("use_block", True),
            vgm_models=interp.get("variogram_models", ["Sph", "Exp", "Gau"]),
            rnor_use=rnor.get("use", True),
            rnor_wet=rnor.get("wet_threshold", 1.0),
            rnor_smooth=rnor.get("smoothing", True),
            shapefile_path=paths.get("shapefile_path"),
            dem_file=paths.get("dem_file"),
            auxvar=merging.get("auxiliary_variables") or merging.get("covariables"),
            global_mrg_opts=(
                exp.get("merging_options")
                or exp.get("global_merging_options")
                or exp.get("global_options")
            ),
            log_dir=log_dir,
        )
        total_time += t3
        consolidate_daily_files(out_dir, "rr_mrg_")

        # Verificacion estricta de completitud post-fusion (100% de dias requeridos)
        mrg_complete, _, mrg_count, mrg_total = check_daily_files_coverage(
            out_dir, "rr_mrg_", start_date, end_date
        )
        if not mrg_complete:
            err_msg = f"Fusion espacial incompleta: se generaron {mrg_count} de {mrg_total} archivos diarios requeridos."
            return 1, out3, (err3 + "\n" + err_msg).strip(), total_time

        return rc3, out3, err3, total_time

    def _run_temperature_experiment(
        self, exp: Dict[str, Any], out_dir: Path, log_dir: Path
    ) -> tuple[int, str, str, float]:
        paths = exp.get("paths", {})
        period = exp.get("period", {})
        start_date = str(period.get("start_date", "19910101"))
        end_date = str(period.get("end_date", "20201231"))
        merging = exp.get("merging", {})
        interp = merging.get("interpolation", {})
        if not interp and "interp_method" in merging:
            interp = {"method": merging["interp_method"]}
        elif not interp and isinstance(merging.get("passes"), list) and len(merging["passes"]) > 0:
            first_pass = merging["passes"][0]
            if isinstance(first_pass, dict) and "interp_method" in first_pass:
                interp = {"method": first_pass["interp_method"]}
        bias_cfg = exp.get("bias_correction", {}) or {}

        var_type = str(exp.get("variable_type", exp.get("id", "tmax"))).lower()
        var_prefix = "tmin" if ("tmin" in var_type or "tn" in var_type or "min" in var_type) else "tmax"
        eff_var_id = paths.get("var_id", "temp")
        dem_file = paths.get("dem_file")
        total_time = 0.0

        # 5-Step Canonical CDT Pipeline for Temperature:
        # Step 1: Compute Downscaling Coefficients (if DEM provided)
        # Step 2: Downscaling Reanalysis Grids (if DEM provided)
        # Step 3: Compute Bias Coefficients
        # Step 4: Apply Bias Correction
        # Step 5: Merging Data

        effective_down_dir = paths.get("satellite_dir", "")
        effective_down_format = paths.get("satellite_format", f"{var_prefix}_%s%s%s.nc")

        if dem_file and Path(dem_file).exists():
            # Step 1: Compute Downscaling Coefficients
            down_dir = out_dir / "down_coeffs"
            cand_down_rds = list(down_dir.rglob("STN_DEM_GLM_COEF.rds"))
            if cand_down_rds and cand_down_rds[0].stat().st_size > 500:
                print(f"  --> [Paso 1/5] [Cache] Coeficientes de desescalado ya calculados previamente.")
                down_coef_file = cand_down_rds[0]
            else:
                down_dir.mkdir(parents=True, exist_ok=True)
                print(f"  --> [Paso 1/5] Calculando coeficientes de desescalado termico (Lapse Rate)...")
                rc0a, out0a, err0a, t0a = self.bridge.compute_downscaling_coefficients_temp(
                    time_step=exp.get("time_step", "daily"),
                    station_file=paths.get("stations_file", ""),
                    dem_file=dem_file,
                    output_dir=down_dir,
                    base_period_all_years=True,
                    start_year=int(str(start_date)[:4]),
                    end_year=int(str(end_date)[:4]),
                    log_dir=log_dir,
                )
                total_time += t0a
                if rc0a != 0:
                    return rc0a, out0a, err0a, total_time
                cand_down_rds = list(down_dir.rglob("STN_DEM_GLM_COEF.rds"))
                down_coef_file = cand_down_rds[0] if cand_down_rds else (down_dir / "STN_DEM_GLM_COEF.rds")

            # Step 2: Downscale Reanalysis Grids
            downscaled_dir = out_dir / "downscaled"
            down_complete, resume_down_date, down_count, down_total = check_daily_files_coverage(
                downscaled_dir, f"{var_prefix}_down_", start_date, end_date
            )
            if down_complete:
                print(f"  --> [Paso 2/5] [Cache] Grillas desescaladas ya completas ({down_count}/{down_total}).")
            else:
                step2_start = resume_down_date or start_date
                if resume_down_date and resume_down_date != start_date:
                    print(f"  --> [Paso 2/5] [Resume] Reanudando desescalado desde {step2_start} ({down_count} dias procesados)...")
                else:
                    print(f"  --> [Paso 2/5] Desescalando grillas termometricas a resolucion del DEM...")
                rc0b, out0b, err0b, t0b = self.bridge.downscale_temperature(
                    time_step=exp.get("time_step", "daily"),
                    start_date=step2_start,
                    end_date=end_date,
                    netcdf_dir=paths.get("satellite_dir", ""),
                    netcdf_format=paths.get("satellite_format", f"{var_prefix}_%s%s%s.nc"),
                    down_coef_file=down_coef_file,
                    dem_file=dem_file,
                    output_dir=downscaled_dir,
                    var_id=eff_var_id,
                    output_format=f"{var_prefix}_down_%s%s%s.nc",
                    log_dir=log_dir,
                )
                total_time += t0b
                if rc0b != 0:
                    return rc0b, out0b, err0b, total_time

            effective_down_dir = consolidate_daily_files(downscaled_dir, f"{var_prefix}_down_")
            effective_down_format = f"{var_prefix}_down_%s%s%s.nc"
        else:
            print(f"  --> [Paso 1-2/5] Sin archivo DEM especificado. Utilizando grillas reanalisis directas.")

        # Step 3: Compute Bias Coefficients
        bias_method = str(bias_cfg.get("method", "mbvar")).lower()
        effective_adj_dir = effective_down_dir
        effective_adj_format = effective_down_format

        if bias_method and bias_method not in ("none", "null", "false"):
            bias_coeffs_dir = out_dir / "bias_coeffs"
            b_interp = bias_cfg.get("interpolation", {})
            if not b_interp and "interp_method" in bias_cfg:
                b_interp = {"method": bias_cfg["interp_method"]}

            cand_rds = [f for f in bias_coeffs_dir.rglob("*.rds") if f.is_file()]
            if cand_rds and cand_rds[0].stat().st_size > 500:
                print(f"  --> [Paso 3/5] [Cache] Coeficientes de sesgo ya calculados previamente.")
                actual_bias_dir = cand_rds[0].parent
            else:
                bias_coeffs_dir.mkdir(parents=True, exist_ok=True)
                print(f"  --> [Paso 3/5] Calculando coeficientes de sesgo termico ({bias_method})...")
                rc1, out1, err1, t1 = self.bridge.compute_bias_coefficients(
                    variable_type="temperature",
                    time_step=exp.get("time_step", "daily"),
                    station_file=paths.get("stations_file", ""),
                    netcdf_dir=effective_down_dir,
                    netcdf_format=effective_down_format,
                    output_dir=bias_coeffs_dir,
                    bias_method=bias_method,
                    distr_name=bias_cfg.get("distribution") or bias_cfg.get("distr") or "norm",
                    interp_method=b_interp.get("method", "okr"),
                    nmin=b_interp.get("nmin", 4),
                    nmax=b_interp.get("nmax", 12),
                    maxdist=b_interp.get("maxdist", 3.5),
                    use_block=b_interp.get("use_block", True),
                    vgm_models=b_interp.get("variogram_models", ["Sph", "Exp", "Gau", "Pen"]),
                    dem_file=dem_file,
                    var_id=eff_var_id,
                    start_year=int(str(start_date)[:4]),
                    end_year=int(str(end_date)[:4]),
                    global_bias_opts=(
                        exp.get("biascoeff_options")
                        or exp.get("bias_options")
                        or exp.get("global_bias_options")
                        or exp.get("global_options")
                    ),
                    log_dir=log_dir,
                )
                total_time += t1
                if rc1 != 0:
                    return rc1, out1, err1, total_time

                cand_rds = [f for f in bias_coeffs_dir.rglob("*.rds") if f.is_file()]
                actual_bias_dir = cand_rds[0].parent if cand_rds else bias_coeffs_dir

            # Step 4: Apply Bias Correction
            adj_dir = out_dir / "bias_adjusted"
            adj_complete, resume_adj_date, adj_count, adj_total = check_daily_files_coverage(
                adj_dir, f"{var_prefix}_adj_", start_date, end_date
            )
            if adj_complete:
                print(f"  --> [Paso 4/5] [Cache] Grillas termometricas ajustadas ya completas ({adj_count}/{adj_total}).")
            else:
                step4_start = resume_adj_date or start_date
                if resume_adj_date and resume_adj_date != start_date:
                    print(f"  --> [Paso 4/5] [Resume] Reanudando ajuste de sesgo desde {step4_start} ({adj_count} dias procesados)...")
                else:
                    print(f"  --> [Paso 4/5] Aplicando ajuste de sesgo a grillas termometricas desescaladas...")
                rc2, out2, err2, t2 = self.bridge.apply_bias_correction_temp(
                    time_step=exp.get("time_step", "daily"),
                    start_date=step4_start,
                    end_date=end_date,
                    netcdf_dir=effective_down_dir,
                    netcdf_format=effective_down_format,
                    bias_dir=actual_bias_dir,
                    bias_format=None,
                    bias_method=bias_method,
                    output_dir=adj_dir,
                    var_id=eff_var_id,
                    output_format=f"{var_prefix}_adj_%s%s%s.nc",
                    log_dir=log_dir,
                )
                total_time += t2
                if rc2 != 0:
                    return rc2, out2, err2, total_time

            effective_adj_dir = consolidate_daily_files(adj_dir, f"{var_prefix}_adj_")
            effective_adj_format = f"{var_prefix}_adj_%s%s%s.nc"

        # Step 5: Merging Data
        consolidate_daily_files(out_dir, f"{var_prefix}_mrg_")
        mrg_complete, resume_mrg_date, mrg_count, mrg_total = check_daily_files_coverage(
            out_dir, f"{var_prefix}_mrg_", start_date, end_date
        )
        if mrg_complete:
            print(f"  --> [Paso 5/5] [Cache] Fusion espacial ya completada previamente ({mrg_count}/{mrg_total}).")
            return 0, "Cached", "", total_time

        if resume_mrg_date and resume_mrg_date != start_date:
            print(f"  --> [Paso 5/5] [Resume] Reanudando fusion espacial ({mrg_count} de {mrg_total} dias ya procesados)...")
        else:
            print(f"  --> [Paso 5/5] Ejecutando fusion espacial final (Merging)...")

        m_method = str(merging.get("method", "RK")).upper()
        if m_method == "BARNES":
            m_method_clean = "SBA"
            interp_method_clean = "barnes"
        elif m_method in ("RK", "REGR.KRIGING", "REGR_KRIGING"):
            m_method_clean = "RK"
            interp_method_clean = interp.get("method") or "okr"
            if interp_method_clean.lower() in ("regr.kriging", "regr_kriging"):
                interp_method_clean = "okr"
        else:
            m_method_clean = "SBA"
            interp_method_clean = interp.get("method") or "idw"

        rc3, out3, err3, t3 = self.bridge.merge_temperature(
            time_step=exp.get("time_step", "daily"),
            start_date=start_date,
            end_date=end_date,
            station_file=paths.get("stations_file", ""),
            netcdf_dir=effective_adj_dir,
            netcdf_format=effective_adj_format,
            output_dir=out_dir,
            var_id=eff_var_id,
            merge_method=m_method_clean,
            nrun=merging.get("nrun", 3 if isinstance(merging.get("passes"), list) and len(merging.get("passes")) > 1 else 1),
            pass_ratios=merging.get("passes", [1.0, 0.75, 0.5]),
            interp_method=interp_method_clean,
            nmin=interp.get("nmin", 4),
            nmax=interp.get("nmax", 12),
            maxdist=interp.get("maxdist", 3.5),
            use_block=interp.get("use_block", True),
            vgm_models=interp.get("variogram_models", ["Sph", "Exp", "Gau", "Pen"]),
            dem_file=dem_file,
            auxvar=merging.get("auxiliary_variables") or merging.get("covariables"),
            global_mrg_opts=(
                exp.get("merging_options")
                or exp.get("global_merging_options")
                or exp.get("global_options")
            ),
            log_dir=log_dir,
        )
        total_time += t3
        consolidate_daily_files(out_dir, f"{var_prefix}_mrg_")

        # Verificacion estricta de completitud post-fusion (100% de dias requeridos)
        mrg_complete, _, mrg_count, mrg_total = check_daily_files_coverage(
            out_dir, f"{var_prefix}_mrg_", start_date, end_date
        )
        if not mrg_complete:
            err_msg = f"Fusion espacial incompleta: se generaron {mrg_count} de {mrg_total} archivos diarios requeridos."
            return 1, out3, (err3 + "\n" + err_msg).strip(), total_time

        return rc3, out3, err3, total_time

    def _print_execution_summary(self) -> None:
        print("\n" + "=" * 80)
        print("               RESUMEN DE EJECUCIÓN DE EXPERIMENTOS CDT")
        print("=" * 80)
        for res in self.results_summary:
            status_tag = f"[{res.get('status', 'DONE')}]"
            t_str = res.get("time_formatted", f"{res.get('time_sec', 0.0):.2f}s")
            desc = res.get("description", "")
            print(f"  {status_tag:18} | {res['id']:32} | Tiempo: {t_str:>11} | {desc}")
        if len(self.results_summary) > 1:
            total_sec = sum(res.get("time_sec", 0.0) for res in self.results_summary)
            print("-" * 80)
            print(f"  TIEMPO TOTAL ACUMULADO DE LA SUITE: {format_duration(total_sec)} ({total_sec:.2f}s)")
        print("=" * 80 + "\n")


def main() -> None:
    """Command-line entry point for experiment runner."""
    parser = argparse.ArgumentParser(
        description="Lanzador de Experimentos CDT (Precipitación, Tmax y Tmin 1991-2020)"
    )
    parser.add_argument(
        "--config", "-c",
        type=str,
        default=None,
        help="Ruta al archivo YAML de experimento, archivo batch o carpeta con archivos YAML.",
    )
    parser.add_argument(
        "--suite", "-s", "--variable", "-v",
        type=str,
        choices=["rainfall", "tmax", "tmin", "all"],
        default=None,
        help="Ejecuta una suite completa predefinida: 'rainfall' (10 exp), 'tmax' (8 exp), 'tmin' (8 exp) o 'all' (26 exp).",
    )
    parser.add_argument(
        "--base-config", "-b",
        type=str,
        default="config/global_config.yaml",
        help="Ruta al archivo de configuracion base/comun con rutas y parametros globales.",
    )
    parser.add_argument(
        "--rscript",
        type=str,
        default=None,
        help="Ruta personalizada al ejecutable Rscript (opcional).",
    )
    parser.add_argument(
        "--region", "--domain",
        type=str,
        choices=["ca", "rd", "all"],
        default="ca",
        help="Dominio territorial a procesar: 'ca' (Centroamérica), 'rd' (República Dominicana) o 'all' (General). Por defecto 'ca'.",
    )
    parser.add_argument(
        "--cores", "--nb-cores",
        type=str,
        default="auto",
        help="Número de núcleos CPU para cálculo paralelo ('auto' detecta N-1 núcleos dinámicamente, o pasar un número entero como 8).",
    )
    parser.add_argument(
        "--check-env",
        action="store_true",
        help="Ejecuta el diagnóstico y verificación del entorno de R, Rtools/GCC y paquetes requeridos.",
    )
    parser.add_argument(
        "--check-data", "--check-inputs", "--validate-inputs", "--verify-data",
        action="store_true",
        dest="check_data",
        help="Verifica exhaustivamente la presencia, formato y completitud de todos los datos e insumos (estaciones, DEM, shapefile, grillas diarias 1991-2020).",
    )
    parser.add_argument(
        "--benchmark", "--generate-report",
        action="store_true",
        help="Genera el reporte de benchmark, ranking multicriterio (leaderboard), gráficos de Taylor/boxplots y dashboard HTML interactivo.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Fuerza la reejecución completa de experimentos e ignora checkpoints o archivos previamente generados.",
    )

    args = parser.parse_args()

    # Determine regional directory names
    exp_out_dir = PROJECT_ROOT / "output" / f"experiments_{args.region}" if args.region in ("ca", "rd") else PROJECT_ROOT / "output" / "experiments"
    bench_out_dir = PROJECT_ROOT / "output" / f"benchmark_{args.region}" if args.region in ("ca", "rd") else PROJECT_ROOT / "output" / "benchmark"

    # 1. Modo Verificación de Entorno (--check-env)
    # Siempre ejecuta usando únicamente la biblioteca estándar de Python
    if args.check_env:
        status = check_system_environment(rscript_path=args.rscript)
        print_environment_report(status)
        if not args.suite and not args.config and not args.check_data:
            sys.exit(0 if status.get("is_ready") else 1)

    # 2. Para el resto de operaciones, verificar que las dependencias de Python estén instaladas
    if not _check_python_requirements():
        sys.exit(1)

    # 3. Modo Verificación de Datos e Insumos (--check-data / --validate-inputs)
    if args.check_data:
        from launcher.data_preprocessor import validate_project_inputs
        base_path = Path(args.base_config) if args.base_config else PROJECT_ROOT / "config" / "global_config.yaml"
        res = validate_project_inputs(config_path_or_dict=base_path, region=args.region, auto_split_3d=False, verbose=True)
        if not args.suite and not args.config:
            sys.exit(0 if res.get("is_ready") else 1)

    if args.benchmark:
        from launcher.benchmark_reporter import run_full_benchmark_suite
        run_full_benchmark_suite(
            experiments_dir=exp_out_dir,
            output_dir=bench_out_dir
        )
        return

    suite_targets = []
    if args.suite:
        if args.suite == "rainfall":
            suite_targets.append(PROJECT_ROOT / "config" / "experiments_rainfall")
        elif args.suite == "tmax":
            suite_targets.append(PROJECT_ROOT / "config" / "experiments_tmax")
        elif args.suite == "tmin":
            suite_targets.append(PROJECT_ROOT / "config" / "experiments_tmin")
        elif args.suite == "all":
            suite_targets.append(PROJECT_ROOT / "config" / "experiments_rainfall")
            suite_targets.append(PROJECT_ROOT / "config" / "experiments_tmax")
            suite_targets.append(PROJECT_ROOT / "config" / "experiments_tmin")
    elif args.config:
        suite_targets.append(Path(args.config))
    elif not args.check_env and not args.check_data:
        # Default fallback: run rainfall baseline
        suite_targets.append(PROJECT_ROOT / "config" / "experiments_rainfall" / "EXP_R01_SBA_IDW_Baseline.yaml")

    all_summaries = []
    for target in suite_targets:
        runner = ExperimentRunner(
            config_target=target,
            base_config_path=args.base_config,
            region=args.region,
            nb_cores=args.cores,
            rscript_path=args.rscript,
        )
        res = runner.run_all_experiments(force=args.force)
        all_summaries.extend(res)

    # Auto-generate benchmark report if any experiments completed
    if all_summaries:
        try:
            from launcher.benchmark_reporter import run_full_benchmark_suite
            run_full_benchmark_suite(
                experiments_dir=exp_out_dir,
                output_dir=bench_out_dir
            )
        except Exception as e:
            print(f"[!] Advertencia al generar reporte de benchmark post-corrida: {e}")


if __name__ == "__main__":
    main()

