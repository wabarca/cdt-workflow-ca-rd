# Protocolo Metodológico Maestro y Matriz de Experimentos de Fusión Climática con CDT (1991–2020)
## Aplicación en Climas Complejos: Centroamérica y República Dominicana
### Batería Completa de 31 Experimentos: Precipitación (15: Fase 1 y Fase 2), Temperatura Máxima (8) y Temperatura Mínima (8)

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
   - **Falta de resolución de inversiones térmicas nocturnas y drenaje catabático:** Durante la noche, el enfriamiento radiativo provoca el drenaje de aire denso y frío (*cold-air pooling*) hacia el fondo de valles intramontanos cerrados (Constanza y Valle Nuevo en RD, Quetzaltenango en Guatemala), registrándose heladas y temperaturas bajo cero ($< 0\ ^\circ\text{C}$), mientras que las cumbres adyacentes permanecen más cálidas (inversión térmica). Los modelos globales no resuelven este desacople sin ponderación vertical estricta ($\Delta z$).
   - **Asimetría por intrusiones de frentes fríos invernales (*Nortes*):** Las invasiones de aire polar modificado generan descensos térmicos abruptos y asimétricos en laderas expuestas al norte que las distribuciones gaussianas estándar no capturan (Alfaro et al., 2018).

**Estructura de la Matriz de Evaluación (31 Experimentos):**
Para aislar rigurosamente los efectos físicos y estadísticos de cada componente, se formulan **tres conjuntos experimentales independientes**:
- **15 Experimentos de Precipitación (`EXP-R01` a `EXP-R15`)**:
  - *Fase 1 (Cribado Exploratorio: R01 a R10):* Evaluación de familias de interpolación (IDW, Kriging Ordinario por Bloques, Regression Kriging orográfico, Barnes, Cressman, Shepard Modificado, Spheremap Gran Círculo) y modelos de sesgo (Gamma, Weibull, Multiplicativo móvil).
  - *Fase 2 (Optimización Dirigida: R11 a R15):* Refinamiento sobre los ganadores de la Fase 1 (Shepard y Spheremap) variando estimadores de mediana robusta, malla gruesa costera, acotamiento local orográfico anti-fuga transcordillera (0.9°), Quantile Mapping no paramétrico (eCDF) y transición de lluvia continua suave (`RnoRCutOff: 2`).
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

## 5. Matriz de 31 Experimentos: Tablas con Justificación Física Celda por Celda y Flujo por Pasos

### 5.1 Arquitectura de Flujo Secuencial por Pasos en CDT

La metodología de fusión en CDT se estructura en etapas analíticas secuenciales independientes que permiten aislar y evaluar rigurosamente el impacto de cada técnica en el modelado climático:

#### Cadena de Procesamiento para Precipitación (3 Etapas en CDT)
*CDT Menú: Gridding > Merging Climate Data > Rainfall Data*

| Paso en CDT | Acción en CDT | Opciones y Parámetros que se Varían (Detalle Exhaustivo) |
| :--- | :--- | :--- |
| **Paso 1: Compute Bias Coefficients**<br>*(Cálculo de Coefs. de Sesgo)* | Modela estadísticamente las discrepancias espaciales y distribucionales entre satélite y observaciones de estaciones de superficie. | • **Métodos de Estimación de Sesgo:** Multiplicativo móvil (`mbvar`, ventana temporal móvil de $\pm 5$ días), Mensual climatológico fijo (`mbmon`), Quantile Mapping paramétrico (`qmdist` con función analítica teórica), Quantile Mapping empírico no paramétrico (`qmecdf` directamente sobre la curva observada).<br>• **Distribuciones de Probabilidad:** Bernoulli-Gamma, Bernoulli-Weibull, Bernoulli-LogNormal (modelado mixto: probabilidad de ocurrencia binaria *wet $\ge 1.0\text{ mm}$* y distribución de intensidad continua).<br>• **Interpolación Espacial de Coeficientes:** IDW ($p=2.0$, radios de búsqueda $0.9^\circ$ a $1.5^\circ$, $nmin=3–4, nmax=8–12$), Kriging Ordinario (`okr`), Kriging por Bloques (`use_block=TRUE` con integración sobre celdas de $0.05^\circ$ para solventar la discrepancia de soporte espacial punto-celda), Vecino más cercano 3D (Shepard), Spheremap (gran círculo).<br>• **Estimador Central:** Media aritmética estándar (`mean`) vs. Mediana robusta (`median`) ante convección extrema atípica.<br>• **Malla Gruesa Complementaria:** Inclusión de grilla soporte (`addCoarseGrid: true`, resolución $1.0^\circ$) para amortiguar residuales en litorales y bordes sin estaciones.<br>• **Salida:** Archivo binario `.rds` estructurado con la matriz de coeficientes y cuantiles. |
| **Paso 2: Apply Bias Correction**<br>*(Aplicación de Ajuste de Sesgo)* | Transforma las 10,958 grillas diarias de satélite aplicando las funciones de calibración del Paso 1. | • **Rango Temporal:** Serie continua de 30 años (1991–2020, 10,958 pasos diarios).<br>• **Archivo de Entrada:** Parámetros estructurados en `.rds` del Paso 1.<br>• **Transformación Matemática:** Corrección multiplicativa proporcional celda por celda o traslación cuantil a cuantil de la función de distribución acumulada (CDF).<br>• **Salida Estandarizada:** Grillas NetCDF calibradas `rr_adj_%s%s%s.nc` estructuradas conforme a la convención CF-1.8. |
| **Paso 3: Merging Data**<br>*(Fusión Espacial de Residuales)* | Combina las grillas satelitales corregidas (*first guess*) con las observaciones puntuales de estaciones mediante interpolación de residuales. | • **Métodos de Fusión:** Spatio-Temporal Bias Adjustment (**SBA**), Cressman Objective Analysis (**CSc**), Barnes Objective Analysis (**BSc**), Regression Kriging (**RK**).<br>• **Esquemas Multi-Pasada:** 1 única pasada ($1.0^\circ$), 3 pasadas decrecientes ($1.0^\circ, 0.75^\circ, 0.50^\circ$), 3 pasadas locales de alta resolución ($1.0^\circ, 0.67^\circ, 0.33^\circ$) o 4 pasadas restrictivas Cressman ($1.0^\circ, 0.75^\circ, 0.50^\circ, 0.25^\circ$).<br>• **Máscara Lluvia/No-Lluvia (RnoR):** Desactivada (`use=false`), Activada con corte binario rígido (`RnoRCutOff = 3`, umbral $0.5\text{ mm}$), Activada con **transición continua suave** (`RnoRCutOff = 2`, función lineal de $0.1$ a $1.0\text{ mm}$ con pesos probabilísticos continuos vía Logit GLM).<br>• **Covariables Físicas Acopladas en RK:** Elevación (DEM), pendiente (*slope*), orientación (*aspect*), coordenadas lat/lon.<br>• **Métodos de Interpolación de Residuales:** IDW ($p=2.0$), OKR por bloques, Shepard Modificado con control de derivadas direccionales, Spheremap en esfera real terrestre, Barnes gaussiano.<br>• **Salida Final:** NetCDF diarios fusionados y ensamblados en archivo 3D multitemporal conforme a CF-1.8. |

#### Cadena de Procesamiento para Temperatura (5 Etapas en CDT)
*CDT Menú: Gridding > Merging Climate Data > Temperatures Data*

