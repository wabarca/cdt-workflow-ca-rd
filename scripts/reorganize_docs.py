"""Reorganizes markdown files in docs/ into a clean 10-module logical curriculum.
Preserves all existing content, combines overlapping files, updates cross-references,
and produces a fresh, professional docs/README.md.
"""

from pathlib import Path
import re

docs_dir = Path("docs")

# 1. Read existing files
doc_01_cli = (docs_dir / "01_automatizacion_terminal_cli.md").read_text(encoding="utf-8")
doc_02_fund = (docs_dir / "02_gridding_merging_fundamentos.md").read_text(encoding="utf-8")
doc_03_interp = (docs_dir / "03_metodos_interpolacion_residuales.md").read_text(encoding="utf-8")
doc_04_rnor = (docs_dir / "04_merging_precipitacion_rnor.md").read_text(encoding="utf-8")
doc_05_dem = (docs_dir / "05_merging_temperatura_dem.md").read_text(encoding="utf-8")
doc_06_prod = (docs_dir / "06_ejemplos_scripts_produccion.md").read_text(encoding="utf-8")
doc_07_chirts = (docs_dir / "07_flujo_completo_temperatura_chirts.md").read_text(encoding="utf-8")
doc_08_chirps = (docs_dir / "08_flujo_completo_precipitacion_chirps.md").read_text(encoding="utf-8")
doc_09_arch = (docs_dir / "09_arquitectura_lanzadores_python_y_dependencias.md").read_text(encoding="utf-8")
doc_11_dock = (docs_dir / "11_guia_despliegue_contenedores_docker_apptainer.md").read_text(encoding="utf-8")
doc_12_diag_r = (docs_dir / "12_diagnostico_fase1_y_diseno_fase2_precipitacion.md").read_text(encoding="utf-8")
doc_13_dem_bat = (docs_dir / "13_influencia_dem_batimetria_desescalado_temperatura.md").read_text(encoding="utf-8")
doc_14_diag_t = (docs_dir / "14_diagnostico_fase1_y_diseno_fase2_temperatura.md").read_text(encoding="utf-8")

# --- Module 01: Fundamentos de Gridding y Merging en CDT ---
# From doc_02_fund
mod_01 = re.sub(r"^# 02\..*?\n", "# 01. Fundamentos del Proceso de Fusión (Merging) y Gridding en CDT\n", doc_02_fund, flags=re.MULTILINE)

# --- Module 02: Métodos de Interpolación de Residuales ---
# From doc_03_interp
mod_02 = re.sub(r"^# 03\..*?\n", "# 02. Métodos Geoestadísticos y Parámetros de Interpolación de Residuales\n", doc_03_interp, flags=re.MULTILINE)

# --- Module 03: Tratamiento Fisiográfico, DEM y Batimetría Costera ---
# From doc_13_dem_bat
mod_03 = re.sub(r"^# 13\..*?\n", "# 03. Tratamiento Fisiográfico del DEM, Batimetría Marina y Protección Insular\n", doc_13_dem_bat, flags=re.MULTILINE)

# --- Module 04: Secuencia de Fusión de Precipitación (CHIRPS) y Máscara RnoR ---
# Combine doc_08_chirps (full workflow) + doc_04_rnor (mathematical details of RnoR)
mod_04_title = "# 04. Secuencia de Procesamiento de Precipitación (CHIRPS) y Máscara Rain-No-Rain\n\n"
# Strip titles
doc_08_body = re.sub(r"^# 08\..*?\n", "", doc_08_chirps, flags=re.MULTILINE)
doc_04_body = re.sub(r"^# 04\..*?\n", "", doc_04_rnor, flags=re.MULTILINE)

mod_04 = mod_04_title + doc_08_body + "\n\n---\n\n# Anexo Metodológico Detallado: Algoritmo y Opciones de la Máscara Rain-No-Rain (RnoR)\n\n" + doc_04_body

# --- Module 05: Secuencia de Fusión y Desescalado de Temperatura (CHIRTS) ---
# Combine doc_07_chirts (5-step workflow) + doc_05_dem (GLM modeling with DEM, Slope, Aspect)
mod_05_title = "# 05. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM\n\n"
doc_07_body = re.sub(r"^# 07\..*?\n", "", doc_07_chirts, flags=re.MULTILINE)
doc_05_body = re.sub(r"^# 05\..*?\n", "", doc_05_dem, flags=re.MULTILINE)

mod_05 = mod_05_title + doc_07_body + "\n\n---\n\n# Anexo Metodológico Detallado: Modelado de Covariables Topográficas (DEM, Pendiente, Aspecto)\n\n" + doc_05_body

# --- Module 06: Diagnóstico Científico y Benchmark de Precipitación ---
# From doc_12_diag_r
mod_06 = re.sub(r"^# 12\..*?\n", "# 06. Diagnóstico Científico de Fase 1 y Resultados del Benchmark de Precipitación (Fase 2)\n", doc_12_diag_r, flags=re.MULTILINE)

