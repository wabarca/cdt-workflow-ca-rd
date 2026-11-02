# Documentación Técnica y Metodológica Oficial: Climate Data Tools (CDT v8.0)

> **Proyecto:** “Escenarios de Cambio Climático de Alta Resolución en Centroamérica y el Caribe”  
> **Grupo Oficial:** Grupo de Trabajo Regional de Escenarios de Cambio Climático de Centroamérica y el Caribe  
> **Horizonte Climatológico:** Serie histórica estándar **1991–2020** (10,958 días continuos)  
> **Bases de Reanálisis:** CHIRPS v2.0 ($0.05^\circ$), CHIRTS-daily ($0.05^\circ$), DEM SRTM (90 m / 1 km)

Esta carpeta contiene la documentación técnica, matemática, física y metodológica para la automatización, experimentación controlada y reconstrucción climática de alta resolución mediante **Climate Data Tools (CDT)** acoplado a la suite de orquestación en Python.

---

## Estructura Curricular y Mapa de Navegación de la Documentación

La documentación se organiza en **4 bloques lógicos y 10 módulos secuenciales**:

### Bloque I: Fundamentos Teóricos y Tratamiento Fisiográfico
1. [**01. Fundamentos del Proceso de Fusión (Merging) y Gridding en CDT**](01_fundamentos_gridding_merging_cdt.md)
   - Conceptos de soporte espacial, grilla continua satelital vs. observaciones puntuales in situ, formulación general de residuales y etapas del proceso.
2. [**02. Métodos Geoestadísticos y Parámetros de Interpolación de Residuales**](02_metodos_interpolacion_residuales.md)
   - Formulación matemática de SBA, Regression Kriging (RK), IDW, Kriging Ordinario por Bloques con semivariogramas teóricos, análisis objetivo de Barnes y Cressman, y método de Shepard Modificado.
3. [**03. Tratamiento Fisiográfico del DEM, Batimetría Marina y Protección Insular**](03_tratamiento_fisiografico_dem_batimetria.md)
   - Modelado del gradiente térmico vertical adiabático ($\\Gamma \approx -6.5\ ^\circ\text{C/km}$), clampeo obligatorio de cotas submarinas negativas a $0\text{ msnm}$, protección integral de islas habitadas y continuidad litoral.

### Bloque II: Secuencias de Procesamiento Oficiales por Variable (Workflows)
4. [**04. Secuencia de Procesamiento de Precipitación (CHIRPS) y Máscara Rain-No-Rain**](04_secuencia_precipitacion_chirps_rnor.md)
   - Flujo de 3 pasos en CDT: cálculo de coeficientes de sesgo multiplicativo y distribucional (Bernoulli-Gamma/Weibull), aplicación a grillas diarias NetCDF de CHIRPS, y fusión geoestadística acoplada a la máscara probabilística Lluvia/No-Lluvia (RnoR).
5. [**05. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM**](05_secuencia_temperatura_chirts_dem.md)
   - Flujo de 5 pasos en CDT: cálculo de coeficientes de desescalado orográfico, reducción de escala a 1 km, cálculo de sesgo diurno ($T_{\max}$) y nocturno ($T_{\min}$), aplicación del ajuste y fusión espacial de residuales.

### Bloque III: Diagnóstico Científico, Diseño Experimental y Benchmarks
6. [**06. Diagnóstico Científico de Fase 1 y Resultados del Benchmark de Precipitación (Fase 2)**](06_diagnostico_y_benchmark_precipitacion.md)
   - Evaluación exploratoria preliminar de los 10 experimentos de Fase 1, optimización dirigida en Fase 2 (5 experimentos), ranking consolidado de los 15 experimentos evaluados sobre 29 estaciones ciegas holdout y coronación del modelo ganador `EXP_R15_Shepard_RnoR_Smooth`.
7. [**07. Diagnóstico Científico y Resultados del Benchmark de Temperatura (Tmax y Tmin)**](07_diagnostico_y_benchmark_temperatura.md)
   - Análisis de 24 experimentos térmicos (12 $T_{\max}$ y 12 $T_{\min}$), diagnóstico de la divergencia termodinámica convectiva diurna vs. desacople e inversiones nocturnas, justificación de por qué la Línea Base se rechaza climatológicamente, y selección de ganadores oficiales (`EXP_TX11` y `EXP_TN10`).

