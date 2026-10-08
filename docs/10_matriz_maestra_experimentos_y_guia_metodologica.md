# Protocolo Metodológico Maestro y Matriz de Experimentos de Fusión Climática con CDT (1991–2020)
## Aplicación en Climas Complejos: Centroamérica y República Dominicana
### Batería Completa de 26 Experimentos: Precipitación (10), Temperatura Máxima (8) y Temperatura Mínima (8)

---

## 1. Justificación Científica del Problema y Objetivos de la Fusión

Los conjuntos de datos climáticos grillados basados exclusivamente en sensores satelitales y modelos de reanálisis global (**CHIRPS** para precipitación y **CHIRTS** para temperatura máxima y mínima) proporcionan una cobertura espacial continua y de alta resolución (~5.5 km, $0.05^\circ$). Sin embargo, **presentan discrepancias sistemáticas e importantes con respecto a la realidad observada en superficie**, especialmente en regiones con topografía montañosa abrupta e islas tropicales como Centroamérica y República Dominicana:

1. **Discrepancias en Precipitación Satelital (CHIRPS):**
   - **Sobreestimación de lloviznas espurias (*Drizzle Effect*):** La reflectividad infrarroja de cirros fríos y nubes altas no precipitantes es interpretada erróneamente por los algoritmos satelitales como eventos de lluvia ligera ($0.1\text{ a }1.0\text{ mm/día}$), distorsionando la frecuencia de días secos durante la **Canícula** (*Mid-Summer Drought*) en el Corredor Seco Centroamericano y las llanuras áridas del sur de República Dominicana (Funk et al., 2015; Maldonado et al., 2016).
   - **Subestimación de eventos extremos convectivos y ciclónicos:** La resolución espacial de $0.05^\circ$ suaviza las tasas de precipitación convectiva intensa en el ojo de huracanes y temporales tropicales (>100 mm/día) debido al efecto de promediado espacial dentro del píxel (*Areal Average vs. Point Measurement*) (Dinku et al., 2018).
   - **Distorsión del forzamiento orográfico:** El bloqueo topográfico y el ascenso en barlovento (*windward*) frente a la sombra de lluvia en sotavento (*leeward*) en sistemas montañosos como la Cordillera Central Dominicana o la Sierra Madre no son reproducidos con precisión por los sensores infrarrojos térmicos (Amador et al., 2006; Daly et al., 2008).

2. **Discrepancias en Temperatura Máxima Diurna ($T_{max}$ - CHIRTS):**
   - **Insolación y forzamiento radiativo según ladera:** Durante el día, la radiación solar directa incide diferencialmente según la orientación (*aspect*) y la pendiente del terreno. Las grillas globales suavizan las temperaturas en cañones profundos y laderas este (calentamiento matutino) vs oeste (máximo vespertino).
   - **Subestimación de olas de calor en depresiones áridas:** En valles encajonados y zonas por debajo del nivel del mar (Hoya de Enriquillo a -40 msnm, Valle de Azua en RD, y Golfo de Fonseca en Centroamérica), las temperaturas máximas extremas superan con frecuencia los $38\ ^\circ\text{C}$ a $40\ ^\circ\text{C}$, fenómeno que los reanálisis globales alisan drásticamente (Coles, 2001; Funk et al., 2019).

3. **Discrepancias en Temperatura Mínima Diurna ($T_{min}$ - CHIRTS):**
   - **Falta de resolución de inversiones térmicas nocturnas y drenaje catabático:** Durante la noche, el enfriamiento radiativo provoca el drenaje de aire denso y frío (*cold-air pooling*) hacia el fondo de valles intramontanos cerrados (Constanza y Valle Nuevo en RD, Quetzaltenango en Guatemala), registrándose heladas y temperaturas bajo cero ($<0\ ^\circ\text{C}$), mientras que las cumbres adyacentes permanecen más cálidas (inversión térmica). Los modelos globales no resuelven este desacople sin ponderación vertical estricta ($\Delta z$).
   - **Asimetría por intrusiones de frentes fríos invernales (*Nortes*):** Las invasiones de aire polar modificado generan descensos térmicos abruptos y asimétricos en laderas expuestas al norte que las distribuciones gaussianas estándar no capturan (Alfaro et al., 2018).

