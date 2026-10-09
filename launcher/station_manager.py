"""CDT Station Data Manager and Cross-Validation Evaluator.

Handles:
1. Parsing CDT station CSV files (handling 3-line or 4-line headers: ID, LON, LAT, [ELEV]).
2. Splitting station files into Training (included in Merging) and Validation (omitted/holdout)
   based on an external CSV list of station IDs.
3. Extracting time series from assembled 3D NetCDF CF-1.8 files at station coordinates.
4. Computing continuous and categorical metrics (KGE, RMSE, MAE, PBIAS, POD, FAR, ETS, HSS).
5. Generating detailed CSV and JSON validation reports per experiment.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import xarray as xr

from launcher.metrics import compute_categorical_metrics, compute_continuous_metrics


def normalize_id(val: Any) -> str:
    """Normalize station ID by stripping quotes, whitespace, and formatting."""
    if val is None:
        return ""
    s = str(val).strip().strip('"').strip("'").strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def read_holdout_station_ids(holdout_file: Union[str, Path]) -> List[str]:
    """Read list of station IDs to omit from a CSV or text file.
    
    Supports:
    - CSV with header ('id', 'station_id', 'code', 'station', etc.)
    - CSV with multiple columns (searches for ID column)
    - CSV without header (single column of IDs)
    - Comma/semicolon/tab/newline separated text
    """
    path = Path(holdout_file).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Holdout stations file not found: {path}")

    ids: List[str] = []
    # Try reading with pandas first for intelligent column matching
    try:
        df = pd.read_csv(path, dtype=str)
        if not df.empty:
            id_cols = [c for c in df.columns if str(c).strip().lower() in (
                "id", "station_id", "station", "codigo", "code", "stn_id", "estacion", "name", "id_estacion", "cod_estacion"
            )]
            target_col = id_cols[0] if id_cols else df.columns[0]
            raw_vals = df[target_col].dropna().tolist()
            ids = [normalize_id(v) for v in raw_vals if normalize_id(v)]
    except Exception:
        pass

    if not ids:
        with open(path, "r", encoding="utf-8-sig") as f:
            lines = [line.strip() for line in f if line.strip()]
        
        for i, line in enumerate(lines):
            parts = [p.strip() for p in line.replace(";", ",").replace("\t", ",").split(",") if p.strip()]
            if not parts:
                continue
            val = parts[0]
            if i == 0 and val.lower() in ("id", "station_id", "station", "codigo", "code", "stn_id", "estacion", "name", "id_estacion"):
                continue
            norm = normalize_id(val)
            if norm:
                ids.append(norm)

    unique_ids = list(dict.fromkeys(ids))
    return unique_ids


def parse_cdt_station_file(station_file: Union[str, Path]) -> Tuple[pd.DataFrame, Dict[str, Any], int]:
    """Parse a CDT station CSV file with metadata header lines.
    
    Returns:
        df_data: DataFrame with dates as index and station IDs as columns.
        metadata: Dict with 'id', 'lon', 'lat', 'elev' (if present) as lists.
        header_line_count: Number of header lines (3 or 4).
    """
    path = Path(station_file).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Station file not found: {path}")

    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f if line.strip()]

    if len(lines) < 4:
        raise ValueError(f"Station file {path} has too few lines ({len(lines)}).")

    # Detect delimiter in header
    first_line = lines[0]
    delimiter = "," if "," in first_line else (";" if ";" in first_line else "\t" if "\t" in first_line else None)

    def split_row(r: str) -> List[str]:
        if delimiter:
            return [x.strip() for x in r.split(delimiter)]
        return r.split()

    row0 = split_row(lines[0]) # IDs
    row1 = split_row(lines[1]) # LON
    row2 = split_row(lines[2]) # LAT
    row3 = split_row(lines[3]) # ELEV or Date

    # Check if row3 is Elevation or First Date (Dates are usually 8 digits like 19910101)
    tag3 = row3[0].upper().strip().strip('"').strip("'")
    has_elev = False
    if tag3 in ("ELEV", "ELV", "ALT", "ALTITUDE", "HEIGHT", "ELEVATION"):
        has_elev = True
    else:
        # Check if first column of row3 looks like a date (8 numeric characters e.g. 19910101)
        if len(tag3) == 8 and tag3.isdigit():
            has_elev = False
        else:
            # Check if row 4 is a date
            if len(lines) > 4:
                row4 = split_row(lines[4])
                tag4 = row4[0].strip().strip('"').strip("'")
                if len(tag4) == 8 and tag4.isdigit():
                    has_elev = True

    header_lines = 4 if has_elev else 3
    station_ids = [normalize_id(s) for s in row0[1:]]
    lons = [float(str(x).strip().strip('"')) for x in row1[1:]]
    lats = [float(str(x).strip().strip('"')) for x in row2[1:]]
    elevs = [float(str(x).strip().strip('"')) for x in row3[1:]] if has_elev else [np.nan] * len(station_ids)

    # Read the rest of data lines
    data_rows = []
    dates = []
    for line in lines[header_lines:]:
        parts = split_row(line)
        if not parts:
            continue
        dates.append(parts[0].strip().strip('"'))
        # Replace missing flags (-99, -999, NA, null) with np.nan
        vals = []
        for x in parts[1:]:
            try:
                v = float(str(x).strip().strip('"'))
                if v in (-99.0, -999.0, -9999.0):
                    vals.append(np.nan)
                else:
                    vals.append(v)
            except ValueError:
                vals.append(np.nan)
        data_rows.append(vals)

    df_data = pd.DataFrame(data_rows, index=dates, columns=station_ids)
    metadata = {
        "id": station_ids,
        "lon": lons,
        "lat": lats,
        "elev": elevs,
        "has_elev": has_elev,
        "delimiter": delimiter or ",",
    }
    return df_data, metadata, header_lines


def split_cdt_station_file(
    station_file: Union[str, Path],
    holdout_file: Union[str, Path],
    output_dir: Union[str, Path],
) -> Dict[str, Any]:
    """Split CDT station file into training (included in merging) and holdout (validation).
    
    Writes:
    - {output_dir}/stations_training.csv
    - {output_dir}/stations_holdout.csv
    
    Returns:
        Summary dictionary with paths, station counts, and lists of IDs.
    """
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    holdout_ids = read_holdout_station_ids(holdout_file)
    df_data, meta, header_lines = parse_cdt_station_file(station_file)

    all_ids = meta["id"]
    norm_all = [normalize_id(s) for s in all_ids]
    norm_holdout = {normalize_id(h) for h in holdout_ids if normalize_id(h)}

    val_indices = [i for i, ns in enumerate(norm_all) if ns in norm_holdout]
    val_ids = [all_ids[i] for i in val_indices]
    train_ids = [all_ids[i] for i in range(len(all_ids)) if i not in set(val_indices)]

    if not train_ids:
        raise ValueError("All stations were matched as holdout! No stations remaining for training.")
    if not val_ids and holdout_ids:
        print(f"      [!] Advertencia: Ninguna estación del archivo holdout ({len(holdout_ids)} estaciones) coincidió con los IDs del archivo principal ({len(all_ids)} estaciones).")
        print(f"          Muestra IDs archivo de estaciones : {all_ids[:5]}")
        print(f"          Muestra IDs archivo holdout       : {holdout_ids[:5]}")

    delim = meta["delimiter"]

    # Helper to write CDT CSV
    def write_cdt_csv(filepath: Path, subset_ids: List[str]):
        if not subset_ids:
            return
        idx_map = [all_ids.index(s) for s in subset_ids]
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=delim)
            # Row 0: ID
            writer.writerow(["ID"] + subset_ids)
            # Row 1: LON
            writer.writerow(["LON"] + [meta["lon"][i] for i in idx_map])
            # Row 2: LAT
            writer.writerow(["LAT"] + [meta["lat"][i] for i in idx_map])
            # Row 3: ELEV (if present)
            if meta["has_elev"]:
                writer.writerow(["ELEV"] + [meta["elev"][i] for i in idx_map])
            
            # Data rows
            sub_df = df_data[subset_ids]
            for date_val, row_vals in sub_df.iterrows():
                formatted_vals = [f"{v:.2f}" if not np.isnan(v) else "-99.0" for v in row_vals]
                writer.writerow([date_val] + formatted_vals)

    train_file = out_path / "stations_training.csv"
    holdout_file_out = out_path / "stations_holdout.csv"

    write_cdt_csv(train_file, train_ids)
    write_cdt_csv(holdout_file_out, val_ids)

    return {
        "total_stations": len(all_ids),
        "training_count": len(train_ids),
        "holdout_count": len(val_ids),
        "training_stations_file": str(train_file),
        "holdout_stations_file": str(holdout_file_out),
        "training_ids": train_ids,
        "holdout_ids": val_ids,
    }


def evaluate_netcdf_against_stations(
    netcdf_path: Union[str, Path],
    station_file: Union[str, Path],
    var_name: Optional[str] = None,
    var_type: str = "rainfall",
    wet_threshold: float = 1.0,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Extract reconstructed grid series at station coordinates and compute validation metrics.
    
    Args:
        netcdf_path: Path to assembled 3D CF-1.8 NetCDF file.
        station_file: Path to CDT station CSV (e.g. stations_holdout.csv).
        var_name: Name of data variable in NetCDF (auto-detected if None).
        var_type: 'rainfall' or 'temperature'.
        wet_threshold: Threshold in mm for categorical rainfall metrics.

    Returns:
        df_metrics: DataFrame with metrics per individual station.
        summary: Dict with aggregated regional metrics (mean, median, etc.).
    """
    nc_path = Path(netcdf_path).resolve()
    if not nc_path.exists():
        raise FileNotFoundError(f"NetCDF file not found: {nc_path}")

    df_obs, meta, _ = parse_cdt_station_file(station_file)
    station_ids = meta["id"]
    lons = meta["lon"]
    lats = meta["lat"]

    # Open NetCDF using xarray
    ds = xr.open_dataset(nc_path)

    # Detect data variable
    if not var_name:
        possible_vars = ["precip", "precipitation", "precip_amount", "temp", "tmax", "tmin", "air_temperature"]
        for pv in possible_vars:
            if pv in ds.data_vars:
                var_name = pv
                break
        if not var_name:
            # Pick first data variable
            var_name = list(ds.data_vars.keys())[0]

    da = ds[var_name]

    # Detect coordinate names
    lat_name = next((c for c in da.coords if c.lower() in ("latitude", "lat", "y")), "lat")
    lon_name = next((c for c in da.coords if c.lower() in ("longitude", "lon", "x")), "lon")
    time_name = next((c for c in da.coords if c.lower() in ("time", "t", "date")), "time")

    # Format NetCDF time array to YYYYMMDD string format
    nc_times = pd.to_datetime(da[time_name].values).strftime("%Y%m%d")

    results_per_stn: List[Dict[str, Any]] = []

    for stn_id, stn_lon, stn_lat in zip(station_ids, lons, lats):
        # Extract nearest grid cell
        try:
            point_series = da.sel(
                {lon_name: stn_lon, lat_name: stn_lat},
                method="nearest"
            ).values
        except Exception:
            # Fallback indexer
            lats_arr = da[lat_name].values
            lons_arr = da[lon_name].values
            ilat = np.abs(lats_arr - stn_lat).argmin()
            ilon = np.abs(lons_arr - stn_lon).argmin()
            point_series = da.isel({lat_name: ilat, lon_name: ilon}).values

        df_sim = pd.Series(point_series, index=nc_times, name="sim")
        obs_series = df_obs[stn_id].dropna()

        # Inner join on matching dates
        df_matched = pd.concat([obs_series.rename("obs"), df_sim], axis=1, join="inner").dropna()

        if len(df_matched) < 5:
            continue

        o_vals = df_matched["obs"].values
        s_vals = df_matched["sim"].values

        cont_m = compute_continuous_metrics(o_vals, s_vals)
        cat_m = compute_categorical_metrics(o_vals, s_vals, threshold=wet_threshold) if var_type in ("rainfall", "rain", "precip") else {}

        stn_record = {
            "station_id": stn_id,
            "lon": stn_lon,
            "lat": stn_lat,
            "n_samples": cont_m["n_samples"],
            "r": cont_m["r"],
            "r2": cont_m["r2"],
            "kge": cont_m["kge"],
            "rmse": cont_m["rmse"],
            "mae": cont_m["mae"],
            "pbias": cont_m["pbias"],
        }
        if cat_m:
            stn_record.update({
                "pod": cat_m["pod"],
                "far": cat_m["far"],
                "fbi": cat_m["fbi"],
                "ets": cat_m["ets"],
                "hss": cat_m["hss"],
            })

        results_per_stn.append(stn_record)

    ds.close()

    df_results = pd.DataFrame(results_per_stn)
    if df_results.empty:
        return df_results, {"status": "NO_MATCHING_DATA"}

    # Compute Regional Aggregates
    summary = {
        "total_stations_evaluated": len(df_results),
        "mean_kge": float(df_results["kge"].mean(skipna=True)),
        "median_kge": float(df_results["kge"].median(skipna=True)),
        "mean_r": float(df_results["r"].mean(skipna=True)),
        "mean_rmse": float(df_results["rmse"].mean(skipna=True)),
        "mean_mae": float(df_results["mae"].mean(skipna=True)),
        "mean_pbias": float(df_results["pbias"].mean(skipna=True)),
    }
    if "pod" in df_results.columns:
        summary.update({
            "mean_pod": float(df_results["pod"].mean(skipna=True)),
            "mean_far": float(df_results["far"].mean(skipna=True)),
            "mean_ets": float(df_results["ets"].mean(skipna=True)),
            "mean_hss": float(df_results["hss"].mean(skipna=True)),
        })

    return df_results, summary
