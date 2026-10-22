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
   - **Falta de resolución de inversiones térmicas nocturnas y drenaje catabático:** Durante la noche, el enfriamiento radiativo provoca el drenaje de aire denso y frío (*cold-air pooling*) hacia el fondo de valles intramontanos cerrados (Constanza y Valle Nuevo en RD, Quetzaltenango en Guatemala), registrándose heladas y temperaturas bajo cero ($< 0\ ^\circ\text{C}$), mientras que las cumbres adyacentes permanecen más cálidas (inversión térmica). Los modelos globales no resuelven este desacople sin ponderación vertical estricta ($\Delta z$).
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

## 5. Matriz de 26 Experimentos: Tablas con Justificación Física Celda por Celda y Flujo por Pasos

### 5.1 Arquitectura de Flujo Secuencial por Pasos en CDT y Justificación Climatológica

La metodología de fusión en CDT se estructura en etapas analíticas secuenciales independientes que permiten aislar y evaluar rigurosamente el impacto de cada técnica en el modelado climático:

#### Cadena de Procesamiento para Precipitación (3 Etapas en CDT)
*CDT Menú: Gridding > Merging Climate Data > Rainfall Data*

| Paso | Acción en CDT | Opciones / Parámetros que se varían | Justificación Física y Climatológica Regional |
| :--- | :--- | :--- | :--- |
| **Paso 1: Compute Bias Coefficients**<br>*(Cálculo de Coeficientes de Sesgo)* | Modela estadísticamente las discrepancias espaciales y distribucionales entre satélite y estaciones. | • Método: Multiplicativo móvil (`mbvar`), Mensual (`mbmon`), Quantile Mapping con distribución (`qmdist`), QM empírico (`qmecdf`).<br>• Distribuciones: Bernoulli-Gamma, Bernoulli-Weibull, Bernoulli-LogNormal.<br>• Interpolación de coeficientes: IDW ($p=2$), Kriging Ordinario (`okr`), Kriging por bloques (`use_block`).<br>• Umbral de lluvia: $wet=1.0\text{ mm}$. | La lluvia tropical presenta alta variabilidad por convección de mesoescala y forzamiento orográfico. CHIRPS tiende a sobreestimar lloviznas y subestimar eventos convectivos severos. Modelar la ocurrencia (Bernoulli) y la magnitud (Gamma/Weibull) con Kriging por bloques remueve el sesgo distribucional sin crear "ojos de buey" (*bulls-eyes*). |
| **Paso 2: Apply Bias Correction**<br>*(Aplicación del Ajuste de Sesgo)* | Transforma las 10,958 grillas diarias de satélite aplicando los coeficientes calculados. | • Rango temporal: 1991–2020 continuo.<br>• Archivo `.rds` de parámetros del Paso 1.<br>• Formato de salida: `rr_adj_%s%s%s.nc`. | Garantiza que las propiedades distribucionales y los extremos de la serie satelital completa queden calibrados contra las estaciones de superficie antes de intentar cualquier asimilación puntual, preservando la textura sinóptica. |
| **Paso 3: Merging Data**<br>*(Fusión Espacial de Datos)* | Combina las grillas satelitales corregidas (*first guess*) con las observaciones de estaciones. | • Método de fusión: Spatio-Temporal Bias Adjustment (SBA), Cressman, Barnes, Regression Kriging (RK).<br>• Pasadas multiescala (`nrun = 3`, radios decrecientes: $1.0^\circ, 0.75^\circ, 0.5^\circ$).<br>• Máscara Lluvia/No-Lluvia (RnoR: `use`, `wet`, `smooth`).<br>• Covariables: DEM, pendiente, orientación (*aspect*), lat/lon.<br>• Máscara de recorte espacial (shapefile con buffer de 10 km). | En zonas semiáridas (Corredor Seco y Azua), propagar lluvia a celdas secas genera lluvia irreal; la máscara RnoR preserva las rachas secas de la Canícula. Las pasadas multiescala corrigen sesgos regionales y ajustan la señal convectiva local en puntos de estación. |

#### Cadena de Procesamiento para Temperatura (5 Etapas en CDT)
*CDT Menú: Gridding > Merging Climate Data > Temperatures Data*

