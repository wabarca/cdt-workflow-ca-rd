# 05. Secuencia de Procesamiento de Temperatura (CHIRTS) y Modelado Topográfico con DEM


Este documento detalla exhaustivamente la cadena de procesamiento de **Temperatura** en CDT, desde la preparación de archivos NetCDF 3D multitemporales (1991–2020) hasta la fusión final, explicando el fundamento climatológico/estadístico de cada menú y la **matriz de experimentos parametrizables** para investigación y publicación científica.

---

## 1. Cadena de Procesamiento en el Menú de CDT

```mermaid
flowchart TD
    A["1. Data Preparation: Split 3D NetCDF<br>(1991–2020 a 1 NetCDF/día)"] --> B["2. Compute Downscaling Coefficients<br>(Modelado del Gradiente Térmico / Lapse Rate)"]
    B --> C["3. Downscaling Data<br>(Reducción de Escala Reanálisis a Malla DEM)"]
    C --> D["4. Compute Bias Coefficients<br>(Ajuste de Sesgo: Multiplicativo / Quantile Mapping)"]
    D --> E["5. Apply Bias Correction<br>(Corrección del Proxy de Temperatura)"]
    E --> F["6. Merging Data<br>(Fusión Final con Estaciones: SBA / RK / Kriging)"]
    F --> G["7. Data Preparation: Concatenate / Aggregate NetCDF<br>(1 NetCDF Multitemporal Final 1991–2020)"]
```

---

## 2. Detalle Paso a Paso: Menús, Estadística y Climatología

### Paso 1: Data Preparation > Split 3D NetCDF Files
- **Qué hace el software:** Lee el archivo NetCDF original que contiene las 3 dimensiones $(X, Y, \text{Tiempo})$ para el periodo 1991–2020, decodifica el calendario (`gregorian`, `noleap`, `365_day`, `julian`) y genera un archivo NetCDF individual 2D $(Lon, Lat)$ por cada día/mes con nomenclatura homogénea (`tmax_19910101.nc`).
- **Sentido físico/computacional:** Permite el procesamiento paralelo masivo, modularidad temporal y acceso aleatorio eficiente sin cargar terabytes en la memoria RAM.

---

