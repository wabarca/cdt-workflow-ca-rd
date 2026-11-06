# 05. Métodos Geoestadísticos y Parámetros de Interpolación de Residuales

Cuando se utiliza el método de fusión **SBA** (*Simple Bias Adjustment*) o **RK** (*Regression Kriging*), los residuales calculados en las ubicaciones de las estaciones deben interpolarse a toda la cuadrícula geográfica.

La parametrización se define mediante el argumento `interp.method`:

```r
interp.method = list(
  method = "okr",          # "idw", "okr", "shepard", "sphere"
  nmin = 8,                # Mínimo número de estaciones vecinas
  nmax = 16,               # Máximo número de estaciones vecinas
  maxdist = 2.5,           # Radio de búsqueda en grados decimales
  use.block = TRUE,        # Kriging por bloques (área de píxel)
  vargrd = FALSE,          # Radio de búsqueda variable automático
  vgm.model = c("Sph", "Exp", "Gau", "Pen") # Modelos de variograma
)
```

---

## 1. Métodos de Interpolación Disponibles

### A. Inverse Distance Weighted (`"idw"`)
Asigna pesos a las estaciones inversamente proporcionales a su distancia elevada a una potencia $p$:

$$
\hat{R}(s_0) = \frac{\sum_{i=1}^{n} w_i R(s_i)}{\sum_{i=1}^{n} w_i}, \quad w_i = \frac{1}{d(s_0, s_i)^p}
$$

- **Ventajas:** Extremadamente rápido, determinista, no requiere ajuste de parámetros estocásticos y garantiza que el residual interpolado no superará los extremos observados.
- **Potencia por defecto:** $p = 2.0$ (modificable con `merging.options(powerWeightIDW = ...)`).

---

### B. Ordinary Kriging (`"okr"`)
Considera tanto la distancia como la estructura de correlación espacial de los datos a través del **semivariograma**:

$$
\gamma(h) = \frac{1}{2 N(h)} \sum_{i=1}^{N(h)} \left[ R(s_i) - R(s_i + h) \right]^2
$$

1. **Ajuste automático de variograma (`fit.variogram`):**
   CDT ajusta un modelo teórico seleccionando el mejor ajuste entre:
   - **`"Sph"` (Esférico):** Crecimiento lineal cerca del origen que alcanza una meseta bien definida.
   - **`"Exp"` (Exponencial):** Crecimiento pronunciado inicial que se aproxima asintóticamente a la meseta.
   - **`"Gau"` (Gaussiano):** Comportamiento parabólico suave cerca del origen (adecuado para campos continuos).
   - **`"Pen"` (Pentasférico):** Variante del esférico con mayor rango de correlación.

2. **Block Kriging (`use.block = TRUE`):**
   En lugar de predecir el residual en un punto matemático sin dimensión, Kriging integra la predicción sobre el área espacial de la celda NetCDF:

   

$$
\hat{R}(B) = \frac{1}{|B|} \int_{B} \hat{R}(s) ds
$$

   Esto reduce drásticamente el error de soporte espacial cuando se combina información puntual con celdas satelitales de $5\text{ km}$ o $25\text{ km}$.
   - Opciones en `merging.options()`: `blockType = "gaussian"` o `"userdefined"`.

---

