"""Script to reorganize docs into 4 logical blocks:
Bloque I: Guía de Ejecución, Automatización y Despliegue (01, 02, 03)
Bloque II: Fundamentos Teóricos y Tratamiento Fisiográfico (04, 05, 06)
Bloque III: Secuencias de Procesamiento Oficiales por Variable (Workflows) (07, 08)
Bloque IV: Diagnóstico Científico, Benchmarks y Resultados Consolidados (09, 10)
README.md index.
"""

import os
import re

docs_dir = "docs"

def read_doc(fname):
    with open(os.path.join(docs_dir, fname), "r", encoding="utf-8") as f:
        return f.read()

# Read all old docs into memory
docs = {
    "01": read_doc("01_fundamentos_gridding_merging_cdt.md"),
    "02": read_doc("02_metodos_interpolacion_residuales.md"),
    "03": read_doc("03_tratamiento_fisiografico_dem_batimetria.md"),
    "04": read_doc("04_secuencia_precipitacion_chirps_rnor.md"),
    "05": read_doc("05_secuencia_temperatura_chirts_dem.md"),
    "06": read_doc("06_diagnostico_y_benchmark_precipitacion.md"),
    "07": read_doc("07_diagnostico_y_benchmark_temperatura.md"),
    "08": read_doc("08_arquitectura_lanzadores_python.md"),
    "09": read_doc("09_guia_ejecucion_produccion_y_scripts.md"),
    "10": read_doc("10_despliegue_contenedores_docker_apptainer.md"),
}

# -------------------------------------------------------------------------
# Helper functions
# -------------------------------------------------------------------------
def clean_math(text):
    # Ensure block equations $$ have empty lines before and after
    text = re.sub(r'(?<!\$)\$\$(?!\$)(.*?)\$\$(?!\$)', lambda m: '\n\n$$\n' + m.group(1).strip() + '\n$$\n\n' if '\n' not in m.group(1) else m.group(0), text)
    
    # Fix Cressman cases if single backslash or missing \\
    text = text.replace(
        r"W_i = \begin{cases}" + "\n" + r"\dfrac{R_c^2 - d_i^2}{R_c^2 + d_i^2}, & d_i < R_c \\" + "\n" + r"0, & d_i \ge R_c" + "\n" + r"\end{cases}",
        r"W_{ij} = \begin{cases}" + "\n" + r"\dfrac{R^2 - d_{ij}^2}{R^2 + d_{ij}^2} & \text{si } d_{ij} < R \\" + "\n" + r"0 & \text{si } d_{ij} \geq R" + "\n" + r"\end{cases}"
    )
    
    # Also handle if already had W_{ij}
    text = re.sub(
        r'\\begin\{cases\}.*?\\end\{cases\}',
        lambda m: m.group(0).replace(r'\ 0 & \text{si } d_{ij} \ge R', r'\\ 0 & \text{si } d_{ij} \geq R')
                            .replace(r'\ 0 & \text{si } d_{ij} \ge R_c', r'\\ 0 & \text{si } d_{ij} \geq R_c')
                            .replace(r'0, & d_i \ge R_c', r'0, & d_i \geq R_c'),
        text,
        flags=re.DOTALL
    )
    
    # Fix malformed subscripts in equations
    text = text.replace(r'\text{DEM}{\text{fine}}(s{\text{fine}})', r'\text{DEM}_{\text{fine}}(s_{\text{fine}})')
    text = text.replace(r'\hat{R}{\text{fine}}(s{\text{fine}})', r'\hat{R}_{\text{fine}}(s_{\text{fine}})')
    text = text.replace(r'f_m(\text{DEM}{\text{fino}})', r'f_m(\text{DEM}_{\text{fino}})')
    text = text.replace(r'\hat{R}{\text{fino}}(s_{\text{fino}})', r'\hat{R}_{\text{fino}}(s_{\text{fino}})')
    text = text.replace(r'\hat{T}{\text{corrected}}(s) = F{\text{stn}}^{-1}\left( F_{\text{proxy}}(T_{\text{downscaled}}(s)) \right)',
                        r'\hat{T}_{\text{corrected}}(s) = F_{\text{stn}}^{-1}\left( F_{\text{proxy}}(T_{\text{downscaled}}(s)) \right)')
    text = text.replace(r'F{\text{stn}}^{-1}', r'F_{\text{stn}}^{-1}')
    text = text.replace(r'\hat{T}{\text{corrected}}', r'\hat{T}_{\text{corrected}}')
    
    # Fix non-ASCII characters inside math mode
    text = text.replace(r'F_{\text{estación}}', r'F_{\text{stn}}')
    text = text.replace(r'F_{\text{estacin}}', r'F_{\text{stn}}')
    text = text.replace(r'\text{Límites}', r'\text{Limites}')
    text = text.replace(r'\text{Lmites}', r'\text{Limites}')
    text = text.replace(r'\text{elevación}', r'\text{elevacion}')
    text = text.replace(r'\text{elevacin}', r'\text{elevacion}')
    
    # Fix $(4, 12)$ in tables to plain text
    text = text.replace(r'$(4, 12)$, $(6, 16)$, $(8, 24)$', '(4, 12), (6, 16), (8, 24)')
    text = text.replace(r'$(4, 12)$, $(8, 16)$, $(10, 30)$', '(4, 12), (8, 16), (10, 30)')
    
    # Clean multiple consecutive blank lines before $$
    text = re.sub(r'\n{3,}\$\$', '\n\n$$', text)
    text = re.sub(r'\$\$\n{3,}', '$$\n\n', text)
    
    return text

