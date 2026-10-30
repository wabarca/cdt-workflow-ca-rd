# Documentación Técnica y Guía de Automatización: Climate Data Tools (CDT v8.0)

Esta carpeta contiene la documentación técnica, matemática y metodológica para el procesamiento automatizado, la experimentación científica y la reconstrucción climática con **Climate Data Tools (CDT)** utilizando series diarias del periodo climatológico estándar **1991–2020** (10,958 días) de **CHIRPS** (precipitación), **CHIRTS** (temperatura máxima y mínima), **DEM SRTM** (topografía), **Shapefiles** de recorte regional (Centroamérica y República Dominicana), **estaciones meteorológicas** de superficie y la suite de **orquestación en Python**.

---

## Índice de Módulos Técnicos Unificados

1. [**01. Automatización y Ejecución desde Terminal (CLI / Headless)**](file:///d:/Workspace/CDT-8.0/docs/01_automatizacion_terminal_cli.md)
   - Arquitectura sin GUI, funciones exportadas `*CMD`, ejecución mediante `Rscript`, control de logging y orquestación desde Python.

2. [**02. Fundamentos del Proceso de Fusión (Merging)**](file:///d:/Workspace/CDT-8.0/docs/02_gridding_merging_fundamentos.md)
   - Algoritmo paso a paso, métodos SBA, RK, Cressman, Barnes y esquema multi-pasada iterativo.

3. [**03. Métodos y Parámetros de Interpolación de Residuales**](file:///d:/Workspace/CDT-8.0/docs/03_metodos_interpolacion_residuales.md)
   - IDW, Ordinary Kriging (Block Kriging, modelos de variograma), Shepard, Spheremap, NN-3D y _fail-safes_.

4. [**04. Fusión de Precipitación y Máscara Rain-No-Rain**](file:///d:/Workspace/CDT-8.0/docs/04_merging_precipitacion_rnor.md)
   - Máscara probabilística RnoR (Logit vs Aditivo), funciones de corte (CutOff 1, 2, 3), suavizado espacial y límites físicos.

5. [**05. Fusión de Temperatura y Modelado Topográfico**](file:///d:/Workspace/CDT-8.0/docs/05_merging_temperatura_dem.md)
   - Gradiente térmico vertical (_lapse rate_), regresión GLM con covariables DEM, pendiente y aspecto/orientación.

6. [**06. Plantillas y Scripts de Producción**](file:///d:/Workspace/CDT-8.0/docs/06_ejemplos_scripts_produccion.md)
   - Scripts listos para ejecución en producción, servidores headless, tareas programadas (cron / Task Scheduler) y orquestadores Python.

7. [**07. Flujo Completo de Temperatura (CHIRTS) y Diseño Experimental**](file:///d:/Workspace/CDT-8.0/docs/07_flujo_completo_temperatura_chirts.md)
   - Cadena: _Split 3D NC → Downscaling Coef → Downscale Data → Bias Coef → Bias Correction → Merging → Concatenate 3D_.
   - Justificación de dinámicas diurnas ($T_{max}$) vs nocturnas ($T_{min}$), inversiones térmicas y frentes fríos (_Nortes_).

8. [**08. Flujo Completo de Precipitación (CHIRPS) y Diseño Experimental**](file:///d:/Workspace/CDT-8.0/docs/08_flujo_completo_precipitacion_chirps.md)
   - Cadena: _Split 3D NC → Bias Coef → Bias Correction → Merging + RnoR → Concatenate 3D_.
   - Modelado de variables mixtas cero-continuas (Bernoulli-Gamma, Bernoulli-Weibull) y métricas de validación.

9. [**09. Arquitectura de Lanzadores en Python y Verificación de Dependencias**](file:///d:/Workspace/CDT-8.0/docs/09_arquitectura_lanzadores_python_y_dependencias.md)
   - Diseño del orquestador híbrido en Python para ejecutar lotes de experimentos.
   - Diagnóstico multiplataforma: comprobación de ejecutables `Rscript` (ej. R 4.4.3), librerías de sistema en Linux y Rtools en Windows.
   - Guía de uso de la CLI, flags (`--suite`, `--config`, `--base-config`), partición automática de estaciones omitidas y ensamblado NetCDF 3D CF-1.8.

10. [**10. Protocolo Metodológico Maestro y Matriz Completa de 31 Experimentos**](file:///d:/Workspace/CDT-8.0/docs/10_matriz_maestra_experimentos_y_guia_metodologica.md)
    - **Módulo Técnico Unificado:** Integra la significancia estadística y climatológica profunda de la interpolación, la justificación fisiográfica regional (Pacífico, Caribe, Corredor Seco, Azua, Enriquillo, valles altos), las tablas comparativas de los **31 experimentos** (15 Lluvia: Fase 1 y 2, 8 $T_{max}$, 8 $T_{min}$) con justificación celda por celda, fórmulas de validación cruzada independiente ($KGE$, $RMSE$, $MAE$, $PBIAS$, $POD$, $FAR$, $ETS$, $HSS$), evaluación de hardware en estación Linux Ubuntu (Intel Core i9-10850K @ 3.60GHz, 32 GB RAM DDR4, SSD NVMe 400 GB) y 19 referencias bibliográficas científicas con DOIs verificados.


11. [**11. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity**](file:///d:/Workspace/CDT-8.0/docs/11_guia_despliegue_contenedores_docker_apptainer.md)
    - Procedimientos de ejecución en contenedores inmutables: `Dockerfile`, `docker-compose.yml`, DevContainers y `Apptainer.def` para supercómputo HPC / SLURM.

12. [**12. Diagnóstico Científico de Fase 1 y Diseño/Resultados de Fase 2 (Precipitación)**](file:///d:/Workspace/CDT-8.0/docs/12_diagnostico_fase1_y_diseno_fase2_precipitacion.md)
    - Diagnóstico de los 10 experimentos de la Fase 1, diseño de los 5 experimentos de la Fase 2, y análisis exhaustivo del **tablero de liderazgo consolidado de los 15 experimentos** evaluados sobre las 29 estaciones de validación ciega independiente (*holdout*), donde **EXP_R15_Shepard_RnoR_Smooth** se corona como el modelo ganador absoluto ($KGE = 0.3791$, $Skill = 0.5007$, $PBIAS = -4.39\%$, $POD = 69.22\%$, $ETS = 0.3287$).


13. [**13. Influencia del DEM, Batimetría y Orografía en el Desescalado y Corrección de Temperatura**](file:///d:/Workspace/CDT-8.0/docs/13_influencia_dem_batimetria_desescalado_temperatura.md)
    - Fundamento físico del gradiente adiabático (*lapse rate*), cuantificación de la brecha altimétrica (Δz ≈ 1,820 m) y error térmico inducido (> 10 °C).
    - Análisis comparativo: DEM continental terrestre (z >= 0) vs. modelos con batimetría (GEBCO, -8,390 m a +5,611 m) y mecanismos de fallo numérico en regresiones lineales.
    - Justificación de la secuencia de 5 pasos en CDT: por qué el desescalado orográfico es indispensable antes del ajuste de sesgo cuantitativo (*Quantile Mapping*).
    - Lección metodológica y blindaje del sistema ante valores centinela faltantes ('-99' vs '-99.0').


14. [**14. Diagnóstico Científico de Fase 1 y Diseño Metodológico de Fase 2 (Temperatura Tmax y Tmin)**](file:///d:/Workspace/CDT-8.0/docs/14_diagnostico_fase1_y_diseno_fase2_temperatura.md)
    - Análisis exhaustivo de los resultados de la Fase 1 (EXP_01 a EXP_08) evaluados contra las 29 estaciones de validación ciega independiente.
    - Diagnóstico de la divergencia termodinámica entre forzamiento diurno (Tmax: r ≈ 0.79, KGE = 0.68) e inversiones nocturnas/drenaje catabático (Tmin: r ≈ 0.67, MAE = 1.76 °C con NN-3D).
    - Explicación del colapso del Quantile Mapping teórico analítico (norm, gumbel, snorm) y formulación de la Fase 2 de optimización dirigida (EXP_T09 a EXP_T12).
    - Incorporación de Shepard Modificado 3D, Quantile Mapping Empírico no paramétrico (qmecdf), híbridos Regression Kriging + Barnes y SBA IDW local multiescala.

---

## Estructura de Configuraciones y Suites Experimentales

- **Configuración Maestra Global:** [`config/global_config.yaml`](file:///d:/Workspace/CDT-8.0/config/global_config.yaml)
- **Estaciones de Validación Independiente:** [`data/stations/validation_holdout_stations.csv`](file:///d:/Workspace/CDT-8.0/data/stations/validation_holdout_stations.csv)
- **Suite de Precipitación (Fase 1: EXP_R01 a R10 | Fase 2: EXP_R11 a R15):** [`config/experiments_rainfall/`](file:///d:/Workspace/CDT-8.0/config/experiments_rainfall)
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
