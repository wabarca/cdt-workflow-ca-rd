# Documentación Técnica y Metodológica: Climate Data Tools (CDT v8.0)

> **Proyecto:** “Escenarios de Cambio Climático de Alta Resolución en Centroamérica y el Caribe”  
> **Grupo Oficial:** Grupo de Trabajo Regional de Escenarios de Cambio Climático de Centroamérica y el Caribe  
> **Horizonte Climatológico:** Serie histórica estándar **1991–2020** (10,958 días continuos)  
> **Bases de Reanálisis y Satélite:** CHIRPS ($0.05^\circ$), CHIRTS-ERA5 ($0.05^\circ$), DEM Continental Saneado ($z \ge 0\text{ msnm}$)  
> **Alcance Geográfico del Benchmark:** Centroamérica (`--region ca`, 29 estaciones ciegas independientes) y República Dominicana (`--region rd`).

Esta carpeta contiene la documentación técnica, física y metodológica para la automatización, experimentación controlada y reconstrucción climática mediante **Climate Data Tools (CDT)** acoplado a la suite de orquestación en Python.

---

## Guía Rápida de Comandos CLI (Procesamiento en Paralelo y Evaluación Automática de `EXP_00`)

El orquestador en Python ([`launcher/experiment_runner.py`](../launcher/experiment_runner.py)) cuenta con **procesamiento en paralelo multihilo habilitado** (`--cores 18`), soporte para insumos regionales independientes (`--region ca` y `--region rd`), y **evaluación automática de la rejilla satelital original sin corregir (`EXP_00`)** junto con la generación del reporte de benchmark al finalizar cada suite:

```bash
# 1. Comprobar el entorno de R y validar los insumos regionales (Estaciones, DEM, Shapefile y NetCDFs 3D/2D):
python launcher/experiment_runner.py --check-env
python launcher/experiment_runner.py --check-data --region ca
python launcher/experiment_runner.py --check-data --region rd

# 2. Ejecutar suites completas con 18 hilos en paralelo (incluye auto-evaluación de EXP_00 + Benchmark):
python launcher/experiment_runner.py --suite rainfall --region ca --cores 18   # Control EXP_R00 + 15 Exp. Precipitación (~55.3 h)
python launcher/experiment_runner.py --suite tmax     --region ca --cores 18   # Control EXP_TX00 + 12 Exp. Tmax (~18.5 h)
python launcher/experiment_runner.py --suite tmin     --region ca --cores 18   # Control EXP_TN00 + 12 Exp. Tmin (~18.5 h)

# 3. Ejecutar corrida en lote completa (42 configuraciones: 3 Controles EXP_00 + 39 Experimentos CDT, 1991–2020):
python launcher/experiment_runner.py --suite all      --region ca --cores 18   # 42 configuraciones (~92.4 h)

# 4. Ejecutar un experimento individual:
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R15_Shepard_RnoR_Smooth.yaml --region ca --cores 18

# 5. Regenerar el dashboard de benchmark (figuras a 300 DPI + reporte HTML):
python launcher/experiment_runner.py --benchmark --region ca
```

---

## Estructura Curricular y Mapa de Navegación de la Documentación

La documentación se organiza en **5 bloques lógicos y 12 módulos secuenciales**, comenzando por la guía de ejecución y producción:

### Bloque I: Guías de Ejecución, Automatización y Arquitectura del Sistema
1. [**01. Guía de Ejecución desde Terminal (CLI / Headless) y Scripts de Producción**](01_guia_ejecucion_produccion_y_scripts.md)
   - Ejecución desde línea de comandos, banderas CLI (`--suite`, `--config`, `--region`, `--cores`, `--force`), evaluación automática del control satelital `EXP_00`, scripts en R para producción desatendida y plantillas de automatización bash/cron.
2. [**02. Arquitectura del Orquestador en Python, CLI y Ensamblado NetCDF (CF-1.8)**](02_arquitectura_lanzadores_python.md)
   - Diseño del puente *headless* con CDT ([`launcher/cdt_bridge.py`](../launcher/cdt_bridge.py)), orquestador paralelo multiproceso ([`launcher/experiment_runner.py`](../launcher/experiment_runner.py)), separación regional de NetCDFs 3D y grillas diarias 2D (`ca` y `rd`), particionador de estaciones ciegas ([`launcher/station_manager.py`](../launcher/station_manager.py)), evaluador de rejilla original ([`launcher/evaluate_raw_baseline.py`](../launcher/evaluate_raw_baseline.py)) y ensamblado en archivos NetCDF 3D estándar CF-1.8.
3. [**03. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity**](03_despliegue_contenedores_docker_apptainer.md)
   - Procedimientos para garantizar reproducibilidad exacta y portabilidad inmutable en servidores locales, clústeres de supercómputo HPC con gestor SLURM y entornos en la nube.

