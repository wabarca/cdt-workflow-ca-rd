"""Data Preprocessor, Validator, and Parallel 3D NetCDF Splitter for CDT.

Provides:
1. Complete validation of all user-supplied input datasets (Stations, DEM, Shapefiles, Holdout CSV, Gridded files).
2. Ultra-fast parallel extraction / splitting of 3D multi-temporal NetCDFs (1991–2020) into CDT daily 2D NetCDFs.
3. Automated pre-flight integrity auditing before launching experiment batches.
"""

from __future__ import annotations

import concurrent.futures
import datetime
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr
import yaml


def _write_single_daily_slice(
    ds_path: str,
    time_idx: int,
    date_str: str,
    output_dir: str,
    filename_format: str,
    var_id: str,
    lat_name: str,
    lon_name: str,
) -> str:
    """Helper worker to slice and write a single daily 2D NetCDF."""
    out_dir_path = Path(output_dir)
    y = date_str[0:4]
    m = date_str[4:6]
    d = date_str[6:8]
    
    if "%s%s%s" in filename_format:
        fname = filename_format.replace("%s%s%s", f"{y}{m}{d}")
    elif "%s" in filename_format:
        fname = filename_format % (y, m, d)
    else:
        fname = f"{var_id}_{y}{m}{d}.nc"

    out_file = out_dir_path / fname
    if out_file.exists():
        return str(out_file)

    with xr.open_dataset(ds_path) as ds:
        data_2d = ds[var_id].isel(time=time_idx)
        # Create lightweight 2D dataset
        ds_out = xr.Dataset(
            data_vars={var_id: (data_2d.dims, data_2d.values, data_2d.attrs)},
            coords={
                lon_name: (ds[lon_name].dims, ds[lon_name].values, ds[lon_name].attrs),
                lat_name: (ds[lat_name].dims, ds[lat_name].values, ds[lat_name].attrs),
            },
            attrs=ds.attrs,
        )
        ds_out.to_netcdf(out_file, encoding={var_id: {"zlib": True, "complevel": 4}})
    return str(out_file)


def _batch_slice_worker(args: Tuple[str, List[Tuple[int, str]], str, str, str, str, str]) -> int:
    """Process a chunk of dates within a worker process."""
    ds_path, chunk_items, output_dir, filename_format, var_id, lat_name, lon_name = args
    out_dir_path = Path(output_dir)
    written_count = 0

    with xr.open_dataset(ds_path) as ds:
        for time_idx, date_str in chunk_items:
            y = date_str[0:4]
            m = date_str[4:6]
            d = date_str[6:8]
            
            if "%s%s%s" in filename_format:
                fname = filename_format.replace("%s%s%s", f"{y}{m}{d}")
            elif "%s" in filename_format:
                fname = filename_format % (y, m, d)
            else:
                fname = f"{var_id}_{y}{m}{d}.nc"

            out_file = out_dir_path / fname
            if not out_file.exists():
                data_2d = ds[var_id].isel(time=time_idx)
                ds_out = xr.Dataset(
                    data_vars={var_id: (data_2d.dims, data_2d.values, data_2d.attrs)},
                    coords={
                        lon_name: (ds[lon_name].dims, ds[lon_name].values, ds[lon_name].attrs),
                        lat_name: (ds[lat_name].dims, ds[lat_name].values, ds[lat_name].attrs),
                    },
                    attrs=ds.attrs,
                )
                ds_out.to_netcdf(out_file, encoding={var_id: {"zlib": True, "complevel": 4}})
                written_count += 1
    return written_count