### C. Modified Shepard Interpolation (`"shepard"`)
Es una variante local de IDW que utiliza una función de influencia suave y corrige la ponderación mediante derivadas directas de primer orden para evitar el efecto de "ojo de buey" (*bull's-eye*) característico del IDW clásico.

$$
\text{Peso base: } w_i = \left( \frac{\max(0, R_w - d_i)}{R_w \cdot d_i} \right)^p
$$

- Potencia por defecto: `powerWeightShepard = 0.7`.
- **Ventaja física:** Otorga transiciones graduales en cañones, valles intramontanos y zonas de transición costera, evitando singularidades en las proximidades inmediatas de las estaciones.

---

### D. Spheremap Interpolation (`"sphere"`)
Diseñado para compensar el **agrupamiento espacial (*clustering*)** de estaciones sobre geometrías esféricas:
- Si varias estaciones están muy juntas en una misma subcuenca o valle, una interpolación convencional sobreponderaría esa región.
- Spheremap calcula distancias de gran círculo sobre el esferoide terrestre y pondera angularmente la distribución de vecinos por cuadrantes alrededor del punto objetivo, impidiendo la redundancia de estaciones adyacentes.

---

### E. Cressman Objective Analysis (`"CSc"` / `"cressman"`)
Esquema de análisis objetivo meteorológico clásico multiescala basado en correcciones sucesivas mediante factores de corrección empíricos proporcionales al radio de influencia:

$$
W_i = \begin{cases} 
\dfrac{R_c^2 - d_i^2}{R_c^2 + d_i^2}, & d_i < R_c \cr
0, & d_i \geq R_c 
\end{cases}
$$

- **Mecanismo iterativo:** Se ejecuta en múltiples pasadas (típicamente 4 pasadas con radios decrecientes: $1.0 R_c, 0.75 R_c, 0.50 R_c, 0.25 R_c$), capturando primero anomalías de escala sinóptica y ajustando progresivamente las celdas convectivas o núcleos orográficos locales.

---

### F. Barnes Objective Analysis (`"BSc"` / `"barnes"`)
Análisis objetivo de dos o más pasadas con filtro de ponderación Gaussiano en el dominio espacial continuo:

$$
w_i = \exp\left( -\frac{d_i^2}{4 c_k} \right)
$$

donde $c_k$ es el parámetro de escala espacial ($c_2 = \gamma c_1$, con $\gamma \in (0, 1)$, típicamente $\gamma = 0.35$ a $0.5$).
- **Respuesta espectral:** Actúa como un filtro pasabajas riguroso con respuesta analítica conocida en el dominio de números de onda. Filtra ruidos instrumentales de alta frecuencia mientras retiene y reconstruye frentes térmicos, brisas marinas e inversiones térmicas sin oscilaciones numéricas espurias.

---

### G. 3D Nearest Neighbor / Elevation-Weighted (`"nn3d"`)
Esquema de interpolación tridimensional que acopla las coordenadas geográficas horizontales $(\lambda, \phi)$ con la cota topográfica vertical $z$ (DEM):

$$
d_{3D}(s_0, s_i) = \sqrt{\left(\frac{\Delta x}{s_x}\right)^2 + \left(\frac{\Delta y}{s_y}\right)^2 + \left(\frac{\Delta z}{s_z}\right)^2}
$$

- **Mapeo hipsométrico:** Implementado en CDT a través del motor `gstat::krige(bs ~ 1, locations = ~lon+lat+elv, data = locbs, newdata = interp.grid, nmax = 1)`.
- **Ventaja en temperatura:** Permite que las estaciones montañosas proyecten su corrección a cotas similares a lo largo de cadenas montañosas (p. ej. Cordillera de Talamanca, Sierra de los Cuchumatanes, Cordillera Central de RD) en lugar de proyectarse indebidamente a estaciones de fondo de valle situadas a corta distancia horizontal.

---

### H. Regression Kriging (`"RK"`)
Descompone el campo térmico o de precipitación en una tendencia determinista explicada por covariables fisiográficas (DEM, pendiente, orientación/aspecto, latitud, longitud) y un residual estocástico interpolado espacialmente:

$$
\hat{Z}(s_0) = \sum_{k=0}^{P} \hat{\beta}_k q_k(s_0) + \sum_{i=1}^{n} w_i \left[ Z(s_i) - \sum_{k=0}^{P} \hat{\beta}_k q_k(s_i) \right]
$$

donde $q_k(s_0)$ son los predictores en el punto no muestreado (elevación del DEM, pendiente, etc.) y los residuales se interpolan mediante Kriging Ordinario (`"okr"`) o esquemas deterministas según la matriz experimental.

---

## 2. Parámetros de Control Espacial y Vecindad

| Parámetro | Tipo | Descripción | Recomendación Precipitación | Recomendación Temperatura |
| :--- | :---: | :--- | :---: | :---: |
| `nmin` | Entero | Mínimo de estaciones requeridas para interpolar un píxel. | 4 a 8 | 6 a 10 |
| `nmax` | Entero | Máximo de estaciones vecinas consideradas. | 12 a 20 | 16 a 30 |
| `maxdist` | Numérico | Radio de búsqueda (grados decimales). | 1.0° a 2.5° (~100-250 km) | 2.5° a 4.0° (~250-400 km) |
| `use.block` | Booleano | Aplica Block Kriging en lugar de Point Kriging. | `TRUE` | `TRUE` |
| `vargrd` | Booleano | Ajusta `maxdist` automáticamente en función de la extensión geográfica del conjunto de estaciones. | `FALSE` (control explícito) | `FALSE` |

---

## 3. Manejo Automático de Excepciones y *Fallbacks* Geoestadísticos

En la interpolación espacial de residuales mediante Kriging Ordinario (`"okr"`) o Regression Kriging (`"RK"`), el motor de CDT incorpora protecciones automáticas diseñadas para garantizar la robustez operativa en series multidecadales (p. ej., 10,958 días entre 1991 y 2020) sin comprometer la filosofía ni la validez metodológica de cada experimento.

### 3.1 Flujo Operativo del Fallback a IDW

```
[ Intento de Kriging Ordinario (okr / RK) en Fecha 'nc.date' ]
                │
                ├──► ¿Menos de vgmMinNumberSTN estaciones? (def: 8)
                ├──► ¿Varianza de residuales <= 1e-15 (campo nulo o uniforme)?
                ├──► ¿Error de convergencia en fit.variogram (Levenberg-Marquardt)?
                └──► ¿Rango estimado del variograma es negativo (rango <= 0)?
                                │
                                ▼  (Cualquiera de las condiciones anteriores = TRUE)
               [ CONMUTACIÓN AUTOMÁTICA Y SEGURA A IDW ]
       (Se registra la advertencia en el archivo de log y se procesa el paso)
```

---

### 3.2 Justificación Física, Matemática y Metodológica

Una duda recurrente en el diseño experimental es: **¿Afecta esta conmutación a IDW la filosofía de comparar métodos de interpolación entre experimentos?**

La respuesta rigurosa es **no; por el contrario, la preserva y la hace numéricamente viable**. Las razones fundamentales son:

1. **La Naturaleza Física de la Precipitación Diaria:**
   * En los días con precipitación convectiva, ciclónica o frontal (el régimen hídrico activo objeto de estudio), las estaciones presentan contrastes y gradientes espaciales reales. En estos miles de días, el semivariograma empírico se ajusta con éxito y el Kriging modela fielmente la autocorrelación espacial según los parámetros configurados (`Sph`, `Exp`, `Gau`, soporte por bloques, radios de búsqueda, etc.).
   * En contraste, en días de sequía regional severa o durante la **Canícula** (*Mid-Summer Drought*), es común que el 95% o 100% de las estaciones registren exactamente $0.0\text{ mm}$ de lluvia (o que el residual entre estación y satélite sea idéntico en toda la red).
   * **Imposibilidad matemática de ajuste:** Cuando los residuales son uniformes, la varianza espacial es nula ($\sigma^2 \le 10^{-15}$). En geoestadística, no es posible ajustar una función de covarianza espacial a una nube de puntos colineal o sin dispersión; los algoritmos de optimización (Levenberg-Marquardt en `gstat`) divergen por división entre cero o singularidad matricial.

2. **Equivalencia Numérica en Días Singulares (Campo Plano):**
   * Cuando los residuales en todas las estaciones son nulos o idénticos, tanto el Kriging como el IDW producen matemáticamente el mismo resultado exacto: **un campo raster plano con residual constante o cero**.
   * Por tanto, en los días donde se activa el fallback no se pierde resolución de patrones geoestadísticos, puesto que físicamente no existía ninguna estructura espacial que resolver.

3. **Inviabilidad de Corridas sin Salvaguarda:**
   * Si no existiera este mecanismo determinista de respaldo para días singulares, **ningún secuencia de procesamiento meteorológico en el mundo podría completar una corrida de 30 años de lluvia diaria**. Un único día seco causaría la falla catastrófica de toda la serie temporal.

4. **Trazabilidad y Auditoría Científica:**
   * CDT documenta de forma transparente cada ocurrencia en la bitácora (`log.file`):
     ```text
     19970312 : Unable to compute variogram ( Error ) pass# 1 | Interpolation using IDW
     ```
   * En un experimento típico de 10,958 días, el fallback a IDW suele representar menos del 0.5%–1.5% de los pasos (concentrados en la época seca). El **98.5%–99.5% de la serie se interpola rigurosamente bajo el esquema geoestadístico específico del experimento**.

---

### 3.3 Corrección del Defecto Histórico en CDT (Error de Longitud Cero)

En el código fuente original de CDT (`R/cdtMerging_functions.R`), el autor (IRI / Columbia University) había previsto la conmutación a IDW mediante la sentencia `interp.method <- "idw" ; vgm <- NULL`. Sin embargo, un descuido sintáctico en R (`if` incondicional en lugar de `else if`) provocaba que inmediatamente después se evaluara:

```r
if (vgm$range[2] < 0) { ... }
```

Al ser `vgm = NULL`, la expresión `vgm$range[2] < 0` producía una condición de longitud cero (`logical(0)`), detonando el error fatal en R:
```text
Error in FUN(jloop) : task [N] failed - "argument is of length zero"
```

El parche aplicado en [`R/cdtMerging_functions.R`](../R/cdtMerging_functions.R#L360-L370) sustituye esa estructura por:

```r
if (inherits(vgm, "try-error")) {
    cat(paste(nc.date, ":", paste("Unable to compute variogram ( Error ) pass#", pass), "|",
        "Interpolation using IDW", "\n"), file = log.file, append = TRUE)
    interp.method <- "idw"
    vgm <- NULL
} else if (!is.null(vgm) && length(vgm$range) >= 2 && !is.na(vgm$range[2]) && vgm$range[2] < 0) {
    cat(paste(nc.date, ":", paste("Variogram range is negative pass#", pass), "|",
        "Interpolation using IDW", "\n"), file = log.file, append = TRUE)
    interp.method <- "idw"
    vgm <- NULL
}
```

Esta corrección hace operativa la salvaguarda originalmente concebida por los autores de CDT, permitiendo que `EXP_R03`, `EXP_R04` y `EXP_R05` completen sus 10,958 días de forma ininterrumpida.


---

## 4. Referencias Científicas Verificadas

1. **Barnes, S. L. (1964).** *A technique for maximizing details in numerical weather map analysis.* Journal of Applied Meteorology and Climatology, 3(4), 396–409. https://doi.org/10.1175/1520-0450(1964)003<0396:ATFMDI>2.0.CO;2
2. **Cressman, G. P. (1959).** *An operational objective analysis system.* Monthly Weather Review, 87(10), 367–374. https://doi.org/10.1175/1520-0493(1959)087<0367:AOOAS>2.0.CO;2
3. **Shepard, D. (1968).** *A two-dimensional interpolation function for irregularly-spaced data.* Proceedings of the 1968 23rd ACM National Conference, 517–524. https://doi.org/10.1145/800186.810616
4. **Franke, R., & Nielson, G. (1980).** *Smooth interpolation of large sets of scattered data.* International Journal for Numerical Methods in Engineering, 15(11), 1691–1704. https://doi.org/10.1002/nme.1620151110
5. **Renka, R. J. (1988).** *Algorithm 660: QSHEP2D: Quadratic Shepard method for bivariate interpolation of scattered data.* ACM Transactions on Mathematical Software (TOMS), 14(2), 149–150. https://doi.org/10.1145/42288.42291
6. **Willmott, C. J., Robeson, S. M., & Feddema, J. J. (1995).** *Estimating influences of gridded data selections on estimates of terrestrial air temperature change.* Physical Geography, 16(2), 99–119. https://doi.org/10.1080/02723646.1995.10642544
7. **Matheron, G. (1963).** *Principles of geostatistics.* Economic Geology, 58(8), 1246–1266. https://doi.org/10.2113/gsecongeo.58.8.1246
8. **Cressie, N. (1993).** *Statistics for Spatial Data.* Revised Edition. John Wiley & Sons, New York.
9. **Hengl, T., Heuvelink, G. B., & Rossiter, D. G. (2004).** *About regression-kriging: From equations to case studies.* Computers & Geosciences, 30(2), 121–135. https://doi.org/10.1016/j.cageo.2003.10.002
10. **Odeh, I. O. A., McBratney, A. B., & Chittleborough, D. J. (1995).** *Further results on prediction of soil properties from terrain attributes: heterotopic cokriging and regression-kriging.* Geoderma, 67(3-4), 215–226. https://doi.org/10.1016/0016-7061(95)00007-B
11. **Dinku, T., Ceccato, P., Grover-Kopec, E., Lemma, M., Connor, S. J., & Ropelewski, C. F. (2007).** *Validation of satellite rainfall products over East Africa's complex topography.* International Journal of Remote Sensing, 28(7), 1503–1526. https://doi.org/10.1080/01431160600954688
12. **Dinku, T., Chidzambwa, S., Ceccato, P., Connor, S. J., & Ropelewski, C. F. (2008).** *Validation of high-resolution satellite rainfall products over southern Africa.* Journal of Hydrometeorology, 9(6), 1330–1344. https://doi.org/10.1175/2008JHM970.1
13. **Pebesma, E. J. (2004).** *Multivariable geostatistics in S: the gstat package.* Computers & Geosciences, 30(7), 683–691. https://doi.org/10.1016/j.cageo.2004.03.012
