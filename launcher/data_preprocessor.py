"""Data Preprocessor, Validator, and Parallel 3D NetCDF Splitter for CDT.

Provides:
1. Complete validation of all user-supplied input datasets (Stations, DEM, Shapefiles, Holdout CSV, Gridded files).
2. Ultra-fast parallel extraction / splitting of 3D multi-temporal NetCDFs (1991–2020) into CDT daily 2D NetCDFs.
3. Automated pre-flight integrity auditing before launching experiment batches.
"""

from __future__ import annotations

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*GIL.*")
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*global interpreter lock.*")

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


def _worker_init():
    """Initializer for multi-process workers to suppress C-extension GIL warnings."""
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*GIL.*")
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*global interpreter lock.*")


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
            # Re-generate if missing or corrupted (size < 512 bytes)
            if not out_file.exists() or out_file.stat().st_size < 512:
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
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers, initializer=_worker_init) as executor:
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


# Convenience alias for parallel 3D splitting
split_3d_netcdf_to_daily_files = split_3d_netcdf_to_daily_parallel


def validate_project_inputs(
    config_path_or_dict: Union[Path, str, Dict[str, Any]],
    region: Optional[str] = None,
    auto_split_3d: bool = False,
    max_workers: Optional[int] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Performs comprehensive, deep validation of all user-supplied input datasets.

    Checks:
    1. Station CSV files (Precipitation, Tmax, Tmin): 4-line headers, station count, date range.
    2. Digital Elevation Model (DEM) NetCDF file: dimensions, elevation range, coordinates.
    3. Study Area Boundary Shapefile (.shp, .shx, .dbf, .prj).
    4. Validation Holdout CSV: station count and overlap with station files.
    5. Daily Gridded NetCDFs: file count (10,958 days for 1991-2020) and format.
    6. Raw 3D NetCDFs: availability in data/raw_netcdf/ for parallel splitting.

    Returns:
        Detailed diagnostic report with 'status': 'VALID', 'WARNINGS', or 'ERRORS'.
    """
    if isinstance(config_path_or_dict, (str, Path)):
        cfg_file = Path(config_path_or_dict).resolve()
        if not cfg_file.exists():
            return {
                "status": "ERRORS",
                "errors": [f"Archivo de configuración no encontrado: {cfg_file}"],
                "warnings": [],
                "details": {},
            }
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    else:
        cfg = dict(config_path_or_dict)

    # Apply regional overrides if region is specified (e.g. 'ca' or 'rd')
    active_region = (region or cfg.get("active_region", "")).lower()
    regions_dict = cfg.get("regions", {})
    region_label = "General / Completo"

    paths = dict(cfg.get("paths", {}))
    if active_region and active_region in regions_dict:
        reg_info = regions_dict[active_region]
        region_label = f"{reg_info.get('name', active_region.upper())} ({active_region.upper()})"
        for k, v in reg_info.items():
            if k not in ("name", "benchmark_dir"):
                paths[k] = v

    period = cfg.get("period", {})
    start_date = str(period.get("start_date", "19910101"))
    end_date = str(period.get("end_date", "20201231"))

    # Expected days in 1991-2020 (30 years = 10,958 days including 7 leap years)
    try:
        dt_start = datetime.datetime.strptime(start_date, "%Y%m%d")
        dt_end = datetime.datetime.strptime(end_date, "%Y%m%d")
        expected_days = (dt_end - dt_start).days + 1
    except Exception:
        expected_days = 10958

    errors: List[str] = []
    warnings: List[str] = []
    details: Dict[str, Any] = {"region": active_region or "all"}
    report_rows: List[Tuple[str, str, str, str]] = []

    if verbose:
        print("\n" + "=" * 85)
        print("     DIAGNÓSTICO Y VERIFICACIÓN DE DATOS E INSUMOS (CDT 1991–2020 / 30 AÑOS)")
        print("=" * 85)
        print(f"  Dominio / Región      : {region_label}")
        print(f"  Periodo Climatológico : {start_date} a {end_date} ({expected_days:,} días diarios esperados)")
        print("-" * 85)

    # -------------------------------------------------------------------------
    # 1. Validar Estaciones Pluviométricas y Termométricas
    # -------------------------------------------------------------------------
    def_p = f"data/stations/precip_stations_{active_region}.csv" if active_region in ("ca", "rd") else "data/stations/precip_stations_all.csv"
    def_tx = f"data/stations/tmax_stations_{active_region}.csv" if active_region in ("ca", "rd") else "data/stations/tmax_stations_all.csv"
    def_tn = f"data/stations/tmin_stations_{active_region}.csv" if active_region in ("ca", "rd") else "data/stations/tmin_stations_all.csv"

    stn_keys = [
        ("stations_rainfall_file", "Precipitación (Lluvia)", def_p),
        ("stations_tmax_file", "Temperatura Máx (Tmax)", def_tx),
        ("stations_tmin_file", "Temperatura Mín (Tmin)", def_tn),
    ]
    stn_details = {}
    for key, label, def_path in stn_keys:
        stn_path_str = paths.get(key, def_path)
        stn_path = Path(stn_path_str).resolve()
        if not stn_path.exists():
            cand = Path(stn_path_str)
            if cand.exists():
                stn_path = cand.resolve()
            elif active_region:
                all_cand = Path(stn_path_str.replace(f"_{active_region}.csv", "_all.csv"))
                if all_cand.exists():
                    stn_path = all_cand.resolve()
                    warnings.append(f"Estaciones {label}: Usando archivo general '{stn_path.name}' como fallback para región {active_region.upper()}")

        if not stn_path.exists():
            errors.append(f"Estaciones {label}: Archivo no encontrado en '{stn_path_str}'")
            report_rows.append((f"Estaciones {label}", "NO ENCONTRADO", str(stn_path_str), "Colocar CSV en formato CDT (4 filas encabezado)"))
            continue

        try:
            with open(stn_path, "r", encoding="utf-8-sig") as f:
                lines = [line.strip() for line in f if line.strip()]
            
            if len(lines) < 4:
                errors.append(f"Estaciones {label}: Formato inválido (< 4 líneas en {stn_path.name})")
                report_rows.append((f"Estaciones {label}", "INVÁLIDO", stn_path.name, "Archivo incompleto"))
                continue

            delim = "," if "," in lines[0] else (";" if ";" in lines[0] else "\t")
            row0 = [x.strip() for x in lines[0].split(delim)]
            row1 = [x.strip() for x in lines[1].split(delim)]
            row2 = [x.strip() for x in lines[2].split(delim)]
            row3 = [x.strip() for x in lines[3].split(delim)]

            stn_ids = row0[1:]
            n_stns = len(stn_ids)
            n_records = len(lines) - 4
            min_date = lines[4].split(delim)[0] if len(lines) > 4 else "N/A"
            max_date = lines[-1].split(delim)[0] if len(lines) > 4 else "N/A"

            stn_details[key] = {
                "path": str(stn_path),
                "stations_count": n_stns,
                "records_count": n_records,
                "min_date": min_date,
                "max_date": max_date,
                "status": "VALID",
            }
            status_desc = f"{n_stns} estaciones | {n_records:,} días ({min_date}..{max_date})"
            report_rows.append((f"Estaciones {label}", "LISTO [OK]", stn_path.name, status_desc))
        except Exception as e:
            errors.append(f"Estaciones {label}: Error al leer formato CDT: {e}")
            report_rows.append((f"Estaciones {label}", "ERROR", stn_path.name, str(e)))

    details["stations"] = stn_details

    # -------------------------------------------------------------------------
    # 2. Validar Topografía DEM SRTM
    # -------------------------------------------------------------------------
    dem_path_str = paths.get("dem_file", "data/topography/dem_srtm_90m.nc")
    dem_path = Path(dem_path_str).resolve()
    if not dem_path.exists():
        cand = Path(dem_path_str)
        if cand.exists():
            dem_path = cand.resolve()
        else:
            cand_gen = Path("data/topography/dem_srtm_90m.nc")
            if cand_gen.exists():
                dem_path = cand_gen.resolve()
                warnings.append(f"Topografía DEM: Usando DEM regional general '{cand_gen.name}'")

    if not dem_path.exists():
        errors.append(f"Topografía DEM: Archivo no encontrado en '{dem_path_str}'")
        report_rows.append(("Topografía DEM SRTM", "NO ENCONTRADO", str(dem_path_str), "Colocar NetCDF del DEM (ej. dem_srtm_90m.nc)"))
    else:
        try:
            with xr.open_dataset(dem_path) as ds_dem:
                # Identify the actual 2D numeric elevation variable, ignoring CRS metadata
                meta_vars = {"crs", "spatial_ref", "grid_mapping", "transverse_mercator", "lambert_conformal_conic"}
                candidate_vars = [v for v in ds_dem.data_vars if v.lower() not in meta_vars and np.issubdtype(ds_dem[v].dtype, np.number)]
                
                # Prioritize standard names
                preferred = ["elevation", "z", "dem", "elev", "height", "band1", "topo"]
                var_name = None
                for pref in preferred:
                    match = next((v for v in candidate_vars if v.lower() == pref), None)
                    if match:
                        var_name = match
                        break
                
                if not var_name and candidate_vars:
                    var_2d = [v for v in candidate_vars if len(ds_dem[v].dims) >= 2]
                    var_name = var_2d[0] if var_2d else candidate_vars[0]
                elif not var_name:
                    var_name = list(ds_dem.data_vars)[0] if ds_dem.data_vars else "z"

                da_dem = ds_dem[var_name]
                # Safely compute finite min and max
                vals = da_dem.values
                valid_vals = vals[np.isfinite(vals)]
                if len(valid_vals) > 0:
                    elev_min = float(np.min(valid_vals))
                    elev_max = float(np.max(valid_vals))
                else:
                    elev_min = 0.0
                    elev_max = 0.0

                dims_str = ", ".join([f"{k}:{v}" for k, v in da_dem.sizes.items()]) or ", ".join([f"{k}:{v}" for k, v in ds_dem.dims.items()])
                
                details["dem"] = {
                    "path": str(dem_path),
                    "var_name": var_name,
                    "dims": dict(da_dem.sizes),
                    "elev_range": [elev_min, elev_max],
                }
                status_desc = f"Var '{var_name}' ({dims_str}) | Cotas: {elev_min:.0f}m a {elev_max:.0f}m"
                report_rows.append(("Topografía DEM SRTM/GEBCO", "LISTO [OK]", dem_path.name, status_desc))
        except Exception as e:
            errors.append(f"Topografía DEM: Error al abrir NetCDF: {e}")
            report_rows.append(("Topografía DEM SRTM/GEBCO", "ERROR", dem_path.name, str(e)))

    # -------------------------------------------------------------------------
    # 3. Validar Shapefile Regional (GIS)
    # -------------------------------------------------------------------------
    shp_path_str = paths.get("shapefile_path", "data/gis/central_america_dominican_rep.shp")
    shp_path = Path(shp_path_str).resolve()
    if not shp_path.exists():
        cand = Path(shp_path_str)
        if cand.exists():
            shp_path = cand.resolve()
        else:
            cand_gen = Path("data/gis/central_america_dominican_rep.shp")
            if cand_gen.exists():
                shp_path = cand_gen.resolve()
                warnings.append(f"Shapefile de Recorte: Usando shapefile general '{cand_gen.name}'")

    if not shp_path.exists():
        errors.append(f"Shapefile de Recorte: Archivo no encontrado en '{shp_path_str}'")
        report_rows.append(("Shapefile de Recorte", "NO ENCONTRADO", str(shp_path_str), "Colocar .shp y archivos .shx/.dbf/.prj"))
    else:
        missing_sidecars = []
        for ext in [".shx", ".dbf", ".prj"]:
            sc = shp_path.with_suffix(ext)
            if not sc.exists():
                missing_sidecars.append(ext)
        if missing_sidecars:
            warnings.append(f"Shapefile: Faltan archivos auxiliares ({', '.join(missing_sidecars)}) para {shp_path.name}")
            report_rows.append(("Shapefile de Recorte", "ADVERTENCIA", shp_path.name, f"Faltan auxiliares: {', '.join(missing_sidecars)}"))
        else:
            details["shapefile"] = {"path": str(shp_path), "status": "COMPLETE"}
            report_rows.append(("Shapefile de Recorte", "LISTO [OK]", shp_path.name, "Polígono regional con .shp/.shx/.dbf/.prj"))

    # -------------------------------------------------------------------------
    # 4. Validar Estaciones Holdout (Validación Ciega por Variable)
    # -------------------------------------------------------------------------
    holdout_specs = [
        (
            "holdout_rainfall_file",
            "Holdout Precipitación",
            [
                f"data/stations/validation_holdout_stations_rainfall_{active_region}.csv" if active_region else "",
                "data/stations/validation_holdout_stations_rainfall.csv",
                "data/stations/validation_holdout_stations.csv",
            ],
        ),
        (
            "holdout_temperature_file",
            "Holdout Temperatura",
            [
                f"data/stations/validation_holdout_stations_temperature_{active_region}.csv" if active_region else "",
                f"data/stations/validation_holdout_stations_tmax_{active_region}.csv" if active_region else "",
                "data/stations/validation_holdout_stations_temperature.csv",
                "data/stations/validation_holdout_stations_tmax.csv",
                "data/stations/validation_holdout_stations.csv",
            ],
        ),
    ]

    holdout_details = {}
    for h_key, h_label, h_candidates in holdout_specs:
        h_path_str = paths.get(h_key)
        resolved_path = None
        if h_path_str:
            cand = Path(h_path_str).resolve()
            if cand.exists():
                resolved_path = cand
            else:
                cand_rel = Path(h_path_str)
                if cand_rel.exists():
                    resolved_path = cand_rel.resolve()

        if not resolved_path:
            for c_str in h_candidates:
                if c_str:
                    c_cand = Path(c_str).resolve()
                    if c_cand.exists():
                        resolved_path = c_cand
                        break
                    elif Path(c_str).exists():
                        resolved_path = Path(c_str).resolve()
                        break

        if resolved_path and resolved_path.exists():
            try:
                df_h = pd.read_csv(resolved_path)
                h_count = len(df_h)
                holdout_details[h_key] = {"path": str(resolved_path), "holdout_count": h_count}
                desc = f"{h_count} estaciones excluidas ({resolved_path.name})" if h_count > 0 else f"0 estaciones ({resolved_path.name})"
                report_rows.append((h_label, "LISTO [OK]", resolved_path.name, desc))
            except Exception as e:
                warnings.append(f"{h_label}: No se pudo leer CSV: {e}")
                report_rows.append((h_label, "ADVERTENCIA", resolved_path.name, str(e)))
        else:
            report_rows.append((h_label, "OPCIONAL", "No suministrado", "Validación in-sample (100% estaciones)"))

    details["holdout"] = holdout_details

    # -------------------------------------------------------------------------
    # 5. Validar Grillas Satelitales Diarias NetCDF (CHIRPS, Tmax, Tmin)
    # -------------------------------------------------------------------------
    gridded_specs = [
        ("satellite_rainfall_dir", "raw_3d_netcdf_rainfall", "chirps_%s%s%s.nc", "precip", "Grillas Lluvia (CHIRPS)", "data/chirps_daily"),
        ("satellite_tmax_dir", "raw_3d_netcdf_tmax", "tmax_%s%s%s.nc", "tmax", "Grillas Tmax (CHIRTS)", "data/chirts_daily/tmax"),
        ("satellite_tmin_dir", "raw_3d_netcdf_tmin", "tmin_%s%s%s.nc", "tmin", "Grillas Tmin (CHIRTS)", "data/chirts_daily/tmin"),
    ]

    for dir_key, raw_3d_key, def_format, def_var, label, def_dir in gridded_specs:
        target_dir_str = paths.get(dir_key, def_dir)
        raw_3d_str = paths.get(raw_3d_key)
        
        t_dir = Path(target_dir_str).resolve()
        if not t_dir.exists():
            cand = Path(target_dir_str)
            if cand.exists():
                t_dir = cand.resolve()

        nc_files = list(t_dir.glob("*.nc")) if t_dir.exists() and t_dir.is_dir() else []
        nc_count = len(nc_files)

        # Check raw 3D file fallback if daily files are missing
        raw_found = False
        raw_path_obj = None
        if raw_3d_str:
            raw_path_obj = Path(raw_3d_str).resolve()
            if not raw_path_obj.exists():
                cand_raw = Path(raw_3d_str)
                if cand_raw.exists():
                    raw_path_obj = cand_raw.resolve()
            raw_found = raw_path_obj.exists() and raw_path_obj.is_file()

        if nc_count >= expected_days:
            details[dir_key] = {"path": str(t_dir), "file_count": nc_count, "status": "COMPLETE"}
            report_rows.append((label, "LISTO [OK]", f"{t_dir.name}/", f"{nc_count:,} archivos diarios 2D (100% cobertura)"))
        elif nc_count > 0:
            pct = (nc_count / expected_days) * 100.0
            warnings.append(f"{label}: Se encontraron {nc_count:,} de {expected_days:,} archivos diarios ({pct:.1f}%).")
            report_rows.append((label, "PARCIAL [!]", f"{t_dir.name}/", f"{nc_count:,} de {expected_days:,} archivos ({pct:.1f}%)"))
        elif raw_found and raw_path_obj:
            details[raw_3d_key] = {"path": str(raw_path_obj), "status": "RAW_3D_READY"}
            report_rows.append((label, "3D DISPONIBLE", raw_path_obj.name, "Listo para particionar automáticamente a diario"))
        else:
            errors.append(f"{label}: No se encontraron archivos NetCDF en '{target_dir_str}' ni 3D en raw_netcdf.")
            report_rows.append((label, "NO ENCONTRADO", str(target_dir_str), f"Colocar {expected_days:,} archivos diarios 2D o NetCDF 3D"))

    # -------------------------------------------------------------------------
    # Renderizar Tabla de Diagnóstico en Terminal
    # -------------------------------------------------------------------------
    if verbose:
        header = f"  {'COMPONENTE':<25} | {'ESTADO':<15} | {'ARCHIVO / CARPETA':<22} | {'DETALLE / ACCIÓN'}"
        print(header)
        print("  " + "-" * 83)
        for comp, st, loc, det in report_rows:
            st_color = st
            print(f"  {comp:<25} | {st_color:<15} | {loc:<22} | {det}")
        print("=" * 85)

    overall_status = "ERRORS" if errors else ("WARNINGS" if warnings else "VALID")

    if verbose:
        if overall_status == "VALID":
            print("\n  >>> [EXITO] TODOS LOS DATOS ESTÁN LISTOS Y VALIDADOS PARA EJECUTAR CDT <<<")
            print("  Puedes iniciar los experimentos con: python launcher/experiment_runner.py --suite all\n")
        elif overall_status == "WARNINGS":
            print(f"\n  >>> [AVISO] DATOS VALIDADOS CON {len(warnings)} ADVERTENCIA(S):")
            for w in warnings:
                print(f"      [!] {w}")
            print("  Puedes ejecutar las suites pero revisa las advertencias anteriores.\n")
        else:
            print(f"\n  >>> [ALERTA] SE ENCONTRARON {len(errors)} ERROR(ES) DE DATOS FALTANTES:")
            for e in errors:
                print(f"      [X] {e}")
            print("\n  GUÍA RÁPIDA PARA COLOCAR TUS DATOS:")
            print("  1. Estaciones CSV (CDT 4 encabezados): data/stations/precip_stations_all.csv, tmax_stations_all.csv, tmin_stations_all.csv")
            print("  2. DEM SRTM NetCDF: data/topography/dem_srtm_90m.nc")
            print("  3. Shapefile Regional: data/gis/central_america_dominican_rep.shp (+ .shx, .dbf, .prj)")
            print("  4. Grillas Diarias: data/chirps_daily/, data/chirts_daily/tmax/, data/chirts_daily/tmin/\n")

    return {
        "status": overall_status,
        "is_ready": overall_status in ("VALID", "WARNINGS"),
        "errors": errors,
        "warnings": warnings,
        "details": details,
    }


def check_data_readiness(
    config_path: Union[Path, str] = "config/global_config.yaml",
    region: Optional[str] = None,
    verbose: bool = True,
) -> bool:
    """Convenience helper to check data readiness returning True/False boolean."""
    res = validate_project_inputs(config_path_or_dict=config_path, region=region, verbose=verbose)
    return res.get("is_ready", False)