def natural_tone(text):
    text = text.replace("para la publicación científica", "para la evaluación y validación técnica")
    text = text.replace("para publicación científica", "para la validación del modelo")
    text = text.replace("Publicación Científica", "Evaluación Cuantitativa del Desempeño")
    text = text.replace("publicación científica", "documentación técnica y operativa")
    text = text.replace("publicaciones científicas indexadas", "publicaciones científicas de referencia")
    text = text.replace("Documentación Maestra Confidencial / Privada", "Documentación Técnica Complementaria")
    return text

def update_links(text):
    # Mapping old to new filenames
    mapping = [
        ("01_fundamentos_gridding_merging_cdt.md", "04_fundamentos_gridding_merging_cdt.md"),
        ("02_metodos_interpolacion_residuales.md", "05_metodos_interpolacion_residuales.md"),
        ("03_tratamiento_fisiografico_dem_batimetria.md", "06_tratamiento_fisiografico_dem_batimetria.md"),
        ("04_secuencia_precipitacion_chirps_rnor.md", "07_secuencia_precipitacion_chirps_rnor.md"),
        ("05_secuencia_temperatura_chirts_dem.md", "08_secuencia_temperatura_chirts_dem.md"),
        ("06_diagnostico_y_benchmark_precipitacion.md", "09_diagnostico_y_benchmark_precipitacion.md"),
        ("07_diagnostico_y_benchmark_temperatura.md", "10_diagnostico_y_benchmark_temperatura.md"),
        ("08_arquitectura_lanzadores_python.md", "02_arquitectura_lanzadores_python.md"),
        ("09_guia_ejecucion_produccion_y_scripts.md", "01_guia_ejecucion_produccion_y_scripts.md"),
        ("10_despliegue_contenedores_docker_apptainer.md", "03_despliegue_contenedores_docker_apptainer.md"),
    ]
    for old_n, new_n in mapping:
        text = text.replace(old_n, new_n)
    return text

# =============================================================================
# BUILD NEW 01: Guía de Ejecución y Scripts de Producción (with parallel processing)
# =============================================================================
new_01 = docs["09"]

# Replace heading and inject Parallel Processing section right at the top
intro_parallel = """# 01. Guía de Ejecución desde Terminal (CLI / Headless) y Scripts de Producción

## 1. Ejecución Rápida y Procesamiento en Paralelo Habilitado

Para entornos de producción y servidores de alto rendimiento, el flujo de ejecución no interactivo se gestiona mediante el orquestador en Python (`launcher/experiment_runner.py`), el cual cuenta con **procesamiento en paralelo habilitado** a nivel de procesos e hilos concurrentes.

### Capacidad Multihilo Calibrada (--cores)
El orquestador divide el periodo histórico de 30 años (**1991–2020**, 10,958 días continuos) en lotes diarios distribuidos entre los hilos del procesador. Por defecto, en la estación de trabajo calibrada se utilizan **18 hilos de procesamiento paralelo** (`--cores 18`), optimizando el rendimiento sin sobrecargar la memoria RAM (consumo menor al 15%, ~4.6 GB máx.).

```bash
# 1. Comprobación del entorno y paquetes R espaciales requeridos:
python launcher/experiment_runner.py --check-env

# 2. Ejecutar suites completas con procesamiento en paralelo (18 cores):
python launcher/experiment_runner.py --suite rainfall --cores 18   # 15 Experimentos de Precipitación (~55.3 h)
python launcher/experiment_runner.py --suite tmax     --cores 18   # 12 Experimentos de Tmax (~18.5 h)
python launcher/experiment_runner.py --suite tmin     --cores 18   # 12 Experimentos de Tmin (~18.5 h)

# 3. Ejecutar la batería completa de los 39 experimentos:
python launcher/experiment_runner.py --suite all      --cores 18   # 39 Experimentos en lote continuo (~92.4 h)

# 4. Ejecutar un experimento individual de producción:
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R15_Shepard_RnoR_Smooth.yaml --cores 18

# 5. Generar el reporte consolidado de resultados en PDF:
python launcher/generate_pdf.py
```

---

"""

# Replace the original intro of 09 with intro_parallel
old_09_intro_match = re.search(r'# 09\. Guía de Ejecución.*?\n\n## 1\. Introducción', new_01, re.DOTALL)
if old_09_intro_match:
    new_01 = new_01[:old_09_intro_match.start()] + intro_parallel + "## 2. Modo No Interactivo en CDT y Funciones Exportadas" + new_01[old_09_intro_match.end():]
else:
    new_01 = intro_parallel + new_01

# Renumber sections in new_01
new_01 = new_01.replace("## 2. Funciones de Línea de Comandos Exportadas", "## 2. Funciones de Línea de Comandos Exportadas en CDT")
new_01 = new_01.replace("## 3. Configuración de Opciones Globales", "## 3. Configuración de Opciones Globales (`merging.options`)")
new_01 = new_01.replace("## 4. Estructura de Parámetros de Entrada", "## 4. Estructura de Parámetros de Entrada")
new_01 = new_01.replace("## 5. Scripts de Producción", "## 5. Scripts de Producción")

# Update experiment numbers in the python launcher section of 01
new_01 = new_01.replace("# 10 Experimentos de Lluvia", "# 15 Experimentos de Lluvia (Fase 1 + Fase 2)")
new_01 = new_01.replace("# 8 Experimentos de Tmax", "# 12 Experimentos de Tmax (Fase 1 + Fase 2)")
new_01 = new_01.replace("# 8 Experimentos de Tmin", "# 12 Experimentos de Tmin (Fase 1 + Fase 2)")
new_01 = new_01.replace("# 26 Experimentos, 1991–2020", "# 39 Experimentos completos, 1991–2020")
new_01 = new_01.replace("pipeline_merging_", "secuencia_merging_")

new_01 = clean_math(natural_tone(update_links(new_01)))


# =============================================================================
# BUILD NEW 02: Arquitectura del Orquestador (from old 08)
# =============================================================================
new_02 = docs["08"]
new_02 = re.sub(r'# 08\. Arquitectura.*?\n', '# 02. Arquitectura del Orquestador en Python, CLI y Ensamblado NetCDF (CF-1.8)\n', new_02)
new_02 = clean_math(natural_tone(update_links(new_02)))


# =============================================================================
# BUILD NEW 03: Despliegue en Contenedores (from old 10)
# =============================================================================
new_03 = docs["10"]
new_03 = re.sub(r'# 10\. Guía de Despliegue.*?\n', '# 03. Guía de Despliegue en Contenedores: Docker, Docker Compose y Apptainer / Singularity\n', new_03)
# Fix table with $(pwd)
new_03 = new_03.replace('(`--bind $(pwd):/workspace`)', '(`--bind \\$(pwd):/workspace`)')
new_03 = clean_math(natural_tone(update_links(new_03)))


# =============================================================================
# BUILD NEW 04: Fundamentos de Fusión (from old 01)
# =============================================================================
new_04 = docs["01"]
new_04 = re.sub(r'# 01\. Fundamentos.*?\n', '# 04. Fundamentos del Proceso de Fusión (Merging) y Gridding en CDT\n', new_04)
new_04 = clean_math(natural_tone(update_links(new_04)))


# =============================================================================
# BUILD NEW 05: Métodos Geoestadísticos e Interpolación (from old 02)
# =============================================================================
new_05 = docs["02"]
new_05 = re.sub(r'# 02\. Métodos Geoestadísticos.*?\n', '# 05. Métodos Geoestadísticos y Parámetros de Interpolación de Residuales\n', new_05)
new_05 = clean_math(natural_tone(update_links(new_05)))


# =============================================================================
# BUILD NEW 06: Tratamiento Fisiográfico DEM (from old 03)
# =============================================================================
new_06 = docs["03"]
new_06 = re.sub(r'# 03\. Tratamiento Fisiográfico.*?\n', '# 06. Tratamiento Fisiográfico del DEM, Batimetría Marina y Protección Insular\n', new_06)
new_06 = clean_math(natural_tone(update_links(new_06)))


# =============================================================================
# BUILD NEW 07: Secuencia Precipitación (from old 04) - WITH BOTH PHASE 1 & PHASE 2
# =============================================================================
new_07 = docs["04"]
new_07 = re.sub(r'# 04\. Secuencia de Procesamiento de Precipitación.*?\n', '# 07. Secuencia de Procesamiento de Precipitación (CHIRPS) y Máscara Rain-No-Rain\n', new_07)
new_07 = new_07.replace("## 4. Métricas de Evaluación para la Publicación Científica", "## 4. Métricas de Evaluación Cuantitativa del Desempeño")

# Update Section 5 in new_07 to detail Phase 1 AND Phase 2
sec5_rain = """## 5. Matriz Completa de Experimentos Pluviales: Fase 1 y Fase 2

La batería completa de **15 experimentos de precipitación** se organiza en dos fases analíticas ejecutadas sobre la serie histórica 1991–2020:

### 5.1 Fase 1: Evaluación Exploratoria Preliminar (10 Experimentos)
Aísla el efecto del método de corrección de sesgo, la máscara RnoR y los interpoladores geoestadísticos estándar:

| ID Exp. | Método Bias (Paso 1) | Apply Bias (Paso 2) | Merging (Paso 3) | Hipótesis y Configuración |
| :---: | :--- | :--- | :--- | :--- |
| **`EXP-R01`** | `mbvar` (\\pm 5 d) + IDW (1.5°) | Proporcional | SBA 1 pasada (1.0°) + IDW (1.5°) | **Línea Base Control:** Sin filtro RnoR; cuantifica la sobreestimación base de lloviznas (*drizzle*). |
| **`EXP-R02`** | `mbvar` (\\pm 5 d) + IDW (1.5°) | Proporcional | SBA 3 pasadas + IDW + **RnoR Logit (CutOff=3)** | **Impacto RnoR Duro:** Evalúa corte rígido a 0.5 mm en lloviznas espurias. |
| **`EXP-R03`** | `qmdist` Bernoulli-Gamma + OKR | Mapeo cuantil | SBA 3 pasadas + OKR por bloques | **Distribución Gamma Estándar:** Ajuste paramétrico teórico estándar en meteorología tropical. |
| **`EXP-R04`** | `qmdist` Bernoulli-Weibull + OKR | Mapeo cuantil | SBA 3 pasadas + OKR por bloques | **Extremos Ciclónicos:** Modela colas pesadas asociadas a huracanes y ondas del este. |
| **`EXP-R05`** | `qmdist` Bernoulli-Weibull + OKR | Mapeo cuantil | **RK** (DEM + Slope + Coords) | **Modelo Orográfico Completo:** Covariables de relieve en la tendencia pluvial. |
| **`EXP-R06`** | `mbvar` (\\pm 5 d) + NN-3D | Proporcional | **Barnes (BSc)** 3 pasadas gaussianas | **Amortiguamiento Costero:** Filtrado continuo para llanuras litorales y brisas marinas. |
| **`EXP-R07`** | `mbmon` (mensual) + IDW | Proporcional | **Cressman (CSc)** 4 pasadas decrecientes | **Configuración Guía Oficial CDT:** Radios decrecientes (1.0° a 0.25°) para captar mesoescala. |
| **`EXP-R08`** | `mbvar` (\\pm 5 d) + IDW | Proporcional | **Shepard Modificado** (radio 1.5°) | **Relieve Complejo:** Ponderación local con derivadas direccionales de Taylor. |
| **`EXP-R09`** | `mbvar` (\\pm 5 d) + IDW | Proporcional | **Spheremap** (Gran Círculo) | **Geometría Esférica:** Distancias geodésicas reales para evitar distorsiones longitudinales. |
| **`EXP-R10`** | `qmdist` Bernoulli-Gamma + OKR | Mapeo cuantil | **RK Máxima Complejidad** (DEM+Slope+Aspect+Coords) | **Acoplamiento Topográfico Total:** Insolación y laderas barlovento/sotavento. |

---

### 5.2 Fase 2: Optimización Dirigida de Precipitación (5 Experimentos)
Diseñada a partir de los hallazgos de la Fase 1, donde Shepard Modificado y Spheremap demostraron ser superiores al Kriging:

| ID Exp. | Método Bias (Paso 1) | Apply Bias (Paso 2) | Merging (Paso 3) | Hipótesis y Configuración de Optimización |
| :---: | :--- | :--- | :--- | :--- |
| **`EXP-R11`** | `mbvar` (\\pm 5 d) + **Mediana** + Grilla Gruesa (1.0°) | Proporcional | Shepard Modificado (radio 1.5°) + Grilla Gruesa | **Estabilidad Marina y Extremos:** Función mediana para neutralizar tormentas aisladas y amortiguamiento costero. |
| **`EXP-R12`** | `mbvar` (\\pm 5 d) + IDW (1.0°) | Proporcional | Shepard Confinado Local (radio 0.9°, 3 pasadas) | **Confinamiento Local:** Radios estrechos para evitar propagación de lluvia a través de divisorias continentales. |
| **`EXP-R13`** | **QM Empírico (`qmecdf`)** + Shepard | Mapeo cuantil empírico | Shepard Modificado (radio 1.5°) | **No Paramétrico:** Calibra cuantiles directamente sobre la curva observada sin distribución teórica prefijada. |
| **`EXP-R14`** | `mbvar` (\\pm 5 d) + **Mediana** + Spheremap | Proporcional | Spheremap Gran Círculo (radio 1.5°) | **Esferoide con Mediana:** Combina distancias de gran círculo en el Caribe con estimación robusta de sesgo. |
| **`EXP-R15`**<br>**(GANADOR)** | `mbvar` (\\pm 5 d) + IDW (1.2°) | Proporcional | Shepard (radio 1.2°) + **RnoR Suave (`CutOff=2`, smooth=TRUE)** | **MODELO GANADOR OFICIAL:** Suprime lloviznas espurias (*drizzle*) sin cortes artificiales. Máximo GSS (0.501) y KGE (0.379). |

### Ejecución de Suites desde Terminal:
```bash
# Ejecutar la suite completa de 15 experimentos de precipitación con 18 hilos:
python launcher/experiment_runner.py --suite rainfall --cores 18
```
"""

# Replace Section 5 in new_07
sec5_rain_start = new_07.find("## 5. Matriz de Experimentos Pluviales")
if sec5_rain_start != -1:
    new_07 = new_07[:sec5_rain_start] + sec5_rain
else:
    new_07 = new_07 + "\n\n" + sec5_rain

new_07 = clean_math(natural_tone(update_links(new_07)))


# =============================================================================
# BUILD NEW 08: Secuencia Temperatura (from old 05) - WITH BOTH PHASE 1 & PHASE 2
# =============================================================================
new_08 = docs["05"]
new_08 = re.sub(r'# 05\. Secuencia de Procesamiento de Temperatura.*?\n', '# 08. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM\n', new_08)

