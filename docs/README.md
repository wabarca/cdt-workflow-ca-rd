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

# 4. Ejecutar un experimento individual (ej. modelo ganador de lluvia):
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R15_Shepard_RnoR_Smooth.yaml --region ca --cores 18

# 5. Regenerar el dashboard de benchmark (figuras a 300 DPI + reporte HTML) o el informe PDF:
python launcher/experiment_runner.py --benchmark --region ca
python launcher/generate_pdf.py
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

### Bloque IV: Diagnóstico Científico, Benchmarks y Metodología de Validación
9. [**09. Diagnóstico Científico de Fase 1 y Resultados del Benchmark de Precipitación (Fase 2)**](09_diagnostico_y_benchmark_precipitacion.md)
   - Evaluación de los 10 experimentos de Fase 1, optimización dirigida en Fase 2 (5 experimentos), ranking consolidado de las 16 configuraciones evaluadas sobre 29 estaciones ciegas *holdout* y selección del modelo ganador `EXP_R15_Shepard_RnoR_Smooth`.
10. [**10. Diagnóstico Científico y Resultados del Benchmark de Temperatura (Tmax y Tmin)**](10_diagnostico_y_benchmark_temperatura.md)
    - Análisis de las 26 configuraciones térmicas (13 $T_{\max}$ y 13 $T_{\min}$ incluyendo controles `EXP_00`), diagnóstico de la divergencia termodinámica convectiva diurna vs. desacople e inversiones nocturnas, justificación física del rechazo a la Línea Base 2D sin DEM, y selección de ganadores físicos (`EXP_TX11_RK_Barnes_Hybrid` y `EXP_TN10_QM_Empirical_ECDF`).
11. [**12. Metodología de Evaluación Estadística, Métricas y Validación Cruzada en CDT 8.0**](12_metodologia_evaluacion_metricas_y_validacion.md)
    - Formulación matemática rigurosa en KaTeX ($\text{KGE}_{2012}$, $r$, $R^2$, $\text{RMSE}$, $\text{MAE}$, $\text{PBIAS}$, $\text{POD}$, $\text{FAR}$, $\text{ETS}$, $\text{HSS}$), distinción entre Rejilla Original (`EXP_00`), Línea Base 2D (`EXP_01`) y Ganador Físico, agregación regional (media vs. mediana), Diagrama de Taylor e interpretación física del desempeño en Centroamérica y el Caribe.

### Bloque V: Auditoría del Código Fuente en R y Ejecución Desatendida (*Headless*)
12. [**11. Modificaciones al Código Fuente R de CDT y Resolución de la Paralelización**](11_modificaciones_codigo_fuente_r_y_paralelizacion.md)
    - Diagnóstico del bucle de ventanas en Tcl/Tk (`tcltk`), desactivación fija del paralelismo en la interfaz original, aislamiento de memoria en procesos secundarios (clústeres locales PSOCK), aceleración de cuantiles empíricos mediante nudos ordenados (`stats::knots`), omisión inteligente de archivos ya calculados (*smart file skip*) e inventario detallado de ajustes en `R/`.

---

## Resumen de Modelos Ganadores Físicos vs. Controles (`EXP_00` y `EXP_01`)

| Variable Climática | Configuración Ganadora Física | Familia Metodológica | Desempeño Cuantitativo (Holdout Ciego) | Ganancia vs. Rejilla Original (`EXP_00`) y Justificación Física |
| :--- | :--- | :--- | :--- | :--- |
| **Precipitación Diaria** | **`EXP_R15_Shepard_RnoR_Smooth`** | SBA Multiescala + Shepard Modificado + RnoR Suave (`CutOff = 2`) | **GSS:** 0.501 \| **KGE:** **0.379** \| **ETS:** 0.329 \| **RMSE:** 12.88 mm | **+0.095 pts (+33.5%) en KGE vs. CHIRPS crudo (`0.284`)**. Suprime lloviznas espurias (*drizzle*) sin cortes binarios abruptos y preserva gradientes en laderas. |
| **Temperatura Máxima ($T_{\max}$)** | **`EXP_TX11_RK_Barnes_Hybrid`** | RK (DEM + Lat + Lon) + Barnes Gaussiano Continuo | **GSS:** 0.719 \| **KGE:** **0.690** \| **$r$:** 0.743 \| **RMSE:** 2.06 $^\circ\text{C}$ | **+0.172 pts (+33.2%) en KGE vs. CHIRTS crudo (`0.518`)**. Forzamiento orográfico real con DEM continental ($z \ge 0\text{ m}$) y filtrado continuo de brisas marinas. |
| **Temperatura Mínima ($T_{\min}$)** | **`EXP_TN10_QM_Empirical_ECDF`** | RK (DEM + Pendiente) + QM Empírico Celda a Celda (NN-3D) | **GSS:** **0.613** \| **KGE:** **0.543** \| **RMSE:** **1.92 $^\circ\text{C}$** \| **MAE:** 1.57 $^\circ\text{C}$ | **+0.131 pts (+31.8%) en KGE vs. CHIRTS crudo (`0.412`)**. Menor error absoluto y cuadrático del estudio; captura inversiones nocturnas y pozas de aire frío en valles. |

---

## Documentación Técnica Complementaria (`docs-private/`)

Para consultar los documentos internos complementarios del proyecto:
- **Informe Maestro del Benchmark (Markdown y PDF):** `docs-private/reporte_maestro_benchmark_cdt.md` y `docs-private/reporte_maestro_benchmark_cdt.pdf` (generado vía `python launcher/generate_pdf.py`).
- **Fundamento Metodológico sobre CHIRPS (v2 vs. v3) y el Desfase Horario (07:00 AM Local vs. 00:00 UTC):** `docs-private/fundamento_metodologico_chirps_desfase_horario_cdt.md`.