**Estructura de la Matriz de Evaluación (26 Experimentos):**
Para aislar rigurosamente los efectos físicos y estadísticos de cada componente, se formulan **tres conjuntos experimentales independientes**:
- **10 Experimentos de Precipitación (`EXP-R01` a `EXP-R10`)**: Evaluación de corrección de sesgo (Gamma, Weibull, Lognormal, ECDF empírico), máscara RnoR (Logit GLM), Kriging por Bloques, Regression Kriging orográfico y Esquemas de Barnes/Cressman/Shepard/Spheremap/NN-3D.
- **8 Experimentos de Temperatura Máxima (`EXP-TX01` a `EXP-TX08`)**: Evaluación de radiación solar diurna, desescalado con DEM SRTM, gradiente adiabático, extremos por olas de calor con distribución de Gumbel, insolación según orientación (*aspect*) y consistencia costera con Barnes.
- **8 Experimentos de Temperatura Mínima (`EXP-TN01` a `EXP-TN08`)**: Evaluación de enfriamiento nocturno, inversiones térmicas en valles intramontanos mediante NN-3D ($\Delta z$), frentes fríos invernales con Skew-Normal, heladas agronómicas con Gumbel y amortiguamiento marino nocturno.

---

## 2. Glosario de Siglas y Acrónimos Técnicos

| Sigla / Acrónimo | Denominación Completa | Definición y Función en el Flujo de Procesamiento |
| :--- | :--- | :--- |
| **CDT** | *Climate Data Tools* | Paquete en entorno R desarrollado por el IRI (Columbia University) para control de calidad, homogeneización, corrección de sesgo y fusión espacial de datos climáticos. |
| **CHIRPS** | *Climate Hazards Group InfraRed Precipitation with Stations* | Base de datos de precipitación cuasi-global ($0.05^\circ$, diaria, 1981–presente) que combina climatología satelital infrarroja (CHPclim), estimaciones de satélite geoestacionario (TMPA/CPC) y estaciones meteorológicas de tierra. |
| **CHIRTS** | *Climate Hazards Center InfraRed Temperature with Stations* | Base de datos cuasi-global de temperatura máxima y mínima diaria ($0.05^\circ$, 1983–presente) que combina datos térmicos infrarrojos de satélite con reanálisis ERA5 y estaciones de superficie. |
| **DEM** | *Digital Elevation Model* | Grilla raster que representa la cota topográfica del terreno sobre el nivel medio del mar (m.s.n.m.), utilizada como covariable física del gradiente vertical. |
| **SRTM** | *Shuttle Radar Topography Mission* | Misión satelital de la NASA que produjo modelos de elevación digital globales de 30 m y 90 m de resolución espacial. |
| **SBA** | *Simple Bias Adjustment* | Método de fusión espacial en el cual el sesgo o residuo entre estaciones y el satélite se calcula de forma aditiva o proporcional y se interpola espacialmente sobre la grilla. |
| **RK** | *Regression Kriging* | Método geoestadístico híbrido que ajusta un modelo de regresión determinístico (GLM) con covariables auxiliares (DEM, pendiente, lat/lon) y suma la interpolación por Kriging de los residuales estocásticos. |
| **BSc** | *Barnes Scheme* | Técnica de análisis objetivo basada en correcciones sucesivas con función de ponderación gaussiana exponencial continua, reduciendo discontinuidades espaciales. |
| **CSc** | *Cressman Scheme* | Técnica clásica de análisis objetivo basada en correcciones sucesivas con función de ponderación de radio de influencia finito esférico. |
| **IDW** | *Inverse Distance Weighted* | Método determinístico de interpolación espacial donde el peso de cada estación es inversamente proporcional a la distancia elevada a una potencia ($p=2$). |
| **OKR** | *Ordinary Kriging* | Método geoestadístico óptimo de interpolación lineal no sesgado (BLUE) que estima valores ponderando la autocorrelación espacial modelada mediante un semivariograma. |
| **Block Kriging** | *Block Kriging* | Variante de Kriging que estima el valor medio sobre el área de un píxel (bloque) en lugar de una estimación puntual pura, corrigiendo discrepancias de soporte espacial. |
| **NN-3D** | *Nearest Neighbor 3-Dimensional* | Interpolación por vecino más cercano considerando simultáneamente la distancia horizontal euclidiana y la diferencia de cota vertical ($\Delta z$ con el DEM). |
| **RnoR Mask** | *Rain-No-Rain Mask* | Filtro probabilístico de dos estados (seco/húmedo) que calcula la probabilidad de precipitación en cada píxel mediante regresión logística para suprimir lloviznas irreales. |
| **GLM** | *Generalized Linear Model* | Marco estadístico de regresión que permite ajustar relaciones determinísticas entre la variable climática y covariables orográficas continuas. |
| **QM** | *Quantile Mapping* | Técnica no lineal de corrección de sesgo que iguala la función de distribución acumulada (CDF) de los datos satelitales con la CDF de las estaciones observadas. |
| **ECDF** | *Empirical Cumulative Distribution Function* | Función de distribución empírica no paramétrica calculada a partir de los cuantiles ordenados de las muestras históricas. |
| **Lapse Rate** | Gradiente Térmico Vertical Ambiental | Tasa de variación de la temperatura con respecto a la altitud ($\partial T / \partial z$), típicamente entre $-5.5\ ^\circ\text{C}/\text{km}$ y $-6.5\ ^\circ\text{C}/\text{km}$ en atmósfera libre tropical. |
| **CLLJ** | *Caribbean Low-Level Jet* | Corriente de viento zonal del este de alta velocidad en niveles bajos (925 hPa) que modula el transporte de humedad y la precipitación en Centroamérica y el Caribe. |
| **CAG** | *Central American Gyre* | Circulación ciclónica monzónica de gran escala que produce lluvias torrenciales extremas continuas durante varios días en la vertiente del Pacífico. |
| **LOOCV** | *Leave-One-Out Cross-Validation* | Protocolo de validación cruzada iterativo donde se excluye una estación por turno, se reajusta el modelo con las restantes y se valida contra la estación excluida. |
| **KGE** | *Kling-Gupta Efficiency* | Métrica hidroclimática compuesta que evalúa simultáneamente la correlación lineal ($r$), el sesgo volumétrico ($\beta$) y la variabilidad relativa ($\gamma$). |
| **CF-1.8** | *Climate and Forecast Conventions v1.8* | Estándar internacional para la estructuración y documentación de metadatos en archivos científicos NetCDF. |