# Update Section 5 in new_08 to detail Phase 1 AND Phase 2 for Tmax and Tmin
sec5_temp = """## 5. Matriz Completa de Experimentos Térmicos: Fase 1 y Fase 2 ($T_{\\max}$ y $T_{\\min}$)

La batería comprende **24 experimentos térmicos** (12 para $T_{\\max}$ y 12 para $T_{\\min}$) estructurados según las 5 etapas oficiales de CDT:

### 5.1 Suite B: Temperatura Máxima Diurna ($T_{\\max}$: 12 Experimentos)

| ID Exp. | Fase | Desescalado Topográfico (Pasos 1-2) | Compute / Apply Bias (Pasos 3-4) | Merging de Residuales (Paso 5) | Hipótesis Física Diurna |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **`EXP-TX01`** | F1 | Lineal plano sin DEM (0.05°) | `mbvar` (\\pm 5 d) + IDW (3.5°) | SBA monocapa (1 pasada a 1.0°) | **Línea Base Control:** Ignora el relieve; sesgo artificial cálido en cumbres. |
| **`EXP-TX02`** | F1 | Regresión estación–DEM SRTM | `qmdist` (Normal) + IDW | **RK** (DEM) + OKR por bloques | **Gradiente Adiabático:** Tasa vertical estándar (\\approx -6.5 °C/km). |
| **`EXP-TX03`** | F1 | Regresión DEM + Pendiente | `qmdist` (Skew-Normal) + OKR | **RK** (DEM + Pendiente + Coords) | **Asimetría por Laderas:** Captura pendientes térmicas en cordilleras. |
| **`EXP-TX04`** | F1 | Desescalado orográfico 3D | `mbvar` (\\pm 5 d) + **NN-3D (\\Delta z)** | **RK** (DEM + Pendiente + Aspect) | **Insolación por Orientación:** Sol matutino al este vs vespertino al oeste. |
| **`EXP-TX05`** | F1 | Regresión altimétrica DEM | `qmdist` (Gumbel) + OKR | **RK** (DEM + Coords) | **Olas de Calor:** Ajuste de colas extremas en valles áridos y depresiones. |
| **`EXP-TX06`** | F1 | Regresión regional DEM | `mbvar` (\\pm 5 d) + IDW | **Barnes (BSc)** 3 pasadas gaussianas | **Brisas y Llanuras Costeras:** Suavizado continuo sin saltos espaciales. |
| **`EXP-TX07`** | F1 | Regresión altimétrica DEM | `mbmon` (mensual) + IDW | **Cressman (CSc)** 4 pasadas | **Guía Oficial CDT:** Radios decrecientes contra contaminación de valles cálidos. |
| **`EXP-TX08`** | F1 | Multivariado DEM+Slope+Aspect | `qmdist` (Skew-Normal) + OKR | **RK Total** (DEM+Slope+Aspect+Coords) | **Máxima Complejidad Diurna:** Acoplamiento total de relieve e insolación. |
| **`EXP-TX09`** | F2 | Bilineal con DEM SRTM | `mbvar` (\\pm 5 d) + **NN-3D (\\Delta z)** | **SBA** (1.0°, 0.67°, 0.33°) + Shepard | **Shepard Térmico NN-3D:** Derivadas direccionales locales en residuales. |
| **`EXP-TX10`** | F2 | Bilineal con DEM SRTM | **QM Empírico (`qmecdf`)** + NN-3D | **RK** (DEM + Pendiente) + IDW | **QM Empírico Celda a Celda:** Modela olas de calor directamente sobre la curva observada. |
| **`EXP-TX11`**<br>**(GANADOR)** | F2 | Bilineal con DEM SRTM | `mbvar` (\\pm 5 d) + IDW (3.5°) | **RK (DEM + Lat + Lon)** + **Barnes Residuos (2.0°)** | **MODELO GANADOR TMAX:** Descompone el campo diurno en tendencia orográfica real y Barnes continuo. Máx KGE (0.690). |
| **`EXP-TX12`** | F2 | Bilineal con DEM SRTM | `mbvar` (\\pm 5 d) + NN-3D | **SBA Multiescala Local** (1.0°, 0.50°, 0.25°) | **SBA Local con NN-3D:** Confinamiento a 0.25° con control vertical de cota. |

---

### 5.2 Suite C: Temperatura Mínima Nocturna ($T_{\\min}$: 12 Experimentos)

| ID Exp. | Fase | Desescalado Topográfico (Pasos 1-2) | Compute / Apply Bias (Pasos 3-4) | Merging de Residuales (Paso 5) | Hipótesis Física Nocturna |
| :---: | :---: | :--- | :--- | :--- | :--- |
| **`EXP-TN01`** | F1 | Lineal plano sin DEM (0.05°) | `mbvar` (\\pm 5 d) + IDW (3.5°) | SBA monocapa (1 pasada a 1.0°) | **Línea Base Control:** Ignora el enfriamiento nocturno y drenaje catabático. |
| **`EXP-TN02`** | F1 | Regresión estación–DEM SRTM | `qmdist` (Normal) + IDW | **RK** (DEM) + OKR por bloques | **Gradiente Térmico Nocturno:** Tasa estándar en terreno abierto. |
| **`EXP-TN03`** | F1 | Regresión DEM + Pendiente | `qmdist` (Skew-Normal) + OKR | **RK** (DEM + Pendiente + Coords) | **Frentes Fríos (*Nortes*):** Caídas térmicas asimétricas en invierno. |
| **`EXP-TN04`** | F1 | Desescalado orográfico 3D | `mbvar` (\\pm 5 d) + **NN-3D (\\Delta z)** | **RK** (DEM + Pendiente + Coords) | **Inversiones Térmicas:** Aislamiento vertical estricto cima-valle. |
| **`EXP-TN05`** | F1 | Regresión altimétrica DEM | `qmdist` (Gumbel) + OKR | **RK** (DEM + Coords) | **Heladas Agronómicas:** Ajuste de colas frías extremas (<0 °C). |
| **`EXP-TN06`** | F1 | Regresión regional DEM | `mbvar` (\\pm 5 d) + IDW | **Barnes (BSc)** 3 pasadas gaussianas | **Amortiguamiento Marino:** Regulación térmica nocturna en costas caribeñas. |
| **`EXP-TN07`** | F1 | Regresión altimétrica DEM | `mbmon` (mensual) + IDW | **Cressman (CSc)** 4 pasadas | **Pozas Frías Confinadas:** Radios decrecientes contra dispersión espuria. |
| **`EXP-TN08`** | F1 | Multivariado DEM+Slope+Aspect | `qmdist` (Skew-Normal) + NN-3D | **RK Total** (DEM+Slope+Aspect+Coords) | **Drenaje Catabático en Laderas:** Acoplamiento topográfico completo. |
| **`EXP-TN09`** | F2 | Bilineal con DEM SRTM | `mbvar` (\\pm 5 d) + **NN-3D (\\Delta z)** | **SBA** (1.0°, 0.67°, 0.33°) + Shepard | **Shepard Térmico Nocturno:** Interpolación local no lineal en residuales. |
| **`EXP-TN10`**<br>**(GANADOR)** | F2 | Bilineal con DEM SRTM | **QM Empírico (`qmecdf`)** + **NN-3D (\\Delta z)** | **RK (DEM + Pendiente)** + IDW (2.0°) | **MODELO GANADOR ABSOLUTO TMIN:** Resuelve inversiones y pozas de aire frío (*cold-air pooling*). Menor RMSE (1.92 °C), menor MAE (1.57 °C) y GSS (0.613). |
| **`EXP-TN11`** | F2 | Bilineal con DEM SRTM | `mbvar` (\\pm 5 d) + IDW (3.5°) | **RK (DEM + Lat + Lon)** + Barnes (2.0°) | **Híbrido Determinista-Gaussiano:** Segundo mejor RMSE (2.07 °C). |
| **`EXP-TN12`** | F2 | Bilineal con DEM SRTM | `mbvar` (\\pm 5 d) + NN-3D | **SBA Multiescala Local** (1.0°, 0.50°, 0.25°) | **SBA Local con NN-3D:** Confinamiento local estricto para mínimas nocturnas. |

### Ejecución de Suites desde Terminal:
```bash
# Ejecutar suites de 12 experimentos con 18 hilos:
python launcher/experiment_runner.py --suite tmax --cores 18
python launcher/experiment_runner.py --suite tmin --cores 18
```
"""

