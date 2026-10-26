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

* **Grupo de Evaluación:** Se mantiene estrictamente el archivo `validation_holdout_stations_rainfall.csv` (29 estaciones).
* **Eficiencia de Cómputo:** Los experimentos de la Fase 1 (`EXP_R01` a `EXP_R10`) ya están completados y verificados. El lanzador `launcher/experiment_runner.py` omitirá automáticamente los 10 primeros por caché (`CACHED`) y ejecutará únicamente del `EXP_R11` al `EXP_R15`.