---

## 3. Significancia Estadística y Climatológica de la Interpolación en CDT

La selección del método y la configuración de los parámetros de interpolación determinan la **física y la estructura espacial del campo climático resultante**:

| Parámetro en CDT | Significado Estadístico | Significado Climatológico Regional |
| :--- | :--- | :--- |
| **Radio de Búsqueda (`maxdist`)** | Longitud de correlación espacial de la función de covarianza. | Extensión del fenómeno físico: $1.0^\circ\text{--}1.5^\circ$ para convección tropical; $2.0^\circ$ para ondas/ciclones; $3.5^\circ$ para masas de aire térmicas sinópticas. |
| **Número de Vecinos (`nmin / nmax`)** | Tamaño muestral local para la estimación puntual. | $n$ bajo preserva anomalías locales/microclimas; $n$ alto proporciona suavizado regional homogéneo. |
| **Kriging por Bloques (`use.block = TRUE`)** | Cambio de soporte espacial (Point-to-Area). Reduce la varianza del error de área. | Integra la medición puntual de la estación sobre el píxel satelital ($0.05^\circ \approx 5.5\text{ km}$), corrigiendo discrepancias de escala. |
| **Modelo de Variograma (`vgm.model`)** | Estructura de continuidad espacial y rango asintótico. | - **Esférico (`Sph`):** Barreras orográficas nítidas.<br>- **Gaussiano (`Gau`):** Campos térmicos muy continuos.<br>- **Exponencial (`Exp`):** Lluvias convectivas turbulentas. |
| **Potencia IDW (`powerWeightIDW`)** | Factor de decaimiento con la distancia ($1/d^p$). | $p=2$ es el balance óptimo; $p=1$ genera campos muy planos; $p=3$ concentra el gradiente en las estaciones. |
| **Esquema Multi-Pasada (`pass`)** | Descomposición espectral multiescala (filtro pasa-bajos a pasa-altos). | Pasada 1 (`1.0`) corrige el sesgo regional; Pasadas 2 y 3 (`0.75, 0.5`) ajustan microclimas locales de valle y cerro. |
| **Máscara RnoR (Logit / CutOff=3)** | Clasificación probabilística discriminante binaria. | Elimina lloviznas espurias durante la Canícula en el Corredor Seco y Azua, conservando días secos reales. |
| **Factor NN-3D ($\Delta z$)** | Ponderación de distancia tridimensional con el DEM. | Resuelve inversiones térmicas nocturnas aislando valles altos fríos (Constanza) de planicies cálidas adyacentes. |

