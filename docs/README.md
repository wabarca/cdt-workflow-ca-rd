# Documentación Técnica y Guía de Automatización: Climate Data Tools (CDT v8.0)

Esta carpeta contiene la documentación técnica, matemática y metodológica para el procesamiento automatizado, la experimentación científica y la reconstrucción climática con **Climate Data Tools (CDT)** utilizando series diarias del periodo climatológico estándar **1991–2020** (10,958 días) de **CHIRPS** (precipitación), **CHIRTS** (temperatura máxima y mínima), **DEM SRTM** (topografía), **Shapefiles** de recorte regional (Centroamérica y República Dominicana), **estaciones meteorológicas** de superficie y la suite de **orquestación en Python**.

---

## Índice de Módulos Técnicos Unificados

1. [**01. Automatización y Ejecución desde Terminal (CLI / Headless)**](file:///d:/Workspace/CDT-8.0/docs/01_automatizacion_terminal_cli.md)
   - Arquitectura sin GUI, funciones exportadas `*CMD`, ejecución mediante `Rscript`, control de logging y orquestación desde Python.

2. [**02. Fundamentos del Proceso de Fusión (Merging)**](file:///d:/Workspace/CDT-8.0/docs/02_gridding_merging_fundamentos.md)
   - Algoritmo paso a paso, métodos SBA, RK, Cressman, Barnes y esquema multi-pasada iterativo.

3. [**03. Métodos y Parámetros de Interpolación de Residuales**](file:///d:/Workspace/CDT-8.0/docs/03_metodos_interpolacion_residuales.md)
   - IDW, Ordinary Kriging (Block Kriging, modelos de variograma), Shepard, Spheremap, NN-3D y *fail-safes*.

4. [**04. Fusión de Precipitación y Máscara Rain-No-Rain**](file:///d:/Workspace/CDT-8.0/docs/04_merging_precipitacion_rnor.md)
   - Máscara probabilística RnoR (Logit vs Aditivo), funciones de corte (CutOff 1, 2, 3), suavizado espacial y límites físicos.

5. [**05. Fusión de Temperatura y Modelado Topográfico**](file:///d:/Workspace/CDT-8.0/docs/05_merging_temperatura_dem.md)
   - Gradiente térmico vertical (*lapse rate*), regresión GLM con covariables DEM, pendiente y aspecto/orientación.

6. [**06. Plantillas y Scripts de Producción**](file:///d:/Workspace/CDT-8.0/docs/06_ejemplos_scripts_produccion.md)
   - Scripts listos para ejecución en producción, servidores headless, tareas programadas (cron / Task Scheduler) y orquestadores Python.

7. [**07. Flujo Completo de Temperatura (CHIRTS) y Diseño Experimental**](file:///d:/Workspace/CDT-8.0/docs/07_flujo_completo_temperatura_chirts.md)
   - Cadena: *Split 3D NC $\rightarrow$ Downscaling Coef $\rightarrow$ Downscale Data $\rightarrow$ Bias Coef $\rightarrow$ Bias Correction $\rightarrow$ Merging $\rightarrow$ Concatenate 3D*.
   - Justificación de dinámicas diurnas ($T_{max}$) vs nocturnas ($T_{min}$), inversiones térmicas y frentes fríos (*Nortes*).

8. [**08. Flujo Completo de Precipitación (CHIRPS) y Diseño Experimental**](file:///d:/Workspace/CDT-8.0/docs/08_flujo_completo_precipitacion_chirps.md)
   - Cadena: *Split 3D NC $\rightarrow$ Bias Coef $\rightarrow$ Bias Correction $\rightarrow$ Merging + RnoR $\rightarrow$ Concatenate 3D*.
   - Modelado de variables mixtas cero-continuas (Bernoulli-Gamma, Bernoulli-Weibull) y métricas de validación.

9. [**09. Arquitectura de Lanzadores en Python y Verificación de Dependencias**](file:///d:/Workspace/CDT-8.0/docs/09_arquitectura_lanzadores_python_y_dependencias.md)
   - Diseño del orquestador híbrido en Python para ejecutar lotes de experimentos.
   - Diagnóstico multiplataforma: comprobación de ejecutables `Rscript` (ej. R 4.4.3), librerías de sistema en Linux y Rtools en Windows.
   - Guía de uso de la CLI, flags (`--suite`, `--config`, `--base-config`), partición automática de estaciones omitidas y ensamblado NetCDF 3D CF-1.8.

10. [**10. Protocolo Metodológico Maestro y Matriz Completa de 26 Experimentos**](file:///d:/Workspace/CDT-8.0/docs/10_matriz_maestra_experimentos_y_guia_metodologica.md)
    - **Módulo Técnico Unificado:** Integra la significancia estadística y climatológica profunda de la interpolación, la justificación fisiográfica regional (Pacífico, Caribe, Corredor Seco, Azua, Enriquillo, valles altos), las tablas comparativas de los **26 experimentos** (10 Lluvia, 8 $T_{max}$, 8 $T_{min}$) con justificación celda por celda, fórmulas de validación cruzada independiente ($KGE$, $RMSE$, $MAE$, $PBIAS$, $POD$, $FAR$, $ETS$, $HSS$), evaluación de hardware en Intel Xeon Silver 4210R y 19 referencias bibliográficas científicas con DOIs verificados.
    - Base técnica compilada en el documento PDF: [**`Matriz_Experimentos_CDT_Centroamerica_Dominicana.pdf`**](file:///d:/Workspace/CDT-8.0/docs/Matriz_Experimentos_CDT_Centroamerica_Dominicana.pdf).

11. [**11. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity**](file:///d:/Workspace/CDT-8.0/docs/11_guia_despliegue_contenedores_docker_apptainer.md)
    - Procedimientos de ejecución en contenedores inmutables: `Dockerfile`, `docker-compose.yml`, DevContainers y `Apptainer.def` para supercómputo HPC / SLURM.

---

## Estructura de Configuraciones y Suites Experimentales

- **Configuración Maestra Global:** [`config/global_config.yaml`](file:///d:/Workspace/CDT-8.0/config/global_config.yaml)
- **Estaciones de Validación Independiente:** [`data/stations/validation_holdout_stations.csv`](file:///d:/Workspace/CDT-8.0/data/stations/validation_holdout_stations.csv)
- **Suite de Precipitación (10 Experimentos):** [`config/experiments_rainfall/`](file:///d:/Workspace/CDT-8.0/config/experiments_rainfall)
- **Suite de Temperatura Máxima (8 Experimentos):** [`config/experiments_tmax/`](file:///d:/Workspace/CDT-8.0/config/experiments_tmax)
- **Suite de Temperatura Mínima (8 Experimentos):** [`config/experiments_tmin/`](file:///d:/Workspace/CDT-8.0/config/experiments_tmin)

---

## Guía Rápida de Ejecución desde Python

```bash
# 1. Comprobación del entorno de R y paquetes espaciales
python launcher/experiment_runner.py --check-env

# 2. Ejecutar suites temáticas completas:
python launcher/experiment_runner.py --suite rainfall   # 10 Experimentos de Lluvia (~6 h)
python launcher/experiment_runner.py --suite tmax       # 8 Experimentos de Tmax (~11.5 h)
python launcher/experiment_runner.py --suite tmin       # 8 Experimentos de Tmin (~11.5 h)

# 3. Ejecutar corrida batch completa (26 Experimentos, ~28–31.5 h):
python launcher/experiment_runner.py --suite all
```
