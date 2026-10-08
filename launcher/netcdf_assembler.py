"""NetCDF Assembler & CF-1.8 Compliance Engine.

Concatenates daily 2D NetCDF files (1991-2020) into a single unified 3D NetCDF
file with strict adherence to the Climate and Forecast (CF-1.8) metadata conventions.
"""

from __future__ import annotations

import datetime
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import netCDF4 as nc
import numpy as np


def extract_date_from_filename(filename: str) -> Optional[datetime.date]:
    """Extract YYYYMMDD date from NetCDF file name."""
    # Matches patterns like rr_mrg_20200115.nc, tmax_adj_19910520.nc, 19910101.nc
    match = re.search(r"(\d{4})(\d{2})(\d{2})", filename)
    if match:
        year, month, day = map(int, match.groups())
        try:
            return datetime.date(year, month, day)
        except ValueError:
            return None
    return None


def assemble_daily_netcdfs_to_cf18(
    input_dir: Union[str, Path],
    output_netcdf_path: Union[str, Path],
    variable_name: str = "precip",
    variable_type: str = "rainfall",
    title: str = "High-Resolution Daily Climate Reconstructed Gridded Dataset (1991-2020)",
    institution: str = "Climate Data Tools (CDT) Evaluation Suite",
    source_info: str = "CDT v8.0 Merging Pipeline with In-Situ Stations and CHIRPS/CHIRTS",
    compression_level: int = 4,
) -> Path:
    """Concatenate daily 2D NetCDF files into a single CF-1.8 compliant 3D NetCDF.

    Args:
        input_dir: Folder containing the daily 2D NetCDF files.
        output_netcdf_path: Destination path for the 3D NetCDF file.
        variable_name: Name of the variable inside the NetCDF ('precip', 'temp', 'tmax', 'tmin').
        variable_type: 'rainfall' or 'temperature'.
        title: Global title attribute.
        institution: Research institution or project name.
        source_info: Source description attribute.
        compression_level: Deflate compression level (1-9).

    Returns:
        Path to the generated NetCDF file.
    """
    input_dir = Path(input_dir).resolve()
    output_netcdf_path = Path(output_netcdf_path).resolve()
    output_netcdf_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Discover and sort daily files by date
    all_nc_files = list(input_dir.glob("*.nc"))
    if not all_nc_files:
        raise FileNotFoundError(f"No NetCDF (*.nc) files found in directory: {input_dir}")

    dated_files: List[Tuple[datetime.date, Path]] = []
    for f in all_nc_files:
        d = extract_date_from_filename(f.name)
        if d:
            dated_files.append((d, f))

    if not dated_files:
        raise ValueError(f"Could not parse dates from NetCDF file names in: {input_dir}")

    dated_files.sort(key=lambda x: x[0])
    dates = [x[0] for x in dated_files]
    file_paths = [x[1] for x in dated_files]

    # 2. Read spatial grid coordinates from the first sample file
    with nc.Dataset(file_paths[0], "r") as sample_ds:
        # Detect longitude coordinate
        lon_var_name = next((v for v in sample_ds.variables if v.lower() in ("lon", "longitude", "x")), None)
        lat_var_name = next((v for v in sample_ds.variables if v.lower() in ("lat", "latitude", "y")), None)
        
        if not lon_var_name or not lat_var_name:
            raise KeyError(f"Could not detect Lon/Lat variables in sample file: {file_paths[0]}")

        lons = np.array(sample_ds.variables[lon_var_name][:], dtype=np.float32)
        lats = np.array(sample_ds.variables[lat_var_name][:], dtype=np.float32)

        # Detect primary climate variable
        var_candidates = [variable_name, "precip", "temp", "tmax", "tmin", "rfe", "rr", "bias"]
        src_var_name = next((v for v in sample_ds.variables if v.lower() in var_candidates), None)
        if not src_var_name:
            # Fallback to the first non-coordinate variable
            src_var_name = [v for v in sample_ds.variables if v not in (lon_var_name, lat_var_name)][0]

    n_times = len(dates)
    n_lats = len(lats)
    n_lons = len(lons)

    # 3. Create CF-1.8 Compliant NetCDF-4 Destination Dataset
    ref_date = datetime.date(1991, 1, 1)
    time_units = "days since 1991-01-01 00:00:00"
    time_values = np.array([(d - ref_date).days for d in dates], dtype=np.int32)

    if output_netcdf_path.exists():
        output_netcdf_path.unlink()

    with nc.Dataset(str(output_netcdf_path), "w", format="NETCDF4") as ds:
        # Define Global Attributes (CF-1.8 Conventions)
        ds.Conventions = "CF-1.8"
        ds.title = title
        ds.institution = institution
        ds.source = source_info
        ds.history = f"Created on {datetime.datetime.now().isoformat()} using CDT Python Assembler"
        ds.references = "https://iri.columbia.edu/~rijaf/CDTUserGuide/index.html"
        ds.spatial_resolution = f"{abs(lons[1]-lons[0]):.4f} deg" if len(lons) > 1 else "Unknown"
        ds.time_coverage_start = dates[0].isoformat()
        ds.time_coverage_end = dates[-1].isoformat()
        ds.geographic_region = "Central America and Dominican Republic"

        # Create Dimensions
        ds.createDimension("time", n_times)
        ds.createDimension("latitude", n_lats)
        ds.createDimension("longitude", n_lons)

        # Create Coordinate Variables
        time_var = ds.createVariable("time", "i4", ("time",), zlib=True)
        time_var.standard_name = "time"
        time_var.long_name = "Time in calendar days"
        time_var.units = time_units
        time_var.calendar = "standard"
        time_var.axis = "T"
        time_var[:] = time_values

        lat_var = ds.createVariable("latitude", "f4", ("latitude",), zlib=True)
        lat_var.standard_name = "latitude"
        lat_var.long_name = "Latitude coordinate"
        lat_var.units = "degrees_north"
        lat_var.axis = "Y"
        lat_var[:] = lats

        lon_var = ds.createVariable("longitude", "f4", ("longitude",), zlib=True)
        lon_var.standard_name = "longitude"
        lon_var.long_name = "Longitude coordinate"
        lon_var.units = "degrees_east"
        lon_var.axis = "X"
        lon_var[:] = lons

        # Create Primary Climate Data Variable with CF metadata
        fill_val = -99.0
        if variable_type in ("rainfall", "rain", "precip"):
            main_var = ds.createVariable(
                variable_name, "f4", ("time", "latitude", "longitude"),
                fill_value=fill_val, zlib=True, complevel=compression_level,
                chunksizes=(min(30, n_times), min(100, n_lats), min(100, n_lons))
            )
            main_var.standard_name = "precipitation_amount"
            main_var.long_name = "Daily Merged Station-Satellite Rainfall"
            main_var.units = "mm"
            main_var.coordinates = "time latitude longitude"
            main_var.cell_methods = "time: sum"
        else:
            main_var = ds.createVariable(
                variable_name, "f4", ("time", "latitude", "longitude"),
                fill_value=fill_val, zlib=True, complevel=compression_level,
                chunksizes=(min(30, n_times), min(100, n_lats), min(100, n_lons))
            )
            main_var.standard_name = "air_temperature"
            main_var.long_name = f"Daily Merged Air Temperature ({variable_name.upper()})"
            main_var.units = "degC"
            main_var.coordinates = "time latitude longitude"
            main_var.cell_methods = "time: mean"

        # 4. Fill Data Layer by Layer (Iterate through daily files)
        for idx, (dt, fpath) in enumerate(zip(dates, file_paths)):
            with nc.Dataset(fpath, "r") as day_ds:
                val = day_ds.variables[src_var_name][:]
                val = np.array(val, dtype=np.float32)
                # Ensure 2D shape (n_lats, n_lons)
                if val.ndim == 2:
                    if val.shape == (n_lons, n_lats):
                        val = val.T
                elif val.ndim == 3:
                    val = val[0]
                    if val.shape == (n_lons, n_lats):
                        val = val.T
                
                # Replace NaNs with fill_val
                val[np.isnan(val)] = fill_val
                main_var[idx, :, :] = val

    print(f"[OK] Ensamblado NetCDF CF-1.8 exitoso: {output_netcdf_path} ({n_times} pasos temporales)")
    return output_netcdf_path