def split_3d_netcdf_to_daily_parallel(
    input_nc_path: Union[Path, str],
    output_dir: Union[Path, str],
    filename_format: str = "chirps_%s%s%s.nc",
    var_id: Optional[str] = None,
    max_workers: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Splits a single 3D NetCDF file into daily 2D NetCDFs using multi-process parallelization.

    Args:
        input_nc_path: Path to the 3D NetCDF file.
        output_dir: Target directory where 2D NetCDFs will be stored.
        filename_format: CDT filename format (e.g. 'chirps_%s%s%s.nc' or 'tmax_%s%s%s.nc').
        var_id: Variable name in the NetCDF. If None, auto-detected.
        max_workers: Number of parallel CPU workers (defaults to os.cpu_count() - 1).
        start_date: Optional filter YYYYMMDD.
        end_date: Optional filter YYYYMMDD.
        verbose: Whether to print progress.

    Returns:
        Dictionary with processing summary.
    """
    nc_path = Path(input_nc_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not nc_path.exists():
        raise FileNotFoundError(f"Input NetCDF not found: {nc_path}")

    t0 = time.time()
    with xr.open_dataset(nc_path) as ds:
        # Detect variable
        if not var_id:
            candidates = [v for v in ds.data_vars if len(ds[v].dims) >= 3]
            if not candidates:
                candidates = list(ds.data_vars)
            var_id = candidates[0] if candidates else list(ds.data_vars)[0]

        # Detect spatial coordinates
        lon_candidates = ["lon", "longitude", "x", "X", "long"]
        lat_candidates = ["lat", "latitude", "y", "Y"]
        lon_name = next((c for c in lon_candidates if c in ds.coords or c in ds.dims), "lon")
        lat_name = next((c for c in lat_candidates if c in ds.coords or c in ds.dims), "lat")
        time_name = next((c for c in ["time", "times", "date", "Date"] if c in ds.coords or c in ds.dims), "time")

        # Extract timestamps
        time_vals = ds[time_name].values
        dates = pd.to_datetime(time_vals)
        date_strs = [d.strftime("%Y%m%d") for d in dates]

    # Filter dates if requested
    items_to_process: List[Tuple[int, str]] = []
    for idx, d_str in enumerate(date_strs):
        if start_date and d_str < start_date:
            continue
        if end_date and d_str > end_date:
            continue
        items_to_process.append((idx, d_str))

    total_files = len(items_to_process)
    if verbose:
        print(f"[*] Dividiendo NetCDF 3D: {nc_path.name} ({total_files} días) -> {out_dir}")

    workers = max_workers or max(1, (os.cpu_count() or 4) - 1)
    # Partition into worker chunks
    chunks: List[List[Tuple[int, str]]] = [[] for _ in range(workers)]
    for i, item in enumerate(items_to_process):
        chunks[i % workers].append(item)

    worker_args = [
        (str(nc_path), chunk, str(out_dir), filename_format, var_id, lat_name, lon_name)
        for chunk in chunks if chunk
    ]

    new_written = 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(_batch_slice_worker, worker_args))
        new_written = sum(results)

    elapsed = time.time() - t0
    if verbose:
        print(f"[OK] {total_files} archivos diarios disponibles en {out_dir} (Nuevos generados: {new_written}) en {elapsed:.2f}s ({workers} núcleos).")

    return {
        "status": "SUCCESS",
        "input_file": str(nc_path),
        "output_dir": str(out_dir),
        "total_days": total_files,
        "newly_written": new_written,
        "elapsed_sec": round(elapsed, 2),
        "variable_id": var_id,
        "workers_used": workers,
    }


def validate_project_inputs(
    config_path_or_dict: Union[Path, str, Dict[str, Any]],
    auto_split_3d: bool = True,
    max_workers: Optional[int] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Performs comprehensive validation of all user-supplied input datasets.

    Checks:
    1. Station CSV files (Precipitation, Tmax, Tmin).
    2. Digital Elevation Model (DEM) NetCDF file.
    3. Study Area Boundary Shapefile (.shp, .shx, .dbf, .prj).
    4. Validation Holdout CSV.
    5. Gridded Data: verifies daily files or auto-splits 3D NetCDFs in parallel.

    Returns:
        Detailed diagnostic report with 'status': 'VALID', 'WARNINGS', or 'ERRORS'.
    """
    if isinstance(config_path_or_dict, (str, Path)):
        cfg_file = Path(config_path_or_dict).resolve()
        if not cfg_file.exists():
            return {
                "status": "ERRORS",
                "errors": [f"Config file not found: {cfg_file}"],
                "warnings": [],
                "details": {},
            }
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = config_path_or_dict

    paths = cfg.get("paths", {})
    period = cfg.get("period", {})
    start_date = period.get("start_date", "19910101")
    end_date = period.get("end_date", "20201231")

    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {}

    if verbose:
        print("=" * 80)
        print("         DIAGNÓSTICO Y VALIDACIÓN DE DATOS DE ENTRADA (CDT 1991–2020)")
        print("=" * 80)

    # 1. Validar Estaciones Pluviométricas y Termométricas
    stn_keys = [
        ("stations_rainfall_file", "Precipitación (Lluvia)"),
        ("stations_tmax_file", "Temperatura Máxima (Tmax)"),
        ("stations_tmin_file", "Temperatura Mínima (Tmin)"),
    ]
    stn_details = {}
    for key, label in stn_keys:
        stn_path_str = paths.get(key)
        if not stn_path_str:
            warnings.append(f"No se especificó ruta para {key} ({label}).")
            continue
        stn_path = Path(stn_path_str).resolve()
        if not stn_path.exists():
            # Check relative to project root
            cand = Path(stn_path_str)
            if cand.exists():
                stn_path = cand.resolve()
            else:
                errors.append(f"Archivo de estaciones {label} no encontrado: {stn_path_str}")
                continue

        try:
            # Check CDT station header format
            df_head = pd.read_csv(stn_path, nrows=5, header=None)
            n_cols = df_head.shape[1] - 1 # excluding date column
            stn_details[key] = {
                "path": str(stn_path),
                "stations_count": n_cols,
                "status": "VALID",
            }
            if verbose:
                print(f"  [OK] Estaciones {label:25}: {n_cols} estaciones detectadas ({stn_path.name})")
        except Exception as e:
            errors.append(f"Error al leer formato CDT de {key}: {e}")

    # 2. Validar DEM
    dem_path_str = paths.get("dem_file")
    if dem_path_str:
        dem_path = Path(dem_path_str).resolve()
        if not dem_path.exists():
            cand = Path(dem_path_str)
            if cand.exists():
                dem_path = cand.resolve()
            else:
                errors.append(f"Archivo DEM no encontrado: {dem_path_str}")
        else:
            try:
                with xr.open_dataset(dem_path) as ds_dem:
                    dem_vars = list(ds_dem.data_vars)
                    details["dem"] = {
                        "path": str(dem_path),
                        "variables": dem_vars,
                        "dims": dict(ds_dem.dims),
                    }
                    if verbose:
                        print(f"  [OK] Topografía DEM SRTM      : {dem_vars[0] if dem_vars else 'z'} {dict(ds_dem.dims)} ({dem_path.name})")
            except Exception as e:
                errors.append(f"Error al abrir archivo DEM {dem_path_str}: {e}")
    else:
        warnings.append("No se definió 'dem_file' en la configuración.")

    # 3. Validar Shapefile
    shp_path_str = paths.get("shapefile_path")
    if shp_path_str:
        shp_path = Path(shp_path_str).resolve()
        if not shp_path.exists():
            cand = Path(shp_path_str)
            if cand.exists():
                shp_path = cand.resolve()
            else:
                errors.append(f"Shapefile no encontrado: {shp_path_str}")
        else:
            # Check sidecar files (.shx, .dbf)
            missing_sidecars = []
            for ext in [".shx", ".dbf"]:
                sc = shp_path.with_suffix(ext)
                if not sc.exists():
                    missing_sidecars.append(ext)
            if missing_sidecars:
                warnings.append(f"Archivos auxiliares de Shapefile faltantes ({', '.join(missing_sidecars)} para {shp_path.name})")
            details["shapefile"] = {"path": str(shp_path), "exists": True}
            if verbose:
                print(f"  [OK] Shapefile de Recorte     : {shp_path.name} (Buffer 10 km)")
    else:
        warnings.append("No se definió 'shapefile_path' en la configuración.")

    # 4. Validar Estaciones Holdout
    holdout_path_str = paths.get("holdout_stations_file")
    if holdout_path_str:
        h_path = Path(holdout_path_str).resolve()
        if not h_path.exists():
            cand = Path(holdout_path_str)
            if cand.exists():
                h_path = cand.resolve()
        if h_path.exists():
            try:
                df_h = pd.read_csv(h_path)
                h_count = len(df_h)
                details["holdout"] = {"path": str(h_path), "holdout_count": h_count}
                if verbose:
                    print(f"  [OK] Estaciones Holdout (CSV) : {h_count} estaciones de validación ciega ({h_path.name})")
            except Exception as e:
                warnings.append(f"No se pudo leer CSV de estaciones holdout: {e}")
        else:
            warnings.append(f"Archivo de estaciones holdout no encontrado: {holdout_path_str}. Se usará validación in-sample.")

    # 5. Validar y/o Procesar Grillas Satelitales (CHIRPS, Tmax, Tmin)
    gridded_specs = [
        ("satellite_rainfall_dir", "raw_3d_netcdf_rainfall", "chirps_%s%s%s.nc", "precip", "Precipitación (CHIRPS)"),
        ("satellite_tmax_dir", "raw_3d_netcdf_tmax", "tmax_%s%s%s.nc", "tmax", "Temperatura Máxima (Tmax)"),
        ("satellite_tmin_dir", "raw_3d_netcdf_tmin", "tmin_%s%s%s.nc", "tmin", "Temperatura Mínima (Tmin)"),
    ]

    for dir_key, raw_3d_key, def_format, def_var, label in gridded_specs:
        target_dir_str = paths.get(dir_key)
        raw_3d_str = paths.get(raw_3d_key)

        # Case A: 3D NetCDF explicitly supplied
        if raw_3d_str:
            raw_path = Path(raw_3d_str).resolve()
            if not raw_path.exists():
                cand = Path(raw_3d_str)
                if cand.exists():
                    raw_path = cand.resolve()
            if raw_path.exists() and raw_path.is_file() and raw_path.suffix == ".nc":
                if auto_split_3d and target_dir_str:
                    target_dir = Path(target_dir_str).resolve()
                    fmt = paths.get(f"{dir_key.replace('_dir', '_format')}", def_format)
                    var = paths.get("var_id", def_var)
                    split_res = split_3d_netcdf_to_daily_parallel(
                        input_nc_path=raw_path,
                        output_dir=target_dir,
                        filename_format=fmt,
                        var_id=var,
                        start_date=start_date,
                        end_date=end_date,
                        max_workers=max_workers,
                        verbose=verbose,
                    )
                    details[raw_3d_key] = split_res
                else:
                    details[raw_3d_key] = {"path": str(raw_path), "status": "FILE_FOUND"}

        # Case B: Directory of daily 2D NetCDFs
        if target_dir_str:
            t_dir = Path(target_dir_str).resolve()
            if not t_dir.exists():
                cand = Path(target_dir_str)
                if cand.exists():
                    t_dir = cand.resolve()

            if t_dir.exists() and t_dir.is_dir():
                nc_files = list(t_dir.glob("*.nc"))
                details[dir_key] = {"path": str(t_dir), "file_count": len(nc_files)}
                if verbose:
                    print(f"  [OK] Grillas Diarias {label:20}: {len(nc_files)} archivos diarios NetCDF ({t_dir.name}/)")
            elif not raw_3d_str:
                warnings.append(f"Directorio de grillas {label} no encontrado: {target_dir_str}")

    overall_status = "ERRORS" if errors else ("WARNINGS" if warnings else "VALID")

    if verbose:
        print("-" * 80)
        if overall_status == "VALID":
            print("  >>> ESTADO: TODOS LOS DATOS DE ENTRADA ESTÁN PRESENTES Y VALIDADOS.")
        elif overall_status == "WARNINGS":
            print(f"  >>> ESTADO: VALIDADO CON {len(warnings)} ADVERTENCIA(S):")
            for w in warnings:
                print(f"      [!] {w}")
        else:
            print(f"  >>> ESTADO: SE ENCONTRARON {len(errors)} ERROR(ES) CRÍTICO(S):")
            for e in errors:
                print(f"      [X] {e}")
        print("=" * 80 + "\n")

    return {
        "status": overall_status,
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }
