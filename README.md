# Climate Data Tools (CDT v8.0)

> [!NOTE]
> **Estructura del Documento / Document Structure:**
>
> - **Parte 1 (Inglés / English):** Contiene las [instrucciones originales de instalación de CDT](#parte-1-instrucciones-originales-de-instalación-de-cdt-original-installation-guide) desarrolladas por el IRI (Columbia University) para Windows, macOS y Linux.
> - **Parte 2 (Español / Spanish):** Contiene la [Suite de Automatización, Orquestación y Experimentos Científicos](#parte-2-suite-de-automatización-orquestación-y-experimentos-científicos-19912020) en Python para la ejecución de los 31 experimentos (15 de Precipitación organizados en Fase 1 y Fase 2, 8 de $T_{max}$ y 8 de $T_{min}$), verificación de datos (`--check-data`), despliegue en contenedores Docker/Apptainer y generación de benchmarks.

---

# Parte 1: Instrucciones Originales de Instalación de CDT (Original Installation Guide)

Climate Data Tools `CDT` is a set of utility functions for meteorological data quality control, homogenization and merging station data with satellite and others proxies such as reanalysis, all functions are available in the GUI mode.

## `CDT` installation on Windows

### 1) Install `R`

Go to the CRAN website [CRAN](https://CRAN.R-project.org).
Then click on the link [Download R for Windows](https://cran.r-project.org/bin/windows/) and [base](https://cran.r-project.org/bin/windows/base/). Download the latest version of `R`.
Install the downloaded file (example: R-4.3.0-win.exe). Perform a default installation (Just click on **Next**).

```
CDT requires R version 4.0.0 or higher. It is recommend to have the latest version of R.
```

### 2) Install `Rtools`

Go to the CRAN website [CRAN](https://CRAN.R-project.org).
Then click on the link [Download R for Windows](https://cran.r-project.org/bin/windows/) and [Rtools](https://cran.r-project.org/bin/windows/Rtools/). Download the recommended version of `Rtools` compatible with your R version.
Install the downloaded file. Follow the installation instructions displayed on the page.

### 3) Install `CDT`

Open `R` and install `devtools` package with:

```
install.packages("devtools")
```

Now, you can install the the development version of `CDT` from GitHub with:

```r
library(devtools)
install_github("rijaf-iri/CDT")
```

## `CDT` installation on MacOS X

### 1) Install `XQuartz`

Type `XQuartz` in Apple's search, if you don't find it, that means `XQuartz` is not installed yet. It's better to update `XQuartz` to the latest version if it is already installed.

Download and install it from [https://www.xquartz.org](https://www.xquartz.org/).

Restart your computer.

### 2) Install `Tcl/Tk`

#### Check `Tcl/Tk` installation

Check if the `Tcl/Tk` libraries are already installed in your computer. Open a terminal and run the following command:

```bash
echo 'puts $tcl_library;exit 0' | tclsh
```

If `Tcl/Tk` libraries are installed in your computer, you should get the path to the Tcl library like this: `/usr/local/lib/tcl8.6`.

If `Tcl/Tk` libraries are not yet installed in your computer, you can install ActiveTcl&#174;. Go directly to the ActiveTcl&#174; installation below.

#### Check `Tktable` package

Check if the package `Tktable` is installed. Run the following command from terminal:

```bash
echo 'puts [package require Tktable];exit 0' | tclsh
```

If the package is installed, you should have the version number of the package. If `Tktable` is not installed, you can download it from [here](https://sourceforge.net/projects/tktable/files/tktable/2.10/Tktable2.10.tar.gz/download).

Change to the directory where you downloaded `Tktable` archive file.

```bash
cd ~/path/to/Tktable/archive
```

Uncompressed the archive file.

```bash
tar -zxvf Tktable2.10.tar.gz
```

This will create a subdirectory `Tktable2.10` with all the files in it. Change to this directory.

```bash
cd Tktable2.10
```

The default installation path of `Tktable` is under `/usr/local`. If the Tcl Library Path directory is under this directory, you can install `Tktable` by default using the following commands:

```bash
./configure
make install
```

If Tcl Library Path directory is anywhere else. Check the `auto_path` global variable using the following command

```bash
echo 'puts $auto_path;exit 0' | tclsh
```

You should have a list of directories like this: `/usr/local/lib/tcl8.6` `/usr/local/lib`. You need to set the `--prefix` option of configure

```bash
./configure --prefix=/usr/local
make install
```

#### Check `BWidget` package

Check if the package BWidget is installed. Run the following command from terminal:

```bash
echo 'puts [package require BWidget];exit 0' | tclsh
```

If the package is installed, you should have the version number of the package. If `BWidget` is not installed, you can download it from [here](https://sourceforge.net/projects/tcllib/files/BWidget/1.9.12/bwidget-1.9.12.zip/download).
Unzipped the file `bwidget-1.9.12.zip` and copy it under the Tcl Library Path directory. Copy the bwidget directory `bwidget-1.9.12` under one of the `auto_path` global variable directories.

> **Note**
> If you install `Tktable` and `BWidget` anywhere else, remember the path you put the packages, you will need it when you install `CDT`.

#### Install ActiveTcl&#174;

Download ActiveTcl&#174; from [https://www.activestate.com/products/activetcl/downloads/](https://www.activestate.com/products/activetcl/downloads/).

ActiveTcl&#174; executables will be installed (`wish`, `tclsh` and `tkcon`) in `/usr/local/bin` and the library will be put in `/usr/local/lib/tcl8.6` or `/usr/local/lib/tcl8.5` depending on the version.

`Tktable` will be put in `/Library/Tcl/teapot/package/macosx10.5-i386-x86_64/lib/Tktable2.11`
and `BWidget` in `/Library/Tcl/teapot/package/tcl/lib/BWidget1.9.8`.

### 3) Install GDAL/GEOS/PROJ.4

Download and install `GDAL` binaries from [http://www.kyngchaos.com/software/frameworks](http://www.kyngchaos.com/software/frameworks). Install the latest version of **GDAL Complete**.

`GDAL` will be installed in `/Library/Frameworks/GDAL.framework`,

`GEOS` in `/Library/Frameworks/GEOS.framework`

and `PROJ` in `/Library/Frameworks/PROJ.framework`.

The configuration files are located in

`GEOS`: `/Library/Frameworks/GEOS.framework/unix/bin/geos-config`

`GDAL`: `/Library/Frameworks/GDAL.framework/unix/bin/gdal-config`

And `PROJ` `include` and `lib` are located in `/Library/Frameworks/PROJ.framework/unix/include` and
`/Library/Frameworks/PROJ.framework/unix/lib` respectively.

Remember these paths, you will need them when you install the package `rgdal` and `rgeos` on `R`.

### 4) Install `R`

Download and install `R` binary for your MacOS X version from [https://cran.r-project.org/bin/macosx](https://cran.r-project.org/bin/macosx/)

```
CDT requires R version 4.0.0 or higher. We recommend that you have the latest version of R.
```

### 5) Install `CDT`

Open `R` and install `devtools` package with:

```r
install.packages("devtools")
```

Now, you can install the development version of `CDT` from GitHub with:

```r
library(devtools)
install_github("rijaf-iri/CDT")
```

If you get a warning message telling you that `Tktable` or `BWidget` not found, you need to edit CDT's local configuration for Tcl: `~/Library/Application Support/CDT/config/Tcl_config.json`.
Go to the MacOS configuration and change `Tktable.auto` or `Bwidget.auto` to `false`, then set the full path to `Tktable` or `BWidget` directory with `Tktable.path` or `Bwidget.path`, as shown in the following example:

```json
"MacOS": {
    "Tktable.auto": false,
    "Tktable.path": "/Library/Tcl/teapot/package/macosx10.5-i386-x86_64/lib/Tktable2.11",
    "Bwidget.auto": false,
    "Bwidget.path": "/Library/Tcl/teapot/package/tcl/lib/BWidget1.9.8"
  },
```

After editing `Tcl_config.json`, save it. Open a new `R` session and load and start `CDT`.

## `CDT` installation on Ubuntu

### 1) Install `Tcl/Tk`

Check if the `Tcl/Tk` libraries are already installed in your computer, make sure that the `*-dev` packages are installed. If not, you can install it with:

```bash
sudo apt-get install tk-dev tcl-dev
```

Check if the Tcl package `Tktable` is installed. If it is not installed, you can download it from [here](https://sourceforge.net/projects/tktable/files/tktable/2.10/Tktable2.10.tar.gz/download).

Check if the Tcl package `BWidget` is installed. If it is not installed, you can download it from [here](https://sourceforge.net/projects/tcllib/files/BWidget/1.9.12/bwidget-1.9.12.zip/download).

> **Note**
> See MacOS X `Tktable` and `BWidget` installation.

### 2) Install GDAL/OGR

Add the `PPA` to your sources

```bash
sudo add-apt-repository ppa:ubuntugis/ppa
sudo apt-get update && sudo apt-get upgrade
```

Install `GDAL`

```bash
sudo apt-get install gdal-bin libgdal-dev
```

Verify the installation with

```bash
ogrinfo
```

Get the installation path of `gdal-config` and `geos-config`. Save these paths somewhere, you will need it later when installing the `R` packages `rgdal` and `rgeos`.

### 3) Install `NetCDF`

```bash
sudo apt-get install netcdf-bin libnetcdf-dev
```

### 4) Install `R`

Install `R` if not installed yet.
Add the `R` repository to your sources

```
CDT requires R version 4.0.0 or higher. We recommend that you have the latest version of R, this implies that you have to install R from source.
```

```bash
sudo add-apt-repository "deb http://cran.rstudio.com/bin/linux/ubuntu $(lsb_release -sc)/"
sudo apt-get update
```

Add GPG key

```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys E084DAB9
```

Install R

```bash
sudo apt-get install r-base r-base-dev
```

### 5) Install `R` package `ncdf4`

```bash
sudo apt-get install r-cran-ncdf4
```

You can install `ncdf4` package with:

```r
## edit the path
nc_config <- '/usr/bin/nc-config'

install.packages('ncdf4', type = "source",
        configure.args = paste0('--with-nc-config=', nc_config))
```

### 6) Install `CDT`

Open `R` and install `devtools` package with:

```r
install.packages("devtools")
```

Now, you can install the development version of `CDT` from GitHub with:

```r
devtools::install_github("rijaf-iri/CDT")
```

If you get a warning message telling you that `Tktable` or `BWidget` not found, you need to edit CDT’s local configuration for Tcl: `~/.local/CDT/config/Tcl_config.json`
Go to the Linux configuration and change `Tktable.auto` or `Bwidget.auto` to `false`, then set the full path to `Tktable` or `BWidget` directory with `Tktable.path` or `Bwidget.path`.

## Usage

```r
# Load  CDT library
library(CDT)

# Starting CDT
startCDT()
```

## Updating `CDT`

To only update `CDT` without updating all dependencies packages, enter the following command on `R` console

```r
if(packageVersion("devtools") >= "2.0.0"){
    devtools::install_github("rijaf-iri/CDT", dependencies = FALSE,
                              upgrade = FALSE, force = TRUE)
}else{
    devtools::install_github("rijaf-iri/CDT", dependencies = FALSE,
                              upgrade_dependencies = FALSE, force = TRUE)
}
```

To update `CDT` and all dependencies packages, use

```r
update.packages(ask = FALSE)
devtools::install_github("rijaf-iri/CDT")
```

---

# Parte 2: Suite de Automatización, Orquestación y Experimentos Científicos (1991–2020)

Este repositorio incluye una capa de orquestación en Python de grado de producción diseñada para ejecutar y validar **31 experimentos científicos controlados** (15 para Precipitación Diaria CHIRPS divididos en Fase 1: R01–R10 y Fase 2: R11–R15, 8 para Temperatura Máxima Diaria CHIRTS $T_{max}$ y 8 para Temperatura Mínima Diaria CHIRTS $T_{min}$) para el periodo climatológico estándar **1991–2020 (10,958 días / 30 años)** sobre **Centroamérica y República Dominicana**.

## Guía Rápida de Ejecución

### Opción A: Ejecución Nativa con Python

```bash
# 1. Comprobar entorno de R, herramientas de compilación y paquetes espaciales
python launcher/experiment_runner.py --check-env

# 2. Verificar que los datos e insumos estén listos en sus carpetas (Estaciones, DEM, Shapefile, Grillas 1991-2020)
python launcher/experiment_runner.py --check-data             # Valida región por defecto (Centroamérica)
python launcher/experiment_runner.py --check-data --region rd # Valida República Dominicana

# 3. Ejecutar suite de Precipitación (15 Experimentos: Fase 1 y Fase 2, ~35-38h en 18 núcleos)
python launcher/experiment_runner.py --suite rainfall --cores 18
python launcher/experiment_runner.py --suite rainfall --region rd --cores 18

# 4. Ejecutar suite de Temperatura Máxima (8 Experimentos, ~14-15h)
python launcher/experiment_runner.py --suite tmax --cores 18
python launcher/experiment_runner.py --suite tmax --region rd --cores 18

# 5. Ejecutar suite de Temperatura Mínima (8 Experimentos, ~14-15h)
python launcher/experiment_runner.py --suite tmin --cores 18
python launcher/experiment_runner.py --suite tmin --region rd --cores 18

# 6. Ejecutar corrida batch completa (31 Experimentos, ~63-68h continuas)
python launcher/experiment_runner.py --suite all --cores 18
python launcher/experiment_runner.py --suite all --region rd --cores 18

# 7. Generar reporte de benchmark, diagramas de Taylor y dashboard interactivo HTML
python launcher/experiment_runner.py --benchmark
python launcher/experiment_runner.py --benchmark --region rd
```

> **Plataforma de Hardware Calibrada y Paralelismo:** Calibrado en estación Linux Ubuntu 24.04.5 LTS con procesador Intel(R) Core(TM) i9-10850K @ 3.60GHz (10 núcleos / 20 hilos), 32 GB RAM DDR4 y SSD NVMe 400 GB. Por defecto, el orquestador detecta automáticamente los núcleos disponibles (`N - 1`), o puedes asignar explícitamente los núcleos deseados con `--cores 18`. Los tiempos de ejecución se visualizan dinámicamente en formato legible de horas, minutos y segundos (`1h 48m 22s`).

### Opción B: Ejecución Desatendida en Segundo Plano (`nohup` en Linux / WSL / Servidores)

Para ejecuciones completas de larga duración (~63 a 68 horas), se debe lanzar el proceso desacoplado de la terminal, desactivando la variable `DISPLAY` (para evitar conflictos de `tcltk`/X11 en entornos sin entorno gráfico) y usando el flag `-u` de Python (para registrar logs en tiempo real sin latencia de búfer):

```bash
# Ejecutar toda la suite en segundo plano (producción desatendida)
DISPLAY= nohup python -u launcher/experiment_runner.py --suite all --cores 18 > corrida_completa.log 2>&1 &

# Monitorear el progreso en tiempo real
tail -f corrida_completa.log

# Verificar el proceso activo en el sistema
ps aux | grep experiment_runner
```

> **Tolerancia a Fallos y Reanudación:** Si el servidor se reinicia o el proceso se detiene, basta con relanzar el mismo comando. El orquestador detectará las grillas diarias ya generadas y reanudará automáticamente desde el día exacto de interrupción sin reprocesar. Para forzar un reprocesamiento desde cero, utilice la bandera `--force`.

### Opción C: Ejecución en Contenedores Docker / Docker Compose (Cero Dependencias en el Host)

```bash
# 1. Construir la imagen del contenedor
docker compose build

# 2. Diagnóstico del entorno dentro del contenedor
docker compose run --rm cdt-runner python launcher/experiment_runner.py --check-env

# 3. Verificar datos dentro del contenedor
docker compose run --rm cdt-runner python launcher/experiment_runner.py --check-data --region ca
docker compose run --rm cdt-runner python launcher/experiment_runner.py --check-data --region rd

# 4. Ejecutar suites o corrida batch completa con reporte interactivo
docker compose run --rm cdt-runner python launcher/experiment_runner.py --suite rainfall --region ca
docker compose run --rm cdt-runner python launcher/experiment_runner.py --suite all --region rd
```

## Resultados del Benchmark de Precipitación: 15 Experimentos (Fase 1 y Fase 2)

Los 15 experimentos de precipitación diaria (CHIRPS 1991–2020) fueron ejecutados y calibrados en una estación Linux Ubuntu 24.04.5 LTS (Intel Core i9-10850K @ 3.60GHz, 32 GB RAM DDR4, SSD NVMe 400 GB) y evaluados contra **29 estaciones de validación ciega independiente (*holdout*)**:

| Rank | Experimento ID | Método de Fusión y Configuración Clave | KGE | $r$ | RMSE (mm) | PBIAS (%) | POD | ETS | HSS | Global Skill | Clasificación |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **EXP_R15_Shepard_RnoR_Smooth** | **Shepard Modificado + RnoR Suave (CutOff 2, rad 1.2°)** | **0.3791** | **0.4791** | **12.88** | **-4.39%** | **0.6922** | **0.3287** | **0.4785** | **0.5007** | **GANADOR (Rank 1)** |
| **2** | **EXP_R12_Shepard_Local_Orn** | Shepard Confinado Local Anti-Cruce (rad 0.9° ~100 km) | 0.3716 | 0.4685 | 13.21 | -3.21% | 0.6731 | 0.3238 | 0.4735 | 0.4991 | Fase 2 (Rank 2) |
| **3** | **EXP_R08_Shepard_Complex_Relief** | Shepard Relieve Complejo Estándar (rad 1.5°) | 0.3749 | 0.4794 | 12.89 | -6.30% | 0.6650 | 0.3147 | 0.4638 | 0.4888 | Fase 1 (Rank 3) |
| **4** | **EXP_R11_Shepard_Median_Coarse** | Shepard Mediana Robusta + Malla Gruesa (rad 1.5°) | 0.3753 | 0.4787 | 12.77 | -6.70% | 0.6746 | 0.3213 | 0.4697 | 0.4885 | Fase 2 (Rank 4) |
| **5** | **EXP_R14_Spheremap_Median** | Spheremap Gran Círculo + Mediana + Malla Gruesa | 0.3621 | 0.4552 | 13.56 | -4.43% | 0.6540 | 0.3174 | 0.4660 | 0.4863 | Fase 2 (Rank 5) |
| **6** | **EXP_R09_Spheremap_Trans_Caribe** | Spheremap Gran Círculo Estándar (rad 1.5°) | 0.3584 | 0.4584 | 13.59 | -4.59% | 0.6477 | 0.3132 | 0.4633 | 0.4843 | Fase 1 (Rank 6) |
| **7** | **EXP_R07_Cressman_Spherical** | Cressman Celdas Aisladas (Guía Oficial CDT: 4 pasadas 1.0° a 0.25°) | 0.3318 | 0.4468 | 14.44 | +3.64% | 0.6299 | 0.2958 | 0.4436 | 0.4724 | Guía CDT |
| **8** | **EXP_R13_QM_Empirical_ECDF** | Quantile Mapping Empírico No-Paramétrico (qmecdf) | 0.3196 | 0.4655 | 13.08 | -5.57% | 0.6393 | 0.2995 | 0.4458 | 0.4658 | Fase 2 (Rank 8) |
| **9** | **EXP_R06_Barnes_Gauss_Coastal** | Barnes BSc Gaussiano Costero (NN-3D con DEM) | 0.3087 | 0.4490 | 14.22 | +4.08% | 0.6461 | 0.2976 | 0.4450 | 0.4635 | Fase 1 (Rank 9) |
| **10** | **EXP_R01_SBA_IDW_Baseline** | Control Nulo / IDW Plano Monocapa (Sin RnoR) | 0.3353 | 0.4861 | 12.22 | -13.53% | 0.6657 | 0.2743 | 0.4178 | 0.4396 | Línea Base |
| **11** | **EXP_R02_SBA_IDW_RnoR** | SBA IDW 3 pasadas + RnoR (Corte Rígido 0.5 mm) | 0.2631 | 0.4659 | 12.39 | -22.15% | 0.6132 | 0.2718 | 0.4109 | 0.3743 | Fase 1 (Rank 11) |
| **12** | **EXP_R05_RK_Topography_BW** | Regression Kriging Topográfico (Weibull + DEM) | 0.2147 | 0.4166 | 13.28 | -18.28% | 0.5216 | 0.2010 | 0.3215 | 0.3463 | Fase 1 (Rank 12) |
| **13** | **EXP_R03_SBA_OKR_BernoulliGamma** | QM Paramétrico Gamma + OKR por Bloques | -0.0277 | 0.4275 | 14.87 | -5.83% | 0.6389 | 0.2460 | 0.3729 | 0.3231 | Fase 1 (Rank 13) |
| **14** | **EXP_R04_SBA_OKR_BernoulliWeib** | QM Paramétrico Weibull + OKR por Bloques | 0.0159 | 0.4306 | 14.51 | -11.98% | 0.6357 | 0.2475 | 0.3733 | 0.3148 | Fase 1 (Rank 14) |
| **15** | **EXP_R10_RK_FullTopography_Asp** | RK Máxima Complejidad (DEM + Pendiente + Aspect) | 0.1062 | 0.4112 | 14.11 | -18.36% | 0.5084 | 0.1901 | 0.3073 | 0.3045 | Fase 1 (Rank 15) |

> **Hallazgos Clave:**
> 1. **Modelo Ganador:** `EXP_R15_Shepard_RnoR_Smooth` supera a todos los esquemas evaluados ($\text{Skill} = 0.5007$, $\text{KGE} = 0.3791$, $\text{POD} = 69.22\%$, $\text{ETS} = 0.3287$). La transición continua suave (`RnoRCutOff: 2`) entre 0.1 y 1.0 mm eliminó la subestimación severa de lluvia de la máscara binaria rígida ($\text{PBIAS} = -4.39\%$ frente a $-22.15\%$ en `R02`).
> 2. **Familia Dominante:** La formulación de Shepard Modificado dominó los primeros 4 lugares del benchmark (`R15`, `R12`, `R08`, `R11`), debido a que su ponderación direccional atenúa la fuga espuria de humedad a través de barreras orográficas abruptas.

## Estructura de Preparación de Datos (`data/`)

- **Estaciones y Listas de Exclusión (`data/stations/`):**
  - Para Centroamérica: `precip_stations_ca.csv`, `tmax_stations_ca.csv`, `tmin_stations_ca.csv`
  - Para Rep. Dominicana: `precip_stations_rd.csv`, `tmax_stations_rd.csv`, `tmin_stations_rd.csv`
  - _(Opcional)_ Archivo general combinado: `precip_stations_all.csv`, `tmax_stations_all.csv`, `tmin_stations_all.csv`
  - Formato CDT (4 líneas de encabezado: `ID`, `LON`, `LAT`, `ELEV`).
  - **Validación Cruzada Independiente (*Holdout*):**
    - `validation_holdout_stations_rainfall.csv` → IDs de estaciones omitidas para **Precipitación**.
    - `validation_holdout_stations_temperature.csv` → IDs de estaciones omitidas para **Temperatura (Tmax/Tmin)**.
- **Grillas Satelitales (`data/chirps_daily/` y `data/chirts_daily/{tmax,tmin}/`):** Archivos NetCDF diarios 2D (o NetCDFs 3D multitemporales en `data/raw_netcdf/` para particionar automáticamente).
- **Topografía (`data/topography/`):** DEM SRTM/GEBCO en NetCDF (`dem_srtm_central_america.nc`, `dem_srtm_dominicana.nc` o `dem_srtm_90m.nc`).
- **Cartografía GIS (`data/gis/`):** Shapefile con buffer 10 km (`central_america.shp`, `republica_dominicana.shp` o `central_america_dominican_rep.shp` junto con `.shx`, `.dbf`, `.prj`).

## Módulos de Documentación Técnica

Para fundamentos matemáticos profundos, justificaciones físicas, menús de CDT GUI/CLI y pautas de publicación, consulta la carpeta [`docs/`](docs/README.md):

- [**Índice General de Documentación Técnica**](docs/README.md)
- [**Guía de Preparación de Datos (`data/`) y Arquitectura de Lanzadores**](docs/09_arquitectura_lanzadores_python_y_dependencias.md)
- [**Protocolo Metodológico Maestro y Matriz de 31 Experimentos**](docs/10_matriz_maestra_experimentos_y_guia_metodologica.md)
- [**Diagnóstico Científico de Fase 1 y Diseño/Resultados de Fase 2 (Precipitación)**](docs/12_diagnostico_fase1_y_diseno_fase2_precipitacion.md)
- [**Influencia del DEM, Batimetría y Orografía en el Desescalado de Temperatura**](docs/13_influencia_dem_batimetria_desescalado_temperatura.md)
- [**Diagnóstico Científico de Fase 1 y Diseño Metodológico de Fase 2 (Temperatura)**](docs/14_diagnostico_fase1_y_diseno_fase2_temperatura.md)
- [**Guía de Despliegue en Contenedores (Docker, Compose, Apptainer/Singularity)**](docs/11_guia_despliegue_contenedores_docker_apptainer.md)
- [**Documento PDF Compilado**](docs/Matriz_Experimentos_CDT_Centroamerica_Dominicana.pdf)
