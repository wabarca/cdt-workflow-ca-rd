"""Experiment Matrix Runner for CDT in Python.

Loads YAML experiment configurations (single experiment or batches),
executes runs systematically via the CDT bridge, records parameters,
assembles final CF-1.8 compliant 3D NetCDFs, and outputs execution audit reports.
"""

from __future__ import annotations

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
import time
from typing import Any, Dict, List, Optional, Union

from launcher.env_checker import check_system_environment, print_environment_report


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



def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries."""
    merged = dict(base)
    for k, v in override.items():
        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = _deep_merge(merged[k], v)
        else:
            merged[k] = v
    return merged


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
                paths["var_id"] = paths.get("var_id", "tmax")
            elif var_type in ("tmin", "tn", "temp_min", "temperature_min"):
                paths["satellite_dir"] = paths.get("satellite_tmin_dir", paths.get("satellite_temperature_dir", "data/chirts_daily/tmin"))
                paths["satellite_format"] = paths.get("satellite_tmin_format", "tmin_%s%s%s.nc")
                paths["var_id"] = paths.get("var_id", "tmin")
            else:
                paths["satellite_dir"] = paths.get("satellite_temperature_dir", "data/chirts_daily")
                paths["satellite_format"] = paths.get("satellite_temperature_format", "tmax_%s%s%s.nc")
                paths["var_id"] = paths.get("var_id", "temp")

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

    def run_all_experiments(self) -> List[Dict[str, Any]]:
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

            # Create working copy of exp dict with effective training station path
            exp_exec = dict(exp)
            exp_exec["paths"] = dict(paths)
            exp_exec["paths"]["stations_file"] = training_station_file

            t0 = time.time()
            if var_type in ("rainfall", "rain", "precip"):
                ret_code, stdout, stderr, elapsed = self._run_rainfall_experiment(exp_exec, out_dir, log_dir)
            elif var_type in ("temperature", "temp", "tmax", "tmin"):
                ret_code, stdout, stderr, elapsed = self._run_temperature_experiment(exp_exec, out_dir, log_dir)
            else:
                print(f"[!] Unknown variable type: {var_type}. Skipping.")
                continue

            status_str = "SUCCESS" if ret_code == 0 else "FAILED"
            manifest_data["timestamp_end"] = datetime.datetime.now().isoformat()
            manifest_data["execution_time_sec"] = elapsed
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
                    search_dirs = [out_dir, out_dir / "Data_Merged", out_dir / "Merged_Data", out_dir / "Output"]
                    daily_nc_dir = next((d for d in search_dirs if d.exists() and list(d.glob("*.nc"))), out_dir)
                    
                    if list(daily_nc_dir.glob("*.nc")):
                        out_nc_name = post_proc.get("output_filename", f"{var_type}_daily_1991_2020_{exp_id}.nc")
                        assembled_nc_path = out_dir / out_nc_name
                        print(f"  --> Ensamblando archivos NetCDF diarios en producto 3D CF-1.8...")
                        assemble_daily_netcdfs_to_cf18(
                            input_dir=daily_nc_dir,
                            output_netcdf_path=assembled_nc_path,
                            variable_name=paths.get("var_id", "precip" if var_type in ("rainfall", "precip") else "temp"),
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
                    df_metrics, val_summary = evaluate_netcdf_against_stations(
                        netcdf_path=assembled_nc_path,
                        station_file=val_target_file,
                        var_name=paths.get("var_id", "precip" if var_type in ("rainfall", "precip") else "temp"),
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
                "output_dir": str(out_dir),
                "assembled_nc": str(assembled_nc_path) if assembled_nc_path else "N/A",
                "kge": manifest_data.get("validation", {}).get("summary_results", {}).get("mean_kge", "N/A"),
            })

            icon = "[OK]" if ret_code == 0 else "[FAIL]"
            print(f"  >>> {icon} {exp_id} completado con estado {status_str} en {elapsed:.2f}s")

        self._print_execution_summary()
        return self.results_summary

    def _run_rainfall_experiment(
        self, exp: Dict[str, Any], out_dir: Path, log_dir: Path
    ) -> tuple[int, str, str, float]:
        paths = exp.get("paths", {})
        period = exp.get("period", {})
        merging = exp.get("merging", {})
        interp = merging.get("interpolation", {})
        rnor = exp.get("rnor_mask", {})

        return self.bridge.merge_rainfall(
            time_step=exp.get("time_step", "daily"),
            start_date=period.get("start_date", "19910101"),
            end_date=period.get("end_date", "20201231"),
            station_file=paths.get("stations_file", ""),
            netcdf_dir=paths.get("satellite_dir", ""),
            netcdf_format=paths.get("satellite_format", "chirps_%s%s%s.nc"),
            output_dir=out_dir,
            var_id=paths.get("var_id", "precip"),
            merge_method=merging.get("method", "SBA"),
            nrun=merging.get("nrun", 3),
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
            auxvar=merging.get("auxiliary_variables"),
            global_mrg_opts=exp.get("global_options"),
            log_dir=log_dir,
        )

    def _run_temperature_experiment(
        self, exp: Dict[str, Any], out_dir: Path, log_dir: Path
    ) -> tuple[int, str, str, float]:
        paths = exp.get("paths", {})
        period = exp.get("period", {})
        merging = exp.get("merging", {})
        interp = merging.get("interpolation", {})

        return self.bridge.merge_temperature(
            time_step=exp.get("time_step", "daily"),
            start_date=period.get("start_date", "19910101"),
            end_date=period.get("end_date", "20201231"),
            station_file=paths.get("stations_file", ""),
            netcdf_dir=paths.get("satellite_dir", ""),
            netcdf_format=paths.get("satellite_format", "tmax_%s%s%s.nc"),
            output_dir=out_dir,
            var_id=paths.get("var_id", "temp"),
            merge_method=merging.get("method", "RK"),
            nrun=merging.get("nrun", 3),
            pass_ratios=merging.get("passes", [1.0, 0.75, 0.5]),
            interp_method=interp.get("method", "idw"),
            nmin=interp.get("nmin", 8),
            nmax=interp.get("nmax", 24),
            maxdist=interp.get("maxdist", 3.5),
            use_block=interp.get("use_block", True),
            vgm_models=interp.get("variogram_models", ["Sph", "Exp", "Gau", "Pen"]),
            dem_file=paths.get("dem_file"),
            auxvar=merging.get("auxiliary_variables"),
            shapefile_path=paths.get("shapefile_path"),
            global_mrg_opts=exp.get("global_options"),
            log_dir=log_dir,
        )

    def _print_execution_summary(self) -> None:
        print("\n" + "=" * 80)
        print("               RESUMEN DE EJECUCIÓN DE EXPERIMENTOS CDT")
        print("=" * 80)
        for res in self.results_summary:
            status_tag = f"[{res['status']}]"
            print(f"  {status_tag:10} | {res['id']:32} | Tiempo: {res['time_sec']:>6.2f}s | {res['description']}")
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
        res = runner.run_all_experiments()
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