### Bloque IV: Arquitectura de Software, Automatización y Despliegue
8. [**08. Arquitectura del Orquestador en Python, CLI y Ensamblado NetCDF (CF-1.8)**](08_arquitectura_lanzadores_python.md)
   - Diseño del puente headless con CDT (`launcher/cdt_bridge.py`), orquestador paralelo multiproceso (`launcher/experiment_runner.py`), particionador de estaciones ciegas (`station_manager.py`), evaluador de métricas cuantitativas y ensamblado en archivos NetCDF 3D conformes al estándar CF-1.8.
9. [**09. Guía de Ejecución desde Terminal (CLI / Headless) y Scripts de Producción**](09_guia_ejecucion_produccion_y_scripts.md)
   - Guía práctica para lanzar simulaciones desde la terminal, banderas de comando CLI (`--suite`, `--config`, `--cores`), ejecución desatendida en segundo plano con `nohup`, reanudación automática ante fallos y plantillas de scripts para cron/programador de tareas.
10. [**10. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity**](10_despliegue_contenedores_docker_apptainer.md)
    - Procedimientos para garantizar reproducibilidad exacta y portabilidad inmutable en servidores locales, clústeres de supercómputo HPC con SLURM y entornos en la nube.

---

## Documentación Maestra Confidencial / Privada

Para acceder al protocolo metodológico integral, la matriz maestra con justificación celda por celda de los 39 experimentos, la auditoría del hardware y los tableros de validación ciega holdout consolidados, consulte el documento maestro en la carpeta privada (fuera del repositorio Git):
- **Documento Markdown Maestro:** `docs-private/reporte_maestro_benchmark_cdt.md`
- **Documento PDF de Nivel de Publicación:** `docs-private/reporte_maestro_benchmark_cdt.pdf` (Generado automáticamente mediante `python launcher/generate_pdf.py`).

---

## Resumen de Modelos Ganadores Oficiales

| Variable Climática | Configuración Ganadora Oficial | Familia Metodológica | Desempeño Cuantitativo (Holdout Ciego) | Justificación Físico-Climatológica |
| :--- | :--- | :--- | :--- | :--- |
| **Precipitación Diaria** | **`EXP_R15_Shepard_RnoR_Smooth`** | SBA Multiescala + Shepard Modificado + RnoR Suave (`CutOff = 2`) | **GSS:** 0.501 \| **KGE:** 0.379 \| **ETS:** 0.329 \| **RMSE:** 12.88 mm | Suprime lloviznas espurias (*drizzle*) en la Canícula sin discontinuidades y preserva gradientes en cañones y laderas escarpadas. |
| **Temperatura Máxima ($T_{\max}$)** | **`EXP_TX11_RK_Barnes_Hybrid`** | RK (DEM + Lat + Lon) + Barnes Gaussiano Continuo | **GSS:** 0.719 \| **KGE:** **0.690** \| **$r$:** 0.743 \| **RMSE:** 2.06 $^\circ\text{C}$ | Forzamiento orográfico real con DEM en zonas sin estaciones y filtrado continuo de brisas marinas y transiciones litorales. |
| **Temperatura Mínima ($T_{\min}$)** | **`EXP_TN10_QM_Empirical_ECDF`** | RK (DEM + Pendiente) + QM Empírico Celda a Celda (NN-3D) | **GSS:** **0.613** \| **KGE:** 0.543 \| **RMSE:** **1.92 $^\circ\text{C}$** \| **MAE:** 1.57 $^\circ\text{C}$ | Menor error absoluto y cuadrático del benchmark; captura inversiones nocturnas y pozas de aire frío (*cold-air pooling*) sin distorsionar colas frías. |

---

## Guía Rápida de Comandos CLI

```bash
# Diagnóstico de dependencias R y paquetes espaciales
python launcher/experiment_runner.py --check-env

# Ejecutar suites completas (Workstation con 18 hilos en paralelo):
python launcher/experiment_runner.py --suite rainfall --cores 18   # 15 Experimentos de Precipitación (~55.3 h)
python launcher/experiment_runner.py --suite tmax     --cores 18   # 12 Experimentos de Tmax (~18.5 h)
python launcher/experiment_runner.py --suite tmin     --cores 18   # 12 Experimentos de Tmin (~18.5 h)

# Ejecutar corrida batch completa de los 39 experimentos:
python launcher/experiment_runner.py --suite all      --cores 18   # 39 Experimentos (~92.4 h continuas)

# Generar el documento PDF maestro de publicación (ReportLab):
python launcher/generate_pdf.py
```