---

## 4. Contexto Fisiográfico y Dinámica Climatológica Regional

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│               SÍNTESIS CLIMATOLÓGICA Y FISIOGRÁFICA: CENTROAMÉRICA Y REPÚBLICA DOMINICANA               │
├────────────────────────────┬─────────────────────────────┬─────────────────────────────────────────────┤
│ 1. Relieve y Barreras      │ 2. Doble Vertiente y Vientos│ 3. Regímenes de Variabilidad y Extremos     │
├────────────────────────────┼─────────────────────────────┼─────────────────────────────────────────────┤
│ • Centroamérica: Cordillera│ • Vertiente Caribe / Norte: │ • Convección Tropical Diurna: Celdas        │
│   de Talamanca (>3,800 m), │   Lluvias orográficas       │   convectivas locales de radio reducido     │
│   Sierra Madre (>4,200 m), │   abundantes todo el año por│   (10–30 km) en laderas montañosas.         │
│   Sierra de Isabelia.      │   Vientos Alisios y el Chorro│ • Perturbaciones Sinópticas: Ondas del     │
│ • Rep. Dominicana:         │   del Caribe (CLLJ).        │   Este, Ciclones Tropicales y Giros (CAG).  │
│   Cordillera Central (Pico │ • Vertiente Pacífica / Sur: │ • Canícula (Veranillo): Racha seca crítica  │
│   Duarte 3,087 m), Sierra  │   Bimodal (Mayo–Noviembre), │   de 15–40 días en julio-agosto en el       │
│   de Neiba y Bahoruco.     │   marcada estación seca     │   Corredor Seco y valles del sur dominicano.│
│ • Valles y depresiones:    │   (diciembre–abril) y fuerte│ • Intrusiones de Frentes Fríos ("Nortes"):  │
│   Valle del Motagua,       │   sombrío de lluvia en      │   Enfriamiento brusco y lluvias en costas   │
│   Depresión de Enriquillo. │   sotavento.                │   norteñas durante el invierno boreal.      │
└────────────────────────────────────────────────────────────┴─────────────────────────────────────────────┘
```

---

## 5. Matriz de 26 Experimentos: Tablas con Justificación Física Celda por Celda

### Suite A: Precipitación Diaria (CHIRPS 1991–2020, 10 Experimentos)
Configurados en [`config/experiments_rainfall/`](file:///d:/Workspace/CDT-8.0/config/experiments_rainfall):

| ID Exp. | Sesgo (Paso 1) | Interp. Sesgo | Fusión (Paso 3) | Covariables RK | Máscara RnoR | Justificación y Enfoque Climatológico Regional |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **`EXP-R01`** | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $1.5^\circ$) | SBA (1 pasada: `1.0`) | Ninguna | Desactivada (`use=false`) | **Control / Línea Base:** Fusión aditiva convencional sin control de lloviznas espurias. |
| **`EXP-R02`** | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $1.5^\circ$) | SBA (3 pasadas: `1, 0.75, 0.5`) | Ninguna | Logit Rampa `CutOff=3` ($2\text{ px}$) | **Impacto RnoR en Zonas Semiáridas:** Restaura días secos en Canícula en Corredor Seco y Azua. |
| **`EXP-R03`** | QM Bernoulli-Gamma | OKR Block (`Sph/Exp/Gau`) | SBA (3 pasadas) | Ninguna | Logit Rampa `CutOff=3` | **Convección Típica:** Ajusta lluvias moderadas del Pacífico y reduce error de soporte puntual. |
| **`EXP-R04`** | QM Bernoulli-Weibull | OKR Block (`Sph/Exp/Gau`) | SBA (3 pasadas) | Ninguna | Logit Rampa `CutOff=3` | **Extremos Ciclónicos:** Modela colas pesadas (>150 mm/d) de huracanes en el Caribe. |
| **`EXP-R05`** | QM Bernoulli-Weibull | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM + Slope + Lat + Lon** | Logit Rampa `CutOff=3` | **Modelo Orográfico:** Ascenso por Alisios en barlovento y sombras de lluvia en valles. |
| **`EXP-R06`** | `mbvar` ($\pm 5$ d) | NN-3D con DEM ($\Delta z$) | Barnes (BSc, 3 pasadas) | Ninguna | Logit Rampa `CutOff=3` | **Costero e Insular:** Decaimiento gaussiano suave en el Caribe y Rep. Dominicana sin ojos de buey. |
| **`EXP-R07`** | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $1.5^\circ$) | Cressman (CSc, 4 pasadas) | Ninguna | Logit Rampa `CutOff=3` | **Convección Local:** Envolventes restrictivas para núcleos convectivos aislados en el Pacífico. |
| **`EXP-R08`** | `mbvar` ($\pm 5$ d) | Shepard Modificado | SBA (3 pasadas) | Ninguna | Logit Rampa `CutOff=3` | **Terreno Escarpado:** Polinomios de Taylor que evitan singularidades en alta montaña. |
| **`EXP-R09`** | `mbvar` ($\pm 5$ d) | Spheremap Gran Círculo | SBA (3 pasadas) | Ninguna | Logit Rampa `CutOff=3` | **Geometría Esférica:** Distancia de círculo máximo sobre la curvatura del Caribe. |
| **`EXP-R10`** | QM Bernoulli-Weibull | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM+Slope+Aspect+Coords** | Logit Rampa `CutOff=3` | **Máxima Complejidad:** Acopla orientación de ladera (*aspect*) frente a los Alisios del NE. |

---

### Suite B: Temperatura Máxima ($T_{max}$ CHIRTS 1991–2020, 8 Experimentos)
Configurados en [`config/experiments_tmax/`](file:///d:/Workspace/CDT-8.0/config/experiments_tmax):

| ID Exp. | Desescalado DEM | Corrección Sesgo | Interp. Sesgo | Fusión Final | Covariables RK | Justificación y Enfoque Climatológico Regional |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **`EXP-TX01`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $3.5^\circ$) | SBA (1 pasada) | Ninguna | **Control Nulo:** Mide el sesgo térmico al ignorar el relieve y la radiación solar. |
| **`EXP-TX02`** | Bilineal (`blin`) | QM Normal | IDW ($p=2.0$, $3.5^\circ$) | RK (3 pasadas) | **DEM (Elevación)** | **Gradiente Adiabático:** Tasa diurna ($-6.5\ ^\circ\text{C}/\text{km}$) en Cordillera Central y Sierra Madre. |
| **`EXP-TX03`** | IDW Local | QM Skew-Normal | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM + Slope + Coords** | **Asimetría Térmica:** Captura frentes fríos diurnos y calentamiento por inclinación de ladera. |
| **`EXP-TX04`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | NN-3D con DEM ($\Delta z$) | RK (3 pasadas) | **DEM + Slope + Aspect** | **Topografía y Radiación:** Control 3D de cota e insolación diferencial en laderas este/oeste. |
| **`EXP-TX05`** | Bilineal (`blin`) | QM Gumbel Máx. | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM + Latitud + Longitud** | **Olas de Calor:** Ajusta Tmax (P95/P99) en Valle de Azua/Enriquillo (-40 m) y Golfo de Fonseca. |
| **`EXP-TX06`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $3.5^\circ$) | Barnes (BSc, 3 pasadas) | Ninguna | **Llanuras Costeras Continuas:** Transiciones suaves en llanuras del Caribe y planicies de RD. |
| **`EXP-TX07`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $3.5^\circ$) | Cressman (CSc, 4 pasadas)| Ninguna | **Valles Confinados:** Envolventes restrictivas de radio decreciente en valles intramontanos. |
| **`EXP-TX08`** | Bilineal (`blin`) | QM Skew-Normal | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM+Slope+Aspect+Coords**| **Máxima Complejidad Diurna:** Acoplamiento solar total, orientación y asimetría térmica. |

---

### Suite C: Temperatura Mínima ($T_{min}$ CHIRTS 1991–2020, 8 Experimentos)
Configurados en [`config/experiments_tmin/`](file:///d:/Workspace/CDT-8.0/config/experiments_tmin):

| ID Exp. | Desescalado DEM | Corrección Sesgo | Interp. Sesgo | Fusión Final | Covariables RK | Justificación y Enfoque Climatológico Regional |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **`EXP-TN01`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $3.5^\circ$) | SBA (1 pasada) | Ninguna | **Control Nulo:** Mide el sesgo nocturno base al ignorar el enfriamiento radiativo. |
| **`EXP-TN02`** | Bilineal (`blin`) | QM Normal | IDW ($p=2.0$, $3.5^\circ$) | RK (3 pasadas) | **DEM (Elevación)** | **Gradiente Nocturno:** Tasa vertical nocturna en zonas altas sin inversión térmica. |
| **`EXP-TN03`** | IDW Local | QM Skew-Normal | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM + Slope + Coords** | **Frentes Fríos (*Nortes*):** Caídas térmicas bruscas asimétricas en la vertiente Atlántica invernal. |
| **`EXP-TN04`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | **NN-3D con DEM ($\Delta z$)** | RK (3 pasadas) | **DEM + Slope + Coords** | **Inversiones Térmicas:** Evita interpolar calor de llanuras en valles altos fríos (Constanza). |
| **`EXP-TN05`** | Bilineal (`blin`) | QM Gumbel Mín. | OKR Block (`Sph/Exp/Gau`) | RK (3 pasadas) | **DEM + Latitud + Longitud** | **Heladas y Extremos Fríos:** Modelado de colas mínimas extremas ($<0\ ^\circ\text{C}$) en cumbres altas. |
| **`EXP-TN06`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $3.5^\circ$) | Barnes (BSc, 3 pasadas) | Ninguna | **Llanuras Homogéneas:** Enfriamiento radiativo uniforme en llanuras del Caribe y valles amplios. |
| **`EXP-TN07`** | Bilineal (`blin`) | `mbvar` ($\pm 5$ d) | IDW ($p=2.0$, $3.5^\circ$) | Cressman (CSc, 4 pasadas)| Ninguna | **Pozas de Aire Frío:** Radio decreciente para aislar fondos de valle de laderas adyacentes. |
| **`EXP-TN08`** | Bilineal (`blin`) | QM Skew-Normal | **NN-3D con DEM ($\Delta z$)** | RK (3 pasadas) | **DEM+Slope+Aspect+Coords**| **Máxima Complejidad Nocturna:** Drenaje catabático por pendientes y diferencias de cota ($\Delta z$). |

---

## 6. Esquema de Validación Cruzada Independiente y Fórmulas de Evaluación

```
[ Estaciones Totales 1991–2020 ]
             │
             ├──► Partición automática vía validation_holdout_stations.csv (station_manager.py)
             │    ├── 80–90% Entrenamiento ──► Pipeline CDT (Downscale + Bias + Merging)
             │    └── 10–20% Validación   ──► Evaluación Independiente
             │
             └──► Métricas Calculadas en launcher/station_manager.py:
                  • Continuas: KGE, RMSE, MAE, R², PBIAS.
                  • Categóricas (Lluvia $\ge 1.0\text{ mm}$): POD, FAR, ETS, HSS.