# --- Module 07: Diagnóstico Científico y Benchmark de Temperatura ---
# From doc_14_diag_t
mod_07 = re.sub(r"^# 14\..*?\n", "# 07. Diagnóstico Científico y Resultados del Benchmark de Temperatura (Tmax y Tmin)\n", doc_14_diag_t, flags=re.MULTILINE)

# --- Module 08: Arquitectura de Lanzadores en Python ---
# From doc_09_arch
mod_08 = re.sub(r"^# 09\..*?\n", "# 08. Arquitectura del Orquestador en Python, CLI y Ensamblado NetCDF (CF-1.8)\n", doc_09_arch, flags=re.MULTILINE)

# --- Module 09: Guía de Ejecución en Terminal y Scripts de Producción ---
# Combine doc_01_cli (Headless execution & functions) + doc_06_prod (Production scripts & schedulers)
mod_09_title = "# 09. Guía de Ejecución desde Terminal (CLI / Headless) y Scripts de Producción\n\n"
doc_01_body = re.sub(r"^# 01\..*?\n", "", doc_01_cli, flags=re.MULTILINE)
doc_06_body = re.sub(r"^# 06\..*?\n", "", doc_06_prod, flags=re.MULTILINE)

mod_09 = mod_09_title + doc_01_body + "\n\n---\n\n# Anexo: Plantillas de Automatización y Tareas Programadas\n\n" + doc_06_body

# --- Module 10: Despliegue en Contenedores ---
# From doc_11_dock
mod_10 = re.sub(r"^# 11\..*?\n", "# 10. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity\n", doc_11_dock, flags=re.MULTILINE)

# Target new files mapping
new_files = {
    "01_fundamentos_gridding_merging_cdt.md": mod_01,
    "02_metodos_interpolacion_residuales.md": mod_02,
    "03_tratamiento_fisiografico_dem_batimetria.md": mod_03,
    "04_secuencia_precipitacion_chirps_rnor.md": mod_04,
    "05_secuencia_temperatura_chirts_dem.md": mod_05,
    "06_diagnostico_y_benchmark_precipitacion.md": mod_06,
    "07_diagnostico_y_benchmark_temperatura.md": mod_07,
    "08_arquitectura_lanzadores_python.md": mod_08,
    "09_guia_ejecucion_produccion_y_scripts.md": mod_09,
    "10_despliegue_contenedores_docker_apptainer.md": mod_10,
}

# Fix cross references in all new files
link_replacements = [
    ("01_automatizacion_terminal_cli.md", "09_guia_ejecucion_produccion_y_scripts.md"),
    ("02_gridding_merging_fundamentos.md", "01_fundamentos_gridding_merging_cdt.md"),
    ("03_metodos_interpolacion_residuales.md", "02_metodos_interpolacion_residuales.md"),
    ("04_merging_precipitacion_rnor.md", "04_secuencia_precipitacion_chirps_rnor.md"),
    ("05_merging_temperatura_dem.md", "05_secuencia_temperatura_chirts_dem.md"),
    ("06_ejemplos_scripts_produccion.md", "09_guia_ejecucion_produccion_y_scripts.md"),
    ("07_flujo_completo_temperatura_chirts.md", "05_secuencia_temperatura_chirts_dem.md"),
    ("08_flujo_completo_precipitacion_chirps.md", "04_secuencia_precipitacion_chirps_rnor.md"),
    ("09_arquitectura_lanzadores_python_y_dependencias.md", "08_arquitectura_lanzadores_python.md"),
    ("11_guia_despliegue_contenedores_docker_apptainer.md", "10_despliegue_contenedores_docker_apptainer.md"),
    ("12_diagnostico_fase1_y_diseno_fase2_precipitacion.md", "06_diagnostico_y_benchmark_precipitacion.md"),
    ("13_influencia_dem_batimetria_desescalado_temperatura.md", "03_tratamiento_fisiografico_dem_batimetria.md"),
    ("14_diagnostico_fase1_y_diseno_fase2_temperatura.md", "07_diagnostico_y_benchmark_temperatura.md"),
    ("10_matriz_maestra_experimentos_y_guia_metodologica.md", "../docs-private/reporte_maestro_benchmark_cdt.md"),
]

# Apply link replacements
for filename, text in new_files.items():
    updated = text
    for old_ref, new_ref in link_replacements:
        updated = updated.replace(old_ref, new_ref)
    new_files[filename] = updated

# Clean old markdown files in docs/
old_md_files = [
    "01_automatizacion_terminal_cli.md",
    "02_gridding_merging_fundamentos.md",
    "03_metodos_interpolacion_residuales.md",
    "04_merging_precipitacion_rnor.md",
    "05_merging_temperatura_dem.md",
    "06_ejemplos_scripts_produccion.md",
    "07_flujo_completo_temperatura_chirts.md",
    "08_flujo_completo_precipitacion_chirps.md",
    "09_arquitectura_lanzadores_python_y_dependencias.md",
    "11_guia_despliegue_contenedores_docker_apptainer.md",
    "12_diagnostico_fase1_y_diseno_fase2_precipitacion.md",
    "13_influencia_dem_batimetria_desescalado_temperatura.md",
    "14_diagnostico_fase1_y_diseno_fase2_temperatura.md",
]