# Replace Section 5 in new_08
sec5_temp_start = new_08.find("## 5. Matriz de Experimentos Térmicos")
if sec5_temp_start != -1:
    new_08 = new_08[:sec5_temp_start] + sec5_temp
else:
    new_08 = new_08 + "\n\n" + sec5_temp

new_08 = clean_math(natural_tone(update_links(new_08)))


# =============================================================================
# BUILD NEW 09: Diagnóstico Precipitación (from old 06)
# =============================================================================
new_09 = docs["06"]
new_09 = re.sub(r'# 06\. Diagnóstico Científico.*?\n', '# 09. Diagnóstico Científico de Fase 1 y Resultados del Benchmark de Precipitación (Fase 2)\n', new_09)
new_09 = clean_math(natural_tone(update_links(new_09)))


# =============================================================================
# BUILD NEW 10: Diagnóstico Temperatura (from old 07)
# =============================================================================
new_10 = docs["07"]
new_10 = re.sub(r'# 07\. Diagnóstico Científico.*?\n', '# 10. Diagnóstico Científico y Resultados del Benchmark de Temperatura (Tmax y Tmin)\n', new_10)
new_10 = clean_math(natural_tone(update_links(new_10)))


# =============================================================================
# BUILD NEW README.md
# =============================================================================
new_readme = """# Documentación Técnica y Metodológica: Climate Data Tools (CDT v8.0)

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
   - Modelado del gradiente térmico vertical adiabático ($\Gamma \approx -6.5\ ^\circ\text{C/km}$), clampeo obligatorio de cotas submarinas negativas a $0\text{ msnm}$, protección integral de islas habitadas y continuidad litoral.

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
| **Temperatura Máxima ($T_{\max}$)** | **`EXP_TX11_RK_Barnes_Hybrid`** | RK (DEM + Lat + Lon) + Barnes Gaussiano Continuo | **GSS:** 0.719 \| **KGE:** **0.690** \| **$r$:** 0.743 \| **RMSE:** 2.06 $^\circ\text{C}$ | Forzamiento orográfico real con DEM en zonas sin estaciones y filtrado continuo de brisas marinas y transiciones litorales. |
| **Temperatura Mínima ($T_{\min}$)** | **`EXP_TN10_QM_Empirical_ECDF`** | RK (DEM + Pendiente) + QM Empírico Celda a Celda (NN-3D) | **GSS:** **0.613** \| **KGE:** 0.543 \| **RMSE:** **1.92 $^\circ\text{C}$** \| **MAE:** 1.57 $^\circ\text{C}$ | Menor error absoluto y cuadrático del benchmark; captura inversiones nocturnas y pozas de aire frío (*cold-air pooling*) sin distorsionar colas frías. |

---

## Documentación Técnica Complementaria

Para consultar el informe unificado en formato imprimible con la auditoría de cómputo en hardware y los tableros completos de validación ciega holdout:
- **Documento Markdown Maestro:** `docs-private/reporte_maestro_benchmark_cdt.md`
- **Documento PDF Imprimible:** `docs-private/reporte_maestro_benchmark_cdt.pdf` (Generado automáticamente mediante `python launcher/generate_pdf.py`).
"""

new_readme = clean_math(natural_tone(update_links(new_readme)))

# =============================================================================
# WRITE ALL NEW FILES (SAFE OVERWRITE)
# =============================================================================
new_files = {
    "01_guia_ejecucion_produccion_y_scripts.md": new_01,
    "02_arquitectura_lanzadores_python.md": new_02,
    "03_despliegue_contenedores_docker_apptainer.md": new_03,
    "04_fundamentos_gridding_merging_cdt.md": new_04,
    "05_metodos_interpolacion_residuales.md": new_05,
    "06_tratamiento_fisiografico_dem_batimetria.md": new_06,
    "07_secuencia_precipitacion_chirps_rnor.md": new_07,
    "08_secuencia_temperatura_chirts_dem.md": new_08,
    "09_diagnostico_y_benchmark_precipitacion.md": new_09,
    "10_diagnostico_y_benchmark_temperatura.md": new_10,
    "README.md": new_readme,
}

for fname, content in new_files.items():
    fpath = os.path.join(docs_dir, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Written {fname} ({len(content)} bytes)")

print("\nAll 10 modules + README.md written successfully!")