### Bloque II: Fundamentos Teóricos y Tratamiento Fisiográfico
4. [**04. Fundamentos del Proceso de Fusión (Merging) y Gridding en CDT**](04_fundamentos_gridding_merging_cdt.md)
   - Conceptos de soporte espacial, grilla continua satelital vs. observaciones puntuales *in situ*, formulación general de residuales y etapas del proceso.
5. [**05. Métodos Geoestadísticos y Parámetros de Interpolación de Residuales**](05_metodos_interpolacion_residuales.md)
   - Formulación matemática de SBA, Regression Kriging (RK), IDW, Kriging Ordinario por Bloques con semivariogramas teóricos, análisis objetivo de Barnes y Cressman, y método de Shepard Modificado, con referencias científicas verificadas.
6. [**06. Tratamiento Fisiográfico del DEM, Batimetría Marina y Protección Insular**](06_tratamiento_fisiografico_dem_batimetria.md)
   - Modelado del gradiente térmico vertical adiabático ($\Gamma \approx -6.5\ ^\circ\text{C/km}$), clampeo obligatorio de cotas submarinas negativas a $0\text{ msnm}$, protección integral de islas habitadas y continuidad litoral.

### Bloque III: Secuencias de Procesamiento Oficiales por Variable (Workflows)
7. [**07. Secuencia de Procesamiento de Precipitación (CHIRPS) y Máscara Rain-No-Rain**](07_secuencia_precipitacion_chirps_rnor.md)
   - Flujo de 3 pasos en CDT: cálculo de sesgo multiplicativo y distribucional (Bernoulli-Gamma/Weibull y Quantile Mapping Empírico), aplicación a grillas diarias NetCDF de CHIRPS, y fusión geoestadística con máscara Lluvia/No-Lluvia (RnoR). Detalle de las **16 configuraciones evaluadas (Control `EXP_R00` + Fase 1: `EXP_R01` a `R10` + Fase 2: `EXP_R11` a `R15`)**.
8. [**08. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM**](08_secuencia_temperatura_chirts_dem.md)
   - Flujo de 5 pasos en CDT: cálculo de coeficientes de desescalado orográfico, reducción de escala a 1 km, cálculo de sesgo diurno ($T_{\max}$) y nocturno ($T_{\min}$), aplicación del ajuste y fusión espacial de residuales. Detalle de las **26 configuraciones térmicas (Controles `EXP_TX00` y `EXP_TN00` + 24 experimentos CDT: `EXP_TX01` a `TX12` y `EXP_TN01` a `TN12`)**.

### Bloque IV: Diseño Experimental en Dos Fases y Metodología de Evaluación
9. [**09. Diseño Experimental en Dos Fases y Criterios Climatológicos para Precipitación**](09_diagnostico_y_benchmark_precipitacion.md)
   - Estructura metodológica de la Fase 1 exploratoria (10 experimentos) y la Fase 2 de optimización dirigida (5 experimentos), hipótesis físicas e hidroclimáticas por experimento, y criterios de admisibilidad climatológica frente a artefactos de interpolación (*ojos de buey* y truncamiento de lloviznas).
10. [**10. Diseño Experimental en Dos Fases y Criterios Termodinámicos para Temperatura (Tmax y Tmin)**](10_diagnostico_y_benchmark_temperatura.md)
    - Diseño de las 26 configuraciones térmicas (Fase 1: `EXP_01`–`08` y Fase 2: `EXP_09`–`12` más controles `EXP_00`), contraste termodinámico entre convección diurna ($T_{\max}$) e inversiones radiativas nocturnas ($T_{\min}$), y criterios de admisibilidad física sobre conservación del gradiente térmico vertical ($\Gamma = -\partial T / \partial z$).
11. [**12. Metodología de Evaluación Estadística, Métricas y Validación Cruzada en CDT 8.0**](12_metodologia_evaluacion_metricas_y_validacion.md)
    - Formulación matemática rigurosa en KaTeX ($\text{KGE}_{2012}$, $r$, $R^2$, $\text{RMSE}$, $\text{MAE}$, $\text{PBIAS}$, $\text{POD}$, $\text{FAR}$, $\text{ETS}$, $\text{HSS}$), distinción entre Rejilla Original (`EXP_00`), Línea Base 2D (`EXP_01`) y modelos físicamente admisibles, agregación regional (media vs. mediana) y Diagrama de Taylor.

### Bloque V: Auditoría del Código Fuente en R y Ejecución Desatendida (*Headless*)
12. [**11. Modificaciones al Código Fuente R de CDT y Resolución de la Paralelización**](11_modificaciones_codigo_fuente_r_y_paralelizacion.md)
    - Diagnóstico del bucle de ventanas en Tcl/Tk (`tcltk`), desactivación fija del paralelismo en la interfaz original, aislamiento de memoria en procesos secundarios (clústeres locales PSOCK), aceleración de cuantiles empíricos mediante nudos ordenados (`stats::knots`), omisión inteligente de archivos ya calculados (*smart file skip*) e inventario detallado de ajustes en `R/`.
