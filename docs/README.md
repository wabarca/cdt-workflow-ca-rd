# Documentación Técnica y Metodológica: Climate Data Tools (CDT v8.0)

> **Proyecto:** “Escenarios de Cambio Climático de Alta Resolución en Centroamérica y el Caribe”  
> **Grupo Oficial:** Grupo de Trabajo Regional de Escenarios de Cambio Climático de Centroamérica y el Caribe  
> **Horizonte Climatológico:** Serie histórica estándar **1991–2020** (10,958 días continuos)  
> **Bases de Reanálisis:** CHIRPS v2.0 ($0.05^\circ$), CHIRTS-daily ($0.05^\circ$), DEM SRTM (90 m / 1 km)  
> **Alcance Geográfico del Benchmark:** Centroamérica (Guatemala a Panamá, 29 estaciones ciegas independientes).

Esta carpeta contiene la documentación técnica, física y metodológica para la automatización, experimentación controlada y reconstrucción climática mediante **Climate Data Tools (CDT)** acoplado a la suite de orquestación en Python.

---

## Guía Rápida de Comandos CLI (Procesamiento en Paralelo Habilitado)

El orquestador en Python (`launcher/experiment_runner.py`) cuenta con **procesamiento en paralelo multihilo habilitado** (`--cores 18` por defecto en estaciones de trabajo) para acelerar el procesamiento de los 10,958 pasos de tiempo diarios:

```bash
# Comprobar el entorno y dependencias de R:
python launcher/experiment_runner.py --check-env

# Ejecutar suites completas con 18 hilos en paralelo:
python launcher/experiment_runner.py --suite rainfall --cores 18   # 15 Experimentos de Precipitación (~55.3 h)
python launcher/experiment_runner.py --suite tmax     --cores 18   # 12 Experimentos de Tmax (~18.5 h)
python launcher/experiment_runner.py --suite tmin     --cores 18   # 12 Experimentos de Tmin (~18.5 h)

# Ejecutar corrida en lote completa (39 experimentos, 1991–2020):
python launcher/experiment_runner.py --suite all      --cores 18   # 39 Experimentos continuos (~92.4 h)

# Ejecutar un experimento individual (ej. modelo ganador de lluvia):
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R15_Shepard_RnoR_Smooth.yaml --cores 18

# Generar el reporte maestro consolidado en PDF:
python launcher/generate_pdf.py
```

---

## Estructura Curricular y Mapa de Navegación de la Documentación

La documentación se organiza en **4 bloques lógicos y 10 módulos secuenciales**, comenzando por la guía de ejecución y producción:

### Bloque I: Guías de Ejecución, Automatización y Arquitectura del Sistema
1. [**01. Guía de Ejecución desde Terminal (CLI / Headless) y Scripts de Producción**](01_guia_ejecucion_produccion_y_scripts.md)
   - Ejecución desde línea de comandos, banderas CLI (`--suite`, `--config`, `--cores`), procesamiento en paralelo multihilo habilitado, scripts en R para producción desatendida y plantillas de automatización bash/cron.
2. [**02. Arquitectura del Orquestador en Python, CLI y Ensamblado NetCDF (CF-1.8)**](02_arquitectura_lanzadores_python.md)
   - Diseño del puente headless con CDT (`launcher/cdt_bridge.py`), orquestador paralelo multiproceso (`launcher/experiment_runner.py`), particionador de estaciones ciegas (`station_manager.py`), evaluador de métricas y ensamblado en archivos NetCDF 3D estándar CF-1.8.
3. [**03. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity**](03_despliegue_contenedores_docker_apptainer.md)
   - Procedimientos para garantizar reproducibilidad exacta y portabilidad inmutable en servidores locales, clústeres de supercómputo HPC con gestor SLURM y entornos en la nube.

### Bloque II: Fundamentos Teóricos y Tratamiento Fisiográfico
4. [**04. Fundamentos del Proceso de Fusión (Merging) y Gridding en CDT**](04_fundamentos_gridding_merging_cdt.md)
   - Conceptos de soporte espacial, grilla continua satelital vs. observaciones puntuales in situ, formulación general de residuales y etapas del proceso.
5. [**05. Métodos Geoestadísticos y Parámetros de Interpolación de Residuales**](05_metodos_interpolacion_residuales.md)
   - Formulación matemática de SBA, Regression Kriging (RK), IDW, Kriging Ordinario por Bloques con semivariogramas teóricos, análisis objetivo de Barnes y Cressman, y método de Shepard Modificado, con referencias científicas verificadas.
6. [**06. Tratamiento Fisiográfico del DEM, Batimetría Marina y Protección Insular**](06_tratamiento_fisiografico_dem_batimetria.md)
   - Modelado del gradiente térmico vertical adiabático ($\Gamma pprox -6.5\ ^\circ	ext{C/km}$), clampeo obligatorio de cotas submarinas negativas a $0	ext{ msnm}$, protección integral de islas habitadas y continuidad litoral.

