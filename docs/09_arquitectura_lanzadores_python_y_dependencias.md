# 09. Arquitectura de Lanzadores en Python y Verificación de Dependencias (Linux y Windows)

Este documento describe la arquitectura técnica, la implementación y la guía exhaustiva de uso para los **scripts lanzadores y orquestadores en Python** encargados de gestionar la ejecución de CDT, diagnosticar el entorno de software y hardware (versión de R, herramientas de compilación y librerías espaciales), particionar estaciones independientes de validación cruzada y ejecutar de forma automatizada las matrices de **26 experimentos** para **Precipitación (CHIRPS)**, **Temperatura Máxima (CHIRTS $T_{max}$)** y **Temperatura Mínima (CHIRTS $T_{min}$)** durante el periodo climatológico 1991–2020 (10,958 días).

---

## 1. Arquitectura del Sistema Híbrido (Python + R/CDT)

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ORQUESTADOR EN PYTHON (launcher/)                                │
│                                                                                                  │
│  1. Pre-flight Check (launcher/env_checker.py):                                                  │
│     • Detección de Rscript (R 4.4.3+), Rtools (Win) / gcc (Linux).                               │
│     • Verificación de paquetes R: CDT, gstat, sf, sp, ncdf4, qmap, doParallel, matrixStats.      │
│                                                                                                  │
│  2. Gestor de Configuraciones YAML (launcher/experiment_runner.py):                              │
│     • Carga global_config.yaml y hereda rutas maestras a CHIRPS, CHIRTS, DEM y Shapefiles.       │
│     • Permite ejecución individual, por suites (--suite rainfall|tmax|tmin) o total (--suite all)│
│                                                                                                  │
│  3. Partición de Estaciones de Validación (launcher/station_manager.py):                        │
│     • Lee lista de exclusión (validation_holdout_stations.csv).                                  │
│     • Genera subset de entrenamiento (usado por CDT) y subset de validación independiente.       │
│                                                                                                  │
│  4. Puente de Ejecución R (launcher/cdt_bridge.py):                                              │
│     • Genera scripts R en memoria con dopar=TRUE, nb.cores=9, gc() periódico y GUI=FALSE.        │
│     • Invoca cdtMergingPrecipCMD / cdtMergingTempCMD capturando stdout, stderr y log_file.txt.   │
│                                                                                                  │
│  5. Ensamblador NetCDF 3D CF-1.8 (launcher/netcdf_assembler.py):                                 │
│     • Transforma los ~10,958 archivos 2D diarios a un único archivo 3D con compresión Deflate.  │
│                                                                                                  │
│  6. Motor de Validación Cuantitativa (launcher/station_manager.py):                              │
│     • Extrae valores de la grilla en estaciones omitidas y calcula KGE, RMSE, MAE, R², POD, FAR.│
│     • Genera experiment_manifest.json, validation_metrics_by_station.csv y logs completos.       │
└────────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                 │ Invocación Rscript Headless
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    MOTOR DE CÁLCULO (CDT en R)                                   │
│  • Mapeo de Cuantiles (Bernoulli-Gamma, Bernoulli-Weibull, Skew-Normal, Gumbel).                 │
│  • Desescalado térmico con DEM SRTM (Gradiente GLM mensual).                                     │
│  • Interpolación geoestadística: Kriging Ordinario por Bloques, IDW, Barnes, Cressman, Shepard,   │
│    Spheremap y NN-3D (Δz).                                                                       │
│  • Máscara probabilística Rain-No-Rain (Logit / Rampa Suave CutOff=3).                           │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Requisitos y Dependencias del Sistema

### A. Requisitos de R y Herramientas de Compilación
- **Versión de R:** R $\ge$ 4.0.0 (Recomendado: **R 4.4.3**).
- **En Windows:** `Rtools44` (imprescindible para compilar módulos Fortran y C de CDT como `src/cdt_interp.f90`).
- **En Linux (Ubuntu/Debian):** `build-essential`, `gfortran`, `gcc`.

### B. Dependencias de Sistema en Linux
Para compilar y ejecutar librerías geoespaciales y NetCDF:

```bash
sudo apt-get update
sudo apt-get install -y \
    r-base-core r-base-dev \
    libnetcdf-dev netcdf-bin \
    libgdal-dev gdal-bin \
    libproj-dev libgeos-dev \
    libudunits2-dev libxml2-dev \
    libcurl4-openssl-dev libssl-dev \
    gfortran
```

### C. Paquetes de R Requeridos
| Paquete R | Propósito |
| :--- | :--- |
| **`CDT`** | Núcleo de fusión, desescalado y corrección de sesgo. |
| **`ncdf4`** | Lectura y escritura de archivos NetCDF 2D y 3D. |
| **`sf` / `sp`** | Manejo de geometrías vectoriales y shapefiles de recorte. |
| **`gstat`** | Geoestadística, variogramas y Kriging Ordinario / Block Kriging. |
| **`matrixStats`** | Operaciones matriciales optimizadas. |
| **`fitdistrplus`** | Ajuste paramétrico de distribuciones teóricas. |
| **`qmap`** | Algoritmos de Quantile Mapping (Bernoulli-Gamma, etc.). |
| **`doParallel` / `foreach`** | Paralelización multinúcleo en el procesamiento de fechas. |
| **`fields`** | Superficies de spline e interpolaciones espaciales. |
| **`lmomco`** | Momentos L para ajuste estadístico de extremos (Gumbel). |

---

## 3. Estructura de Archivos del Proyecto

```
d:/Workspace/CDT-8.0/
├── config/
│   ├── global_config.yaml                  # Configuración maestra común (rutas, fechas, CPU)
│   ├── experiments_rainfall/               # 10 YAMLs de Precipitación (EXP_R01 a EXP_R10)
│   ├── experiments_tmax/                   # 8 YAMLs de Temperatura Máxima (EXP_TX01 a EXP_TX08)
│   └── experiments_tmin/                   # 8 YAMLs de Temperatura Mínima (EXP_TN01 a EXP_TN08)
│
├── launcher/
│   ├── __init__.py
│   ├── env_checker.py                      # Diagnóstico automático de R y librerías
│   ├── data_preprocessor.py                # Validación de entradas y particionado paralelo 3D a diario
│   ├── cdt_bridge.py                       # Generación dinámica de scripts R y ejecución
│   ├── experiment_runner.py                # Lanzador principal y orquestador CLI
│   ├── station_manager.py                  # Partición de estaciones y métricas de validación
│   ├── benchmark_reporter.py               # Leaderboard multicriterio, figuras de Taylor/boxplots y dashboard HTML
│   ├── netcdf_assembler.py                 # Ensamblador NetCDF 3D CF-1.8
│   └── generate_pdf.py                     # Generador del informe PDF en formato vertical
│
├── data/
│   ├── stations/
│   │   ├── precip_stations_all.csv         # Estaciones de precipitación (formato CDT)
│   │   ├── tmax_stations_all.csv           # Estaciones de Tmax (formato CDT)
│   │   ├── tmin_stations_all.csv           # Estaciones de Tmin (formato CDT)
│   │   └── validation_holdout_stations.csv # Lista de IDs de estaciones reservadas para validación
│   ├── chirps_daily/                       # Grillas CHIRPS 1991-2020
│   ├── chirts_daily/                       # Grillas CHIRTS 1991-2020 (tmax/ y tmin/)
│   ├── topography/dem_srtm_90m.nc          # DEM regional
│   └── gis/central_america_dominican_rep.shp # Shapefile de estudio
│
├── Dockerfile                              # Imagen reproducible multi-arquitectura (R 4.4 + Python)
├── docker-compose.yml                      # Servicio orquestador con volúmenes montados
├── Apptainer.def                           # Definición Singularity/Apptainer para supercómputo HPC
├── .devcontainer/devcontainer.json         # Configuración DevContainers para VS Code / Cursor
├── requirements.txt                        # Dependencias de Python
├── output/
│   ├── experiments/                        # Salidas por experimento (NetCDFs 3D, métricas, manifiestos)
│   └── benchmark/                          # Leaderboard consolidado, figuras Taylor/Boxplots y dashboard HTML
├── logs/experiments/                       # Registros de ejecución (stdout, stderr, log_file.txt)
└── docs/                                   # Documentación técnica completa
```

---

## 4. Guía Detallada de Uso de la Línea de Comandos (`launcher/experiment_runner.py`)

### A. Opciones y Parámetros Disponibles

```bash
python launcher/experiment_runner.py [OPCIONES]
```

| Argumento | Alias | Tipo | Descripción |
| :--- | :---: | :---: | :--- |
| `--suite` | `-s`, `--variable`, `-v` | `str` | Ejecuta una suite predefinida: `rainfall` (10 exp), `tmax` (8 exp), `tmin` (8 exp) o `all` (26 exp). |
| `--config` | `-c` | `str` | Ruta a un archivo `.yaml` específico o a una carpeta con archivos `.yaml`. |
| `--base-config` | `-b` | `str` | Ruta al archivo maestro común (por defecto: `config/global_config.yaml`). |
| `--validate-inputs` | | `flag` | Valida la presencia e integridad de todas las entradas y realiza el particionado 3D a 2D en paralelo. |
| `--benchmark` | `--generate-report` | `flag` | Genera el ranking multicriterio (leaderboard), diagramas de Taylor, boxplots y dashboard HTML interactivo. |
| `--check-env` | | `flag` | Ejecuta el diagnóstico del entorno (Rscript, paquetes y compiladores) antes de procesar. |
| `--rscript` | `-r` | `str` | Ruta absoluta al ejecutable `Rscript` (útil si R no está en el `PATH` del sistema). |

---

### B. Flujos de Trabajo Típicos

#### 1. Diagnóstico del Entorno (Pre-flight Check)
Verifica que R 4.4.3, el paquete CDT local y las dependencias geoespaciales estén instaladas:
```bash
# Windows
python launcher/experiment_runner.py --check-env --rscript "C:\Program Files\R\R-4.4.3\bin\Rscript.exe"

# Linux
python launcher/experiment_runner.py --check-env
```

#### 2. Ejecutar un Experimento Individual
Para probar o recalibrar una parametrización específica:
```bash
# Precipitación: Fusión con Kriging Ordinario y distribución Bernoulli-Gamma
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R03_SBA_OKR_BernoulliGamma.yaml

# Temperatura Máxima: Regression Kriging con radiación solar y orientación de ladera (Aspect)
python launcher/experiment_runner.py --config config/experiments_tmax/EXP_TX08_RK_Aspect_Solar_Insolation.yaml

# Temperatura Mínima: Regression Kriging con NN-3D para inversiones térmicas en valles
python launcher/experiment_runner.py --config config/experiments_tmin/EXP_TN04_RK_NN3D_Inversion_Valleys.yaml
```

#### 3. Ejecutar una Suite Completa por Variable
Permite correr secuencialmente todos los experimentos asociados a una variable física:

```bash
# Suite de Precipitación (EXP-R01 a EXP-R10) -> ~5.8 a 6.7 horas
python launcher/experiment_runner.py --suite rainfall

# Suite de Temperatura Máxima (EXP-TX01 a EXP-TX08) -> ~11.0 a 12.5 horas
python launcher/experiment_runner.py --suite tmax

# Suite de Temperatura Mínima (EXP-TN01 a EXP-TN08) -> ~11.0 a 12.5 horas
python launcher/experiment_runner.py --suite tmin
```

