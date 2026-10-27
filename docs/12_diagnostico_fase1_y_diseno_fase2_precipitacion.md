# Diagnóstico Científico de la Fase 1 y Diseño Metodológico de la Fase 2 (Precipitación Diaria)

## 1. Contexto y Objetivos del Benchmark de Lluvia

El objetivo del benchmark es evaluar y seleccionar la configuración óptima de corrección de sesgo y fusión espacial (*merging*) en **CDT 8.0** para la serie histórica diaria de 30 años (1991–2020, 10,958 pasos temporales) en América Central y República Dominicana, utilizando satélite **CHIRPS v2.0** a resolución de $0.05^\circ$ (~5.5 km) y la red de estaciones pluviométricas de superficie.

Para garantizar máxima objetividad científica y evitar sobreajuste (*in-sample overfitting*), se implementó un esquema estricto de **validación ciega (*holdout*)**:
* **Total de estaciones disponibles:** 266 estaciones meteorológicas.
* **Estaciones de entrenamiento (calibración y merging):** 237 estaciones.
* **Estaciones de validación independiente (*holdout*):** 29 estaciones excluidas del entrenamiento, distribuidas representativamente en distintos regímenes climáticos y pisos altitudinales.

---

## 2. Resultados Consolidados de la Fase 1 (Cribado Exploratorio: EXP_R01 a EXP_R10)

La Fase 1 evaluó 10 familias metodológicas representativas del estado del arte en interpolación geoespacial y ajuste de sesgo satelital:

| Experimento ID | Familia / Algoritmo | Ajuste de Sesgo | Interpolación Merging | KGE Medio | $r$ Pearson | RMSE (mm) | POD | FAR | ETS | HSS |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **EXP_R08** | **Modified Shepard (Relieve Complejo)** | `mbvar` (IDW) | **Shepard (3 pasadas)** | **0.375** | **0.479** | **12.89** | **0.665** | **0.304** | **0.315** | **0.464** |
| **EXP_R09** | **Spheremap (Geometría Esférica)** | `mbvar` (IDW) | **Spheremap (3 pasadas)** | **0.358** | **0.458** | **13.59** | 0.648 | 0.296 | 0.313 | 0.463 |
| **EXP_R01** | Control Nulo / IDW Plano (Baseline) | `mbvar` (IDW) | IDW 1 pasada (sin RnoR) | 0.335 | 0.486 | 12.22 | 0.666 | 0.338 | 0.274 | 0.418 |
| **EXP_R07** | Cressman Celdas Aisladas | `mbvar` (IDW) | Cressman (4 pasadas) | 0.332 | 0.447 | 14.44 | 0.630 | 0.305 | 0.296 | 0.444 |
| **EXP_R06** | Barnes BSc Gradientes Costeros | `mbvar` (NN-3D) | Barnes BSc (3 pasadas) | 0.309 | 0.449 | 14.22 | 0.646 | 0.310 | 0.298 | 0.445 |
| **EXP_R02** | SBA IDW con Filtro RnoR | `mbvar` (IDW) | IDW 3 pasadas (RnoR logit) | 0.263 | 0.466 | 12.39 | 0.613 | 0.315 | 0.272 | 0.411 |
| **EXP_R05** | Regression Kriging Topográfico | `qmdist` (Weibull) | RK (DEM + Pendiente) | 0.215 | 0.417 | 13.28 | 0.522 | 0.367 | 0.201 | 0.322 |
| **EXP_R10** | RK Máxima Complejidad Acoplada | `qmdist` (Weibull) | RK (DEM + Pend + Aspect) | 0.106 | 0.411 | 14.11 | 0.508 | 0.376 | 0.190 | 0.307 |
| **EXP_R04** | SBA Kriging Ordinario Bernoulli-Weibull | `qmdist` (Weibull) | OKR por bloques | 0.016 | 0.431 | 14.51 | 0.636 | 0.348 | 0.247 | 0.373 |
| **EXP_R03** | SBA Kriging Ordinario Bernoulli-Gamma | `qmdist` (Gamma) | OKR por bloques | -0.028 | 0.427 | 14.87 | 0.639 | 0.348 | 0.246 | 0.373 |

---

## 3. Diagnóstico Físico y Estadístico de la Fase 1

### 3.1. ¿Por qué el KGE diario se ubica en el rango 0.30 - 0.38?
A primera vista, un KGE de 0.375 puede parecer moderado si se compara con variables como temperatura o caudales mensuales. Sin embargo, para **precipitación diaria tropical en terreno complejo con validación out-of-sample**, este valor es científicamente robusto por las siguientes razones:
1. **Efecto de Doble Penalización (*Double Penalty*):** La lluvia convectiva ocurre en núcleos de 3 a 8 km. Una tormenta que impacta directamente una estación puede no coincidir exactamente en tiempo o en píxel con el sensor satelital, penalizando severamente el KGE diario puntual.
2. **Desempeño Categórico Sólido:** Las métricas de detección diaria son altas: POD de **66.5%**, FAR de **30.4%** y un Heidke Skill Score (HSS) de **0.464**, lo que confirma una alta fidelidad para discernir lluvia de días secos.
3. **Escala Temporal:** Al acumular a escalas pentadales, decadales o mensuales, el ruido convectivo diario se disipa y la correlación y el KGE suben típicamente a valores superiores a **0.80**.

### 3.2. Colapso del Quantile Mapping Teórico (Bernoulli-Gamma y Weibull)
* `EXP_R03` y `EXP_R04` tuvieron los peores desempeños (KGE -0.028 y 0.016).
* **Causa:** Forzar las observaciones a distribuciones paramétricas teóricas de 2 parámetros distorsiona las colas y la alta proporción de ceros (60-80% según la vertiente). El ajuste empírico por ventanas móviles (`mbvar`) demostró ser inmensamente más estable.

### 3.3. La Paradoja Orográfica del Regression Kriging
* Incorporar DEM, pendiente y orientación en `EXP_R05` y `EXP_R10` redujo el KGE a 0.215 y 0.106.
* **Causa:** La orografía centroamericana presenta una banda de condensación máxima a media ladera (1,000–1,800 msnm) y un contraste drástico entre la vertiente Caribe (húmeda) y la vertiente Pacífico (seca). Un modelo de regresión lineal global confunde estas relaciones e introduce artefactos espurios.

### 3.4. Superioridad Numérica de Shepard Modificado y Spheremap
* **Shepard Modificado (`EXP_R08`):** Logró el mejor KGE (0.375), el mejor HSS (0.464) y el menor error en zonas de relieve escarpado porque los polinomios de Taylor locales amortiguan singularidades numéricas.
* **Spheremap (`EXP_R09`):** Ocupó el segundo lugar (KGE 0.358), demostrando la importancia de calcular distancias sobre la esfera terrestre en un istmo rodeado por dos masas oceánicas.

---

## 4. Diseño Metodológico de la Fase 2 (Optimización Dirigida: EXP_R11 a EXP_R15)

Apoyándose en la victoria de Shepard y Spheremap, la Fase 2 formula **5 hipótesis de mejora dirigida** explotando parámetros avanzados de CDT 8.0:

```
                      FASE 1: Cribado (Screening)
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
       Modelos Descartados                Modelos Ganadores
    • QM Teórico (Gamma/Weibull)       • Modified Shepard (EXP_R08: KGE 0.375)
    • Regression Kriging Lineal        • Spheremap (EXP_R09: KGE 0.358)
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
               FASE 2: Refinamiento Dirigido (EXP_R11 - EXP_R15)
           ┌──────────────────────┼──────────────────────┐
           ▼                      ▼                      ▼
    Sesgo Robusto          Acotamiento Espacial    QM No-Paramétrico
   (Mediana vs Media)    (CoarseGrid + Local 0.9°)  (eCDF Empírico)
```

### Detalle de los Experimentos de la Fase 2:

1. **`EXP_R11_Shepard_Median_Coarse` (Shepard Robusto con Mediana y Malla Gruesa):**
   * *Hipótesis:* Sustituir la media aritmética por la mediana (`mulBiasFunction: "median"`) en `mbvar` elimina la sobrestimación causada por tormentas convectivas extremas aisladas. La adición de malla gruesa (`addCoarseGrid: true`) amortigua los residuos hacia 0 en las zonas marítimas y costeras desprovistas de estaciones.
   * *Configuración:* `biascoeff_options: {mulBiasFunction: "median", addCoarseGrid: true}`, SBA Shepard $1.5^\circ$.

2. **`EXP_R12_Shepard_Local_Orn` (Shepard Confinado Orográfico / Anti-Cruce Transcordillera):**
   * *Hipótesis:* Un radio de búsqueda de $1.5^\circ$ (~165 km) cruza la cordillera central y contamina la estación seca del Pacífico con estaciones húmedas del Caribe. Confinar el radio a $0.9^\circ$ (~100 km) con $n_{min}=3, n_{max}=8$ preserva la sombra orográfica real.
   * *Configuración:* SBA Shepard $maxdist = 0.9^\circ$, pasadas $[1.0, 0.67, 0.33]$.

3. **`EXP_R13_QM_Empirical_ECDF` (Quantile Mapping No-Paramétrico eCDF):**
   * *Hipótesis:* La falla de `EXP_R03`/`R04` provino de imponer fórmulas Gamma/Weibull rígidas. El método `qmecdf` realiza mapeo cuantil a cuantil sin distribución analítica predeterminada, capturando eventos extremos sin distorsión.
   * *Configuración:* Bias method `qmecdf`, SBA Shepard $1.5^\circ$.

4. **`EXP_R14_Spheremap_Median` (Geometría Esférica con Mediana y Malla Gruesa):**
   * *Hipótesis:* Acoplar la proyección de gran círculo de Spheremap con el estimador de mediana y contención de malla gruesa para evaluar si supera a Shepard al eliminar distorsiones de borde.
   * *Configuración:* `biascoeff_options: {mulBiasFunction: "median", addCoarseGrid: true}`, SBA Spheremap $1.5^\circ$.

5. **`EXP_R15_Shepard_RnoR_Smooth` (Shepard con Transición Continua de Lluvia):**
   * *Hipótesis:* La máscara RnoR con umbral duro (0.5) penaliza precipitaciones leves en valles secos. Usar `RnoRCutOff: 2` establece una transición gradual continua entre 0.1 y 1.0.
   * *Configuración:* SBA Shepard $1.2^\circ$, `merging_options: {RnoRCutOff: 2}`.

---

## 5. Trazabilidad y Ejecución

* **Grupo de Evaluación:** Se mantiene estrictamente el archivo `validation_holdout_stations_rainfall.csv` (29 estaciones de validación ciega independiente).
* **Eficiencia de Cómputo:** Los experimentos de la Fase 1 (`EXP_R01` a `EXP_R10`) y Fase 2 (`EXP_R11` a `EXP_R15`) se evaluaron integralmente sobre los 30 años climatológicos continuos (1991–2020, 10,958 días).

---

## 6. Resultados Consolidados de la Fase 2 y Ranking Final (15 Experimentos)

La ejecución y evaluación cuantitativa de los 15 experimentos sobre las **29 estaciones de validación ciega independiente (*holdout*)** arroja el siguiente tablero de liderazgo consolidado:

| Rank | Experimento ID | Método de Fusión y Configuración | KGE Medio | KGE Mediana | $r$ Pearson | RMSE (mm) | MAE (mm) | PBIAS (%) | POD | FAR | ETS | HSS | Global Skill | Estado |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **EXP_R15_Shepard_RnoR_Smooth** | **Shepard + RnoR Suave (CutOff 2, rad 1.2°)** | **0.3791** | **0.3978** | **0.4791** | **12.88** | **5.83** | **-4.39%** | **0.6922** | **0.3038** | **0.3287** | **0.4785** | **0.5007** | **GANADOR** |
| **2** | **EXP_R12_Shepard_Local_Orn** | Shepard Confinado Local (rad 0.9° ~100 km) | 0.3716 | 0.4046 | 0.4685 | 13.21 | 5.95 | -3.21% | 0.6731 | 0.2989 | 0.3238 | 0.4735 | 0.4991 | Fase 2 |
| **3** | **EXP_R08_Shepard_Complex_Relief** | Shepard Relieve Escarpado (rad 1.5°) | 0.3749 | 0.4006 | 0.4794 | 12.89 | 5.85 | -6.30% | 0.6650 | 0.3039 | 0.3147 | 0.4638 | 0.4888 | Fase 1 |
| **4** | **EXP_R11_Shepard_Median_Coarse** | Shepard Mediana Robusta + Malla Gruesa (1.5°) | 0.3753 | 0.4041 | 0.4787 | 12.77 | 5.76 | -6.70% | 0.6746 | 0.3037 | 0.3213 | 0.4697 | 0.4885 | Fase 2 |
| **5** | **EXP_R14_Spheremap_Median** | Spheremap Gran Círculo + Mediana + Malla | 0.3621 | 0.3978 | 0.4552 | 13.56 | 6.06 | -4.43% | 0.6540 | 0.2971 | 0.3174 | 0.4660 | 0.4863 | Fase 2 |
| **6** | **EXP_R09_Spheremap_Trans_Caribe** | Spheremap Gran Círculo Estándar (rad 1.5°) | 0.3584 | 0.3992 | 0.4584 | 13.59 | 6.09 | -4.59% | 0.6477 | 0.2959 | 0.3132 | 0.4633 | 0.4843 | Fase 1 |
| **7** | **EXP_R07_Cressman_Spherical** | Cressman Celdas Aisladas (4 pasadas: 1.0° a 0.25°) | 0.3318 | 0.3669 | 0.4468 | 14.44 | 6.44 | +3.64% | 0.6299 | 0.3048 | 0.2958 | 0.4436 | 0.4724 | Guía CDT |
| **8** | **EXP_R13_QM_Empirical_ECDF** | Quantile Mapping Empírico (qmecdf) + Shepard | 0.3196 | 0.3602 | 0.4655 | 13.08 | 6.03 | -5.57% | 0.6393 | 0.3034 | 0.2995 | 0.4458 | 0.4658 | Fase 2 |
| **9** | **EXP_R06_Barnes_Gauss_Coastal** | Barnes BSc Gaussiano Costero (NN-3D) | 0.3087 | 0.3458 | 0.4490 | 14.22 | 6.40 | +4.08% | 0.6461 | 0.3098 | 0.2976 | 0.4450 | 0.4635 | Fase 1 |
| **10** | **EXP_R01_SBA_IDW_Baseline** | Control Nulo / IDW Plano Monocapa (Sin RnoR) | 0.3353 | 0.3984 | 0.4861 | 12.22 | 5.62 | -13.53% | 0.6657 | 0.3379 | 0.2743 | 0.4178 | 0.4396 | Base |
| **11** | **EXP_R02_SBA_IDW_RnoR** | SBA IDW 3 pasadas + RnoR (Corte Rígido 0.5) | 0.2631 | 0.3592 | 0.4659 | 12.39 | 5.56 | -22.15% | 0.6132 | 0.3153 | 0.2718 | 0.4109 | 0.3743 | Fase 1 |
| **12** | **EXP_R05_RK_Topography_BW** | Regression Kriging Topográfico (Weibull) | 0.2147 | 0.3802 | 0.4166 | 13.28 | 5.98 | -18.28% | 0.5216 | 0.3673 | 0.2010 | 0.3215 | 0.3463 | Fase 1 |
| **13** | **EXP_R03_SBA_OKR_BernoulliGamma** | QM Paramétrico Gamma + OKR por Bloques | -0.0277 | 0.3780 | 0.4275 | 14.87 | 6.03 | -5.83% | 0.6389 | 0.3484 | 0.2460 | 0.3729 | 0.3231 | Fase 1 |
| **14** | **EXP_R04_SBA_OKR_BernoulliWeib** | QM Paramétrico Weibull + OKR por Bloques | 0.0159 | 0.3786 | 0.4306 | 14.51 | 5.85 | -11.98% | 0.6357 | 0.3479 | 0.2475 | 0.3733 | 0.3148 | Fase 1 |
| **15** | **EXP_R10_RK_FullTopography_Asp** | RK Máxima Complejidad (DEM + Pend + Aspect) | 0.1062 | 0.3518 | 0.4112 | 14.11 | 6.07 | -18.36% | 0.5084 | 0.3761 | 0.1901 | 0.3073 | 0.3045 | Fase 1 |

---

## 7. Análisis Físico y Climatológico de los Resultados de la Fase 2

### 7.1. ¿Por qué gana EXP_R15_Shepard_RnoR_Smooth?
1. **Transición Continua Suave (`RnoRCutOff: 2`):**
   * En la Fase 1, `EXP_R02` demostró que aplicar una máscara RnoR con corte binario duro a $0.5\text{ mm}$ provocaba un sesgo seco severo ($\text{PBIAS} = -22.15\%$), porque eliminaba eventos de llovizna real ($0.1\text{ a }1.0\text{ mm}$) en valles intermontanos y laderas secas.
   * `EXP_R15` aplica una rampa de transición continua entre $0.1$ y $1.0\text{ mm}$, eliminando el sesgo seco casi en su totalidad ($\text{PBIAS} = -4.39\%$), preservando la detección de días secos en la Canícula sin mutilar la lluvia ligera.
2. **Ponderación Angular y Direccional de Shepard:**
   * La familia Shepard incorpora factores de protección direccional que evitan que varias estaciones agrupadas en una misma vertiente dominen excesivamente la interpolación hacia celdas vecinas a través de barreras montañosas.
   * Esto explica por qué los 4 primeros lugares del benchmark pertenecen todos a la familia Shepard (`EXP_R15`, `EXP_R12`, `EXP_R08`, `EXP_R11`).
3. **Métricas Categóricas Sobresalientes:**
   * `EXP_R15` alcanza el **POD más alto de todo el benchmark (69.22%)**, el **ETS más alto (0.3287)** y el **HSS más alto (0.4785)**, demostrando una discriminación óptima entre eventos de lluvia y días secos.

### 7.2. Aislamiento Orográfico en EXP_R12 (Rank 2)
* `EXP_R12` obtuvo el sesgo más cercano a cero ($\text{PBIAS} = -3.21\%$). Confinar el radio de búsqueda a $0.9^\circ$ (~100 km) confirma la hipótesis física: en un istmo estrecho con una espina dorsal montañosa elevada, radios de búsqueda $>1.5^\circ$ generan "fuga de humedad" artificial desde el Caribe hacia las cuencas secas del Pacífico.

### 7.3. Rescate del Quantile Mapping en EXP_R13
* Frente al colapso de las distribuciones teóricas Gamma ($\text{KGE} = -0.028$) y Weibull ($\text{KGE} = 0.016$), el Quantile Mapping Empírico (`EXP_R13`) elevó el KGE a **0.3196** ($+0.347$ frente a Gamma). La vectorización con interpolación de cuantiles sobre `knots()` redujo el tiempo de cómputo del Paso 2 de más de 30 horas a solo 12 minutos.

---

## 8. Entorno de Hardware Calibrado y Rendimiento de Cómputo

Los experimentos de precipitación de la Fase 1 y Fase 2 fueron ejecutados y calibrados en una estación de trabajo dedicada con las siguientes especificaciones:

* **Sistema Operativo:** Linux Ubuntu 24.04.5 LTS (x86_64, Kernel Linux nativo)
* **Procesador (CPU):** Intel(R) Core(TM) i9-10850K CPU @ 3.60GHz (10 núcleos físicos / 20 hilos, frecuencia base 3.60 GHz, Turbo Boost 5.20 GHz, 20 MB Intel Smart Cache)
* **Memoria RAM:** 32 GB DDR4 @ 3200 MT/s (Dual-Channel)
* **Almacenamiento:** SSD NVMe M.2 PCIe de 400 GB (Lectura/Escritura > 3,000 MB/s)
* **Configuración de Paralelismo:** 18 hilos de procesamiento en paralelo (dejando 2 hilos para el sistema operativo), despachados mediante la suite `launcher/experiment_runner.py --cores 18`.
* **Tiempo Total Suite Precipitación (15 Experimentos / 30 Años / 10,958 Días):** ~35.0 a 38.0 horas continuas. Consumo máximo de memoria: ~4.5 GB (< 15% de RAM disponible).