| Paso en CDT | Acción en CDT | Opciones y Parámetros que se Varían (Detalle Exhaustivo) |
| :--- | :--- | :--- |
| **Paso 1: Compute Downscaling Coefficients**<br>*(Cálculo de Coefs. de Desescalado)* | Modela empíricamente el gradiente térmico vertical ambiental (*lapse rate*, $\partial T/\partial z$) entre estaciones y elevación. | • **Paso Temporal:** Coeficientes diarios móviles ($\pm 5$ días), mensuales fijos o estacionales.<br>• **Topografía Base:** DEM SRTM de 90 m remuestreado a $0.05^\circ$ o resolución nativa de $0.01^\circ$ (~1.1 km).<br>• **Modelado Estadístico:** Regresión lineal univariada estación–altitud o GLM multivariado con pendiente (*slope*) y orientación de ladera (*aspect*).<br>• **Salida:** Archivo binario `.rds` estructurado con la matriz de coeficientes altimétricos por periodo. |
| **Paso 2: Downscaling Data**<br>*(Desescalado Espacial de Grillas)* | Proyecta y remuestrea las grillas térmicas satelitales/reanálisis sobre la malla topográfica fina del DEM. | • **Métodos de Interpolación Espacial:** Bilineal (`blin`), IDW local o Kriging Ordinario (`okr`).<br>• **Resolución y Malla Objetivo:** Grilla regular a $0.05^\circ$ (~5.5 km) o $0.01^\circ$ (~1.1 km) sincronizada con el DEM regional.<br>• **Rango Temporal:** Procesamiento continuo de los 10,958 días (1991–2020).<br>• **Salida Estandarizada:** NetCDF desescalados topográficamente `tmax_down_%s%s%s.nc` / `tmin_down_%s%s%s.nc`. |
| **Paso 3: Compute Bias Coefficients**<br>*(Cálculo de Coeficientes de Sesgo)* | Calcula las discrepancias espaciales y distribucionales entre las temperaturas desescaladas y las estaciones observadas. | • **Métodos de Sesgo Térmico:** Multiplicativo móvil (`mbvar` $\pm 5$ días), Sesgo mensual fijo (`mbmon`), Quantile Mapping paramétrico (`qmdist`), QM empírico no paramétrico (`qmecdf`).<br>• **Distribuciones Teóricas Continuas:** Normal gaussiana (`norm`), Asimétrica Skew-Normal (`snorm` para descensos bruscos por frentes fríos *Nortes* en Tmin u olas de calor en Tmax), Valores extremos Gumbel (`gumbel` para colas de eventos extremos $>P95$ en Tmax o heladas $<P05$ en Tmin), Log-Normal.<br>• **Interpolación Espacial de Coeficientes:** IDW ($p=2.0$, radio sinóptico de $3.5^\circ$, $nmin=4, nmax=12$), OKR con variogramas Sph, Exp, Gau y Pen, Ponderación tridimensional NN-3D considerando diferencia altimétrica $\Delta z$. |
| **Paso 4: Apply Bias Correction**<br>*(Aplicación del Ajuste de Sesgo)* | Aplica las funciones de ajuste calculadas en el Paso 3 a las 10,958 grillas diarias desescaladas. | • **Rango Temporal:** Serie 1991–2020 continua.<br>• **Archivo de Entrada:** Parámetros estructurados y curvas CDF en archivo `.rds` del Paso 3.<br>• **Transformación:** Corrección multiplicativa proporcional o traslación no lineal cuantil a cuantil celda por celda.<br>• **Salida:** Grillas NetCDF calibradas `tmax_adj_%s%s%s.nc` / `tmin_adj_%s%s%s.nc`. |
| **Paso 5: Merging Data**<br>*(Fusión Espacial de Residuales)* | Fusión final entre las grillas desescaladas/ajustadas (*first guess*) y las observaciones puntuales de estaciones. | • **Métodos de Fusión:** Regression Kriging (**RK**) multivariado vs SBA.<br>• **Covariables Físicas Acopladas:** DEM (elevación sobre el nivel del mar), pendiente del terreno, orientación de ladera (*aspect*), coordenadas lat/lon.<br>• **Esquemas Multi-Pasada:** 3 pasadas decrecientes ($1.0^\circ, 0.75^\circ, 0.50^\circ$) o Cressman 4 pasadas ($1.0^\circ, 0.75^\circ, 0.50^\circ, 0.25^\circ$).<br>• **Interpolación de Residuales Térmicos:** IDW ($3.5^\circ$), OKR por bloques, **NN-3D con restricción vertical estricta** ($\Delta z$ con el DEM para resolver inversiones térmicas y drenaje de aire frío nocturno), Barnes (**BSc**) gaussiano continuo para amortiguamiento marino costero.<br>• **Salida Final:** NetCDF diarios fusionados y ensamblados en archivo 3D multitemporal conforme a CF-1.8. |

---