| Paso | Acción en CDT | Opciones / Parámetros que se varían | Justificación Física y Climatológica Regional |
| :--- | :--- | :--- | :--- |
| **Paso 1: Compute Downscaling Coefficients**<br>*(Cálculo de Coefs. de Desescalado)* | Modela el gradiente térmico vertical (*lapse rate*) estación-elevación. | • Paso temporal (diario, mensual, estacional).<br>• DEM de alta resolución (SRTM / GEBCO).<br>• Formato de coeficientes `.rds`. | La temperatura decrece con la altitud según el gradiente adiabático ($\Gamma \approx -5.5\text{ a }-6.5\ ^\circ\text{C}/\text{km}$). En Centroamérica y República Dominicana, la compleja orografía genera marcados contrastes térmicos en distancias de pocos kilómetros. |
| **Paso 2: Downscaling Data**<br>*(Desescalado Espacial de Grillas)* | Proyecta las grillas térmicas sobre la malla topográfica fina del DEM. | • Interpolación: Bilineal (`blin`), IDW, Kriging Ordinario (`okr`).<br>• Grilla objetivo: Resolución de $0.05^\circ$ (~5.5 km).<br>• Formato de salida: `tmax_down_%s%s%s.nc` / `tmin_down_%s%s%s.nc`. | Corrige la distorsión de altura de la grilla satelital/reanálisis. Zonas de alta montaña (Cordillera Central en RD, Cordillera de Talamanca en CR/PA, Sierra Madre en GT/HN) y valles profundos quedan representados con su altitud real. |
| **Paso 3: Compute Bias Coefficients**<br>*(Cálculo de Coeficientes de Sesgo)* | Calcula el sesgo de las temperaturas desescaladas contra estaciones. | • Método: Multiplicativo (`mbvar`), Mapeo de cuantiles paramétrico (`qmdist`) con distribución Normal, Skew-Normal, Gumbel o Log-Normal, o empírico (`qmecdf`).<br>• Interpolación: IDW vs. Kriging Ordinario con variogramas Sph, Exp, Gau, Pen.<br>• Radios de búsqueda ($3.5^\circ$). | La temperatura sigue distribuciones unimodales casi continuas (sin inflación de ceros), pero Tmax presenta asimetría positiva en olas de calor (Skew-Normal o Gumbel), mientras que Tmin presenta colas frías por heladas en zonas altas. |
| **Paso 4: Apply Bias Correction**<br>*(Aplicación del Ajuste de Sesgo)* | Aplica los coeficientes a las 10,958 grillas diarias desescaladas. | • Rango 1991–2020.<br>• Formato: `tmax_adj_%s%s%s.nc` o `tmin_adj_%s%s%s.nc`. | Remueve derivas estacionales y sesgos térmicos regionales previos a la interpolación de residuales con las estaciones. |
| **Paso 5: Merging Data**<br>*(Fusión Espacial de Datos)* | Fusión final entre grillas desescaladas/ajustadas y estaciones. | • Métodos: Regression Kriging (RK) vs. SBA.<br>• Covariables físicas: DEM (altitud), Pendiente (*slope*), Orientación (*aspect*), Coordenadas (lon/lat).<br>• Esquemas de pasadas multiescala.<br>• Interpolación de residuales: IDW, Kriging Ordinario, Vecino más cercano 3D (Shepard), Barnes gaussiano para brisas costeras. | Para Tmax, la pendiente y orientación modulan la radiación solar directa diurna. Para Tmin, el drenaje de aire frío e inversión térmica nocturna en valles se capturan físicamente mediante la covariable de elevación relativa y pendiente en Regression Kriging. |

---

