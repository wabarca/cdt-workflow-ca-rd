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
            # Deteccion adaptativa y segura de memoria en Windows:
            # CDT paralelizado en Windows crea procesos hijos Rscript mediante sockets.
            # Cada proceso R de interpolacion espacial consume entre 350-500 MB.
            # Para evitar OOM / rotura de socket (serialize error writing to connection),
            # calculamos el maximo seguro con base en la memoria libre disponible.
            core_setup = (
                "avail_mem_gb <- tryCatch({\n"
                "  if (.Platform$OS.type == 'windows') {\n"
                "    mem_info <- system2('wmic', c('OS', 'get', 'FreePhysicalMemory', '/Value'), stdout = TRUE, stderr = FALSE)\n"
                "    free_kb <- as.numeric(gsub('[^0-9]', '', grep('FreePhysicalMemory', mem_info, value = TRUE)))\n"
                "    if (length(free_kb) > 0 && !is.na(free_kb)) free_kb / 1024^2 else 6.0\n"
                "  } else 8.0\n"
                "}, error = function(e) 6.0)\n"
                "# Limite seguro de memoria: maximo 1 nucleo por cada 0.8 GB libre, con tope de 8\n"
                "max_safe_cores <- max(2, floor(avail_mem_gb / 1.0))\n"
                "n_cores <- max(1, min(parallel::detectCores() - 1, max_safe_cores))\n"
                "cat(sprintf('[Parallel] Asignados %d nucleos (Memoria libre detectada: %.2f GB)\\n', n_cores, avail_mem_gb))\n"
            )
        
        repo_root = Path(__file__).resolve().parent.parent
        r_repo_root = str(repo_root).replace("\\", "/")

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
            f"repo_root <- \"{r_repo_root}\"\n"
            "# Inyeccion dinamica de parches locales R/ en el namespace de CDT\n"
            "tryCatch({\n"
            "  r_patch_files <- c(\n"
            "    file.path(repo_root, 'R', 'cdtUtilities_functions.R'),\n"
            "    file.path(repo_root, 'R', 'cdtMerging_functions.R'),\n"
            "    file.path(repo_root, 'R', 'cdtBias_functions.R'),\n"
            "    file.path(repo_root, 'R', 'cdtTemp_DownscalingReanal_Procs.R')\n"
            "  )\n"
            "  for (r_f in r_patch_files) {\n"
            "    if (file.exists(r_f)) {\n"
            "      tmp_env <- new.env(parent = cdt_env)\n"
            "      sys.source(r_f, envir = tmp_env)\n"
            "      for (fn in ls(envir = tmp_env)) {\n"
            "        tryCatch({\n"
            "          if (bindingIsLocked(fn, cdt_env)) unlockBinding(fn, cdt_env)\n"
            "          assign(fn, get(fn, envir = tmp_env), envir = cdt_env)\n"
            "          lockBinding(fn, cdt_env)\n"
            "        }, error = function(e) NULL)\n"
            "      }\n"
            "    }\n"
            "  }\n"
            "  cat('[CDT-Bridge] Parches locales de R/ cargados exitosamente en namespace CDT.\\n')\n"
            "}, error = function(e) cat(paste('[CDT-Bridge] Error cargando parches:', e$message, '\\n')))\n\n"
            "if (exists('.cdtData', envir = cdt_env)) {\n"
            "  cdt_data <- get('.cdtData', envir = cdt_env)\n"
            "  cdt_data$Config$parallel <- list(dopar = TRUE, detect.cores = FALSE, nb.cores = n_cores)\n"
            "}\n"
            "# Hook defensivo para garantizar que llamadas a cdtLocalConfigData preserven nb.cores\n"
            "tryCatch({\n"
            "  orig_local_cfg <- CDT:::cdtLocalConfigData\n"
            "  unlockBinding('cdtLocalConfigData', cdt_env)\n"
            "  assign('cdtLocalConfigData', function(...) {\n"
            "    orig_local_cfg(...)\n"
            "    if (exists('.cdtData', envir = asNamespace('CDT'))) {\n"
            "      .cd <- get('.cdtData', envir = asNamespace('CDT'))\n"
            "      .cd$Config$parallel <- list(dopar = TRUE, detect.cores = FALSE, nb.cores = n_cores)\n"
            "    }\n"
            "  }, envir = cdt_env)\n"
            "  lockBinding('cdtLocalConfigData', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
            "# Hook defensivo Headless para redirigir mensajes de GUI a la consola (evita error Tcl/Tk)\n"
            "tryCatch({\n"
            "  unlockBinding('Insert.Messages.Out', cdt_env)\n"
            "  assign('Insert.Messages.Out', function(texta, format = FALSE, type = c('error', 'warning', 'info', 'success'), GUI = FALSE) {\n"
            "    cat(paste(texta, collapse = '\\n'), '\\n')\n"
            "  }, envir = cdt_env)\n"
            "  lockBinding('Insert.Messages.Out', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
            "# Hook defensivo Headless para permitir lectura automatica de STN.file sin GUI OpenFiles\n"
            "tryCatch({\n"
            "  unlockBinding('getStnOpenData', cdt_env)\n"
            "  assign('getStnOpenData', function(file.stnfl) {\n"
            "    read.table(file.stnfl, sep = ',', na.strings = '-99', stringsAsFactors = FALSE, header = FALSE)\n"
            "  }, envir = cdt_env)\n"
            "  lockBinding('getStnOpenData', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
            # Hook defensivo Headless para getCDTdataAndDisplayMsg (evita dialogo GUI Tk)
            "tryCatch({\n"
            "  unlockBinding('getCDTdataAndDisplayMsg', cdt_env)\n"
            "  assign('getCDTdataAndDisplayMsg', function(donne, tstep, filename) {\n"
            "    if (is.null(donne)) return(NULL)\n"
            "    CDT:::splitCDTData(donne, tstep)\n"
            "  }, envir = cdt_env)\n"
            "  lockBinding('getCDTdataAndDisplayMsg', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
            # Hook defensivo Headless para asegurar lectura automatica de DEM en getIndex.AllOpenFiles
            "tryCatch({\n"
            "  unlockBinding('getIndex.AllOpenFiles', cdt_env)\n"
            "  assign('getIndex.AllOpenFiles', function(nomfile) {\n"
            "    if (inherits(nomfile, 'tclVar')) nomfile <- tclvalue(nomfile)\n"
            "    if (!is.character(nomfile) || length(nomfile) == 0 || nomfile == '') return(NULL)\n"
            "    if (!exists('.cdtData', envir = asNamespace('CDT'))) return(NULL)\n"
            "    .cd <- get('.cdtData', envir = asNamespace('CDT'))\n"
            "    if (is.null(.cd$OpenFiles$Data)) .cd$OpenFiles$Data <- list()\n"
            "    all.open.file <- do.call(c, lapply(.cd$OpenFiles$Data, '[[', 1))\n"
            "    jfile <- which(all.open.file == nomfile)\n"
            "    if (length(jfile) > 0) return(jfile[1])\n"
            "    if (file.exists(nomfile)) {\n"
            "      nc <- ncdf4::nc_open(nomfile)\n"
            "      vars <- names(nc$var)\n"
            "      vname <- vars[1]\n"
            "      for (v in c('elevation', 'dem', 'z', 'temp', 'tmax', 'tmin', 'precip')) {\n"
            "        if (v %in% vars) { vname <- v; break }\n"
            "      }\n"
            "      dimnames <- tolower(sapply(nc$var[[vname]]$dim, function(d) d$name))\n"
            "      ilon <- which(dimnames %in% c('lon', 'longitude', 'x'))[1]\n"
            "      ilat <- which(dimnames %in% c('lat', 'latitude', 'y'))[1]\n"
            "      if (is.na(ilon) || length(ilon) == 0) ilon <- 1\n"
            "      if (is.na(ilat) || length(ilat) == 0) ilat <- 2\n"
            "      lon <- nc$var[[vname]]$dim[[ilon]]$vals\n"
            "      lat <- nc$var[[vname]]$dim[[ilat]]$vals\n"
            "      z <- ncdf4::ncvar_get(nc, vname)\n"
            "      ncdf4::nc_close(nc)\n"
            "      xo <- order(lon)\n"
            "      yo <- order(lat)\n"
            "      lon <- lon[xo]\n"
            "      lat <- lat[yo]\n"
            "      if (is.matrix(z)) z <- z[xo, yo, drop = FALSE]\n"
            "      dem_data <- list(x = lon, y = lat, lon = lon, lat = lat, z = z)\n"
            "      idx <- length(.cd$OpenFiles$Data) + 1\n"
            "      .cd$OpenFiles$Data[[idx]] <- list(nomfile, dem_data)\n"
            "      return(idx)\n"
            "    }\n"
            "    return(NULL)\n"
            "  }, envir = cdt_env)\n"
            "  lockBinding('getIndex.AllOpenFiles', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
            "# Hook defensivo Headless para extraer metadatos de NetCDF sample sin GUI OpenFiles\n"
            "tryCatch({\n"
            "  unlockBinding('getNCDFSampleData', cdt_env)\n"
            "  assign('getNCDFSampleData', function(file.netcdf) {\n"
            "    if (is.character(file.netcdf) && file.exists(file.netcdf)) {\n"
            "      nc <- ncdf4::nc_open(file.netcdf)\n"
            "      vars <- names(nc$var)\n"
            "      vname <- vars[1]\n"
            "      for (v in c('precip', 'rainfall', 'temp', 'tmax', 'tmin', 'elevation', 'dem')) {\n"
            "        if (v %in% vars) { vname <- v; break }\n"
            "      }\n"
            "      dimnames <- tolower(sapply(nc$var[[vname]]$dim, function(d) d$name))\n"
            "      ilon <- which(dimnames %in% c('lon', 'longitude', 'x'))[1]\n"
            "      ilat <- which(dimnames %in% c('lat', 'latitude', 'y'))[1]\n"
            "      if (is.na(ilon) || length(ilon) == 0) ilon <- 1\n"
            "      if (is.na(ilat) || length(ilat) == 0) ilat <- 2\n"
            "      lon <- nc$var[[vname]]$dim[[ilon]]$vals\n"
            "      lat <- nc$var[[vname]]$dim[[ilat]]$vals\n"
            "      xo <- order(lon)\n"
            "      yo <- order(lat)\n"
            "      lon <- lon[xo]\n"
            "      lat <- lat[yo]\n"
            "      varinfo <- nc$var[[vname]][c('name', 'prec', 'units', 'longname', 'missval')]\n"
            "      diminfo <- nc$var[[vname]]$dim\n"
            "      ncdf4::nc_close(nc)\n"
            "      return(list(lon = lon, lat = lat, x = lon, y = lat, varid = vname, ilon = ilon, ilat = ilat, xo = xo, yo = yo, nx = length(lon), ny = length(lat), varinfo = varinfo, diminfo = diminfo))\n"
            "    }\n"
            "    return(NULL)\n"
            "  }, envir = cdt_env)\n"
            "  lockBinding('getNCDFSampleData', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
            "# Hook defensivo Headless para evitar llamadas de GUI Tk tabs\n"
            "tryCatch({\n"
            "  unlockBinding('Display_Output_Console_Tab', cdt_env)\n"
            "  assign('Display_Output_Console_Tab', function(...) NULL, envir = cdt_env)\n"
            "  lockBinding('Display_Output_Console_Tab', cdt_env)\n"
            "}, error = function(e) NULL)\n"
            "tryCatch({\n"
            "  unlockBinding('update.OpenTabs', cdt_env)\n"
            "  assign('update.OpenTabs', function(...) NULL, envir = cdt_env)\n"
            "  lockBinding('update.OpenTabs', cdt_env)\n"
            "}, error = function(e) NULL)\n\n"
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
    # STEP 0A: COMPUTE DOWNSCALING COEFFICIENTS (TEMPERATURE)
    # =========================================================================

    def compute_downscaling_coefficients_temp(
        self,
        time_step: str,
        station_file: Union[str, Path],
        dem_file: Union[str, Path],
        output_dir: Union[str, Path],
        base_period_all_years: bool = True,
        start_year: int = 1991,
        end_year: int = 2020,
        min_year: int = 10,
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Compute lapse rate downscaling coefficients station-DEM (Step 1 in Temperature CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        stn_str = str(station_file).replace("\\", "/")
        dem_str = str(dem_file).replace("\\", "/")
        out_str = str(output_dir).replace("\\", "/")

        r_cmd = (
            ".cdt_env <- asNamespace('CDT')\n"
            "CDT:::cdtLocalConfigData()\n"
            ".cd <- get('.cdtData', envir = .cdt_env)\n"
            f".cd$GalParams$period <- {_to_r_val(time_step)}\n"
            f".cd$GalParams$IO.files$STN.file <- {_to_r_val(stn_str)}\n"
            f".cd$GalParams$IO.files$DEM.file <- {_to_r_val(dem_str)}\n"
            f".cd$GalParams$IO.files$dir2save <- {_to_r_val(out_str)}\n"
            f".cd$GalParams$base.period <- list(all.years = {_to_r_val(base_period_all_years)}, start.year = {start_year}, end.year = {end_year}, min.year = {min_year})\n"
            ".cd$GalParams$message <- list('6' = 'Computing Downscaling Coefficients...', '7' = 'Error reading DEM', '8' = 'Calculating GLM lapse rate...', '9' = 'Not enough years', '10' = 'Downscaling coefficients computed successfully')\n"
            "res <- CDT:::Temp_execCoefDown()\n"
            "if (is.null(res) || res != 0) stop('Temp_execCoefDown fallo: retorno NULL o codigo no-cero')\n"
        )
        return self._execute_r_code(r_cmd, log_dir=log_dir, job_name="compute_down_coeffs_temp")

    # =========================================================================
    # STEP 0B: DOWNSCALE TEMPERATURE REANALYSIS/GRIDS (TEMPERATURE)
    # =========================================================================

    def downscale_temperature(
        self,
        time_step: str,
        start_date: str,
        end_date: str,
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        down_coef_file: Union[str, Path],
        dem_file: Union[str, Path],
        output_dir: Union[str, Path],
        var_id: str = "temp",
        interp_method: str = "blin",
        nmin: int = 4,
        nmax: int = 12,
        maxdist: float = 3.5,
        use_block: bool = False,
        vgm_model: str = "Sph",
        grid_from: str = "data",
        output_format: str = "tmax_down_%s%s%s.nc",
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Downscale reanalysis/satellite grids to DEM resolution (Step 2 in Temperature CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        sd_str = str(start_date)
        ed_str = str(end_date)
        s_yr = int(sd_str[:4])
        s_mo = int(sd_str[4:6]) if len(sd_str) >= 6 else 1
        s_dy = int(sd_str[6:8]) if len(sd_str) >= 8 else 1
        e_yr = int(ed_str[:4])
        e_mo = int(ed_str[4:6]) if len(ed_str) >= 6 else 12
        e_dy = int(ed_str[6:8]) if len(ed_str) >= 8 else 31

        sample_path = ""
        if netcdf_dir and Path(netcdf_dir).exists():
            cand_files = list(Path(netcdf_dir).glob("*.nc"))
            if cand_files:
                sample_path = str(cand_files[0]).replace("\\", "/")

        coef_str = str(down_coef_file).replace("\\", "/")
        dem_str = str(dem_file).replace("\\", "/")
        out_str = str(output_dir).replace("\\", "/")

        r_cmd = (
            ".cdt_env <- asNamespace('CDT')\n"
            "CDT:::cdtLocalConfigData()\n"
            ".cd <- get('.cdtData', envir = .cdt_env)\n"
            f".cd$GalParams$period <- {_to_r_val(time_step)}\n"
            f".cd$GalParams$date.range <- list(start.year = {s_yr}, start.mon = {s_mo}, start.day = {s_dy}, end.year = {e_yr}, end.mon = {e_mo}, end.day = {e_dy})\n"
            f".cd$GalParams$DownCoef.file <- {_to_r_val(coef_str)}\n"
            f".cd$GalParams$DEM.file <- {_to_r_val(dem_str)}\n"
            f".cd$GalParams$REANAL <- list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, sample = {_to_r_val(sample_path)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2)\n"
            f".cd$GalParams$grid <- list(from = {_to_r_val(grid_from)}, ncfile = {_to_r_val(dem_str)})\n"
            f".cd$GalParams$interp <- list(method = {_to_r_val(interp_method)}, nmin = {nmin}, nmax = {nmax}, maxdist = {maxdist}, use.block = {_to_r_val(use_block)}, vgm.model = {_to_r_val(vgm_model)}, minstn = 5)\n"
            f".cd$GalParams$output <- list(dir = {_to_r_val(out_str)}, format = {_to_r_val(output_format)})\n"
            ".cd$GalParams$message <- list('8' = 'Downscaling Reanalysis Data...', '9' = 'Downscaling coefficients file not found', '10' = 'Error reading downscaling coefficients', '11' = 'Error reading DEM', '12' = 'Error reading grid NetCDF', '13' = 'Error date range Reanalysis', '14' = 'Downscaling daily temperature grids...', '15' = 'Downscaling completed successfully')\n"
            "res <- CDT:::Temp_execDownscaling()\n"
            "if (is.null(res) || res != 0) stop('Temp_execDownscaling fallo: retorno NULL o codigo no-cero')\n"
        )
        return self._execute_r_code(r_cmd, log_dir=log_dir, job_name=f"downscale_temp_{start_date}_{end_date}")

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
        var_id: Optional[str] = None,
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
        
        # Normalize method names
        bm_raw = str(bias_method).lower()
        if bm_raw in ("qm.dist", "qmdist"):
            cdt_bias_m = "qmdist"
        elif bm_raw in ("qm.ecdf", "qmecdf"):
            cdt_bias_m = "qmecdf"
        elif bm_raw in ("multiplicative.bias.var", "mbvar"):
            cdt_bias_m = "mbvar"
        elif bm_raw in ("admon", "mbmon", "additive.bias.mon"):
            cdt_bias_m = "mbmon"
        else:
            cdt_bias_m = bias_method

        im_raw = str(interp_method).lower()
        if im_raw == "block_okr":
            cdt_interp_m = "okr"
            use_block = True
        elif im_raw in ("nn3d", "nn", "nearest3d"):
            cdt_interp_m = "nn3d"
        elif im_raw in ("idw", "okr", "nns"):
            cdt_interp_m = im_raw
        else:
            # En CDT, el calculo de coeficientes de sesgo (Paso 1) unicamente soporta:
            # 'idw', 'okr', 'nns' y 'nn3d'. Metodos como 'shepard', 'barnes', 'cressman'
            # y 'sphere' son exclusivos del Paso 3 (Merging). Si se especifican para sesgo,
            # mapeamos de forma segura y defensiva a 'idw' para evitar que 'interp.grid' falle.
            cdt_interp_m = "idw"

        # Si se solicita NN-3D pero no existe archivo DEM, hacer fallback a IDW
        if cdt_interp_m == "nn3d" and not dem_str:
            cdt_interp_m = "idw" 

        distr_raw = str(distr_name).lower()
        if var_clim == "rain":
            if "weibull" in distr_raw:
                cdt_distr = "bernweibull"
            elif "lnorm" in distr_raw or "lognormal" in distr_raw:
                cdt_distr = "bernlnorm"
            else:
                cdt_distr = "berngamma"
        else:
            if "snorm" in distr_raw or "skew" in distr_raw:
                cdt_distr = "snorm"
            elif "gumbel" in distr_raw:
                cdt_distr = "gumbel"
            elif "lnorm" in distr_raw or "lognormal" in distr_raw:
                cdt_distr = "lnorm"
            elif "gamma" in distr_raw:
                cdt_distr = "gamma"
            elif "weibull" in distr_raw:
                cdt_distr = "weibull"
            else:
                cdt_distr = "norm"

        sample_path = ""
        if netcdf_dir and Path(netcdf_dir).exists():
            cand_files = list(Path(netcdf_dir).glob("*.nc"))
            if cand_files:
                sample_path = str(cand_files[0]).replace("\\", "/")

        dem_str = str(dem_file).replace("\\", "/") if dem_file and Path(dem_file).exists() else ""
        effective_varid = var_id if var_id else ("precip" if var_clim == "rain" else "temp")

        r_lines = []
        if global_bias_opts:
            r_lines.append(self.set_global_bias_options(global_bias_opts))

        r_cmd = (
            ".cdt_env <- asNamespace('CDT')\n"
            "CDT:::cdtLocalConfigData()\n"
            ".cd <- get('.cdtData', envir = .cdt_env)\n"
            f".cd$GalParams$action <- 'coefbias.{var_clim}'\n"
            f".cd$GalParams$period <- {_to_r_val(time_step)}\n"
            f".cd$GalParams$STN.file <- {_to_r_val(station_file)}\n"
            f".cd$GalParams$INPUT <- list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, sample = {_to_r_val(sample_path)}, varid = {_to_r_val(effective_varid)}, ilon = 1, ilat = 2)\n"
            f".cd$GalParams$base.period <- list(all.years = {_to_r_val(base_period_all_years)}, start.year = {start_year}, end.year = {end_year}, min.year = {min_year})\n"
            f".cd$GalParams$BIAS <- list(method = {_to_r_val(cdt_bias_m)}, distr.name = {_to_r_val(cdt_distr)}, min.length = {min_length}, ts.support = 'points', chunks.exist = FALSE, chunks.dir = '', blon = 1, blat = 1)\n"
            f".cd$GalParams$interp <- list(method = {_to_r_val(cdt_interp_m)}, nmin = {nmin}, nmax = {nmax}, maxdist = {maxdist}, use.block = {_to_r_val(use_block)}, vgm.model = {_to_r_val(vgm_models)}, minstn = 10, demfile = {_to_r_val(dem_str)})\n"
            ".cd$GalParams$grid <- list(from = 'data', pars = NULL)\n"
            f".cd$GalParams$output <- list(dir = {_to_r_val(output_dir)})\n"
            ".cd$GalParams$message <- list('7' = 'Computing bias coefficients...', '8' = 'Error reading sample', '9' = 'Error reading DEM', '10' = 'Error grid', '11' = 'Error NetCDF info', '12' = 'Not enough years')\n"
            "res <- CDT:::computeBiasCoeffClimData()\n"
            "if (is.null(res) || res != 0) stop('computeBiasCoeffClimData fallo: retorno NULL o codigo no-cero')\n"
        )
        r_lines.append(r_cmd)
        return self._execute_r_code("\n".join(r_lines), log_dir=log_dir, job_name=f"compute_bias_{var_clim}")

    # =========================================================================
    # STEP 2: APPLY BIAS CORRECTION (UNIVERSAL ENGINE CDT:::biasCorrectionClimData)
    # =========================================================================

    def apply_bias_correction_precip(
        self,
        time_step: str,
        start_date: str,
        end_date: str,
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        bias_dir: Union[str, Path],
        bias_format: Optional[str] = None,
        bias_method: str = "mbvar",
        output_dir: Union[str, Path] = "output",
        var_id: str = "precip",
        output_format: str = "rr_adj_%s%s%s.nc",
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Apply bias correction to precipitation NetCDF files (Step 2 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        bm = str(bias_method).lower()
        if bm in ("qm.dist", "qmdist"):
            cdt_bias_m = "qmdist"
        elif bm in ("qm.ecdf", "qmecdf"):
            cdt_bias_m = "qmecdf"
        elif bm in ("mbmon", "admon"):
            cdt_bias_m = "mbmon"
        else:
            cdt_bias_m = "mbvar"

        sample_path = ""
        if netcdf_dir and Path(netcdf_dir).exists():
            cand_files = list(Path(netcdf_dir).glob("*.nc"))
            if cand_files:
                sample_path = str(cand_files[0]).replace("\\", "/")

        p_bias_dir = Path(bias_dir)
        cand_rds = list(p_bias_dir.rglob("input_parameters.rds"))
        eff_bias_dir = str(cand_rds[0].parent).replace("\\", "/") if cand_rds else str(bias_dir).replace("\\", "/")

        sd_str = str(start_date)
        ed_str = str(end_date)
        s_yr = int(sd_str[:4])
        s_mo = int(sd_str[4:6]) if len(sd_str) >= 6 else 1
        s_dy = int(sd_str[6:8]) if len(sd_str) >= 8 else 1
        e_yr = int(ed_str[:4])
        e_mo = int(ed_str[4:6]) if len(ed_str) >= 6 else 12
        e_dy = int(ed_str[6:8]) if len(ed_str) >= 8 else 31

        r_cmd = (
            ".cdt_env <- asNamespace('CDT')\n"
            "CDT:::cdtLocalConfigData()\n"
            ".cd <- get('.cdtData', envir = .cdt_env)\n"
            ".cd$GalParams$action <- 'rmbias.rain'\n"
            f".cd$GalParams$period <- {_to_r_val(time_step)}\n"
            f".cd$GalParams$date.range <- list(start.year = {s_yr}, start.mon = {s_mo}, start.day = {s_dy}, end.year = {e_yr}, end.mon = {e_mo}, end.day = {e_dy})\n"
            f".cd$GalParams$INPUT <- list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, sample = {_to_r_val(sample_path)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2)\n"
            f".cd$GalParams$BIAS <- list(method = {_to_r_val(cdt_bias_m)}, dir = {_to_r_val(eff_bias_dir)})\n"
            f".cd$GalParams$output <- list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)})\n"
            ".cd$GalParams$message <- list('7' = 'Applying bias correction...', '8' = 'Error sample NetCDF', '9' = 'Error NetCDF info', '10' = 'Bounding box error')\n"
            "res <- CDT:::biasCorrectionClimData()\n"
            "if (is.null(res) || res != 0) stop('biasCorrectionClimData (precip) fallo: retorno NULL o codigo no-cero')\n"
        )
        return self._execute_r_code(r_cmd, log_dir=log_dir, job_name=f"apply_bias_precip_{start_date}_{end_date}")

    def apply_bias_correction_temp(
        self,
        time_step: str,
        start_date: str,
        end_date: str,
        netcdf_dir: Union[str, Path],
        netcdf_format: str,
        bias_dir: Union[str, Path],
        bias_format: Optional[str] = None,
        bias_method: str = "mbvar",
        output_dir: Union[str, Path] = "output",
        var_id: str = "temp",
        output_format: str = "tmax_adj_%s%s%s.nc",
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Apply bias correction to temperature NetCDF files (Step 2 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        bm = str(bias_method).lower()
        if bm in ("qm.dist", "qmdist"):
            cdt_bias_m = "qmdist"
        elif bm in ("qm.ecdf", "qmecdf"):
            cdt_bias_m = "qmecdf"
        elif bm in ("mbmon", "admon"):
            cdt_bias_m = "mbmon"
        else:
            cdt_bias_m = "mbvar"

        sample_path = ""
        if netcdf_dir and Path(netcdf_dir).exists():
            cand_files = list(Path(netcdf_dir).glob("*.nc"))
            if cand_files:
                sample_path = str(cand_files[0]).replace("\\", "/")

        p_bias_dir = Path(bias_dir)
        cand_rds = list(p_bias_dir.rglob("input_parameters.rds"))
        eff_bias_dir = str(cand_rds[0].parent).replace("\\", "/") if cand_rds else str(bias_dir).replace("\\", "/")

        sd_str = str(start_date)
        ed_str = str(end_date)
        s_yr = int(sd_str[:4])
        s_mo = int(sd_str[4:6]) if len(sd_str) >= 6 else 1
        s_dy = int(sd_str[6:8]) if len(sd_str) >= 8 else 1
        e_yr = int(ed_str[:4])
        e_mo = int(ed_str[4:6]) if len(ed_str) >= 6 else 12
        e_dy = int(ed_str[6:8]) if len(ed_str) >= 8 else 31

        r_cmd = (
            ".cdt_env <- asNamespace('CDT')\n"
            "CDT:::cdtLocalConfigData()\n"
            ".cd <- get('.cdtData', envir = .cdt_env)\n"
            ".cd$GalParams$action <- 'rmbias.temp'\n"
            f".cd$GalParams$period <- {_to_r_val(time_step)}\n"
            f".cd$GalParams$date.range <- list(start.year = {s_yr}, start.mon = {s_mo}, start.day = {s_dy}, end.year = {e_yr}, end.mon = {e_mo}, end.day = {e_dy})\n"
            f".cd$GalParams$INPUT <- list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, sample = {_to_r_val(sample_path)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2)\n"
            f".cd$GalParams$BIAS <- list(method = {_to_r_val(cdt_bias_m)}, dir = {_to_r_val(eff_bias_dir)})\n"
            f".cd$GalParams$output <- list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)})\n"
            ".cd$GalParams$message <- list('7' = 'Applying bias correction...', '8' = 'Error sample NetCDF', '9' = 'Error NetCDF info', '10' = 'Bounding box error')\n"
            "res <- CDT:::biasCorrectionClimData()\n"
            "if (is.null(res) || res != 0) stop('biasCorrectionClimData (temp) fallo: retorno NULL o codigo no-cero')\n"
        )
        return self._execute_r_code(r_cmd, log_dir=log_dir, job_name=f"apply_bias_temp_{start_date}_{end_date}")

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
        auxvar: Optional[Union[Dict[str, bool], list[str]]] = None,
        output_format: str = "rr_mrg_%s%s%s.nc",
        global_mrg_opts: Optional[Dict[str, Any]] = None,
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Run cdtMergingClimDataCMD for rainfall in non-GUI mode (Step 3 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        mm = str(merge_method).upper()
        if mm in ("RK", "REGR.KRIGING", "REGR_KRIGING"):
            cdt_merge_m = "RK"
        elif mm in ("BSC", "BARNES"):
            cdt_merge_m = "BSc"
        elif mm in ("CSC", "CRESSMAN"):
            cdt_merge_m = "CSc"
        else:
            cdt_merge_m = "SBA"

        im = str(interp_method).lower()
        if im == "block_okr":
            cdt_interp_m = "okr"
            use_block = True
        elif im in ("nn3d", "nn"):
            cdt_interp_m = "shepard"
        else:
            cdt_interp_m = im

        if isinstance(pass_ratios, list):
            clean_passes = []
            for p in pass_ratios:
                if isinstance(p, dict):
                    clean_passes.append(float(p.get("radius", 1.0)))
                elif isinstance(p, (int, float)):
                    clean_passes.append(float(p))
            if not clean_passes:
                clean_passes = [1.0, 0.75, 0.5] if nrun > 1 else [1.0]
        else:
            clean_passes = [1.0, 0.75, 0.5] if nrun > 1 else [1.0]

        r_lines = []
        if global_mrg_opts:
            r_lines.append(self.set_global_merging_options(global_mrg_opts))

        shp_exists = shapefile_path is not None and bool(shapefile_path) and Path(shapefile_path).exists()
        blank_dict = {
            "data": shp_exists,
            "shapefile": str(shapefile_path).replace("\\", "/") if shp_exists else "",
        }

        if isinstance(auxvar, list):
            auxvar_dict = {
                "dem": "dem" in auxvar,
                "slope": "slope" in auxvar,
                "aspect": "aspect" in auxvar,
                "lon": "lon" in auxvar or "lon_lat" in auxvar,
                "lat": "lat" in auxvar or "lon_lat" in auxvar,
            }
        elif isinstance(auxvar, dict):
            auxvar_dict = {
                "dem": bool(auxvar.get("dem", False)),
                "slope": bool(auxvar.get("slope", False)),
                "aspect": bool(auxvar.get("aspect", False)),
                "lon": bool(auxvar.get("lon", False) or auxvar.get("lon_lat", False)),
                "lat": bool(auxvar.get("lat", False) or auxvar.get("lon_lat", False)),
            }
        else:
            auxvar_dict = {"dem": False, "slope": False, "aspect": False, "lon": False, "lat": False}

        dem_exists = dem_file is not None and bool(dem_file) and Path(dem_file).exists()
        dem_varid = "elevation" if (dem_exists and "gebco" in str(dem_file).lower()) else "dem"
        dem_dict = {
            "file": str(dem_file).replace("\\", "/") if dem_exists else "",
            "varid": dem_varid,
            "ilon": 1,
            "ilat": 2,
        }

        r_cmd = (
            "res <- cdtMergingClimDataCMD(\n"
            "  variable = 'rain',\n"
            f"  time.step = {_to_r_val(time_step)},\n"
            f"  dates = list(from = 'range', pars = list(start = {_to_r_val(start_date)}, end = {_to_r_val(end_date)})),\n"
            f"  station.data = list(file = {_to_r_val(station_file)}, sep = ',', na.strings = '-99'),\n"
            f"  netcdf.data = list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2),\n"
            f"  merge.method = list(method = {_to_r_val(cdt_merge_m)}, nrun = {_to_r_val(nrun)}, pass = {_to_r_val(clean_passes)}),\n"
            f"  interp.method = list(method = {_to_r_val(cdt_interp_m)}, nmin = {_to_r_val(nmin)}, nmax = {_to_r_val(nmax)}, maxdist = {_to_r_val(maxdist)}, use.block = {_to_r_val(use_block)}, vargrd = {_to_r_val(vargrd)}, vgm.model = {_to_r_val(vgm_models)}),\n"
            f"  auxvar = {_to_r_val(auxvar_dict)},\n"
            f"  dem.data = {_to_r_val(dem_dict)},\n"
            f"  grid = list(from = 'data', pars = NULL),\n"
            f"  RnoR = list(use = {_to_r_val(rnor_use)}, wet = {_to_r_val(rnor_wet)}, smooth = {_to_r_val(rnor_smooth)}),\n"
            f"  blank = {_to_r_val(blank_dict)},\n"
            f"  output = list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)}),\n"
            f"  precision = list(from.data = TRUE, prec = 'short'),\n"
            "  GUI = FALSE\n"
            ")\n"
            "if (is.null(res) || res != 0) stop('cdtMergingClimDataCMD (rainfall) fallo: retorno NULL o codigo no-cero')\n"
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
        auxvar: Optional[Union[Dict[str, bool], list[str]]] = None,
        shapefile_path: Optional[Union[str, Path]] = None,
        output_format: str = "tmax_mrg_%s%s%s.nc",
        global_mrg_opts: Optional[Dict[str, Any]] = None,
        log_dir: Optional[Path] = None,
    ) -> Tuple[int, str, str, float]:
        """Run cdtMergingClimDataCMD for temperature in non-GUI mode (Step 3 in CDT)."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        mm = str(merge_method).upper()
        if mm in ("RK", "REGR.KRIGING", "REGR_KRIGING"):
            cdt_merge_m = "RK"
        elif mm in ("BSC", "BARNES"):
            cdt_merge_m = "BSc"
        elif mm in ("CSC", "CRESSMAN"):
            cdt_merge_m = "CSc"
        else:
            cdt_merge_m = "SBA"

        im = str(interp_method).lower()
        if im == "block_okr":
            cdt_interp_m = "okr"
            use_block = True
        elif im in ("nn3d", "nn"):
            cdt_interp_m = "shepard"
        else:
            cdt_interp_m = im

        if isinstance(pass_ratios, list):
            clean_passes = []
            for p in pass_ratios:
                if isinstance(p, dict):
                    clean_passes.append(float(p.get("radius", 1.0)))
                elif isinstance(p, (int, float)):
                    clean_passes.append(float(p))
            if not clean_passes:
                clean_passes = [1.0, 0.75, 0.5] if nrun > 1 else [1.0]
        else:
            clean_passes = [1.0, 0.75, 0.5] if nrun > 1 else [1.0]

        r_lines = []
        if global_mrg_opts:
            r_lines.append(self.set_global_merging_options(global_mrg_opts))

        shp_exists = shapefile_path is not None and bool(shapefile_path) and Path(shapefile_path).exists()
        blank_dict = {
            "data": shp_exists,
            "shapefile": str(shapefile_path).replace("\\", "/") if shp_exists else "",
        }

        if isinstance(auxvar, list):
            auxvar_dict = {
                "dem": "dem" in auxvar,
                "slope": "slope" in auxvar,
                "aspect": "aspect" in auxvar,
                "lon": "lon" in auxvar or "lon_lat" in auxvar,
                "lat": "lat" in auxvar or "lon_lat" in auxvar,
            }
        elif isinstance(auxvar, dict):
            auxvar_dict = {
                "dem": bool(auxvar.get("dem", True)),
                "slope": bool(auxvar.get("slope", True)),
                "aspect": bool(auxvar.get("aspect", False)),
                "lon": bool(auxvar.get("lon", True) or auxvar.get("lon_lat", True)),
                "lat": bool(auxvar.get("lat", True) or auxvar.get("lon_lat", True)),
            }
        else:
            auxvar_dict = {"dem": True, "slope": True, "aspect": False, "lon": True, "lat": True}

        dem_exists = dem_file is not None and bool(dem_file) and Path(dem_file).exists()
        dem_varid = "elevation" if (dem_exists and "gebco" in str(dem_file).lower()) else "dem"
        dem_dict = {
            "file": str(dem_file).replace("\\", "/") if dem_exists else "",
            "varid": dem_varid,
            "ilon": 1,
            "ilat": 2,
        }

        r_cmd = (
            "res <- cdtMergingClimDataCMD(\n"
            "  variable = 'temp',\n"
            f"  time.step = {_to_r_val(time_step)},\n"
            f"  dates = list(from = 'range', pars = list(start = {_to_r_val(start_date)}, end = {_to_r_val(end_date)})),\n"
            f"  station.data = list(file = {_to_r_val(station_file)}, sep = ',', na.strings = '-99'),\n"
            f"  netcdf.data = list(dir = {_to_r_val(netcdf_dir)}, format = {_to_r_val(netcdf_format)}, varid = {_to_r_val(var_id)}, ilon = 1, ilat = 2),\n"
            f"  merge.method = list(method = {_to_r_val(cdt_merge_m)}, nrun = {_to_r_val(nrun)}, pass = {_to_r_val(clean_passes)}),\n"
            f"  interp.method = list(method = {_to_r_val(cdt_interp_m)}, nmin = {_to_r_val(nmin)}, nmax = {_to_r_val(nmax)}, maxdist = {_to_r_val(maxdist)}, use.block = {_to_r_val(use_block)}, vargrd = {_to_r_val(vargrd)}, vgm.model = {_to_r_val(vgm_models)}),\n"
            f"  auxvar = {_to_r_val(auxvar_dict)},\n"
            f"  dem.data = {_to_r_val(dem_dict)},\n"
            f"  grid = list(from = 'data', pars = NULL),\n"
            f"  RnoR = list(use = FALSE, wet = 1.0, smooth = FALSE),\n"
            f"  blank = {_to_r_val(blank_dict)},\n"
            f"  output = list(dir = {_to_r_val(output_dir)}, format = {_to_r_val(output_format)}),\n"
            f"  precision = list(from.data = TRUE, prec = 'short'),\n"
            "  GUI = FALSE\n"
            ")\n"
            "if (is.null(res) || res != 0) stop('cdtMergingClimDataCMD (temperature) fallo: retorno NULL o codigo no-cero')\n"
        )
        r_lines.append(r_cmd)
        return self._execute_r_code("\n".join(r_lines), log_dir=log_dir, job_name=f"merge_temp_{start_date}_{end_date}")