### 5.2 Suite A: Precipitación Diaria (CHIRPS 1991–2020: 15 Experimentos — Fase 1 y Fase 2)
Configurados en [`config/experiments_rainfall/`](file:///d:/Workspace/CDT-8.0/config/experiments_rainfall):

#### Fase 1: Cribado Exploratorio (EXP-R01 a EXP-R10)

| ID Exp. | Paso 1: Compute Bias Coefficients (Cálculo de Sesgo) | Paso 2: Apply Bias Correction (Aplicación de Sesgo) | Paso 3: Merging Data (Fusión Espacial) | Hipótesis Física y Climatológica Regional |
| :---: | :--- | :--- | :--- | :--- |
| **`EXP-R01`** | • Método: `mbvar` (multiplicativo móvil $\pm 5$ d)<br>• Interp: IDW ($p=2.0$, radio $1.5^\circ$, $nmin=4, nmax=12$) | • Ajuste de grillas satelitales CHIRPS 1991–2020<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA (*Simple Bias Adjustment*)<br>• Pasadas: 1 única pasada (radio $1.0^\circ$)<br>• Interp. residuales: IDW ($1.5^\circ$)<br>• RnoR: **Desactivada** (`use=false`)<br>• Covariables: Ninguna | **Control Nulo Determinista (Línea Base):** Mide la discrepancia satelital pura sin control de lloviznas espurias (*drizzle effect*) ni esquemas multiescala. |
| **`EXP-R02`** | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: IDW ($p=2.0$, radio $1.5^\circ$) | • Ajuste multiplicativo sobre grillas CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala<br>• Pasadas: 3 pasadas decrecientes ($1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• Interp: IDW ($1.5^\circ$)<br>• RnoR: **Activada** (Logit GLM, $wet=1.0\text{ mm}$, $CutOff=3$)<br>• Covariables: Ninguna | **Impacto del Filtro RnoR en Zonas Semiáridas:** Evalúa la restauración de rachas secas reales durante la **Canícula** (*Mid-Summer Drought*) en el Corredor Seco y Azua, eliminando falsa lluvia satelital. |
| **`EXP-R03`** | • Método: `qmdist` (Quantile Mapping)<br>• Distribución: **Bernoulli-Gamma** (probabilidad de lluvia + intensidad)<br>• Interp: Kriging Ordinario por Bloques (`okr`, `use_block=TRUE`, modelos Sph/Exp/Gau, radio $2.0^\circ$) | • Corrección distribucional cuantil a cuantil de la CDF sobre CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala<br>• Pasadas: 3 pasadas ($1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• Interp: Kriging Ordinario por Bloques (`okr`)<br>• RnoR: Activada (Logit GLM)<br>• Covariables: Ninguna | **Régimen Convectivo Tropical Típico:** La distribución Gamma modela la asimetría de lluvias convectivas moderadas; el Kriging por bloques corrige el error de soporte espacial (punto de estación vs. celda de 5.5 km). |
| **`EXP-R04`** | • Método: `qmdist`<br>• Distribución: **Bernoulli-Weibull** (colas pesadas asintóticas)<br>• Interp: Kriging Ordinario por Bloques (`okr`, radio $2.0^\circ$) | • Mapeo no lineal enfocado en cuantiles extremos ($>P95$)<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala<br>• Pasadas: 3 pasadas ($1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• Interp: Kriging Ordinario por Bloques (`okr`)<br>• RnoR: Activada (Logit GLM)<br>• Covariables: Ninguna | **Extremos Ciclónicos y Tormentas Severas:** La función Weibull captura las colas pesadas ($>150\text{ mm/día}$) provocadas por ondas tropicales, ciclones en el Caribe y giros monzónicos (CAG). |
| **`EXP-R05`** | • Método: `qmdist`<br>• Distribución: Bernoulli-Weibull<br>• Interp: Kriging Ordinario por Bloques (`okr`, radio $2.0^\circ$) | • Corrección de extremos sobre grillas CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **Regression Kriging (RK)**<br>• Pasadas: 3 pasadas ($1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• **Covariables físicas: DEM + Pendiente (Slope) + Lat + Lon**<br>• Interp. residuales: OKR por bloques<br>• RnoR: Activada (Logit GLM) | **Forzamiento Orográfico Vertical:** Acopla el relieve en la regresión determinística; modela el ascenso forzado por los vientos Alisios en barlovento y las sombras de lluvia en sotavento. |
| **`EXP-R06`** | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: **NN-3D con elevación DEM ($\Delta z$)** | • Ajuste proporcional tridimensional sobre CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **Barnes Objective Analysis (BSc)**<br>• Pasadas: 3 pasadas con ponderación gaussiana decreciente<br>• RnoR: Activada (Logit GLM)<br>• Covariables: Ninguna | **Gradientes Costeros e Insulares Suaves:** La función de peso gaussiano continuo de Barnes evita singularidades y discontinuidades circulares ("ojos de buey") en islas y franjas costeras. |
| **`EXP-R07`** | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: IDW ($p=2.0$, radio $1.5^\circ$) | • Ajuste sobre grillas satelitales<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **Cressman Objective Analysis (CSc)**<br>• Pasadas: 4 pasadas con envolvente esférica restrictiva ($1.0^\circ, 0.75^\circ, 0.5^\circ, 0.25^\circ$)<br>• RnoR: Activada (Logit GLM)<br>• Covariables: Ninguna | **Celdas Convectivas Aisladas:** Radios de influencia estrictamente finitos en la última pasada ($0.25^\circ \approx 27\text{ km}$) para ajustar núcleos de tormenta muy localizados en la costa del Pacífico. |
| **`EXP-R08`** | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: **Shepard Modificado** | • Ajuste de sesgo con polinomios locales<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala (3 pasadas)<br>• Interp: Shepard Modificado con control de derivadas direccionales<br>• RnoR: Activada (Logit GLM)<br>• Covariables: Ninguna | **Relieve Escarpado y Cañones:** Los polinomios de Shepard evitan sobreoscilaciones numéricas en transiciones topográficas abruptas (zonas de cañones y fallas). |
| **`EXP-R09`** | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: **Spheremap (Gran Círculo)** | • Ajuste sobre CHIRPS en coordenadas esféricas<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala (3 pasadas)<br>• Interp: Spheremap en esfera terrestre real<br>• RnoR: Activada (Logit GLM)<br>• Covariables: Ninguna | **Geometría Esférica Trans-Caribe:** Corrige la distorsión métrica de latitud en distancias zonales amplias a lo largo del arco de las Antillas Mayores. |
| **`EXP-R10`** | • Método: `qmdist`<br>• Distribución: Bernoulli-Weibull<br>• Interp: Kriging Ordinario por Bloques (`okr`) | • Corrección distribucional de extremos ciclónicos<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **Regression Kriging (RK)** multiescala<br>• **Covariables: DEM + Pendiente + Orientación (Aspect) + Lat + Lon**<br>• Interp. residuales: OKR por bloques<br>• RnoR: Activada (Logit GLM) | **Máxima Complejidad Física Acoplada:** Incorpora la orientación de ladera (*aspect*) para capturar la intercepción directa de la humedad transportada por el Chorro del Caribe (CLLJ) del noreste. |

#### Fase 2: Optimización Dirigida (EXP-R11 a EXP-R15)

| ID Exp. | Paso 1: Compute Bias Coefficients (Cálculo de Sesgo) | Paso 2: Apply Bias Correction (Aplicación de Sesgo) | Paso 3: Merging Data (Fusión Espacial) | Hipótesis Física y Climatológica Regional (Fase 2) |
| :---: | :--- | :--- | :--- | :--- |
| **`EXP-R11`** | • Método: `mbvar` ($\pm 5$ d)<br>• `mulBiasFunction: "median"`<br>• `addCoarseGrid: true` (resolución $1.0^\circ$)<br>• Interp: IDW ($1.5^\circ$) | • Ajuste multiplicativo robusto con mediana sobre CHIRPS 1991–2020<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala (3 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• Interp: Shepard Modificado ($1.5^\circ$)<br>• RnoR: Activada (Logit GLM)<br>• `addCoarseGrid: true` | **Mediana Robusta y Malla Gruesa Costera:** El estimador de mediana neutraliza eventos convectivos extremos atípicos que inflan el sesgo multiplicativo; la malla gruesa atenúa los residuos hacia cero en áreas oceánicas y costeras sin estaciones. |
| **`EXP-R12`** | • Método: `mbvar` ($\pm 5$ d)<br>• `mulBiasFunction: "median"`<br>• **Interp: IDW local (radio $0.9^\circ \approx 100\text{ km}$, $nmin=3, nmax=8$)** | • Ajuste con aislamiento transcordillera sobre CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **SBA multiescala local** (3 pasadas: $1.0^\circ, 0.67^\circ, 0.33^\circ$)<br>• **Interp: Shepard local ($0.9^\circ$, $nmin=3, nmax=8$)**<br>• RnoR: Activada (Logit GLM) | **Aislamiento Orográfico Transcordillera:** Un radio de $1.5^\circ$ (~165 km) cruza la cordillera central y contamina la estación seca del Pacífico con estaciones húmedas del Caribe. Confinar el radio a $0.9^\circ$ preserva la sombra orográfica real. |
| **`EXP-R13`** | • Método: **Quantile Mapping Empírico (`qmecdf`)**<br>• Mapeo cuantil a cuantil no paramétrico sin distribución analítica predeterminada<br>• Interp: IDW ($1.5^\circ$) | • Mapeo empírico cuantil a cuantil sobre grillas CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: SBA multiescala (3 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• Interp: Shepard Modificado ($1.5^\circ$)<br>• RnoR: Activada (Logit GLM) | **Quantile Mapping No-Paramétrico (eCDF):** Supera la rigidez de las distribuciones teóricas de 2 parámetros (Gamma/Weibull) que colapsaron en la Fase 1, modelando eventos extremos directamente a partir de la distribución acumulada empírica observada. |
| **`EXP-R14`** | • Método: `mbvar` ($\pm 5$ d)<br>• `mulBiasFunction: "median"`<br>• `addCoarseGrid: true` ($1.0^\circ$)<br>• Interp: IDW ($1.5^\circ$) | • Ajuste esférico sobre grillas CHIRPS<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **SBA multiescala** (3 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• **Interp: Spheremap en esfera real ($1.5^\circ$)**<br>• RnoR: Activada (Logit GLM)<br>• `addCoarseGrid: true` | **Spheremap con Mediana y Malla Gruesa:** Acopla la proyección de gran círculo sobre la curvatura terrestre real con el estimador de mediana y contención de malla gruesa para eliminar distorsiones de borde en el arco de las Antillas. |
| **`EXP-R15`**<br>*(GANADOR)* | • Método: `mbvar` ($\pm 5$ d)<br>• `mulBiasFunction: "median"`<br>• Interp: IDW ($1.2^\circ$, $nmin=4, nmax=10$) | • Ajuste multiplicativo sobre grillas CHIRPS 1991–2020<br>• Salida: `rr_adj_%s%s%s.nc` | • Método: **SBA multiescala** (3 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• Interp: Shepard Modificado ($1.2^\circ$)<br>• **RnoR: Activada con `RnoRCutOff = 2` (Transición Suave)** | **MODELO GANADOR — Transición Continua Suave de Lluvia:** Sustituye el corte binario rígido (0.5 mm) por una función lineal continua entre 0.1 y 1.0 mm. Elimina el subestimado seco de RnoR duro (-4.39% PBIAS vs -22.15% en R02), alcanzando el KGE y Skill Score más altos. |

#### Tablero Consolidado del Benchmark de Precipitación (29 Estaciones de Validación Ciega Holdout)

| Rank | Experimento ID | Método de Fusión y Configuración Clave | KGE | $r$ | RMSE (mm) | PBIAS (%) | POD | FAR | ETS | HSS | Global Skill | Clasificación |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **EXP_R15_Shepard_RnoR_Smooth** | **Shepard Modificado + RnoR Suave (CutOff 2, rad 1.2°)** | **0.3791** | **0.4791** | **12.88** | **-4.39%** | **0.6922** | **0.3038** | **0.3287** | **0.4785** | **0.5007** | **GANADOR (Rank 1)** |
| **2** | **EXP_R12_Shepard_Local_Orn** | Shepard Confinado Local Anti-Cruce (rad 0.9° ~100 km) | 0.3716 | 0.4685 | 13.21 | -3.21% | 0.6731 | 0.2989 | 0.3238 | 0.4735 | 0.4991 | Fase 2 (Rank 2) |
| **3** | **EXP_R08_Shepard_Complex_Relief** | Shepard Relieve Complejo Estándar (rad 1.5°) | 0.3749 | 0.4794 | 12.89 | -6.30% | 0.6650 | 0.3039 | 0.3147 | 0.4638 | 0.4888 | Fase 1 (Rank 3) |
| **4** | **EXP_R11_Shepard_Median_Coarse** | Shepard Mediana Robusta + Malla Gruesa (rad 1.5°) | 0.3753 | 0.4787 | 12.77 | -6.70% | 0.6746 | 0.3037 | 0.3213 | 0.4697 | 0.4885 | Fase 2 (Rank 4) |
| **5** | **EXP_R14_Spheremap_Median** | Spheremap Gran Círculo + Mediana + Malla Gruesa | 0.3621 | 0.4552 | 13.56 | -4.43% | 0.6540 | 0.2971 | 0.3174 | 0.4660 | 0.4863 | Fase 2 (Rank 5) |
| **6** | **EXP_R09_Spheremap_Trans_Caribe** | Spheremap Gran Círculo Estándar (rad 1.5°) | 0.3584 | 0.4584 | 13.59 | -4.59% | 0.6477 | 0.2959 | 0.3132 | 0.4633 | 0.4843 | Fase 1 (Rank 6) |
| **7** | **EXP_R07_Cressman_Spherical** | Cressman Celdas Aisladas (4 pasadas: 1.0° a 0.25°) | 0.3318 | 0.4468 | 14.44 | +3.64% | 0.6299 | 0.3048 | 0.2958 | 0.4436 | 0.4724 | Guía CDT |
| **8** | **EXP_R13_QM_Empirical_ECDF** | Quantile Mapping Empírico No-Paramétrico (qmecdf) | 0.3196 | 0.4655 | 13.08 | -5.57% | 0.6393 | 0.3034 | 0.2995 | 0.4458 | 0.4658 | Fase 2 (Rank 8) |
| **9** | **EXP_R06_Barnes_Gauss_Coastal** | Barnes BSc Gaussiano Costero (NN-3D con DEM) | 0.3087 | 0.4490 | 14.22 | +4.08% | 0.6461 | 0.3098 | 0.2976 | 0.4450 | 0.4635 | Fase 1 (Rank 9) |
| **10** | **EXP_R01_SBA_IDW_Baseline** | Control Nulo / IDW Plano Monocapa (Sin RnoR) | 0.3353 | 0.4861 | 12.22 | -13.53% | 0.6657 | 0.3379 | 0.2743 | 0.4178 | 0.4396 | Línea Base |
| **11** | **EXP_R02_SBA_IDW_RnoR** | SBA IDW 3 pasadas + RnoR (Corte Rígido 0.5 mm) | 0.2631 | 0.4659 | 12.39 | -22.15% | 0.6132 | 0.3153 | 0.2718 | 0.4109 | 0.3743 | Fase 1 (Rank 11) |
| **12** | **EXP_R05_RK_Topography_BW** | Regression Kriging Topográfico (Weibull + DEM) | 0.2147 | 0.4166 | 13.28 | -18.28% | 0.5216 | 0.3673 | 0.2010 | 0.3215 | 0.3463 | Fase 1 (Rank 12) |
| **13** | **EXP_R03_SBA_OKR_BernoulliGamma** | QM Paramétrico Gamma + OKR por Bloques | -0.0277 | 0.4275 | 14.87 | -5.83% | 0.6389 | 0.3484 | 0.2460 | 0.3729 | 0.3231 | Fase 1 (Rank 13) |
| **14** | **EXP_R04_SBA_OKR_BernoulliWeib** | QM Paramétrico Weibull + OKR por Bloques | 0.0159 | 0.4306 | 14.51 | -11.98% | 0.6357 | 0.3479 | 0.2475 | 0.3733 | 0.3148 | Fase 1 (Rank 14) |
| **15** | **EXP_R10_RK_FullTopography_Asp** | RK Máxima Complejidad (DEM + Pendiente + Aspect) | 0.1062 | 0.4112 | 14.11 | -18.36% | 0.5084 | 0.3761 | 0.1901 | 0.3073 | 0.3045 | Fase 1 (Rank 15) |

---

---

### 5.3 Suite B: Temperatura Máxima Diurna ($T_{max}$ CHIRTS / ERA5, 8 Experimentos)
Configurados en [`config/experiments_tmax/`](file:///d:/Workspace/CDT-8.0/config/experiments_tmax):

| ID Exp. | Pasos 1 y 2: Desescalado Topográfico | Paso 3: Compute Bias Coeffs | Paso 4: Apply Bias Correction | Paso 5: Merging Data (Fusión Espacial) | Hipótesis Física y Climatológica Regional |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **`EXP-TX01`** | **[P1]** Coefs: Geométrico neutro.<br>**[P2]** Downscale: Bilineal (`blin`) a $0.05^\circ$ sin DEM. Salida: `tmax_down_%s%s%s.nc`. | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: IDW ($p=2.0$, radio $3.5^\circ$, $nmin=4, nmax=12$) | • Ajuste multiplicativo sobre grillas desescaladas 1991–2020.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: SBA monocapa (1 pasada a $1.0^\circ$)<br>• Interp: IDW ($3.5^\circ$)<br>• Covariables: Ninguna | **Control Nulo Térmico Diurno:** Cuantifica el error sistemático al ignorar el relieve y la insolación solar diurna. |
| **`EXP-TX02`** | **[P1]** Coefs: Regresión mensual estación–DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM 90m ($0.05^\circ$). | • Método: `qmdist`<br>• Distribución: **Normal (`norm`)**<br>• Interp: IDW ($3.5^\circ$) | • Mapeo de cuantiles gaussiano.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **Regression Kriging (RK)** (3 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• **Covariables: DEM (Elevación)**<br>• Interp. residuales: OKR (Sph/Exp/Gau/Pen) | **Gradiente Adiabático Ambiental Diurno:** Modela el enfriamiento por ascenso adiabático ($\Gamma \approx -6.5\ ^\circ\text{C}/\text{km}$) en la Cordillera Central de RD y la Sierra Madre. |
| **`EXP-TX03`** | **[P1]** Coefs: Regresión DEM + Pendiente.<br>**[P2]** Downscale: IDW local sobre DEM SRTM. | • Método: `qmdist`<br>• Distribución: **Skew-Normal (`snorm`)**<br>• Interp: OKR por bloques ($3.5^\circ$) | • Mapeo de cuantiles asimétrico.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas multiescala)<br>• **Covariables: DEM + Pendiente + Lat + Lon**<br>• Interp. residuales: OKR por bloques | **Asimetría Térmica por Laderas y Frentes Fríos:** Captura la asimetría diurna inducida por inclinación del terreno y descensos térmicos transitorios por frentes fríos (*Nortes*). |
| **`EXP-TX04`** | **[P1]** Coefs: Desescalado orográfico 3D.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: **NN-3D con DEM ($\Delta z$)** | • Ajuste de sesgo con control altimétrico vertical.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas multiescala)<br>• **Covariables: DEM + Pendiente + Orientación (Aspect)**<br>• Interp: OKR | **Insolación Diurna Diferencial según Orientación:** Laderas orientadas al este reciben calentamiento matutino rápido; laderas al oeste acumulan el máximo vespertino. |
| **`EXP-TX05`** | **[P1]** Coefs: Regresión mensual altimétrica.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `qmdist`<br>• Distribución: **Gumbel Máximos (`gumbel`)**<br>• Interp: OKR por bloques | • Mapeo cuantil para valores extremos ($>P95$).<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas)<br>• **Covariables: DEM + Latitud + Longitud**<br>• Interp: OKR por bloques | **Olas de Calor en Depresiones Áridas:** Ajusta picos extremos ($>38\ ^\circ\text{C}\text{ a }40\ ^\circ\text{C}$) en la Hoya de Enriquillo ($-40\text{ msnm}$), Valle de Azua y Golfo de Fonseca. |
| **`EXP-TX06`** | **[P1]** Coefs: Regresión regional con DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: IDW ($3.5^\circ$) | • Ajuste proporcional estándar.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **Barnes (BSc)** (3 pasadas gaussianas)<br>• Interp. residuales: Filtro gaussiano continuo<br>• Covariables: Ninguna | **Llanuras y Brisas Costeras Diurnas:** Transición espacial continua sin saltos abruptos a lo largo de llanuras litorales del Caribe y planicies de RD. |
| **`EXP-TX07`** | **[P1]** Coefs: Regresión altimétrica con DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `mbmon` (sesgo medio mensual fijo)<br>• Interp: IDW ($3.5^\circ$) | • Ajuste por mes climatológico.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **Cressman (CSc)** (4 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ, 0.25^\circ$)<br>• Covariables: Ninguna | **Valles Intermontanos Confinados:** Envolventes de radio decreciente para evitar que estaciones cálidas de valles profundos contaminen laderas altas vecinas. |
| **`EXP-TX08`** | **[P1]** Coefs: Multivariado DEM + Slope + Aspect.<br>**[P2]** Downscale: Proyección topográfica completa. | • Método: `qmdist`<br>• Distribución: Skew-Normal (`snorm`)<br>• Interp: OKR por bloques | • Corrección distribucional con asimetría.<br>• Salida: `tmax_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas)<br>• **Covariables: DEM + Pendiente + Aspect + Lat + Lon**<br>• Interp: OKR por bloques | **Máxima Complejidad Diurna:** Acoplamiento determinístico completo de topografía, insolación solar y modelación asimétrica de residuales. |

---

### 5.4 Suite C: Temperatura Mínima Nocturna ($T_{min}$ CHIRTS / ERA5, 8 Experimentos)
Configurados en [`config/experiments_tmin/`](file:///d:/Workspace/CDT-8.0/config/experiments_tmin):

| ID Exp. | Pasos 1 y 2: Desescalado Topográfico | Paso 3: Compute Bias Coeffs | Paso 4: Apply Bias Correction | Paso 5: Merging Data (Fusión Espacial) | Hipótesis Física y Climatológica Regional |
| :---: | :--- | :--- | :--- | :--- | :--- |
| **`EXP-TN01`** | **[P1]** Coefs: Geométrico neutro.<br>**[P2]** Downscale: Bilineal a $0.05^\circ$ sin DEM. Salida: `tmin_down_%s%s%s.nc`. | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: IDW ($p=2.0$, radio $3.5^\circ$) | • Ajuste sobre grillas desescaladas 1991–2020.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: SBA monocapa (1 pasada a $1.0^\circ$)<br>• Interp: IDW ($3.5^\circ$)<br>• Covariables: Ninguna | **Control Nulo Nocturno:** Mide el sesgo nocturno base al ignorar el enfriamiento radiativo y el drenaje de aire frío. |
| **`EXP-TN02`** | **[P1]** Coefs: Regresión mensual estación–DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM 90m ($0.05^\circ$). | • Método: `qmdist`<br>• Distribución: **Normal (`norm`)**<br>• Interp: IDW ($3.5^\circ$) | • Mapeo de cuantiles gaussiano.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ$)<br>• **Covariables: DEM (Elevación)**<br>• Interp. residuales: OKR (Sph/Exp/Gau/Pen) | **Gradiente Térmico Nocturno Ambiental:** Modela la tasa vertical nocturna estándar en zonas abiertas sin inversión térmica marcada. |
| **`EXP-TN03`** | **[P1]** Coefs: Regresión DEM + Pendiente.<br>**[P2]** Downscale: IDW local sobre DEM SRTM. | • Método: `qmdist`<br>• Distribución: **Skew-Normal (`snorm`)**<br>• Interp: OKR por bloques ($3.5^\circ$) | • Mapeo cuantil con asimetría en cola fría.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas multiescala)<br>• **Covariables: DEM + Pendiente + Lat + Lon**<br>• Interp: OKR por bloques | **Invasiones de Frentes Fríos Invernales (*Nortes*):** Captura las caídas abruptas y asimétricas de temperatura en la vertiente Atlántica durante el invierno boreal. |
| **`EXP-TN04`** | **[P1]** Coefs: Desescalado orográfico 3D.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: **NN-3D con elevación DEM ($\Delta z$)** | • Ajuste con aislamiento vertical estricto.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas)<br>• **Covariables: DEM + Pendiente + Lat + Lon**<br>• Interp: OKR por bloques | **Inversiones Térmicas Nocturnas (*Cold-Air Pooling*):** Evita la contaminación térmica entre cimas cálidas y valles altos fríos (ej. Constanza y Valle Nuevo en RD, Quetzaltenango en GT). |
| **`EXP-TN05`** | **[P1]** Coefs: Regresión altimétrica con DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `qmdist`<br>• Distribución: **Gumbel Mínimos (`gumbel`)**<br>• Interp: OKR por bloques | • Mapeo cuantil para colas frías extremas ($< \text{P}_{05}$).<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas)<br>• **Covariables: DEM + Latitud + Longitud**<br>• Interp: OKR por bloques | **Heladas Agronómicas y Extremos Bajo Cero:** Modela eventos de temperaturas mínimas extremas ($< 0\ ^\circ\text{C}$) en altiplanos y cumbres montañosas elevadas. |
| **`EXP-TN06`** | **[P1]** Coefs: Regresión regional con DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `mbvar` ($\pm 5$ d)<br>• Interp: IDW ($3.5^\circ$) | • Ajuste proporcional estándar.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **Barnes (BSc)** (3 pasadas gaussianas)<br>• Interp. residuales: Ponderación gaussiana<br>• Covariables: Ninguna | **Amortiguamiento Marino y Llanuras Homogéneas:** Representa el efecto regulador térmico del océano en costas caribeñas y valles aluviales amplios. |
| **`EXP-TN07`** | **[P1]** Coefs: Regresión altimétrica con DEM.<br>**[P2]** Downscale: Bilineal sobre DEM SRTM. | • Método: `mbmon` (sesgo medio mensual fijo)<br>• Interp: IDW ($3.5^\circ$) | • Corrección mensual estacional.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **Cressman (CSc)** (4 pasadas: $1.0^\circ, 0.75^\circ, 0.5^\circ, 0.25^\circ$)<br>• Covariables: Ninguna | **Pozas de Aire Frío Confinadas:** Radios de búsqueda decrecientes para evitar disipar el aire frío estancado en depresiones hacia cordilleras adyacentes. |
| **`EXP-TN08`** | **[P1]** Coefs: Multivariado DEM + Slope + Aspect.<br>**[P2]** Downscale: Proyección topográfica completa. | • Método: `qmdist`<br>• Distribución: Skew-Normal (`snorm`)<br>• Interp: **NN-3D con DEM ($\Delta z$)** | • Corrección distribucional con restricción vertical $\Delta z$.<br>• Salida: `tmin_adj_%s%s%s.nc` | • Método: **RK** (3 pasadas)<br>• **Covariables: DEM + Pendiente + Aspect + Lat + Lon**<br>• Interp: OKR por bloques | **Máxima Complejidad Nocturna:** Acoplamiento total de drenaje catabático gravitacional en laderas inclinadas y formación de pozas frías en valles cerrados. |

---

## 6. Esquema de Validación Cruzada Independiente (Holdout por CSV) y Métricas Cuantitativas

### 6.1 Mecanismo de Evaluación de CDT y Partición Ciega (Holdout Validation)

El software **Climate Data Tools (CDT)** provee funcionalidades para validación cruzada y evaluación estadística de campos interpolados contra datos de estación. En nuestro marco metodológico automatizado, para garantizar una evaluación **estrictamente independiente, ciega e insesgada** (evitando el sobreajuste o *overfitting* de evaluar un modelo con las mismas estaciones que fueron asimiladas para calibrar sus parámetros), el orquestador (`launcher/station_manager.py`) desacopla el conjunto observacional en dos subconjuntos disjuntos antes de iniciar cualquier procesamiento:

```
[ Red Total de Estaciones de Superficie (1991–2020) ]
                       │
       ┌───────────────┴───────────────────────────────┐
       ▼                                               ▼
[ Subconjunto de Entrenamiento (~80–90%) ]   [ Subconjunto de Validación Ciega (~10–20%) ]
       │                                               │
       ▼                                               │ (Completamente invisible para CDT;
[ Flujo de Procesamiento en CDT ]                     │  no se usa en sesgo ni en interpolación)
  • Paso 1: Cálculo de Coeficientes de Sesgo            │
  • Paso 2: Corrección Distribucional sobre CHIRPS      │
  • Paso 3 / Paso 5: Fusión Geoestadística (SBA/RK)    │
       │                                               │
       ▼                                               │
[ Grillas Diarias Fusionadas NetCDF 1991–2020 ]         │
       │                                               │
       ▼                                               │
[ Ensamblado NetCDF 3D Multitemporal CF-1.8 ]          │
       │                                               │
       └───────────────────────┬───────────────────────┘
                               ▼
            [ Extracción Puntual en Coordenadas (lon, lat) ]
                               │
                               ▼
        [ Evaluación Cuantitativa de Pares Sincronizados (S_t, O_t) ]
          • Métricas Continuas: KGE, r, RMSE, MAE, PBIAS
          • Métricas Categóricas (Lluvia ≥ 1.0 mm/d): POD, FAR, FBI, ETS, HSS
```

1. **Partición Automática por CSV (`holdout_stations_file`):** El usuario define un archivo CSV con los códigos de las estaciones destinadas exclusivamente al test ciego (en este benchmark, 29 estaciones distribuidas de forma representativa a lo largo del gradiente fisiográfico de Centroamérica y República Dominicana).
2. **Aislamiento en CDT:** CDT procesa la serie temporal histórica (10,958 días) asimilando únicamente las estaciones de entrenamiento. Las 29 estaciones de validación permanecen totalmente ausentes de las matrices de calibración y variogramas.
3. **Extracción Post-NetCDF y Sincronización:** Una vez consolidados los campos grillados diarios en el archivo 3D multitemporal conforme al estándar CF-1.8, el evaluador extrae mediante interpolación bilineal/celda más cercana el valor modelado $S_t$ en la coordenada geográfica exacta $(\lambda, \phi)$ de cada estación retenida y lo empareja día a día contra la observación de superficie $O_t$.

---

### 6.2 Métricas Continuas (Magnitud, Dispersión y Distribución del Error)

Las métricas continuas evalúan cuantitativamente la capacidad del producto grillado para reproducir la magnitud, la varianza y la sincronía temporal de las series observadas:

| Métrica | Ecuación Matemática | Qué Cuantifica y Rango Óptimo | Interpretación Física y Climatológica Regional |
| :---: | :--- | :--- | :--- |
| **KGE**<br>*(Kling-Gupta Efficiency)*<br>(Gupta et al., 2009) | $\text{KGE} = 1 - \sqrt{(r - 1)^2 + (\beta - 1)^2 + (\gamma - 1)^2}$<br>donde:<br>• $\beta = \frac{\mu_S}{\mu_O}$ (sesgo medio relativo)<br>• $\gamma = \frac{\text{CV}_S}{\text{CV}_O} = \frac{\sigma_S / \mu_S}{\sigma_O / \mu_O}$ (variabilidad relativa) | Descompone de forma integrada y ortogonal el desempeño en 3 componentes esenciales: dinámica temporal ($r$), sesgo volumétrico ($\beta$) y dispersión relativa ($\gamma$).<br>**Rango:** $(-\infty, 1]$.<br>**Valor Óptimo:** $1.0$.<br>*(Un $\text{KGE} > 0.3$ a escala diaria demuestra habilidad predictiva real respecto a la climatología media).* | **Métrica rectora multiobjetivo:** Evita las distorsiones del coeficiente de Nash-Sutcliffe (NSE) o del RMSE puro, que premian modelos que subestiman la variabilidad natural o que sobreponderan eventos aislados. Garantiza que la reconstrucción climática respete tanto los extremos convectivos como el régimen de estiaje. |
| **$r$**<br>*(Correlación de Pearson)* | $r = \frac{\sum_{i=1}^N (S_i - \bar{S})(O_i - \bar{O})}{\sqrt{\sum_{i=1}^N (S_i - \bar{S})^2 \sum_{i=1}^N (O_i - \bar{O})^2}}$ | Cuantifica la covariación lineal y la sincronía temporal de fases de la señal climática entre modelo y estaciones.<br>**Rango:** $[-1, 1]$.<br>**Valor Óptimo:** $1.0$. | **Sincronía sinóptica:** Evalúa la destreza del producto satelital para captar el paso de perturbaciones sinópticas (ondas del este, ciclones tropicales, giros centroamericanos y frentes fríos *Nortes*) y la estacionalidad bimodal de la lluvia, independientemente de sesgos sistemáticos en magnitud. |
| **RMSE**<br>*(Root Mean Square Error)* | $\text{RMSE} = \sqrt{\frac{1}{N}\sum_{i=1}^N (S_i - O_i)^2}$ | Mide la magnitud media cuadrática del error residual, expresada en las unidades físicas de la variable ($\text{mm/día}$ o $^\circ\text{C}$).<br>**Rango:** $[0, \infty)$.<br>**Valor Óptimo:** $0.0$. | **Sensibilidad a eventos extremos:** Al elevar los residuales al cuadrado, penaliza desproporcionadamente las discrepancias grandes. Resulta clave para identificar fallos graves en tormentas convectivas severas ($>100\text{ mm/día}$) u olas de calor diurnas ($>38\ ^\circ\text{C}$). |
| **MAE**<br>*(Mean Absolute Error)* | $\text{MAE} = \frac{1}{N}\sum_{i=1}^N \lvert S_i - O_i \rvert$ | Mide la magnitud lineal promedio de los residuales absolutos en las mismas unidades físicas ($\text{mm/día}$ o $^\circ\text{C}$).<br>**Rango:** $[0, \infty)$.<br>**Valor Óptimo:** $0.0$. | **Magnitud típica esperada del error:** Representa la discrepancia promedio esperada en un día común. Es una métrica robusta que no se ve sobredimensionada por eventos atípicos (*outliers*), reflejando el error de base en condiciones operativas estándar. |
| **PBIAS**<br>*(Percent Bias)* | $\text{PBIAS} = \frac{\sum_{i=1}^N (S_i - O_i)}{\sum_{i=1}^N O_i} \times 100\%$ | Cuantifica la desviación porcentual neta acumulada entre el volumen estimado por el producto grillado y el volumen observado.<br>**Rango:** $(-\infty, \infty)\%$.<br>**Valor Óptimo:** $0.0\%$. | **Conservación de masa y balance hídrico:** Determina si el producto tiende a la sobreestimación sistemática ($\text{PBIAS} > 0$) o subestimación ($\text{PBIAS} < 0$). Es crucial en estudios hidrológicos de balance hídrico para no falsear el rendimiento hídrico anual de las cuencas. |

---

### 6.3 Métricas Categóricas y Detección de Lluvia ($\ge 1.0\text{ mm/día}$)

Para precipitación, la ocurrencia o no de lluvia es una variable discreta fundamental. Se evalúa mediante una **tabla de contingencia $2 \times 2$** aplicando el umbral estándar de lluvia medible ($wet \ge 1.0\text{ mm/día}$):

```
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┐
│                                 │ Observación: LLUVIA (O ≥ 1.0 mm)│ Observación: SECO (O < 1.0 mm)  │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┤
│ Satélite: LLUVIA (S ≥ 1.0 mm)   │ Acierto / Hit (a)               │ Falsa Alarma / False Alarm (b)  │
│ Satélite: SECO (S < 1.0 mm)     │ Fallo / Miss (c)                │ Negativo Correcto (d)           │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┘
                                Total de Días Evaluados: n = a + b + c + d
```

| Métrica | Ecuación Matemática | Qué Cuantifica y Rango Óptimo | Interpretación Física y Climatológica Regional |
| :---: | :--- | :--- | :--- |
| **POD**<br>*(Probability of Detection / Hit Rate)* | $\text{POD} = \frac{a}{a + c}$ | Fracción de días lluviosos observados que fueron detectados exitosamente por el producto grillado.<br>**Rango:** $[0, 1]$.<br>**Valor Óptimo:** $1.0$. | **Capacidad de detección:** Mide la sensibilidad del producto para registrar la precipitación real sin perder días húmedos relevantes para la agricultura de secano o la recarga de acuíferos. |
| **FAR**<br>*(False Alarm Ratio)* | $\text{FAR} = \frac{b}{a + b}$ | Proporción de días en los que el satélite reportó lluvia pero en realidad se registró día seco en superficie.<br>**Rango:** $[0, 1]$.<br>**Valor Óptimo:** $0.0$. | **Control de lloviznas espurias (*Drizzle Effect*):** Cuantifica directamente el impacto de la reflectividad infrarroja de cirros fríos no precipitantes. Es la métrica clave para verificar la eficacia de la máscara RnoR durante la Canícula. |
| **FBI**<br>*(Frequency Bias Index)* | $\text{FBI} = \frac{a + b}{a + c}$ | Razón directa entre el número total de días lluviosos simulados por el satélite frente a los observados.<br>**Rango:** $[0, \infty)$.<br>**Valor Óptimo:** $1.0$. | **Sesgo de frecuencia de eventos:** $\text{FBI} > 1$ denota una sobreestimación crónica en la frecuencia de eventos (llueve con más frecuencia de la real en el modelo); $\text{FBI} < 1$ indica déficit sistemático en la cantidad de días con lluvia. |
| **ETS**<br>*(Equitable Threat Score / Gilbert Skill Score)* | $\text{ETS} = \frac{a - a_r}{a + b + c - a_r}$<br>donde:<br>$a_r = \frac{(a+b)(a+c)}{n}$ | Capacidad de acierto categórico penalizando tanto falsas alarmas ($b$) como omisiones ($c$), descontando los aciertos que ocurrirían por puro azar climatológico ($a_r$).<br>**Rango:** $[-1/3, 1]$.<br>**Valor Óptimo:** $1.0$.<br>*(Valores $> 0$ certifican habilidad genuina).* | **Destreza equitativa sobre el azar:** Métrica meteorológica estándar que no es vulnerable al sesgo de frecuencia. Excluye aciertos fortuitos debidos a la alta frecuencia de lluvia en climas tropicales húmedos, aislando el valor real agregado por la fusión. |
| **HSS**<br>*(Heidke Skill Score)* | $\text{HSS} = \frac{2(ad - bc)}{(a+c)(c+d) + (a+b)(b+d)}$ | Exactitud de clasificación binaria integral (lluvia / no-lluvia) considerando todos los cuadrantes ($a, b, c, d$), en relación a una predicción aleatoria no correlacionada.<br>**Rango:** $(-\infty, 1]$.<br>**Valor Óptimo:** $1.0$. | **Habilidad categórica global:** Evalúa de forma simultánea el acierto en días secos (rachas sin lluvia en el Corredor Seco y valles de sombra orográfica) y en días húmedos. Premia a los modelos que delimitan nítidamente el inicio y término de la Canícula. |

---

## 7. Rendimiento de Hardware y Modo de Uso del Lanzador en Python

### Evaluación y Calibración en Workstation Linux Ubuntu (18 Núcleos Paralelos, 32 GB RAM DDR4, SSD NVMe 400 GB):

* **Sistema Operativo:** Linux Ubuntu 24.04.5 LTS (x86_64, Kernel nativo)
* **Procesador (CPU):** Intel(R) Core(TM) i9-10850K CPU @ 3.60GHz (10 núcleos físicos / 20 hilos, Frecuencia base 3.60 GHz, Turbo Boost hasta 5.20 GHz, Caché L3 de 20 MB)
* **Memoria RAM:** 32 GB DDR4 @ 3200 MT/s (Dual-Channel)
* **Almacenamiento:** SSD NVMe M.2 PCIe de 400 GB (> 3,000 MB/s lectura/escritura)

| Suite de Experimentos | Núm. Exp. | Días / Exp. | Rango Tiempo por Exp. | Tiempo Total Suite | Consumo RAM Máx. |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precipitación (CHIRPS)** | 15 (Fase 1 y 2) | 10,958 | 1.1 h (IDW/Shepard) a 3.8 h (Block OKR) | **~35.0 – 38.0 horas** | 2.5 – 4.5 GB |
| **Temperatura Máxima ($T_{max}$)** | 8 | 10,958 | 1.2 h (IDW) a 2.3 h (RK DEM) | **~14.0 – 15.0 horas** | 3.5 – 4.6 GB |
| **Temperatura Mínima ($T_{min}$)** | 8 | 10,958 | 1.2 h (IDW) a 2.3 h (RK DEM) | **~14.0 – 15.0 horas** | 3.5 – 4.6 GB |
| **TOTAL GENERAL 31 EXPERIMENTOS** | **31** | **10,958** | — | **~63.0 – 68.0 horas** | **Máx. 4.6 GB (< 15% RAM)** |

> [!NOTE]
> **Diferenciación de Carga Computacional y Optimización Vectorizada:**
> - **Interpolaciones algebraicas (IDW, Barnes, Shepard):** Evalúan funciones analíticas directas ($O(N)$), completando 30 años en ~1.1 a 2.2 horas.
> - **Regression Kriging en Temperatura con DEM:** No utiliza máscara binomial de lluvia, completando cada experimento en ~1.8 a 2.3 horas.
> - **Kriging Ordinario por Bloques con Máscara Logística (Lluvia):** Al tener `use_block: true` y `RnoR: logit`, ejecuta 2 procesos de Kriging por cada una de las 3 pasadas diarias (6 Krigings por día con integración numérica 2D), requiriendo ~3.8 a 4.2 horas.
> - **Optimización en Quantile Mapping Empírico (`EXP_R13`):** Se vectorizó la evaluación de cuantiles mediante interpolación continua sobre `stats::knots()`, logrando una aceleración de 100x en el Paso 2 (de >30 h a 12 minutos), preservando precisión numérica exacta ($0.0$ de discrepancia).

### Formato de Salida y Monitoreo de Tiempos:
El orquestador (`launcher/experiment_runner.py`) implementa la utilidad `format_duration()` que presenta los tiempos de ejecución en formato legible de horas, minutos y segundos:
- Al terminar cada corrida: `>>> [OK] EXP_R15_Shepard_RnoR_Smooth completado con estado SUCCESS en 1h 48m 22s (6502.15s)`.
- En la tabla resumen: columna `Tiempo` formateada y pie con el `TIEMPO TOTAL ACUMULADO DE LA SUITE`.
- En el archivo `manifest.json`: se preserva `execution_time_sec` (numérico) y se añade `execution_time_formatted`.

### Comandos de Ejecución CLI (`launcher/experiment_runner.py`):

```bash
# Diagnóstico de dependencias
python launcher/experiment_runner.py --check-env

# Ejecutar suites completas (Workstation Ubuntu con 18 núcleos)
python launcher/experiment_runner.py --suite rainfall --cores 18   # 15 Exp. Lluvia (~35-38 h)
python launcher/experiment_runner.py --suite tmax     --cores 18   # 8 Exp. Tmax (~14-15 h)
python launcher/experiment_runner.py --suite tmin     --cores 18   # 8 Exp. Tmin (~14-15 h)

# Ejecutar corrida batch completa de los 31 experimentos
python launcher/experiment_runner.py --suite all      --cores 18   # 31 Exp. (~63-68 h continuas)

# Ejecutar un experimento individual parametrizado
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R15_Shepard_RnoR_Smooth.yaml --cores 18
```

### Ejecución Desatendida en Segundo Plano (`nohup` en Linux / WSL / Servidores):

Para corridas prolongadas (~60 h), lance el proceso desacoplado de la terminal, limpiando `DISPLAY` (para evitar el error `connect localhost port 6000: Connection refused` de `tcltk`/X11) y con `python -u` (para registrar logs en tiempo real sin almacenamiento en búfer):

```bash
# Lanzar la corrida completa en segundo plano:
DISPLAY= nohup python -u launcher/experiment_runner.py --suite all --cores 18 > corrida_completa.log 2>&1 &

# Inspección del avance en tiempo real:
tail -f corrida_completa.log
```

> **Tolerancia a Fallos y Reanudación:** El orquestador implementa comprobación diaria de archivos ya generados. Si el proceso se detiene o el servidor se reinicia, relanzar el comando continuará exactamente desde el día pendiente sin reprocesar días previos. Para forzar la reescritura total, use `--force`.

---

## 8. Referencias Bibliográficas Científicas Verificadas

1. **Amador, J. A., Alfaro, E. J., Lizano, O. G., & Magaña, V. O. (2006).** *Atmospheric forcing of the eastern tropical Pacific: A review.* Progress in Oceanography, 69(2–4), 101–142. DOI: [10.1016/j.pocean.2006.03.007](https://doi.org/10.1016/j.pocean.2006.03.007)
2. **Barnes, S. L. (1964).** *A technique for maximizing details in numerical weather map analysis.* Journal of Applied Meteorology, 3(4), 396–409. DOI: [10.1175/1520-0450(1964)003&lt;0396:ATFMDI&gt;2.0.CO;2](https://doi.org/10.1175/1520-0450(1964)003%3C0396:ATFMDI%3E2.0.CO;2)
3. **Coles, S. (2001).** *An Introduction to Statistical Modeling of Extreme Values.* Springer-Verlag, London. DOI: [10.1007/978-1-4471-3675-0](https://doi.org/10.1007/978-1-4471-3675-0)
4. **Cressman, G. P. (1959).** *An operational objective analysis system.* Monthly Weather Review, 87(10), 367–374. DOI: [10.1175/1520-0493(1959)087&lt;0367:AOOAS&gt;2.0.CO;2](https://doi.org/10.1175/1520-0493(1959)087%3C0367:AOOAS%3E2.0.CO;2)
5. **Daly, C., Halbleib, M., Smith, J. I., Gibson, W. P., Doggett, M. K., Taylor, G. H., Curtis, J., & Pasteris, P. P. (2008).** *Physiographically sensitive mapping of temperature and precipitation across the conterminous United States.* International Journal of Climatology, 28(15), 2031–2064. DOI: [10.1002/joc.1688](https://doi.org/10.1002/joc.1688)
6. **Dinku, T., Thomson, M. C., Cousin, R., del Corral, J., Ceccato, P., Hansen, J., & Connor, S. J. (2018).** *Enhancing National Climate Services (ENACTS) for development in Africa.* Climate and Development, 10(7), 664–672. DOI: [10.1080/17565529.2017.1405784](https://doi.org/10.1080/17565529.2017.1405784)
7. **Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., Husak, G., Rowland, J., Harrison, L., Hoell, A., & Michaelsen, J. (2015).** *The climate hazards group infrared precipitation with stations—a new environmental record for monitoring extremes.* Scientific Data, 2(1), 150066. DOI: [10.1038/sdata.2015.66](https://doi.org/10.1038/sdata.2015.66)
8. **Verdin, A., Funk, C., Peterson, P., Landsfeld, M., Tuholske, C., & Grace, K. (2020).** *Development and validation of the CHIRTS-daily quasi-global high-resolution daily temperature data set.* Scientific Data, 7(1), 303. DOI: [10.1038/s41597-020-00643-7](https://doi.org/10.1038/s41597-020-00643-7)
9. **Gudmundsson, L., Bremnes, J. B., Haugen, J. E., & Engen-Skaugen, T. (2012).** *Downscaling RCM precipitation to the scale using statistical transformations–a comparison of methods.* Hydrology and Earth System Sciences, 16(9), 3383–3390. DOI: [10.5194/hess-16-3383-2012](https://doi.org/10.5194/hess-16-3383-2012)
10. **Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).** *Decomposition of the mean squared error and NSE performance measures: Implications for improving hydrological modelling.* Journal of Hydrology, 377(1-2), 80–91. DOI: [10.1016/j.jhydrol.2009.08.003](https://doi.org/10.1016/j.jhydrol.2009.08.003)
11. **Hastenrath, S. (1967).** *Rainfall distribution and regime in Central America.* Archiv für Meteorologie, Geophysik und Bioklimatologie, Serie B, 15(3), 201–241. DOI: [10.1007/BF02243853](https://doi.org/10.1007/BF02243853)
12. **Hastenrath, S. (1991).** *Climate Dynamics of the Tropics.* Atmospheric and Oceanographic Sciences Library, Vol. 8. Springer, Dordrecht. DOI: [10.1007/978-94-011-3156-8](https://doi.org/10.1007/978-94-011-3156-8)
13. **Hengl, T., Heuvelink, G. B., & Rossiter, D. G. (2007).** *About regression-kriging: From equations to case studies.* Computers & Geosciences, 33(10), 1301–1315. DOI: [10.1016/j.cageo.2007.05.001](https://doi.org/10.1016/j.cageo.2007.05.001)
14. **Hidalgo, H. G., Alfaro, E. J., & Quesada-Montano, B. (2017).** *Observed (1970–1999) climate variability in Central America using a high-resolution meteorological dataset with implication to climate change studies.* Climatic Change, 141(1), 13–28. DOI: [10.1007/s10584-016-1786-y](https://doi.org/10.1007/s10584-016-1786-y)
15. **Kedem, B., Chiu, L. S., & North, G. R. (1990).** *Estimation of mean rain rate: Application to satellite observations.* Journal of Geophysical Research: Atmospheres, 95(D2), 1965–1972. DOI: [10.1029/JD095iD02p01965](https://doi.org/10.1029/JD095iD02p01965)
16. **Maldonado, T., Rutgersson, A., Amador, J. A., Alfaro, E. J., & Claremar, B. (2016).** *Variability of the Caribbean low-level jet during boreal winter: large-scale forcings.* International Journal of Climatology, 36(4), 1978–1999. DOI: [10.1002/joc.4472](https://doi.org/10.1002/joc.4472)
17. **Schultz, D. M., Bracken, W. E., & Bosart, L. F. (1998).** *Planetary- and synoptic-scale signatures associated with Central American cold surges.* Monthly Weather Review, 126(1), 5–27. DOI: [10.1175/1520-0493(1998)126&lt;0005:PASSSA&gt;2.0.CO;2](https://doi.org/10.1175/1520-0493(1998)126%3C0005:PASSSA%3E2.0.CO;2)
18. **Shepard, D. (1968).** *A two-dimensional interpolation function for irregularly-spaced data.* Proceedings of the 1968 23rd ACM National Conference, 517–524. DOI: [10.1145/800186.810616](https://doi.org/10.1145/800186.810616)
19. **Themeßl, M. J., Gobiet, A., & Leuprecht, A. (2011).** *Empirical-statistical downscaling and error correction of daily precipitation from regional climate models.* International Journal of Climatology, 31(10), 1530–1544. DOI: [10.1002/joc.2168](https://doi.org/10.1002/joc.2168)
20. **Willmott, C. J., Rowe, C. M., & Philpot, W. D. (1985).** *Small-scale climate maps: A sensitivity analysis of some common assumptions associated with grid-point interpolation and contouring.* The American Cartographer, 12(1), 5–16. DOI: [10.1559/152304085783914686](https://doi.org/10.1559/152304085783914686)
21. **WMO / CF Metadata Conventions Committee (2020).** *NetCDF Climate and Forecast (CF) Metadata Conventions Version 1.8.* World Meteorological Organization. URL: [https://cfconventions.org/](https://cfconventions.org/)