#### 4. Ejecutar la Batería Completa de 26 Experimentos
Ejecuta los 10 experimentos de lluvia, 8 de $T_{max}$ y 8 de $T_{min}$ en un único lote desatendido:
```bash
python launcher/experiment_runner.py --suite all
```

---

## 5. Guía Completa de Preparación de Datos (`data/`) y Archivos de Configuración (`config/`)

### A. Estructura y Contenido Requerido en `data/`

Todos los datos de entrada son suministrados localmente por el usuario. La carpeta `data/` está estructurada en los siguientes submódulos:

```
data/
├── stations/
│   ├── precip_stations_all.csv         # Red pluviométrica histórica (Lluvia)
│   ├── tmax_stations_all.csv           # Red termométrica histórica (Tmax)
│   ├── tmin_stations_all.csv           # Red termométrica histórica (Tmin)
│   └── validation_holdout_stations.csv # Lista de IDs a omitir para validación ciega
│
├── chirps_daily/                       # Grillas diarias 2D CHIRPS (chirps_YYYYMMDD.nc)
├── chirts_daily/
│   ├── tmax/                           # Grillas diarias 2D Tmax (tmax_YYYYMMDD.nc)
│   └── tmin/                           # Grillas diarias 2D Tmin (tmin_YYYYMMDD.nc)
│
├── raw_netcdf/                         # (Opcional) NetCDFs 3D únicos multitemporales (1991–2020)
├── topography/
│   └── dem_srtm_90m.nc                 # Modelo Digital de Elevación SRTM (msnm)
│
└── gis/
    ├── central_america_dominican_rep.shp # Shapefile del dominio (con buffer 10 km)
    ├── central_america_dominican_rep.shx
    ├── central_america_dominican_rep.dbf
    └── central_america_dominican_rep.prj
```

#### 1. Formato de las Estaciones (`data/stations/*.csv`)
Deben cumplir con el estándar oficial de entrada de CDT (separado por comas):
* **Fila 1 (ID):** `"ID", "STN_001", "STN_002", "STN_003", ...`
* **Fila 2 (LON):** `"LON", -70.523, -69.845, -71.210, ...`
* **Fila 3 (LAT):** `"LAT", 18.450, 19.120, 18.890, ...`
* **Fila 4 (ELEV):** `"ELEV", 120.0, 450.5, 1200.0, ...` *(Altitud en msnm; indispensable para desescalado y RK)*
* **Filas 5 en adelante (Datos):** `YYYYMMDD, val_stn1, val_stn2, val_stn3, ...` (Valores diarios; usar `-99` o `NA` para vacíos).

#### 2. Formato del Archivo de Exclusión (*Holdout Validation*):
* **`data/stations/validation_holdout_stations.csv`:** Archivo CSV simple con la columna `station_id`.
  * **Si se desean excluir estaciones:** Se listan los IDs correspondientes:
    ```csv
    station_id
    STN_005
    STN_018
    STN_042
    ```
  * **Si no se desea excluir ninguna estación:** Se deja el archivo únicamente con su cabecera `station_id` (vacío).

#### 3. Grillas Satelitales (Precipitación y Temperatura):
* **Opción Archivos Diarios 2D:** Ubicar los archivos NetCDF diarios en `data/chirps_daily/` (`chirps_YYYYMMDD.nc`), `data/chirts_daily/tmax/` (`tmax_YYYYMMDD.nc`) y `data/chirts_daily/tmin/` (`tmin_YYYYMMDD.nc`).
* **Opción Archivo 3D Único:** Si el usuario dispone de un único archivo NetCDF multitemporal (ej. `chirps_daily_1991_2020.nc`), lo ubica en `data/raw_netcdf/` y especifica su ruta en `config/global_config.yaml`. El lanzador lo particionará en paralelo automáticamente.