for old_f in old_md_files:
    p = docs_dir / old_f
    if p.exists():
        p.unlink()
        print(f"Removed old file: {old_f}")

# Write new 10 modules
for filename, text in new_files.items():
    target = docs_dir / filename
    target.write_text(text, encoding="utf-8")
    print(f"Written new module: {filename} ({len(text)} chars)")

# Write updated README.md
readme_content = """# Documentación Técnica y Metodológica Oficial: Climate Data Tools (CDT v8.0)

> **Proyecto:** “Escenarios de Cambio Climático de Alta Resolución en Centroamérica y el Caribe”  
> **Grupo Oficial:** Grupo de Trabajo Regional de Escenarios de Cambio Climático de Centroamérica y el Caribe  
> **Horizonte Climatológico:** Serie histórica estándar **1991–2020** (10,958 días continuos)  
> **Bases de Reanálisis:** CHIRPS v2.0 ($0.05^\\circ$), CHIRTS-daily ($0.05^\\circ$), DEM SRTM (90 m / 1 km)

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
   - Modelado del gradiente térmico vertical adiabático ($\\\\Gamma \\approx -6.5\\ ^\\circ\\text{C/km}$), clampeo obligatorio de cotas submarinas negativas a $0\\text{ msnm}$, protección integral de islas habitadas y continuidad litoral.

### Bloque II: Secuencias de Procesamiento Oficiales por Variable (Workflows)
4. [**04. Secuencia de Procesamiento de Precipitación (CHIRPS) y Máscara Rain-No-Rain**](04_secuencia_precipitacion_chirps_rnor.md)
   - Flujo de 3 pasos en CDT: cálculo de coeficientes de sesgo multiplicativo y distribucional (Bernoulli-Gamma/Weibull), aplicación a grillas diarias NetCDF de CHIRPS, y fusión geoestadística acoplada a la máscara probabilística Lluvia/No-Lluvia (RnoR).
5. [**05. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM**](05_secuencia_temperatura_chirts_dem.md)
   - Flujo de 5 pasos en CDT: cálculo de coeficientes de desescalado orográfico, reducción de escala a 1 km, cálculo de sesgo diurno ($T_{\\max}$) y nocturno ($T_{\\min}$), aplicación del ajuste y fusión espacial de residuales.

### Bloque III: Diagnóstico Científico, Diseño Experimental y Benchmarks
6. [**06. Diagnóstico Científico de Fase 1 y Resultados del Benchmark de Precipitación (Fase 2)**](06_diagnostico_y_benchmark_precipitacion.md)
   - Evaluación exploratoria preliminar de los 10 experimentos de Fase 1, optimización dirigida en Fase 2 (5 experimentos), ranking consolidado de los 15 experimentos evaluados sobre 29 estaciones ciegas holdout y coronación del modelo ganador `EXP_R15_Shepard_RnoR_Smooth`.
7. [**07. Diagnóstico Científico y Resultados del Benchmark de Temperatura (Tmax y Tmin)**](07_diagnostico_y_benchmark_temperatura.md)
   - Análisis de 24 experimentos térmicos (12 $T_{\\max}$ y 12 $T_{\\min}$), diagnóstico de la divergencia termodinámica convectiva diurna vs. desacople e inversiones nocturnas, justificación de por qué la Línea Base se rechaza climatológicamente, y selección de ganadores oficiales (`EXP_TX11` y `EXP_TN10`).

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
| **Temperatura Máxima ($T_{\\max}$)** | **`EXP_TX11_RK_Barnes_Hybrid`** | RK (DEM + Lat + Lon) + Barnes Gaussiano Continuo | **GSS:** 0.719 \| **KGE:** **0.690** \| **$r$:** 0.743 \| **RMSE:** 2.06 $^\\circ\\text{C}$ | Forzamiento orográfico real con DEM en zonas sin estaciones y filtrado continuo de brisas marinas y transiciones litorales. |
| **Temperatura Mínima ($T_{\\min}$)** | **`EXP_TN10_QM_Empirical_ECDF`** | RK (DEM + Pendiente) + QM Empírico Celda a Celda (NN-3D) | **GSS:** **0.613** \| **KGE:** 0.543 \| **RMSE:** **1.92 $^\\circ\\text{C}$** \| **MAE:** 1.57 $^\\circ\\text{C}$ | Menor error absoluto y cuadrático del benchmark; captura inversiones nocturnas y pozas de aire frío (*cold-air pooling*) sin distorsionar colas frías. |

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
"""

(docs_dir / "README.md").write_text(readme_content, encoding="utf-8")
print("Written docs/README.md successfully.")
