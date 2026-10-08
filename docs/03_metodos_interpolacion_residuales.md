# 03. Métodos y Parámetros de Interpolación de Residuales

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

$$\hat{R}(s_0) = \frac{\sum_{i=1}^{n} w_i R(s_i)}{\sum_{i=1}^{n} w_i}, \quad w_i = \frac{1}{d(s_0, s_i)^p}$$

- **Ventajas:** Extremadamente rápido, determinista, no requiere ajuste de parámetros estocásticos y garantiza que el residual interpolado no superará los extremos observados.
- **Potencia por defecto:** $p = 2.0$ (modificable con `merging.options(powerWeightIDW = ...)`).

---

### B. Ordinary Kriging (`"okr"`)
Considera tanto la distancia como la estructura de correlación espacial de los datos a través del **semivariograma**:

$$\gamma(h) = \frac{1}{2 N(h)} \sum_{i=1}^{N(h)} \left[ R(s_i) - R(s_i + h) \right]^2$$

1. **Ajuste automático de variograma (`fit.variogram`):**
   CDT ajusta un modelo teórico seleccionando el mejor ajuste entre:
   - **`"Sph"` (Esférico):** Crecimiento lineal cerca del origen que alcanza una meseta bien definida.
   - **`"Exp"` (Exponencial):** Crecimiento pronunciado inicial que se aproxima asintóticamente a la meseta.
   - **`"Gau"` (Gaussiano):** Comportamiento parabólico suave cerca del origen (adecuado para campos continuos).
   - **`"Pen"` (Pentasférico):** Variante del esférico con mayor rango de correlación.

2. **Block Kriging (`use.block = TRUE`):**
   En lugar de predecir el residual en un punto matemático sin dimensión, Kriging integra la predicción sobre el área espacial de la celda NetCDF:
   $$\hat{R}(B) = \frac{1}{|B|} \int_{B} \hat{R}(s) ds$$
   Esto reduce drásticamente el error de soporte espacial cuando se combina información puntual con celdas satelitales de $5\text{ km}$ o $25\text{ km}$.
   - Opciones en `merging.options()`: `blockType = "gaussian"` o `"userdefined"`.

---

### C. Modified Shepard Interpolation (`"shepard"`)
Es una variante local de IDW que utiliza una función de influencia suave y corrige la ponderación mediante derivadas directas de primer orden para evitar el efecto de "ojo de buey" (*bull's-eye*) característico del IDW clásico.

$$\text{Peso base: } w_i = \left( \frac{\max(0, R_w - d_i)}{R_w \cdot d_i} \right)^p$$
- Potencia por defecto: `powerWeightShepard = 0.7`.

---

### D. Spheremap Interpolation (`"sphere"`)
Diseñado para compensar el **agrupamiento espacial (*clustering*)** de estaciones:
- Si varias estaciones están muy juntas en una misma subcuenca, una interpolación convencional sobreponderaría esa región.
- Spheremap calcula pesos angulares que reparten la influencia entre cuadrantes alrededor del punto objetivo, evitando que estaciones redundantes distorsionen la estimación.

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

## 3. Manejo Automático de Excepciones y *Fallbacks*

El motor de CDT incorpora protecciones automáticas para garantizar que pipelines masivos de cientos o miles de fechas no se interrumpan:

```
[ Intento de Kriging Ordinario (okr) ]
                │
                ├─► ¿Menos de vgmMinNumberSTN estaciones? (def: 8)
                ├─► ¿Varianza de residuales <= 1e-15?
                ├─► ¿Error en fit.variogram?
                └─► ¿Rango del variograma negativo?
                                │
                                ▼  (Cualquiera de los anteriores = TRUE)
               [ FALLBACK AUTOMÁTICO A IDW ]
                (Se registra la advertencia en log_file.txt y continúa)
```