#### 4. DEM y Shapefile:
* **`data/topography/dem_srtm_90m.nc`:** NetCDF con coordenadas `lon`, `lat` y variable de elevación continua (m).
* **`data/gis/central_america_dominican_rep.shp`:** Polígonos vectoriales con sus archivos sidecar obligatorios (`.shx`, `.dbf`, `.prj`).

---

### B. ¿Qué se Configura en `config/global_config.yaml`?

Este archivo centraliza los parámetros maestros comunes a todos los experimentos:

```yaml
period:
  start_date: "19910101"   # Fecha inicial (YYYYMMDD)
  end_date: "20201231"     # Fecha final (YYYYMMDD)
  time_step: "daily"       # Paso temporal diario

paths:
  # Rutas a NetCDFs 3D únicos (dejar en null si ya tiene archivos diarios 2D)
  raw_3d_netcdf_rainfall: null     # Ej: "data/raw_netcdf/chirps_1991_2020.nc"
  raw_3d_netcdf_tmax: null
  raw_3d_netcdf_tmin: null

  # Directorios de grillas 2D
  satellite_rainfall_dir: "data/chirps_daily"
  satellite_tmax_dir: "data/chirts_daily/tmax"
  satellite_tmin_dir: "data/chirts_daily/tmin"

  # Archivos de estaciones maestras y exclusión
  stations_rainfall_file: "data/stations/precip_stations_all.csv"
  stations_tmax_file: "data/stations/tmax_stations_all.csv"
  stations_tmin_file: "data/stations/tmin_stations_all.csv"
  holdout_stations_file: "data/stations/validation_holdout_stations.csv"

  # Covariables geográficas
  dem_file: "data/topography/dem_srtm_90m.nc"
  shapefile_path: "data/gis/central_america_dominican_rep.shp"

system:
  nb_cores: 9                    # 9 núcleos físicos de CPU para procesamiento paralelo
  dopar: true                    # Activar doSNOW en R
  auto_validate_inputs: true     # Validar presencia de archivos antes de iniciar
  auto_split_3d_netcdf: true     # Particionar NetCDFs 3D automáticamente si existen
```

> [!TIP]
> **¿Qué debe modificar el usuario?**
> Si el usuario coloca sus archivos en las carpetas estándar de `data/` con los nombres por defecto, **no necesita modificar nada**. Solo debe editar `config/global_config.yaml` si sus archivos tienen nombres o rutas distintas.

---

### C. ¿Qué Contienen los Archivos de Experimento Individuales?

Cada archivo en `config/experiments_rainfall/` (10 YAMLs), `config/experiments_tmax/` (8 YAMLs) y `config/experiments_tmin/` (8 YAMLs) hereda de `global_config.yaml` y únicamente especifica la combinación metodológica de ese experimento:

* **`include: "config/global_config.yaml"`**: Importa automáticamente todas las rutas y recursos globales.
* **`id` y `description`**: Identificador único (ej. `EXP_R05_RK_Topography_Weibull`).
* **`downscaling`** *(solo temperatura)*: Método de interpolación de fondo (`blin`, `bicub`, `idw`) y resolución objetivo.
* **`bias_correction`**: Método (`mbvar`, `qm.dist`, `admon`), distribución teórica (`Gamma`, `Weibull`, `Skew-Normal`, `Gumbel`, `ECDF`) y algoritmo de interpolación del sesgo (`idw`, `okr`, `nn3d`).
* **`rnor_mask`** *(solo lluvia)*: Activación de máscara de lloviznas y tipo de rampa (`logit` / `cutoff`).
* **`merging`**: Método de fusión (`SBA`, `RK`, `CSc`, `Barnes`), número de pasadas (`nrun: 3`), radios de búsqueda (`maxdist`) y covariables continuas (`dem`, `slope`, `aspect`, `lon`, `lat`).

---

## 6. Funcionamiento Interno de los Módulos de Soporte

