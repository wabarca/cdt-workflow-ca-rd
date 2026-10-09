"""CDT Bridge: Python wrapper for invoking CDT R functions.

Translates Python configuration dictionaries into valid R expressions,
executes Rscript in a child process, captures logs, and handles execution status.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from launcher.env_checker import find_rscript_executable


def _to_r_val(val: Any) -> str:
    """Format Python objects into valid R syntax literals."""
    if val is None:
        return "NULL"
    elif isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    elif isinstance(val, (int, float)):
        return str(val)
    elif isinstance(val, (str, Path)):
        # Normalize file paths to forward slashes for R compatibility
        clean_str = str(val).replace("\\", "/")
        return f'"{clean_str}"'
    elif isinstance(val, list):
        items = ", ".join(_to_r_val(v) for v in val)
        return f"c({items})"
    elif isinstance(val, dict):
        entries = [f"{k} = {_to_r_val(v)}" for k, v in val.items()]
        return f"list({', '.join(entries)})"
    else:
        return f'"{str(val)}"'


class CDTBridge:
    """High-level Python bridge for Climate Data Tools (CDT) R routines."""

    def __init__(
        self,
        rscript_path: Optional[Union[str, Path]] = None,
        nb_cores: Optional[Union[int, str]] = None,
    ):
        """Initialize CDTBridge with explicit or auto-detected Rscript binary and core count."""
        if rscript_path:
            self.rscript_path = Path(rscript_path).resolve()
        else:
            auto_path = find_rscript_executable()
            if not auto_path:
                raise RuntimeError("Could not find Rscript executable. Please install R 4.4.3+.")
            self.rscript_path = auto_path
        
        self.nb_cores = nb_cores

    def _execute_r_code(
        self,
        r_code: str,
        log_dir: Optional[Path] = None,
        job_name: str = "cdt_job",
    ) -> Tuple[int, str, str, float]:
        """Execute a block of R code using Rscript subprocess."""
        start_time = time.time()

        if isinstance(self.nb_cores, int) and self.nb_cores > 0:
            core_setup = f"n_cores <- {self.nb_cores}\n"
        else:
            core_setup = "n_cores <- max(1, parallel::detectCores() - 1)\n"
        
        full_r_script = (
            "suppressPackageStartupMessages({\n"
            "  library(CDT)\n"
            "  library(ncdf4)\n"
            "  library(doParallel)\n"
            "  library(foreach)\n"
            "})\n\n"
            "# Configuracion automatica de paralelismo de alto rendimiento en CDT\n"
            f"{core_setup}"
            "cdt_env <- asNamespace('CDT')\n"
            "if (exists('.cdtData', envir = cdt_env)) {\n"
            "  cdt_data <- get('.cdtData', envir = cdt_env)\n"
            "  cdt_data$Config$parallel <- list(dopar = TRUE, detect.cores = FALSE, nb.cores = n_cores)\n"
            "}\n\n"
            f"{r_code}\n"
        )

        if log_dir:
            log_dir = Path(log_dir)
            log_dir.mkdir(parents=True, exist_ok=True)
            script_file = log_dir / f"{job_name}.R"
        else:
            import tempfile
            temp_f = tempfile.NamedTemporaryFile(suffix=".R", delete=False)
            script_file = Path(temp_f.name)
            temp_f.close()

        script_file.write_text(full_r_script, encoding="utf-8")
        
        try:
            res = subprocess.run(
                [str(self.rscript_path), "--vanilla", str(script_file)],
                capture_output=True,
                text=True,
                check=False,
            )
            elapsed = time.time() - start_time
            
            if log_dir:
                (log_dir / f"{job_name}_stdout.log").write_text(res.stdout, encoding="utf-8")
                (log_dir / f"{job_name}_stderr.log").write_text(res.stderr, encoding="utf-8")

            return res.returncode, res.stdout, res.stderr, elapsed
        except Exception as e:
            elapsed = time.time() - start_time
            return 1, "", str(e), elapsed

    def set_global_merging_options(self, options: Dict[str, Any]) -> str:
        """Generate R code snippet to configure merging.options()."""
        args_str = ", ".join(f"{k} = {_to_r_val(v)}" for k, v in options.items())
        return f"merging.options({args_str})\n"

    def set_global_bias_options(self, options: Dict[str, Any]) -> str:
        """Generate R code snippet to configure biascoeff.options()."""
        args_str = ", ".join(f"{k} = {_to_r_val(v)}" for k, v in options.items())
        return f"biascoeff.options({args_str})\n"

    # =========================================================================
    # STEP 1: COMPUTE BIAS COEFFICIENTS
    # =========================================================================

    def compute_bias_coefficients(
        self,
        variable_type: str,
        time_step: str,
        station_file: Union[str, Path],
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        output_dir: Union[str, Path],
        bias_method: str = "mbvar",
        distr_name: str = "berngamma",
        min_length: int = 15,
        interp_method: str = "idw",
        nmin: int = 4,
        nmax: int = 10,
        maxdist: float = 2.0,
        use_block: bool = True,
        vgm_models: list[str] = ["Sph", "Exp", "Gau"],
        dem_file: Optional[Union[str, Path]] = None,
        base_period_all_years: bool = True,
        start_year: int = 1991,
        end_year: int = 2020,
        min_year: int = 10,
        global_bias_opts: Optional[Dict[str, Any]] = None,
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Compute and interpolate bias coefficients (Step 1 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        var_clim = "rain" if variable_type in ("rainfall", "rain", "precip") else "temp"
        
        r_lines = []
        if global_bias_opts:
            r_lines.append(self.set_global_bias_options(global_bias_opts))

        # Setup .cdtData$GalParams for computeBiasCoeffClimData
        r_cmd = (
            "cdtLocalConfigData()\n"
            f".cdtData$GalParams$action <- 'coefbias.{var_clim}'\n"
            f".cdtData$GalParams$period <- {_to_r_val(time_step)}\n"
            f".cdtData$GalParams$STN.file <- {_to_r_val(station_file)}\n"
            f".cdtData$GalParams$INPUT <- list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, sample = '', varid = '{'precip' if var_clim == 'rain' else 'temp'}', ilon = 1, ilat = 2)\n"
            f".cdtData$GalParams$base.period <- list(all.years = {_to_r_val(base_period_all_years)}, start.year = {start_year}, end.year = {end_year}, min.year = {min_year})\n"
            f".cdtData$GalParams$BIAS <- list(method = {_to_r_val(bias_method)}, distr.name = {_to_r_val(distr_name)}, min.length = {min_length})\n"
            f".cdtData$GalParams$interp <- list(method = {_to_r_val(interp_method)}, nmin = {nmin}, nmax = {nmax}, maxdist = {maxdist}, use.block = {_to_r_val(use_block)}, vgm.model = {_to_r_val(vgm_models)}, minstn = 10, demfile = {_to_r_val(dem_file)})\n"
            ".cdtData$GalParams$grid <- list(from = 'data', pars = NULL)\n"
            f".cdtData$GalParams$output <- list(dir = {_to_r_val(output_dir)})\n"
            ".cdtData$GalParams$message <- list('7' = 'Computing bias coefficients...', '8' = 'Error reading sample', '9' = 'Error reading DEM', '10' = 'Error grid', '11' = 'Error NetCDF info', '12' = 'Not enough years')\n"
            "res <- computeBiasCoeffClimData()\n"
        )
        r_lines.append(r_cmd)
        return self._execute_r_code("\n".join(r_lines), log_dir=log_dir, job_name=f"compute_bias_{var_clim}")

    # =========================================================================
    # STEP 2: APPLY BIAS CORRECTION
    # =========================================================================

    def apply_bias_correction_precip(
        self,
        time_step: str,
        start_date: str,
        end_date: str,
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        bias_dir: Union[str, Path],
        bias_format: str,
        bias_method: str,
        output_dir: Union[str, Path],
        var_id: str = "precip",
        output_format: str = "rr_adj_%s%s%s.nc",
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Apply bias correction to precipitation NetCDF files (Step 2 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        r_cmd = (
            "res <- cdtBiasCorrectPrecipCMD(\n"
            f"  time.step = {_to_r_val(time_step)},\n"
            f"  dates = list(from = 'range', pars = list(start = {_to_r_val(start_date)}, end = {_to_r_val(end_date)})),\n"
            f"  netcdf.data = list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2),\n"
            f"  bias.method = list(method = {_to_r_val(bias_method)}, dir = {_to_r_val(bias_dir)}, format = {_to_r_val(bias_format)}),\n"
            f"  output = list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)}),\n"
            "  GUI = FALSE\n"
            ")\n"
        )
        return self._execute_r_code(r_cmd, log_dir=log_dir, job_name=f"apply_bias_precip_{start_date}_{end_date}")

    # =========================================================================
    # STEP 3: MERGING DATA (RAINFALL & TEMPERATURE)
    # =========================================================================

    def merge_rainfall(
        self,
        time_step: str,
        start_date: str,
        end_date: str,
        station_file: Union[str, Path],
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        output_dir: Union[str, Path],
        var_id: str = "precip",
        merge_method: str = "SBA",
        nrun: int = 3,
        pass_ratios: list[float] = [1.0, 0.75, 0.5],
        interp_method: str = "idw",
        nmin: int = 6,
        nmax: int = 16,
        maxdist: float = 1.5,
        use_block: bool = True,
        vargrd: bool = False,
        vgm_models: list[str] = ["Sph", "Exp", "Gau"],
        rnor_use: bool = True,
        rnor_wet: float = 1.0,
        rnor_smooth: bool = True,
        shapefile_path: Optional[Union[str, Path]] = None,
        dem_file: Optional[Union[str, Path]] = None,
        auxvar: Optional[Dict[str, bool]] = None,
        output_format: str = "rr_mrg_%s%s%s.nc",
        global_mrg_opts: Optional[Dict[str, Any]] = None,
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Run cdtMergingPrecipCMD in non-GUI mode (Step 3 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        r_lines = []
        if global_mrg_opts:
            r_lines.append(self.set_global_merging_options(global_mrg_opts))

        blank_dict = {
            "data": shapefile_path is not None and bool(shapefile_path),
            "shapefile": str(shapefile_path) if shapefile_path else "",
        }

        auxvar_dict = auxvar or {"dem": False, "slope": False, "aspect": False, "lon": False, "lat": False}
        dem_varid = "elevation" if (dem_file and "gebco" in str(dem_file).lower()) else "dem"
        dem_dict = {"file": str(dem_file) if dem_file else "", "varid": dem_varid, "ilon": 1, "ilat": 2}

        r_cmd = (
            "res <- cdtMergingClimDataCMD(\n"
            "  variable = 'rain',\n"
            f"  time.step = {_to_r_val(time_step)},\n"
            f"  dates = list(from = 'range', pars = list(start = {_to_r_val(start_date)}, end = {_to_r_val(end_date)})),\n"
            f"  station.data = list(file = {_to_r_val(station_file)}, sep = ',', na.strings = '-99'),\n"
            f"  netcdf.data = list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2),\n"
            f"  merge.method = list(method = {_to_r_val(merge_method)}, nrun = {_to_r_val(nrun)}, pass = {_to_r_val(pass_ratios)}),\n"
            f"  interp.method = list(method = {_to_r_val(interp_method)}, nmin = {_to_r_val(nmin)}, nmax = {_to_r_val(nmax)}, maxdist = {_to_r_val(maxdist)}, use.block = {_to_r_val(use_block)}, vargrd = {_to_r_val(vargrd)}, vgm.model = {_to_r_val(vgm_models)}),\n"
            f"  auxvar = {_to_r_val(auxvar_dict)},\n"
            f"  dem.data = {_to_r_val(dem_dict)},\n"
            f"  grid = list(from = 'data', pars = NULL),\n"
            f"  RnoR = list(use = {_to_r_val(rnor_use)}, wet = {_to_r_val(rnor_wet)}, smooth = {_to_r_val(rnor_smooth)}),\n"
            f"  blank = {_to_r_val(blank_dict)},\n"
            f"  output = list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)}),\n"
            f"  precision = list(from.data = TRUE, prec = 'short'),\n"
            "  GUI = FALSE\n"
            ")\n"
        )
        r_lines.append(r_cmd)
        return self._execute_r_code("\n".join(r_lines), log_dir=log_dir, job_name=f"merge_precip_{start_date}_{end_date}")

    def merge_temperature(
        self,
        time_step: str,
        start_date: str,
        end_date: str,
        station_file: Union[str, Path],
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        output_dir: Union[str, Path],
        var_id: str = "temp",
        merge_method: str = "RK",
        nrun: int = 3,
        pass_ratios: list[float] = [1.0, 0.75, 0.5],
        interp_method: str = "idw",
        nmin: int = 8,
        nmax: int = 24,
        maxdist: float = 3.5,
        use_block: bool = True,
        vargrd: bool = False,
        vgm_models: list[str] = ["Sph", "Exp", "Gau", "Pen"],
        dem_file: Optional[Union[str, Path]] = None,
        auxvar: Optional[Dict[str, bool]] = None,
        shapefile_path: Optional[Union[str, Path]] = None,
        output_format: str = "tmax_mrg_%s%s%s.nc",
        global_mrg_opts: Optional[Dict[str, Any]] = None,
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Run cdtMergingClimDataCMD for temperature in non-GUI mode (Step 3 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        r_lines = []
        if global_mrg_opts:
            r_lines.append(self.set_global_merging_options(global_mrg_opts))

        blank_dict = {
            "data": shapefile_path is not None and bool(shapefile_path),
            "shapefile": str(shapefile_path) if shapefile_path else "",
        }

        auxvar_dict = auxvar or {"dem": True, "slope": True, "aspect": False, "lon": True, "lat": True}
        dem_varid = "elevation" if (dem_file and "gebco" in str(dem_file).lower()) else "dem"
        dem_dict = {"file": str(dem_file) if dem_file else "", "varid": dem_varid, "ilon": 1, "ilat": 2}

        r_cmd = (
            "res <- cdtMergingClimDataCMD(\n"
            "  variable = 'temp',\n"
            f"  time.step = {_to_r_val(time_step)},\n"
            f"  dates = list(from = 'range', pars = list(start = {_to_r_val(start_date)}, end = {_to_r_val(end_date)})),\n"
            f"  station.data = list(file = {_to_r_val(station_file)}, sep = ',', na.strings = '-99'),\n"
            f"  netcdf.data = list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2),\n"
            f"  merge.method = list(method = {_to_r_val(merge_method)}, nrun = {_to_r_val(nrun)}, pass = {_to_r_val(pass_ratios)}),\n"
            f"  interp.method = list(method = {_to_r_val(interp_method)}, nmin = {_to_r_val(nmin)}, nmax = {_to_r_val(nmax)}, maxdist = {_to_r_val(maxdist)}, use.block = {_to_r_val(use_block)}, vargrd = {_to_r_val(vargrd)}, vgm.model = {_to_r_val(vgm_models)}),\n"
            f"  auxvar = {_to_r_val(auxvar_dict)},\n"
            f"  dem.data = {_to_r_val(dem_dict)},\n"
            f"  grid = list(from = 'data', pars = NULL),\n"
            f"  RnoR = list(use = FALSE, wet = 1.0, smooth = FALSE),\n"
            f"  blank = {_to_r_val(blank_dict)},\n"
            f"  output = list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)}),\n"
            f"  precision = list(from.data = TRUE, prec = 'short'),\n"
            "  GUI = FALSE\n"
            ")\n"
        )
        r_lines.append(r_cmd)
        return self._execute_r_code("\n".join(r_lines), log_dir=log_dir, job_name=f"merge_temp_{start_date}_{end_date}")