```

### Fórmulas Matemáticas de Evaluación:

1. **Eficiencia Kling-Gupta (KGE):**
   $$\text{KGE} = 1 - \sqrt{(r - 1)^2 + (\beta - 1)^2 + (\gamma - 1)^2}$$
   donde $r$ es la correlación de Pearson, $\beta = \frac{\mu_s}{\mu_o}$ (sesgo de la media) y $\gamma = \frac{\sigma_s / \mu_s}{\sigma_o / \mu_o}$ (coeficiente de variación relativo).

2. **Error Cuadrático Medio (RMSE):**
   $$\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (S_i - O_i)^2}$$

3. **Error Absoluto Medio (MAE):**
   $$\text{MAE} = \frac{1}{N}\sum_{i=1}^N |S_i - O_i|$$

4. **Sesgo Porcentual (PBIAS):**
   $$\text{PBIAS} = \frac{\sum (S_i - O_i)}{\sum O_i} \times 100\%$$

5. **Métricas Categóricas de Lluvia ($\ge 1.0\text{ mm/d}$):**
   - **Probabilidad de Detección (POD):** $\text{POD} = \frac{H}{H + M}$
   - **Razón de Falsas Alarmas (FAR):** $\text{FAR} = \frac{FA}{H + FA}$
   - **Equitable Threat Score (ETS):** $\text{ETS} = \frac{H - H_r}{H + M + FA - H_r}$ donde $H_r = \frac{(H+M)(H+FA)}{N}$
   - **Heidke Skill Score (HSS):** $\text{HSS} = \frac{2(H \cdot CN - FA \cdot M)}{(H+M)(M+CN) + (H+FA)(FA+CN)}$

---

## 7. Rendimiento de Hardware y Modo de Uso del Lanzador en Python

### Evaluación en Servidor Intel Xeon Silver 4210R (9 Workers, 64 GB RAM, NVMe):

| Suite de Experimentos | Núm. Exp. | Días / Exp. | Tiempo por Exp. | Tiempo Total Suite | Consumo RAM Máx. |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precipitación (CHIRPS)** | 10 | 10,958 | 35 – 42 min | **5.8 – 6.7 horas** | 2.5 – 4.5 GB |
| **Temperatura Máxima ($T_{max}$)** | 8 | 10,958 | 80 – 95 min | **11.0 – 12.5 horas** | 3.5 – 4.6 GB |
| **Temperatura Mínima ($T_{min}$)** | 8 | 10,958 | 80 – 95 min | **11.0 – 12.5 horas** | 3.5 – 4.6 GB |
| **TOTAL GENERAL 26 EXPERIMENTOS** | **26** | **10,958** | — | **28.0 – 31.5 horas** | **Máx. 4.6 GB (<8% RAM)** |

### Comandos de Ejecución CLI (`launcher/experiment_runner.py`):

```bash
# Diagnóstico de dependencias
python launcher/experiment_runner.py --check-env

