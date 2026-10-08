# 01. Automatización y Ejecución desde Terminal (CLI / Headless)

## 1. Introducción

Tradicionalmente, **Climate Data Tools (CDT)** se inicia en modo interactivo a través de una interfaz gráfica (GUI) desarrollada sobre `Tcl/Tk` ejecutando en R:

```r
library(CDT)
startCDT()
```

Sin embargo, para entornos de producción, servidores Linux/Windows sin entorno gráfico (servidores *headless*), pipelines operativos diarios y ejecuciones masivas por lotes (*batch jobs*), CDT dispone de una API de comandos no interactivos que operan directamente desde scripts de R y se ejecutan vía terminal con `Rscript`.

---

## 2. Funciones de Línea de Comandos Exportadas

Las principales funciones programáticas disponibles en el espacio de nombres (`NAMESPACE`) de CDT son:

| Función | Archivo Fuente | Descripción |
| :--- | :--- | :--- |
| `cdtMergingPrecipCMD` | `R/cdtMerging_Precip_Cmd.R` | Fusión de datos de precipitación (Estaciones + Satélite/Reanálisis). |
| `cdtMergingTempCMD` | `R/cdtMerging_Temp_Cmd.R` | Fusión de datos de temperatura (Estaciones + Reanálisis). |
| `cdtMergingClimDataCMD` | `R/cdtMerging_ClimData_Cmd.R` | Fusión genérica (`"rain"`, `"temp"`, `"rh"`, `"pres"`, `"prmsl"`, `"rad"`). |
| `cdtBiasCorrectPrecipCMD` | `R/cdtBias_Correction_Precip_Cmd.R` | Corrección previa de sesgo para precipitación. |
| `cdtBiasCorrectTempCMD` | `R/cdtBias_Correction_ClimData_Cmd.R` | Corrección previa de sesgo para temperatura. |
| `cdtCrossValidationPrecipCMD` | `R/cdtCrossValidation_Precip_Cmd.R` | Validación cruzada (Leave-One-Out o K-Fold) para precipitación. |
| `cdtCrossValidationTempCMD` | `R/cdtCrossValidation_Temp_Cmd.R` | Validación cruzada para temperatura. |

Todas estas funciones tienen un argumento común: **`GUI = FALSE`**. Al configurarlo en `FALSE`, los mensajes y advertencias se redirigen a la salida estándar de la consola y a un archivo de registro en disco (`log_file.txt`), evitando cualquier llamada a las ventanas de diálogo de `Tcl/Tk`.

---

## 3. Configuración de Opciones Globales (`merging.options`)

Antes de llamar a las funciones de fusión, es posible parametrizar el comportamiento interno de los algoritmos mediante la función `merging.options()` (`R/cdtMerging_Options_functions.R`):

```r
library(CDT)

merging.options(
  # Cantidad mínima de estaciones con datos válidos para procesar la fecha
  mrgMinNumberSTN = 5,
  
  # Cantidad mínima de estaciones para Regression Kriging (si hay menos, usa SBA)
  rkMinNumberSTN = 8,
  
  # Cantidad mínima de estaciones para calcular variograma empírico (si hay menos, usa IDW)
  vgmMinNumberSTN = 8,
  
  # Usar interpolación local (TRUE) o global (FALSE)
  useLocalInterpolation = TRUE,
  
  # Potencias de ponderación para algoritmos IDW, Shepard y Barnes
  powerWeightIDW = 2.0,
  powerWeightShepard = 0.7,
  powerWeightBarnes = 0.5,
  
  # Inclusión de malla gruesa de fondo con residual cero para estabilidad en los bordes
  addCoarseGrid = FALSE,
  resCoarseGrid = 0.5,
  
  # Guardado de la máscara Rain-No-Rain intermedia en disco (.rds)
  saveRnoR = FALSE,
  dirRnoR = "D:/Salidas/Mascaras_RnoR",
  RnoRModel = "logit",    # "logit" o "additive"
  RnoRCutOff = 3,         # 1, 2 o 3
  RnoRSmoothingPixels = 2
)
```

---

## 4. Estructura de Parámetros de Entrada

Las funciones de comando reciben listas nombradas (`named lists`). A continuación se detallan los bloques principales:

### A. Paso temporal y Rango de Fechas (`time.step`, `dates`)
- `time.step`: `"daily"`, `"pentad"`, `"dekadal"`, `"monthly"`.
- `dates`:
  - Por rango: `list(from = "range", pars = list(start = "20230101", end = "20230131"))`
  - Por archivo de texto: `list(from = "file", pars = list(file = "/ruta/fechas.txt"))`
  - Por vector explícito: `list(from = "dates", pars = list(dates = c("20230101", "20230102")))`

### B. Datos de Estación (`station.data`)
Formato CDT estándar (primeras 3 filas: ID, Longitud, Latitud / opcional Elevación; seguidas de la columna de fecha y los valores de cada estación):
```r
station.data = list(
  file = "/datos/estaciones_precip.csv",
  sep = ",",
  na.strings = "-99"
)
```

### C. Datos Gridded / NetCDF (`netcdf.data`)
Ruta a la carpeta con archivos NetCDF y patrón de nomenclatura usando comodines `%s` para año, mes y día/década:
```r
netcdf.data = list(
  dir = "/datos/satelite_gpm",
  format = "gpm_daily_%s%s%s.nc",  # %s%s%s -> YYYYMMDD
  varid = "precip",                # Nombre de la variable dentro del NetCDF
  ilon = 1,                        # Posición de la dimensión Longitud (1 o 2)
  ilat = 2                         # Posición de la dimensión Latitud (1 o 2)
)
```

### D. Malla de Salida (`grid`)
Permite re-interpolar a una nueva cuadrícula o mantener la misma del NetCDF de entrada:
- Mantener la del proxy: `list(from = "data", pars = NULL)`
- Tomar la de otro archivo NetCDF: `list(from = "ncdf", pars = list(file = "malla.nc", varid = "z", ilon = 1, ilat = 2))`
- Crear una nueva malla regular: `list(from = "new", pars = list(minlon = -90, maxlon = -80, minlat = 10, maxlat = 20, reslon = 0.05, reslat = 0.05))`

### E. Recorte con Shapefile / Blanking (`blank`)
```r
blank = list(
  data = TRUE,
  shapefile = "/datos/gis/cuenca_limites.shp"
)
```

---

## 5. Ejecución en Terminal y Automatización

### Modo Directo con `Rscript`
```bash
Rscript -e "
library(CDT)
cdtMergingPrecipCMD(
  time.step = 'daily',
  dates = list(from = 'range', pars = list(start = '20230501', end = '20230510')),
  station.data = list(file = 'data/stn.csv', sep = ',', na.strings = '-99'),
  netcdf.data = list(dir = 'data/chirps', format = 'chirps_%s%s%s.nc', varid = 'precip', ilon = 1, ilat = 2),
  merge.method = list(method = 'SBA', nrun = 3, pass = c(1, 0.75, 0.5)),
  interp.method = list(method = 'idw', nmin = 6, nmax = 16, maxdist = 1.5, use.block = TRUE, vargrd = FALSE),
  grid = list(from = 'data', pars = NULL),
  RnoR = list(use = TRUE, wet = 1.0, smooth = TRUE),
  output = list(dir = 'output/merged', format = 'rr_mrg_%s%s%s.nc'),
  GUI = FALSE
)
"
```

### Gestión de Tareas Programadas (Cron / Task Scheduler)
Para actualizar datos diariamente al descargar nuevos archivos satelitales:
1. Un script de descarga (p. ej., Python o cURL) obtiene el archivo NetCDF del día.
2. Un script de base de datos actualiza el archivo `.csv` de estaciones en formato CDT.
3. Se invoca el script de CDT: `Rscript /opt/pipelines/run_cdt_merging.R`.
4. El archivo de salida `log_file.txt` se revisa para verificar que la fusión finalizó exitosamente (código de retorno 0).

---

## 6. Orquestación Moderna con el Lanzador de Python

Para ejecutar de manera sistemática y reproducible las matrices de 26 experimentos (10 de Precipitación, 8 de $T_{max}$ y 8 de $T_{min}$) con partición automática de estaciones de validación (`data/stations/validation_holdout_stations.csv`) y concatenación 3D CF-1.8:

```bash
# Diagnóstico de dependencias del sistema
python launcher/experiment_runner.py --check-env

# Ejecutar por suites completas
python launcher/experiment_runner.py --suite rainfall   # 10 Experimentos
python launcher/experiment_runner.py --suite tmax       # 8 Experimentos
python launcher/experiment_runner.py --suite tmin       # 8 Experimentos

# Ejecutar un experimento individual parametrizado en YAML
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R01_SBA_IDW_Baseline.yaml
```