### Bloque III: Secuencias de Procesamiento Oficiales por Variable (Workflows)
7. [**07. Secuencia de Procesamiento de Precipitación (CHIRPS) y Máscara Rain-No-Rain**](07_secuencia_precipitacion_chirps_rnor.md)
   - Flujo de 3 pasos en CDT: cálculo de sesgo multiplicativo y distribucional (Bernoulli-Gamma/Weibull), aplicación a grillas diarias NetCDF de CHIRPS, y fusión geoestadística con máscara Lluvia/No-Lluvia (RnoR). Detalle de los **15 experimentos (Fase 1: EXP-R01 a R10; Fase 2: EXP-R11 a R15)**.
8. [**08. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM**](08_secuencia_temperatura_chirts_dem.md)
   - Flujo de 5 pasos en CDT: cálculo de coeficientes de desescalado orográfico, reducción de escala a 1 km, cálculo de sesgo diurno ($T_{\max}$) y nocturno ($T_{\min}$), aplicación del ajuste y fusión espacial de residuales. Detalle de los **24 experimentos térmicos (Fase 1 y Fase 2: EXP-TX01 a TX12 y EXP-TN01 a TN12)**.

### Bloque IV: Diagnóstico Científico, Benchmarks y Resultados Consolidados
9. [**09. Diagnóstico Científico de Fase 1 y Resultados del Benchmark de Precipitación (Fase 2)**](09_diagnostico_y_benchmark_precipitacion.md)
   - Evaluación exploratoria preliminar de los 10 experimentos de Fase 1, optimización dirigida en Fase 2 (5 experimentos), ranking consolidado de los 15 experimentos evaluados sobre 29 estaciones ciegas holdout y selección del modelo ganador `EXP_R15_Shepard_RnoR_Smooth`.
10. [**10. Diagnóstico Científico y Resultados del Benchmark de Temperatura (Tmax y Tmin)**](10_diagnostico_y_benchmark_temperatura.md)
    - Análisis de 24 experimentos térmicos (12 $T_{\max}$ y 12 $T_{\min}$), diagnóstico de la divergencia termodinámica convectiva diurna vs. desacople e inversiones nocturnas, justificación física del rechazo a la Línea Base sin DEM, y selección de ganadores oficiales (`EXP_TX11` y `EXP_TN10`).

---

## Resumen de Modelos Ganadores Oficiales

| Variable Climática | Configuración Ganadora Oficial | Familia Metodológica | Desempeño Cuantitativo (Holdout Ciego) | Justificación Físico-Climatológica |
| :--- | :--- | :--- | :--- | :--- |
| **Precipitación Diaria** | **`EXP_R15_Shepard_RnoR_Smooth`** | SBA Multiescala + Shepard Modificado + RnoR Suave (`CutOff = 2`) | **GSS:** 0.501 \| **KGE:** 0.379 \| **ETS:** 0.329 \| **RMSE:** 12.88 mm | Suprime lloviznas espurias (*drizzle*) en la Canícula sin discontinuidades y preserva gradientes en cañones y laderas escarpadas. |
| **Temperatura Máxima ($T_{\max}$)** | **`EXP_TX11_RK_Barnes_Hybrid`** | RK (DEM + Lat + Lon) + Barnes Gaussiano Continuo | **GSS:** 0.719 \| **KGE:** **0.690** \| **$r$:** 0.743 \| **RMSE:** 2.06 $^\circ	ext{C}$ | Forzamiento orográfico real con DEM en zonas sin estaciones y filtrado continuo de brisas marinas y transiciones litorales. |
| **Temperatura Mínima ($T_{\min}$)** | **`EXP_TN10_QM_Empirical_ECDF`** | RK (DEM + Pendiente) + QM Empírico Celda a Celda (NN-3D) | **GSS:** **0.613** \| **KGE:** 0.543 \| **RMSE:** **1.92 $^\circ	ext{C}$** \| **MAE:** 1.57 $^\circ	ext{C}$ | Menor error absoluto y cuadrático del benchmark; captura inversiones nocturnas y pozas de aire frío (*cold-air pooling*) sin distorsionar colas frías. |

---

## Documentación Técnica Complementaria

Para consultar el informe unificado en formato imprimible con la auditoría de cómputo en hardware y los tableros completos de validación ciega holdout:
- **Documento Markdown Maestro:** `docs-private/reporte_maestro_benchmark_cdt.md`
- **Documento PDF Imprimible:** `docs-private/reporte_maestro_benchmark_cdt.pdf` (Generado automáticamente mediante `python launcher/generate_pdf.py`).