### A. Partición Automática de Estaciones (`launcher/station_manager.py`)
Cuando un archivo YAML o `global_config.yaml` define `holdout_stations_file`, el gestor:
1. Lee las cabeceras del CSV en formato CDT (Fila 1: `ID`, Fila 2: `LON`, Fila 3: `LAT`, Fila 4: `ELEV`).
2. Identifica las columnas correspondientes a las estaciones listadas en el CSV de exclusión.
3. Escribe en `output/experiments/<ID>/station_split/`:
   - `training_stations.csv`: Contiene el 80–90% de estaciones para la ejecución en CDT.
   - `holdout_validation_stations.csv`: Contiene el 10–20% de estaciones retenidas para validación.

### B. Ensamblado NetCDF 3D CF-1.8 (`launcher/netcdf_assembler.py`)
Una vez completada la fusión diaria por CDT:
1. Escanea todos los archivos diarios `rr_mrg_YYYYMMDD.nc` o `tmax_mrg_YYYYMMDD.nc` en la carpeta de salida.
2. Crea un archivo NetCDF-4 con compresión `zlib=True, complevel=4`.
3. Asigna la dimensión temporal con unidades `days since 1991-01-01 00:00:00` y calendario `gregorian`.
4. Asigna los atributos estándar CF-1.8 (`standard_name`, `units`, `long_name`, `coverage_content_type`, etc.).

### C. Evaluación de Métricas de Validación Independiente
El script compara la serie temporal de cada celda con los registros de la estación de validación independiente:
- **Métricas Continuas:**
  - $R^2 = \left(\frac{\sum (O_i - \bar{O})(S_i - \bar{S})}{\sqrt{\sum (O_i - \bar{O})^2 \sum (S_i - \bar{S})^2}}\right)^2$
  - $\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (S_i - O_i)^2}$
  - $\text{MAE} = \frac{1}{N}\sum_{i=1}^N |S_i - O_i|$
  - $\text{PBIAS} = \frac{\sum (S_i - O_i)}{\sum O_i} \times 100\%$
  - $\text{KGE} = 1 - \sqrt{(r - 1)^2 + (\beta - 1)^2 + (\gamma - 1)^2}$ donde $\beta = \frac{\mu_s}{\mu_o}$ y $\gamma = \frac{\sigma_s / \mu_s}{\sigma_o / \mu_o}$.
- **Métricas Categóricas (Lluvia $\ge 1.0\text{ mm}$):**
  - $\text{POD} = \frac{H}{H + M}$
  - $\text{FAR} = \frac{FA}{H + FA}$
  - $\text{ETS} = \frac{H - H_r}{H + M + FA - H_r}$ donde $H_r = \frac{(H + M)(H + FA)}{N}$
  - $\text{HSS} = \frac{2(H \cdot CN - FA \cdot M)}{(H + M)(M + CN) + (H + FA)(FA + CN)}$

---

## 7. Rendimiento y Tiempos de Cómputo (Intel Xeon Silver 4210R)

Configuración de hardware: **Intel Xeon Silver 4210R (10C/20T @ 2.40 GHz), 9 hilos asignados a CDT, 64 GB RAM, NVMe SSD**:

| Suite | Núm. Exp. | Días por Exp. | Tiempo por Exp. | Tiempo Total Suite | Consumo RAM Máx. |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precipitación (CHIRPS)** | 10 | 10,958 | 35 – 42 min | **5.8 – 6.7 horas** | 2.5 – 4.5 GB |
| **Temperatura Máxima ($T_{max}$)** | 8 | 10,958 | 80 – 95 min | **11.0 – 12.5 horas** | 3.5 – 4.6 GB |
| **Temperatura Mínima ($T_{min}$)** | 8 | 10,958 | 80 – 95 min | **11.0 – 12.5 horas** | 3.5 – 4.6 GB |
| **Total Global** | **26** | **10,958** | — | **28.0 – 31.5 horas** | **4.6 GB (<8% de 64 GB)** |
