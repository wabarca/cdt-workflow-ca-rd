# 06. Plantillas y Scripts de Producción

En este documento se presentan scripts listos para ser adaptados y ejecutados en servidores o tareas automatizadas.

---

## 1. Script de Producción: Fusión de Precipitación Diaria (`pipeline_merging_precip.R`)

```r
#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(CDT)
})

# 1. Configuración de Directorios y Rutas
BASE_DIR       <- "D:/ClimateData"
STN_FILE       <- file.path(BASE_DIR, "stations/daily_precip_cdt.csv")
SATELLITE_DIR  <- file.path(BASE_DIR, "satellite/gpm_imerg_v07")
OUTPUT_DIR     <- file.path(BASE_DIR, "merged/daily_precip")
SHAPEFILE_PATH <- file.path(BASE_DIR, "gis/country_boundary.shp")

# 2. Configuración de Fechas a Procesar
# Puede recibir argumentos de línea de comandos si se desea: args <- commandArgs(trailingOnly = TRUE)
START_DATE <- "20230101"
END_DATE   <- "20230131"

cat(sprintf("=== Iniciando Merging de Precipitación: %s a %s ===\n", START_DATE, END_DATE))

# 3. Opciones Globales de Fusión
merging.options(
  mrgMinNumberSTN       = 5,
  rkMinNumberSTN        = 8,
  vgmMinNumberSTN       = 8,
  useLocalInterpolation = TRUE,
  powerWeightIDW        = 2.0,
  RnoRModel             = "logit",
  RnoRCutOff            = 3,
  RnoRSmoothingPixels   = 2
)

# 4. Invocación de la función no-GUI
status <- cdtMergingPrecipCMD(
  time.step = "daily",
  dates = list(
    from = "range", 
    pars = list(start = START_DATE, end = END_DATE)
  ),
  station.data = list(
    file = STN_FILE, 
    sep = ",", 
    na.strings = "-99"
  ),
  netcdf.data = list(
    dir = SATELLITE_DIR, 
    format = "imerg_%s%s%s.nc",
    varid = "precip", 
    ilon = 1, 
    ilat = 2
  ),
  merge.method = list(
    method = "SBA",               # O "RK" con DEM
    nrun = 3, 
    pass = c(1.0, 0.75, 0.5)
  ),
  interp.method = list(
    method = "idw",              # O "okr"
    nmin = 6, 
    nmax = 16, 
    maxdist = 1.5,
    use.block = TRUE, 
    vargrd = FALSE
  ),
  grid = list(from = "data", pars = NULL),
  RnoR = list(use = TRUE, wet = 1.0, smooth = TRUE),
  blank = list(data = TRUE, shapefile = SHAPEFILE_PATH),
  output = list(dir = OUTPUT_DIR, format = "rr_mrg_%s%s%s.nc"),
  precision = list(from.data = TRUE, prec = "short"),
  GUI = FALSE
)

if (!is.null(status) && status == 0) {
  cat("=== Merging completado exitosamente ===\n")
} else {
  cat("=== Ocurrió una advertencia o error durante la ejecución. Revisar log_file.txt ===\n")
}
```

---

## 2. Script de Producción: Fusión de Temperatura Máxima Diaria con DEM (`pipeline_merging_temp.R`)

```r
#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(CDT)
})

# 1. Configuración de Directorios y Rutas
BASE_DIR       <- "D:/ClimateData"
STN_FILE       <- file.path(BASE_DIR, "stations/daily_tmax_cdt.csv")
REANALYSIS_DIR <- file.path(BASE_DIR, "reanalysis/era5_land_tmax")
DEM_FILE       <- file.path(BASE_DIR, "topography/srtm_dem_90m.nc")
OUTPUT_DIR     <- file.path(BASE_DIR, "merged/daily_tmax")
SHAPEFILE_PATH <- file.path(BASE_DIR, "gis/country_boundary.shp")

START_DATE <- "20230101"
END_DATE   <- "20230131"

cat(sprintf("=== Iniciando Merging de Temperatura (Tmax): %s a %s ===\n", START_DATE, END_DATE))

# 2. Opciones Globales de Fusión
merging.options(
  mrgMinNumberSTN       = 5,
  rkMinNumberSTN        = 8,
  useLocalInterpolation = TRUE,
  powerWeightIDW        = 2.0
)

# 3. Invocación de Merging con Regression Kriging (RK)
status <- cdtMergingTempCMD(
  time.step = "daily",
  dates = list(
    from = "range", 
    pars = list(start = START_DATE, end = END_DATE)
  ),
  station.data = list(
    file = STN_FILE, 
    sep = ",", 
    na.strings = "-99"
  ),
  netcdf.data = list(
    dir = REANALYSIS_DIR, 
    format = "era5_tmax_%s%s%s.nc",
    varid = "t2m", 
    ilon = 1, 
    ilat = 2
  ),
  merge.method = list(
    method = "RK", 
    nrun = 3, 
    pass = c(1.0, 0.75, 0.5)
  ),
  interp.method = list(
    method = "idw", 
    nmin = 8, 
    nmax = 24, 
    maxdist = 3.5,
    use.block = TRUE, 
    vargrd = FALSE
  ),
  auxvar = list(
    dem = TRUE,
    slope = TRUE,
    aspect = FALSE,
    lon = TRUE,
    lat = TRUE
  ),
  dem.data = list(
    file = DEM_FILE, 
    varid = "elevation", 
    ilon = 1, 
    ilat = 2
  ),
  grid = list(from = "data", pars = NULL),
  blank = list(data = TRUE, shapefile = SHAPEFILE_PATH),
  output = list(dir = OUTPUT_DIR, format = "tmax_mrg_%s%s%s.nc"),
  GUI = FALSE
)

if (!is.null(status) && status == 0) {
  cat("=== Merging de temperatura completado exitosamente ===\n")
} else {
  cat("=== Revisar log_file.txt para detalles del procesamiento ===\n")
}
```

---

## 3. Script de Automatización Bash / Cron

Para ejecutar el pipeline diario de forma desatendida en un servidor Linux:

```bash
#!/bin/bash
# crontab: 0 4 * * * /opt/scripts/run_daily_merging.sh >> /var/log/cdt_merging.log 2>&1

set -e

TODAY=$(date +%Y%m%d)
YESTERDAY=$(date -d "yesterday" +%Y%m%d)

echo "[$(date)] Iniciando procesamiento de CDT para fecha: $YESTERDAY"

# 1. Ejecutar script de R
Rscript /opt/scripts/pipeline_merging_precip.R

# 2. Validar código de salida
if [ $? -eq 0 ]; then
    echo "[$(date)] Proceso de CDT finalizado con éxito."
else
    echo "[$(date)] Error en la ejecución de CDT." >&2
    exit 1
fi
```

---

## 4. Automatización con el Lanzador de Python en Producción

Para entornos donde se requiere control de versiones de experimentos (YAML), partición de estaciones de validación independiente y ensamblado NetCDF 3D estándar CF-1.8:

```bash
# Ejecutar verificación del entorno y herramientas R
python launcher/experiment_runner.py --check-env

# Ejecutar corridas de producción por suite:
python launcher/experiment_runner.py --suite rainfall   # 10 Experimentos de Lluvia
python launcher/experiment_runner.py --suite tmax       # 8 Experimentos de Tmax
python launcher/experiment_runner.py --suite tmin       # 8 Experimentos de Tmin

# Ejecutar corrida batch completa (26 Experimentos, 1991–2020)
python launcher/experiment_runner.py --suite all
```