### Paso 2: Gridding > Downscaling Reanalysis > Compute Downscaling Coefficients
- **Ruta de código:** [`R/cdtTemp_DownscalingCoef_Procs.R`](file:///d:/Workspace/CDT-8.0/R/cdtTemp_DownscalingCoef_Procs.R)
- **Fundamento Climatológico:** La temperatura disminuye sistemáticamente con la altitud debido a la descompresión adiabática del aire (*Environmental Lapse Rate*, típicamente entre $-5.0\ ^\circ\text{C}$ y $-6.5\ ^\circ\text{C}$ por cada $1000\text{ m}$). Además, la insolación varía según la pendiente (*slope*) y la orientación de las laderas (*aspect*).
- **Fundamento Estadístico:** Ajusta un Modelo Lineal Generalizado (GLM) para cada mes del año ($m = 1, \dots, 12$) correlacionando la temperatura observada en las estaciones con la topografía:
  
  $$\text{Temp}_m(s) = \beta_{0,m} + \beta_{1,m} \cdot \text{DEM}(s) + \beta_{2,m} \cdot \text{Slope}(s) + \beta_{3,m} \cdot \text{Aspect}(s) + \text{Polinomio}(\text{Lon}, \text{Lat})$$

- **Salida generada:** Archivos `STN_DEM_GLM_COEF.txt` y `STN_DEM_GLM_COEF.rds` con la matriz de 12 filas (una por mes) y los coeficientes ajustados $\beta$.

> [!IMPORTANT]
> **Requisito Físico del DEM (Filtro Anti-Batimetría y Clampeo a Cero):**
> Para que el GLM estime gradientes adiabáticos coherentes ($\beta_{\text{elv}} \approx -0.0055\text{ a } -0.0065\ ^\circ\text{C}/\text{m}$), el archivo NetCDF del DEM **no debe contener cotas batimétricas oceánicas negativas** (como las fosas abisales de hasta $-8390\text{ m}$ en productos globales como GEBCO). Toda elevación menor a cero debe clampearse a nivel medio del mar ($\text{DEM} = \max(\text{DEM}, 0.0)$). Esto preserva el $100\%$ de las islas (Roatán, Guanaja, Coiba, Ometepe) con su cota topográfica real y evita la inversión espuria del gradiente térmico a valores positivos ($\beta > 0$). Para un análisis exhaustivo de la influencia del DEM, consultar [05_secuencia_temperatura_chirts_dem.md](05_secuencia_temperatura_chirts_dem.md).

---

### Paso 3: Gridding > Downscaling Reanalysis > Downscaling Data
- **Ruta de código:** [`R/cdtTemp_DownscalingReanal_Procs.R`](file:///d:/Workspace/CDT-8.0/R/cdtTemp_DownscalingReanal_Procs.R)
- **Fundamento Climatológico:** Los reanálisis o CHIRTS nativos suelen tener resoluciones espaciales gruesas ($0.25^\circ \approx 28\text{ km}$ o $0.05^\circ$). Este paso transfiere la variabilidad orográfica de alta resolución del DEM ($90\text{ m}$ o $1\text{ km}$) al campo térmico grueso.
- **Fundamento Estadístico:**
  1. Agrega el DEM fino a la resolución gruesa del reanálisis: $\text{DEM}_{\text{coarse}}$.
  2. Predice la temperatura gruesa esperada por topografía: $\hat{T}_{\text{coarse}} = f_m(\text{DEM}_{\text{coarse}})$.
  3. Extrae la anomalía climática sinóptica / residual grueso:

     $$R_{\text{coarse}} = T_{\text{reanalysis}} - \hat{T}_{\text{coarse}}$$

  4. Interpola el residual $R_{\text{coarse}}$ a la cuadrícula fina mediante **Bilineal**, **IDW** o **Kriging**.
  5. Reconstruye la temperatura desescalada de alta resolución:

     

$$
T_{\text{downscaled}}(s_{\text{fino}}) = f_m(\text{DEM}_{\text{fino}}) + \hat{R}_{\text{fino}}(s_{\text{fino}})
$$



- **Salida generada:** NetCDFs diarios de temperatura desescalada con la resolución del DEM.

---

### Paso 4: Gridding > Bias Correction > Compute Bias Coefficients (Temperature)
- **Ruta de código:** [`R/cdtBias_functions.R`](file:///d:/Workspace/CDT-8.0/R/cdtBias_functions.R#L211-L320), [`R/cdtBias_Options_functions.R`](file:///d:/Workspace/CDT-8.0/R/cdtBias_Options_functions.R)
- **Fundamento Climatológico:** El reanálisis/satélite desescalado puede tener sesgos sistemáticos debidos a errores en la parametrización de la capa límite, albedo del suelo o nubosidad.
- **Fundamento Estadístico:** Modela la función de transferencia entre estaciones y reanálisis:
  1. **Método Multiplicativo Variable (`"mbvar"` / `"mbmon"`):**
     Calcula el factor de corrección $B_i = \frac{\text{Media}(S_i)}{\text{Media}(G_i)}$ mensual o con ventana móvil de $\pm 5$ días para capturar el ciclo anual continuo.
  2. **Quantile Mapping Paramétrico (`"qmdist"`):**
     Ajusta funciones de densidad de probabilidad acumulada teóricas (CDF):
     - Distribución Normal (`"norm"`): $\mu, \sigma$
     - Log-Normal (`"lnorm"`): $\mu_{\ln}, \sigma_{\ln}$
     - Skew-Normal (`"snorm"`): Asimetría térmica $\mu, \sigma, \xi$
     - Gumbel (`"gumbel"`): Extremos térmicos (olas de calor).
  3. **Quantile Mapping Empírico (`"qmecdf"`):**
     Ajusta directamente las distribuciones empíricas sin asumir una forma paramétrica.
- **Salida generada:** Coeficientes de distribución o mapas de factores de sesgo guardados en disco.

---

### Paso 5: Gridding > Bias Correction > Apply Bias Correction
- **Fundamento Estadístico:** Para cada día $t$, transforma el valor del pixel $x$ mediante la función de cuantiles inversos:

  

$$
\hat{T}_{\text{corrected}}(s) = F_{\text{stn}}^{-1}\left( F_{\text{proxy}}(T_{\text{downscaled}}(s)) \right)
$$



- **Salida generada:** NetCDFs diarios ajustados por sesgo, preservando la media y los cuantiles observados por las estaciones.

---

### Paso 6: Gridding > Merging Climate Data > Temperature Data
- **Ruta de código:** [`R/cdtMerging_Temp_Cmd.R`](file:///d:/Workspace/CDT-8.0/R/cdtMerging_Temp_Cmd.R), [`R/cdtMerging_functions.R`](file:///d:/Workspace/CDT-8.0/R/cdtMerging_functions.R)
- **Fundamento Estadístico:** Ajusta los residuales puntuales finales entre las estaciones y el producto corregido mediante:
  - **Regression Kriging (RK):** Ajusta un GLM dinámico fecha a fecha con covariables espaciales (DEM, Slope, Lon, Lat).
  - **Ordinary Kriging (OKR) / IDW:** Interpola la estructura espacial de los residuales y la adiciona al campo corregido.
  - **Límites físicos:** Clampeo a $[-40\ ^\circ\text{C}, +50\ ^\circ\text{C}]$.

---

## 3. Matriz de Hiperparámetros y Espacio de Búsqueda Experimental

Para una investigación publicable, el objetivo es determinar qué combinación de preprocesamiento, downscaling, corrección de sesgo y fusión produce el menor RMSE, MAE y mayor $R^2$ en validación cruzada.

### Tabla de Parámetros Manipulables para Experimentos

| Etapa | Parámetro en CDT | Opciones / Rango de Variación | Justificación Científica |
| :--- | :--- | :--- | :--- |
| **Downscaling: Lapse Rate** | `useClimato` | `TRUE` (climatológico mensual) vs `FALSE` (serie completa continua) | Evalúa si el gradiente térmico es estacional fijo o dinámico. |
| **Downscaling: Topografía** | `aspect.slope` / `polynomial` | - Solo Elevación (`v ~ z`)<br>- Elevación + Pendiente + Aspecto (`v ~ s + a + z`)<br>- Polinomio espacial Grado 1 o 2 (`order = 1, 2`) | Determina el impacto de la radiación según la orientación de laderas. |
| **Downscaling: Estandarización** | `standardize` | `TRUE` vs `FALSE` | Estabilidad numérica en áreas montañosas de gran desnivel. |
| **Downscaling: Residuales** | `interp.method` | `"blin"` (Bilineal), `"idw"`, `"okr"` (Kriging) | Evalúa cómo se propaga la anomalía sinóptica a la malla fina. |
| **Bias: Método** | `bias.method` | `"mbmon"`, `"mbvar"` ($\pm 5$ días), `"qmdist"`, `"qmecdf"` | Compara ajuste lineal simple vs mapeo no lineal de cuantiles. |
| **Bias: Distribución QM** | `distr.name` (en `qmdist`) | `"norm"`, `"lnorm"`, `"snorm"`, `"gumbel"` | Evalúa el ajuste en olas de frío/calor y asimetría térmica. |
| **Bias: Función Central** | `mulBiasFunction` | `"mean"` vs `"median"` | Robustez frente a valores atípicos (*outliers*). |
| **Merging: Método** | `merge.method\$method` | `"SBA"`, `"RK"`, `"BSc"` (Barnes), `"CSc"` (Cressman) | Determina si la regresión espacial supera al ajuste aditivo simple. |
| **Merging: Pasadas** | `nrun` y `pass` | - 1 pasada: `pass = c(1)`<br>- 2 pasadas: `pass = c(1, 0.5)`<br>- 3 pasadas: `pass = c(1, 0.75, 0.5)` | Refinamiento multiescala: regional vs local. |
| **Merging: Radio Búsqueda** | `interp.method\$maxdist` | $1.5^\circ, 2.5^\circ, 3.5^\circ, 5.0^\circ$ | Rango de correlación espacial térmica. |
| **Merging: Vecindad** | `nmin` / `nmax` | $(4, 12)$, $(8, 16)$, $(10, 30)$ | Densidad y suavidad en la interpolación de residuales. |
| **Merging: Kriging Variograma**| `vgm.model` | `"Sph"`, `"Exp"`, `"Gau"`, `"Pen"` | Forma de la autocorrelación espacial de residuales. |
| **Merging: Soporte de Celda** | `use.block` | `TRUE` (Block Kriging) vs `FALSE` (Point Kriging) | Corrección del error de cambio de soporte espacial. |

---

## 4. Partición Experimental: Dinámicas Físicas de $T_{max}$ vs $T_{min}$

La física atmosférica exige modelar y evaluar de manera independiente los extremos diurnos y nocturnos:

1. **Temperatura Máxima ($T_{max}$, Suite `EXP-TX01` a `EXP-TX08`):**
   - Dominada por la radiación solar directa, el albedo, la pendiente e inclinación (*slope*) y la orientación de la ladera (*aspect*).
   - Extremos modelados mediante distribución **Gumbel** para olas de calor en valles áridos y zonas deprimidas (Valle de Azua, Hoya de Enriquillo, Golfo de Fonseca).
   - Covariables espaciales críticas en Regression Kriging: DEM + Pendiente + Aspecto + Coordenadas.

2. **Temperatura Mínima ($T_{min}$, Suite `EXP-TN01` a `EXP-TN08`):**
   - Dominada por el enfriamiento radiativo nocturno, el desacople de la capa límite superficial, drenaje catabático de aire denso e **inversiones térmicas** en valles altos cerrados (Constanza, Valle Nuevo, Altiplano Occidental de Guatemala).
   - Frentes fríos continentales (*Nortes*) modelados mediante distribución **Skew-Normal** para capturar caídas térmicas bruscas asimétricas.
   - Interpolación de residuales mediante **NN-3D ($\Delta z$)** para impedir la transferencia espuria de calor desde llanuras costeras hacia valles altos.

---

## 5. Ejecución Automatizada con Python Launcher

Las dos suites de temperatura se ejecutan de manera directa y desatendida mediante:

```bash
# Ejecutar suite completa de Temperatura Máxima (8 experimentos)
python launcher/experiment_runner.py --suite tmax

# Ejecutar suite completa de Temperatura Mínima (8 experimentos)
python launcher/experiment_runner.py --suite tmin

# Ejecutar un experimento individual de Tmax (ej. insolación y radiación solar)
python launcher/experiment_runner.py --config config/experiments_tmax/EXP_TX08_RK_Aspect_Solar_Insolation.yaml

# Ejecutar un experimento individual de Tmin (ej. inversiones térmicas en valles)
python launcher/experiment_runner.py --config config/experiments_tmin/EXP_TN04_RK_NN3D_Inversion_Valleys.yaml
```

### Esquema de Validación Cruzada Independiente (Holdout)
```mermaid
flowchart LR
    A["Estaciones Totales (100%)"] --> B["Entrenamiento (80-90% en CDT)"]
    A --> C["Validación Independiente (10-20% Omitidas)"]
    B --> D["secuencia de procesamiento CDT (Downscale + Bias + Merging)"]
    D --> E["Malla Gridded 3D CF-1.8 Final"]
    E --> F["Extracción en Estaciones Omitidas (station_manager.py)"]
    C --> F
    F --> G["Métricas Estadísticas:<br>RMSE, MAE, R², Bias, Kling-Gupta Efficiency (KGE)"]
```


---

# Anexo Metodológico Detallado: Modelado de Covariables Topográficas (DEM, Pendiente, Aspecto)


## 1. Características del Campo de Temperatura

A diferencia de la precipitación, la temperatura (máxima, mínima o media) es un campo biofísico caracterizado por:
1. **Continuidad espacial estricta:** No presenta ceros estructurales ni las discontinuidades abruptas típicas de la lluvia convectiva.
2. **Dominancia orográfica de primer orden:** El factor preponderante en la distribución espacial de la temperatura superficial es la **altitud topográfica**, gobernada por la descompresión adiabática y el gradiente térmico vertical (*lapse rate*, con valores medios de $-5.0$ a $-6.5\ ^\circ\text{C}$ por cada $1000\text{ m}$ de elevación en la troposfera baja tropical).
3. **Efectos de microclima y exposición radiativa:** La orientación (*aspect*) y la pendiente (*slope*) modulan la radiación solar incidente (insolación matutina vs. vespertina), influyendo con fuerza en la temperatura máxima ($T_{\max}$).
4. **Desacoples térmicos locales nocturnos:** El enfriamiento radiativo en noches despejadas produce drenaje catabático de aire frío hacia cuencas y fondos de valle (*cold-air pooling*), generando inversiones térmicas nocturnas donde valles altos amanecen bajo cero mientras las crestas circundantes se mantienen más templadas, factor crucial en la temperatura mínima ($T_{\min}$).
5. **Gradiente latitudinal / continental:** Atenuación sinóptica de la temperatura explicada por la cercanía a las masas oceánicas y la latitud geográfica.

Por estas razones físicas, la fusión de temperatura en CDT depende críticamente de un **Modelo Digital de Elevación (DEM)** de alta fidelidad, utilizándolo como covariable determinística tanto en la fase previa de desescalado (*downscaling*) como en la fusión geoestadística mediante **Regression Kriging (`"RK"`)**.

---

## 2. Influencia Fisiográfica y Termodinámica del DEM en la Temperatura

El Modelo Digital de Elevación (DEM) actúa como la columna vertebral física que ancla las observaciones térmicas gruesas de satélites o reanálisis a la realidad del terreno:

```mermaid
flowchart TD
    A["Modelo Digital de Elevación (DEM)"] --> B["Gradiente Adiabático Ambiental<br>(Lapse Rate: dT/dz)"]
    A --> C["Topografía Derivada:<br>Pendiente (Slope) y Orientación (Aspect)"]
    A --> D["Diferencia Vertical de Cota (dz):<br>NN-3D e Inversiones Térmicas"]
    
    B --> E["Desescalado de Reanálisis<br>(0.25° / 0.05° a 90m / 1km)"]
    C --> F["Modelado de Radiación Solar<br>en Laderas para Tmax"]
    D --> G["Aislamiento de Valles Cerrados<br>y Heladas para Tmin"]
    
    E --> H["Campo Térmico Continuo<br>y Físicamente Coherente"]
    F --> H
    G --> H
```

### 2.1. Gradiente Térmico Vertical Ambiental (*Environmental Lapse Rate*)
En la troposfera tropical, la masa atmosférica disminuye exponencialmente con la altura, reduciendo la presión barométrica. Una parcela de aire que asciende se expande adiabáticamente y se enfría:
$$\frac{\partial T}{\partial z} \approx -6.5\ ^\circ\text{C}/\text{km}$$
Sin un DEM que proporcione la cota precisa $z$, cualquier interpolación espacial generaría manchas isotérmicas ficticias entre estaciones separadas por pocos kilómetros pero ubicadas en distintas altitudes (por ejemplo, una estación costera a $10\text{ msnm}$ con $32\ ^\circ\text{C}$ frente a una estación de montaña a $2000\text{ msnm}$ con $16\ ^\circ\text{C}$). El DEM permite descomponer el campo térmico en un componente determinístico altimétrico y un residuo estocástico sinóptico.

### 2.2. Efectos de Pendiente e Insolación (*Slope* y *Aspect*)
La insolación neta que calienta el suelo depende del ángulo cenital solar relativo a la normal de la ladera:
- Las laderas orientadas al este reciben radiación directa en horas de la mañana con temperaturas ambiente bajas.
- Las laderas orientadas al oeste reciben máxima insolación en horas vespertinas cuando el aire ya ha acumulado calor sensible, alcanzando picos extremos de $T_{\max}$.
- Los cañones profundos experimentan sombreado topográfico temprano.
CDT deriva automáticamente `Slope` y `Aspect` a partir de la malla del DEM mediante derivadas espaciales de segundo orden ($\partial z / \partial x, \partial z / \partial y$), utilizándolas como predictores lineales en el modelo de regresión.

### 2.3. Drenaje Catabático e Inversiones Térmicas Nocturnas
Durante la noche, el enfriamiento radiativo superficial vuelve el aire en contacto con el suelo más denso que el aire libre. La gravedad hace que este flujo fluya ladera abajo (*drainage winds*) y se estanque en cuencas intramontanas cerradas. En estas condiciones:
$$\frac{\partial T}{\partial z} > 0 \quad (\text{en la capa límite superficial del valle})$$
Para capturar este fenómeno en $T_{\min}$, el parámetro de distancia tridimensional (`NN-3D`) utiliza el DEM para penalizar la cercanía horizontal si existe un salto vertical sustancial ($\Delta z$), evitando que estaciones cálidas en valles bajos contaminen la interpolación de valles fríos de montaña.

---

## 3. Rol Crítico del DEM en Cada Etapa del Flujo de CDT

En el flujo integral de temperatura (guía metodológica y menú de CDT), el DEM no es un insumo pasivo; interviene activamente en **cuatro de los cinco pasos principales**:

```mermaid
flowchart LR
    DEM["DEM Filtrado (z >= 0)"]
    
    subgraph S1["Paso 2: Coeficientes Lapse Rate"]
        DEM --> C1["Ajuste GLM Estaciones ~ DEM<br>(Obtención de beta_elv mensual)"]
    end
    
    subgraph S2["Paso 3: Desescalado Espacial"]
        DEM --> C2["Agregación Coarse DEM<br>+ Inyección de Alta Res Fina:<br>T_downscaled = f(DEM_fino) + Res_interp"]
    end
    
    subgraph S3["Paso 5/6: Fusión Espacial (Merging)"]
        DEM --> C3["Regression Kriging (RK)<br>+ Covariables Topográficas<br>+ Restricción Vertical NN-3D"]
    end
```

### Paso A: Modelado del Coeficiente de Desescalado (Lapse Rate Mensual)
En `R/cdtTemp_DownscalingCoef_Procs.R`, CDT extrae la elevación del DEM en cada estación meteorológica y ajusta un modelo lineal mensual:
$$\text{Temp}_m(s_i) = \beta_{0,m} + \beta_{\text{elv},m} \cdot \text{DEM}(s_i) + \sum \beta_{k,m} X_k(s_i) + \varepsilon(s_i)$$
El coeficiente $\beta_{\text{elv},m}$ debe ser **negativo** ($\approx -0.0055$ a $-0.0065\ ^\circ\text{C}/\text{m}$), reflejando que a mayor altitud, menor temperatura.

### Paso B: Reducción de Escala (Downscaling de Grillas a Resolución del DEM)
En `R/cdtTemp_DownscalingReanal_Procs.R`, CDT ejecuta:
1. Agregación de la malla fina del DEM a la malla gruesa del reanálisis/satélite: $\text{DEM}_{\text{coarse}}$.
2. Cálculo de la temperatura esperada por topografía gruesa: $\hat{T}_{\text{coarse}} = \beta_0 + \beta_{\text{elv}} \cdot \text{DEM}_{\text{coarse}}$.
3. Extracción del residual sinóptico grueso: $R_{\text{coarse}} = T_{\text{sat}} - \hat{T}_{\text{coarse}}$.
4. Interpolación espacial del residual a la malla fina del DEM: $\hat{R}_{\text{fine}}$.
5. Reconstrucción física de alta resolución:
   

$$
T_{\text{downscaled}}(s_{\text{fine}}) = \beta_0 + \beta_{\text{elv}} \cdot \text{DEM}_{\text{fine}}(s_{\text{fine}}) + \hat{R}_{\text{fine}}(s_{\text{fine}})
$$



> [!IMPORTANT]
> Observa que si el valor de $\text{DEM}_{\text{fine}}$ o el coeficiente $\beta_{\text{elv}}$ están distorsionados, toda la temperatura de alta resolución colapsará inmediatamente antes de llegar a la fase de fusión.

### Paso C: Fusión Espacial Final (Regression Kriging)
En `R/cdtMerging_Temp_Cmd.R`, CDT utiliza el DEM como covariable base de la tendencia espacial diaria. Las estaciones terrestres se ajustan contra el valor puntual del DEM, y la superficie estimada se calcula evaluando el polinomio de regresión en toda la grilla del DEM antes de sumar los residuos krigeados.

---

## 4. Patología Climatológica: Impacto de la Batimetría Submarina y Valores Negativos

Durante la fase experimental de temperatura en Centroamérica, se identificó un problema técnico crítico que ilustra la sensibilidad matemática del algoritmo:

### 4.1. Diagnóstico del Error por Batimetría Oceánica
Al suministrar un producto global sin procesar como **GEBCO** (`gebco_2026.nc`), el archivo contiene tanto la topografía continental positiva ($z > 0\text{ msnm}$) como la **batimetría del lecho marino** ($z < 0\text{ msnm}$, con profundidades de hasta $-8390\text{ m}$ en fosas abisales del Pacífico y del Caribe):

| Parámetro Topográfico | Archivo Crudo (GEBCO con Batimetría) | Archivo Terrestre Clampeado a Nivel del Mar |
| :--- | :--- | :--- |
| **Elevación Mínima ($z_{\min}$)** | $-8390.0\text{ m}$ (Fosa marina) | $0.0\text{ m}$ (Nivel medio del mar) |
| **Elevación Máxima ($z_{\max}$)** | $+5611.0\text{ m}$ (Cumbre montañosa) | $+5611.0\text{ m}$ (Cumbre montañosa) |
| **Media Regional del DEM** | **$-1708.05\text{ m}$** (Ficticia, océano profundo) | $+350.20\text{ m}$ (Real continental) |
| **Porcentaje de Malla con $z < 0$** | $\approx 68\%$ del dominio centroamericano | $0\%$ (Todo el mar a $0\text{ msnm}$) |

### 4.2. Colapso Matemático del Gradiente Térmico
Cuando CDT calcula el *Lapse Rate* (Paso 2) o la regresión espacial con un DEM batimétrico:
1. En la agregación gruesa ($\text{DEM}_{\text{coarse}}$), los píxeles costeros promedian la tierra ($+500\text{ m}$) con fosas abisales ($-3000\text{ m}$), resultando en elevaciones ficticias de $-1250\text{ m}$.
2. En el GLM, la correlación entre la temperatura observada ($15$ a $32\ ^\circ\text{C}$) y elevaciones que varían entre $-8390\text{ m}$ y $+4000\text{ m}$ se distorsiona completamente, produciendo coeficientes **positivos** espurios ($\beta_{\text{elv}} \approx +0.017\ ^\circ\text{C}/\text{m}$) o interceptos absurdos ($\beta_0 \approx -10\ ^\circ\text{C}$).
3. Al aplicar la reconstrucción:
   

$$
T_{\text{downscaled}} = \beta_0 + \beta_{\text{elv}} \cdot \text{DEM}_{\text{fino}} + \hat{R}
$$


   la topografía continental real positiva ($+1000$ a $+3000\text{ m}$) resta masivamente temperatura o sobre-corrige los residuales, desplomando las temperaturas en tierra a valores inverosímiles ($-10\ ^\circ\text{C}$ a $5\ ^\circ\text{C}$ en costas tropicales).
4. **Consecuencia en Validación:** Las métricas se colapsan a $RMSE > 25\ ^\circ\text{C}$, $PBIAS < -60\%$ y $KGE < -10$, haciendo que los experimentos con DEM parezcan inferiores a un control nulo sin topografía (`EXP_TX01` / `EXP_TN01`).

```mermaid
graph TD
    subgraph DEM_Corrupto["DEM con Batimetría Submarina (-8390 m a +5600 m)"]
        A1["Océano con z < 0<br>(Media regional = -1708 m)"] --> B1["Agregación Coarse mezcla<br>tierra positiva y fosas marinas"]
        B1 --> C1["GLM invierte el signo:<br>beta_elv = +0.017 °C/m (Positivo espurio)"]
        C1 --> D1["Reconstrucción térmica resta decenas de grados en tierra"]
        D1 --> E1["Colapso: RMSE = 24-42 °C, KGE < -10"]
    end
    
    subgraph DEM_Corregido["DEM Clampeado a Nivel del Mar (0 m a +5600 m)"]
        A2["Océano plano z = 0 msnm<br>(Tierra z: 0 a 4200 m)"] --> B2["Agregación Coarse y Fina<br>termodinámicamente coherentes"]
        B2 --> C2["GLM ajusta Lapse Rate real:<br>beta_elv = -0.0055 a -0.0065 °C/m"]
        C2 --> D2["Reconstrucción térmica reproduce gradientes adiabáticos"]
        D2 --> E2["Óptimo: RMSE < 2.5 °C, KGE > 0.85"]
    end
```

---

## 5. Estrategia Óptima: Clampeo a Cero (`elevation < 0 = 0`) y Preservación Insular

Para solucionar este fenómeno, la mejor práctica climatológica y geoespacial consiste en aplicar un **clampeo de elevación al nivel del mar** combinado con un recorte (*bounding box*) regional:

$$\text{DEM}_{\text{clean}}(x, y) = \max\left(\text{DEM}(x, y), \, 0.0\right)$$

### 5.1. ¿Por qué el Clampeo a Cero es Superior al Recorte Vectorial por Polígono de Tierra?

1. **Sentido Físico de Nivel del Mar:** La atmósfera en contacto con el océano descansa sobre una superficie de agua a **$0\text{ metros sobre el nivel medio del mar}$**. Tratar el océano como una llanura térmica horizontal a $0\text{ msnm}$ refleja con exactitud la frontera termodinámica inferior de la atmósfera.
2. **Preservación Total de Islas y Cayos:**
   - En la región existen numerosas estaciones e intereses climatológicos en islas: por ejemplo `HO_Roatan` (Islas de la Bahía de Honduras, $14\text{ msnm}$), Isla de Guanaja, Utila, Isla de Ometepe (Nicaragua), Isla de Coiba y Archipiélago de las Perlas (Panamá), Cayos Miskitos y cayos litorales.
   - Si se intentara recortar (*mask*) el DEM con un shapefile vectorial continental estricto, las discrepancias de escala y resolución entre los vértices del polígono y la malla del ráster inevitablemente convertirían los píxeles insulares en valores ausentes (`NA`), descartando las estaciones insulares o impidiendo generar estimaciones sobre ellas.
   - Al clampear $\text{elevación} = \max(\text{elevación}, 0.0)$, **todas las islas retienen su cota real positiva ($z > 0\text{ msnm}$)**, integrándose perfectamente en el modelo orográfico.
3. **Eliminación de Discontinuidades y Valores Faltantes en Bordes Costeros:**
   - Las rutinas de CDT (`defSpatialPixels`, `interp.surface.grid`, Ordinary Kriging e IDW) requieren matrices regulares continuas.
   - Si las celdas marinas fueran `NA`, las estaciones costeras situadas en el borde continental generarían fallas numéricas en el cálculo de variogramas y en la búsqueda de vecinos espaciales hacia el mar.
   - Al tener una superficie marina continua en $0\text{ msnm}$, la interpolación de residuales transcurre de forma continua, suave y sin singularidades de matriz.

---

## 6. Configuración de Parámetros para Temperatura en `cdtMergingTempCMD`

La llamada estándar en la terminal o script de producción se estructura de la siguiente manera:

```r
cdtMergingTempCMD(
  time.step = "daily",
  dates = list(from = "range", pars = list(start = "19910101", end = "20201231")),
  station.data = list(file = "data/stations/tmax_stations_ca.csv", sep = ",", na.strings = "-99"),
  netcdf.data = list(
    dir = "data/chirts_bias_corrected/tmax", 
    format = "tmax_%s%s%s.nc",
    varid = "temp", 
    ilon = 1, 
    ilat = 2
  ),
  merge.method = list(
    method = "RK",               # Regression Kriging
    nrun = 3, 
    pass = c(1, 0.75, 0.5)
  ),
  interp.method = list(
    method = "idw",              # o "okr" si hay densidad de estaciones
    nmin = 8, 
    nmax = 24, 
    maxdist = 3.5,               # Radio amplio (3.5°) para masas térmicas
    use.block = TRUE, 
    vargrd = FALSE
  ),
  auxvar = list(
    dem = TRUE,                  # Elevación DEM requerida
    slope = TRUE,                # Pendiente derivada del DEM
    aspect = FALSE,              # Orientación (activar en Tmax para radiación)
    lon = TRUE,                  # Longitud
    lat = TRUE                   # Latitud
  ),
  dem.data = list(
    file = "data/topography/dem_ca_continental_land.nc", # DEM limpio sin batimetría
    varid = "elevation", 
    ilon = 1, 
    ilat = 2
  ),
  grid = list(from = "data", pars = NULL),
  output = list(dir = "output/tmax_merged", format = "tmax_mrg_%s%s%s.nc"),
  GUI = FALSE
)
```

---

## 7. Modelado Estadístico por Regresión (GLM en RK)

Para cada fecha diaria $t$, CDT ajusta un Modelo Lineal Generalizado de la familia Gaussiana con las estaciones disponibles:

$$\text{Temp}(s_i) = \beta_0 + \beta_1 \cdot \text{Reanalysis}(s_i) + \beta_2 \cdot \text{DEM}(s_i) + \beta_3 \cdot \text{Slope}(s_i) + \beta_4 \cdot \text{Lon}(s_i) + \beta_5 \cdot \text{Lat}(s_i) + \varepsilon(s_i)$$

1. **Derivación topográfica automática:**
   Si `slope = TRUE` o `aspect = TRUE`, CDT calcula internamente las matrices de pendiente y orientación a partir del archivo NetCDF del DEM mediante la función interna `raster.slope.aspect()`.
2. **Evaluación de la tendencia espacial:**
   Se evalúa la ecuación ajustada en toda la malla de alta resolución del DEM:

   $$\text{Trend}(s) = \hat{\beta}_0 + \hat{\beta}_1 \text{Reanalysis}(s) + \hat{\beta}_2 \text{DEM}(s) + \hat{\beta}_3 \text{Slope}(s) + \hat{\beta}_4 \text{Lon}(s) + \hat{\beta}_5 \text{Lat}(s)$$

3. **Interpolación de residuales térmicos:**
   Los residuales no explicados por la topografía ni por el reanálisis ($\varepsilon_i = \text{Obs}_i - \text{Trend}_i$) representan anomalías locales (inversiones térmicas en valles, brisas costeras, islas de calor urbano) y se interpolan hacia toda la malla con el método seleccionado (`idw` u `okr`).

---

## 8. Límites Físicos y Control de Calidad

- **Límites de temperatura en CDT:** $[-40\ ^\circ\text{C}, +50\ ^\circ\text{C}]$.
- En el caso de variables derivadas (presión atmosférica, humedad relativa), CDT ajusta los rangos correspondientes:
  - Humedad Relativa (`"rh"`): $[0, 100]\%$.
  - Presión Superficial (`"pres"`): $[700, 1100]\text{ hPa}$.
  - Presión a Nivel del Mar (`"prmsl"`): $[850, 1100]\text{ hPa}$.
  - Radiación (`"rad"`): $[0, 1300]\text{ W/m}^2$.