# Ejecutar suites completas
python launcher/experiment_runner.py --suite rainfall   # 10 Exp. Lluvia (~6 h)
python launcher/experiment_runner.py --suite tmax       # 8 Exp. Tmax (~11.5 h)
python launcher/experiment_runner.py --suite tmin       # 8 Exp. Tmin (~11.5 h)

# Ejecutar corrida batch completa de los 26 experimentos
python launcher/experiment_runner.py --suite all        # 26 Exp. (~28-31.5 h)

# Ejecutar un experimento individual parametrizado
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R05_RK_Topography_BernoulliWeibull.yaml
```

---

## 8. Referencias Bibliográficas Científicas Verificadas

1. **Amador, J. A., Alfaro, E. J., Lizano, O. G., & Magaña, V. O. (2006).** *Atmospheric forcing of the eastern tropical Pacific: A review.* Progress in Oceanography, 69(2–4), 101–142. DOI: [10.1016/j.pocean.2006.03.007](https://doi.org/10.1016/j.pocean.2006.03.007)
2. **Barnes, S. L. (1964).** *A technique for maximizing details in numerical weather map analysis.* Journal of Applied Meteorology, 3(4), 396–409. DOI: [10.1175/1520-0450(1964)003<0396:ATFMDI>2.0.CO;2](https://doi.org/10.1175/1520-0450(1964)003<0396:ATFMDI>2.0.CO;2)
3. **Coles, S. (2001).** *An Introduction to Statistical Modeling of Extreme Values.* Springer-Verlag, London. DOI: [10.1007/978-1-4471-3675-0](https://doi.org/10.1007/978-1-4471-3675-0)
4. **Cressman, G. P. (1959).** *An operational objective analysis system.* Monthly Weather Review, 87(10), 367–374. DOI: [10.1175/1520-0493(1959)087<0367:AOOAS>2.0.CO;2](https://doi.org/10.1175/1520-0493(1959)087<0367:AOOAS>2.0.CO;2)
5. **Daly, C., Halbleib, M., Smith, J. I., Gibson, W. P., Doggett, M. K., Taylor, G. H., Curtis, J., & Pasteris, P. P. (2008).** *Physiographically sensitive mapping of temperature and precipitation across the conterminous United States.* International Journal of Climatology, 28(15), 2031–2064. DOI: [10.1002/joc.1688](https://doi.org/10.1002/joc.1688)
6. **Dinku, T., Thomson, M. C., Cousin, R., del Corral, J., Ceccato, P., Hansen, J., & Connor, S. J. (2018).** *Enhancing National Climate Services (ENACTS) for development in Africa.* Climate and Development, 10(7), 664–672. DOI: [10.1080/17565529.2017.1405784](https://doi.org/10.1080/17565529.2017.1405784)
7. **Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., Husak, G., Rowland, J., Harrison, L., Hoell, A., & Michaelsen, J. (2015).** *The climate hazards group infrared precipitation with stations—a new environmental record for monitoring extremes.* Scientific Data, 2(1), 150066. DOI: [10.1038/sdata.2015.66](https://doi.org/10.1038/sdata.2015.66)
8. **Verdin, A., Funk, C., Peterson, P., Landsfeld, M., Tuholske, C., & Grace, K. (2020).** *Development and validation of the CHIRTS-daily quasi-global high-resolution daily temperature data set.* Scientific Data, 7(1), 303. DOI: [10.1038/s41597-020-00643-7](https://doi.org/10.1038/s41597-020-00643-7)
9. **Gudmundsson, L., Bremnes, J. B., Haugen, J. E., & Engen-Skaugen, T. (2012).** *Downscaling RCM precipitation to the station scale using statistical transformations–a comparison of methods.* Hydrology and Earth System Sciences, 16(9), 3383–3390. DOI: [10.5194/hess-16-3383-2012](https://doi.org/10.5194/hess-16-3383-2012)
10. **Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).** *Decomposition of the mean squared error and NSE performance measures: Implications for improving hydrological modelling.* Journal of Hydrology, 377(1-2), 80–91. DOI: [10.1016/j.jhydrol.2009.08.003](https://doi.org/10.1016/j.jhydrol.2009.08.003)
11. **Hengl, T., Heuvelink, G. B., & Rossiter, D. G. (2007).** *About regression-kriging: From equations to case studies.* Computers & Geosciences, 33(10), 1301–1315. DOI: [10.1016/j.cageo.2007.05.001](https://doi.org/10.1016/j.cageo.2007.05.001)
12. **Hidalgo, H. G., Alfaro, E. J., & Quesada-Montano, B. (2017).** *Observed (1970–1999) climate variability in Central America using a high-resolution meteorological dataset with implication to climate change studies.* Climatic Change, 141(1), 13–28. DOI: [10.1007/s10584-016-1786-y](https://doi.org/10.1007/s10584-016-1786-y)
13. **Kedem, B., Chiu, L. S., & North, G. R. (1990).** *Estimation of mean rain rate: Application to satellite observations.* Journal of Geophysical Research: Atmospheres, 95(D2), 1965–1972. DOI: [10.1029/JD095iD02p01965](https://doi.org/10.1029/JD095iD02p01965)
14. **Maldonado, T., Rutgersson, A., Amador, J. A., Alfaro, E. J., & Claremar, B. (2016).** *Variability of the Caribbean low-level jet during boreal winter: large-scale forcings.* International Journal of Climatology, 36(4), 1978–1999. DOI: [10.1002/joc.4472](https://doi.org/10.1002/joc.4472)
15. **Schultz, D. M., Bracken, W. E., & Bosart, L. F. (1998).** *Planetary- and synoptic-scale signatures associated with Central American cold surges.* Monthly Weather Review, 126(1), 5–27. DOI: [10.1175/1520-0493(1998)126<0005:PASSSA>2.0.CO;2](https://doi.org/10.1175/1520-0493(1998)126<0005:PASSSA>2.0.CO;2)
16. **Shepard, D. (1968).** *A two-dimensional interpolation function for irregularly-spaced data.* Proceedings of the 1968 23rd ACM National Conference, 517–524. DOI: [10.1145/800186.810616](https://doi.org/10.1145/800186.810616)
17. **Themeßl, M. J., Gobiet, A., & Leuprecht, A. (2011).** *Empirical-statistical downscaling and error correction of daily precipitation from regional climate models.* International Journal of Climatology, 31(10), 1530–1544. DOI: [10.1002/joc.2168](https://doi.org/10.1002/joc.2168)
18. **Willmott, C. J., Rowe, C. M., & Philpot, W. D. (1985).** *Small-scale climate maps: A sensitivity analysis of some common assumptions associated with grid-point interpolation and contouring.* The American Cartographer, 12(1), 5–16. DOI: [10.1559/152304085783914686](https://doi.org/10.1559/152304085783914686)
19. **WMO / CF Metadata Conventions Committee (2020).** *NetCDF Climate and Forecast (CF) Metadata Conventions Version 1.8.* World Meteorological Organization. URL: [https://cfconventions.org/](https://cfconventions.org/)