### 5.2 Suite A: Precipitación Diaria (CHIRPS 1991–2020, 10 Experimentos)
Configurados en [`config/experiments_rainfall/`](file:///d:/Workspace/CDT-8.0/config/experiments_rainfall):

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

### Evaluación y Calibración en Workstation (18 Núcleos Paralelos, 64 GB RAM, NVMe):

| Suite de Experimentos | Núm. Exp. | Días / Exp. | Rango Tiempo por Exp. | Tiempo Total Suite | Consumo RAM Máx. |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precipitación (CHIRPS)** | 10 | 10,958 | 1.1 h (IDW) a 4.2 h (Block OKR) | **~29.0 – 31.0 horas** | 2.5 – 4.5 GB |
| **Temperatura Máxima ($T_{max}$)** | 8 | 10,958 | 1.2 h (IDW) a 2.4 h (RK DEM) | **~15.0 – 16.0 horas** | 3.5 – 4.6 GB |
| **Temperatura Mínima ($T_{min}$)** | 8 | 10,958 | 1.2 h (IDW) a 2.4 h (RK DEM) | **~15.0 – 16.0 horas** | 3.5 – 4.6 GB |
| **TOTAL GENERAL 26 EXPERIMENTOS** | **26** | **10,958** | — | **~60.0 – 63.0 horas** | **Máx. 4.6 GB (< 8% RAM)** |

> [!NOTE]
> **Diferenciación de Carga Computacional:**
> - **Interpolaciones algebraicas (IDW, Barnes, Shepard):** Evalúan funciones analíticas directas ($O(N)$), completando 30 años en ~1.1 a 2.3 horas.
> - **Regression Kriging en Temperatura con DEM:** No utiliza máscara binomial de lluvia, completando cada experimento en ~2.2 a 2.6 horas.
> - **Kriging Ordinario por Bloques con Máscara Logística (Lluvia):** Al tener `use_block: true` y `RnoR: logit`, ejecuta 2 procesos de Kriging por cada una de las 3 pasadas diarias (6 Krigings por día con integración numérica 2D), requiriendo ~4.0 a 4.5 horas. Con Kriging puntual (`use_block: false`), el tiempo desciende a ~1.8 horas, reduciendo la batería completa a **~48 horas (~2 días)**.

### Formato de Salida y Monitoreo de Tiempos:
El orquestador (`launcher/experiment_runner.py`) implementa la utilidad `format_duration()` que presenta los tiempos de ejecución en formato legible de horas, minutos y segundos:
- Al terminar cada corrida: `>>> [OK] EXP_R03 completado con estado SUCCESS en 4h 16m 40s (15400.25s)`.
- En la tabla resumen: columna `Tiempo` formateada y pie con el `TIEMPO TOTAL ACUMULADO DE LA SUITE`.
- En el archivo `manifest.json`: se preserva `execution_time_sec` (numérico) y se añade `execution_time_formatted`.

### Comandos de Ejecución CLI (`launcher/experiment_runner.py`):

```bash
# Diagnóstico de dependencias
python launcher/experiment_runner.py --check-env

# Ejecutar suites completas (Workstation con 18 núcleos)
python launcher/experiment_runner.py --suite rainfall --cores 18   # 10 Exp. Lluvia (~29-31 h)
python launcher/experiment_runner.py --suite tmax     --cores 18   # 8 Exp. Tmax (~15-16 h)
python launcher/experiment_runner.py --suite tmin     --cores 18   # 8 Exp. Tmin (~15-16 h)

# Ejecutar corrida batch completa de los 26 experimentos
python launcher/experiment_runner.py --suite all      --cores 18   # 26 Exp. (~60-63 h continuas)

# Ejecutar un experimento individual parametrizado
python launcher/experiment_runner.py --config config/experiments_rainfall/EXP_R03_SBA_OKR_BernoulliGamma.yaml --cores 18
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
9. **Gudmundsson, L., Bremnes, J. B., Haugen, J. E., & Engen-Skaugen, T. (2012).** *Downscaling RCM precipitation to the station scale using statistical transformations–a comparison of methods.* Hydrology and Earth System Sciences, 16(9), 3383–3390. DOI: [10.5194/hess-16-3383-2012](https://doi.org/10.5194/hess-16-3383-2012)
10. **Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).** *Decomposition of the mean squared error and NSE performance measures: Implications for improving hydrological modelling.* Journal of Hydrology, 377(1-2), 80–91. DOI: [10.1016/j.jhydrol.2009.08.003](https://doi.org/10.1016/j.jhydrol.2009.08.003)
11. **Hengl, T., Heuvelink, G. B., & Rossiter, D. G. (2007).** *About regression-kriging: From equations to case studies.* Computers & Geosciences, 33(10), 1301–1315. DOI: [10.1016/j.cageo.2007.05.001](https://doi.org/10.1016/j.cageo.2007.05.001)
12. **Hidalgo, H. G., Alfaro, E. J., & Quesada-Montano, B. (2017).** *Observed (1970–1999) climate variability in Central America using a high-resolution meteorological dataset with implication to climate change studies.* Climatic Change, 141(1), 13–28. DOI: [10.1007/s10584-016-1786-y](https://doi.org/10.1007/s10584-016-1786-y)
13. **Kedem, B., Chiu, L. S., & North, G. R. (1990).** *Estimation of mean rain rate: Application to satellite observations.* Journal of Geophysical Research: Atmospheres, 95(D2), 1965–1972. DOI: [10.1029/JD095iD02p01965](https://doi.org/10.1029/JD095iD02p01965)
14. **Maldonado, T., Rutgersson, A., Amador, J. A., Alfaro, E. J., & Claremar, B. (2016).** *Variability of the Caribbean low-level jet during boreal winter: large-scale forcings.* International Journal of Climatology, 36(4), 1978–1999. DOI: [10.1002/joc.4472](https://doi.org/10.1002/joc.4472)
15. **Schultz, D. M., Bracken, W. E., & Bosart, L. F. (1998).** *Planetary- and synoptic-scale signatures associated with Central American cold surges.* Monthly Weather Review, 126(1), 5–27. DOI: [10.1175/1520-0493(1998)126&lt;0005:PASSSA&gt;2.0.CO;2](https://doi.org/10.1175/1520-0493(1998)126%3C0005:PASSSA%3E2.0.CO;2)
16. **Shepard, D. (1968).** *A two-dimensional interpolation function for irregularly-spaced data.* Proceedings of the 1968 23rd ACM National Conference, 517–524. DOI: [10.1145/800186.810616](https://doi.org/10.1145/800186.810616)
17. **Themeßl, M. J., Gobiet, A., & Leuprecht, A. (2011).** *Empirical-statistical downscaling and error correction of daily precipitation from regional climate models.* International Journal of Climatology, 31(10), 1530–1544. DOI: [10.1002/joc.2168](https://doi.org/10.1002/joc.2168)
18. **Willmott, C. J., Rowe, C. M., & Philpot, W. D. (1985).** *Small-scale climate maps: A sensitivity analysis of some common assumptions associated with grid-point interpolation and contouring.* The American Cartographer, 12(1), 5–16. DOI: [10.1559/152304085783914686](https://doi.org/10.1559/152304085783914686)
19. **WMO / CF Metadata Conventions Committee (2020).** *NetCDF Climate and Forecast (CF) Metadata Conventions Version 1.8.* World Meteorological Organization. URL: [https://cfconventions.org/](https://cfconventions.org/)
