# 04. Fusión de Precipitación (Rainfall Data) y Máscara Rain-No-Rain

## 1. Desafíos Físicos y Estadísticos de la Precipitación

A diferencia de la temperatura o la presión atmosférica, la lluvia presenta propiedades estadísticas particulares:
1. **Discontinuidad espacial:** Es un proceso mixto (campos continuos de lluvia intercalados con extensas áreas de precipitación cero).
2. **Distribución altamente asimétrica:** Valores positivos con colas largas (distribución Gamma o Log-normal).
3. **Generación de "lloviznas espurias":** La interpolación clásica de residuales aditivos puede provocar valores positivos pequeños ($0.1$ a $1.5\text{ mm}$) en zonas donde tanto el satélite como las estaciones indicaban día seco.

Para solucionar este problema, CDT integra el módulo de **Máscara Rain-No-Rain (`RnoR`)**.

---

## 2. Configuración del Módulo `RnoR`

En la llamada a `cdtMergingPrecipCMD`:

```r
RnoR = list(
  use = TRUE,     # Activar la máscara
  wet = 1.0,      # Umbral para definir día lluvioso vs seco (en mm)
  smooth = TRUE   # Aplicar filtro de suavizado espacial
)
```

Y en `merging.options()`:

```r
merging.options(
  RnoRModel = "logit",           # Modelo: "logit" o "additive"
  RnoRCutOff = 3,                # Estrategia de corte: 1, 2 o 3
  RnoRUseMerged = FALSE,         # Usar el producto recién fusionado (TRUE) o el satélite original (FALSE)
  RnoRaddCoarse = FALSE,         # Incluir malla gruesa para estabilidad en bordes
  RnoRSmoothingPixels = 2,       # Radio del filtro de suavizado
  saveRnoR = FALSE,              # Guardar la máscara en formato .rds
  dirRnoR = "D:/Salidas/Mascaras"
)
```

---

## 3. Algoritmo Paso a Paso de la Máscara Rain-No-Rain

```
1. Binarización de Estaciones:
   rnr_stn = 1 si Obs >= wet; 0 si Obs < wet

2. Binarización de Campo Gridded:
   rnr_grd = 1 si Proxy >= wet; 0 si Proxy < wet

3. Estimación de Probabilidad Espacial de Lluvia (rnr_field):
   - Si RnoRModel == "logit": Regresión Logística Espacial
   - Si RnoRModel == "additive": Interpolación directa de discrepancias

4. Aplicación de Frontera de Decisión (RnoRCutOff 1, 2 o 3) -> Mask(s)

5. Suavizado Espacial (Opcional):
   Mask_smooth = (2 * Mask + SmoothMatrix(Mask, pixels)) / 3

6. Modulación Final:
   Precip_Merged(s) = Precip_Calculada(s) * Mask_smooth(s)
```

---

## 4. Opciones de Modelado (`RnoRModel`)

### A. Modelo Logístico (`"logit"`) - Predeterminado
Ajusta un modelo de regresión logística para estimar la probabilidad posterior de que ocurra precipitación en la celda $s$:

$$\ln\left(\frac{P(s)}{1 - P(s)}\right) = \alpha_0 + \alpha_1 \cdot \text{Proxy}(s) + \text{InterpResidualesLogit}(s)$$

Garantiza probabilidades estrictamente acotadas en el intervalo $[0, 1]$.

### B. Modelo Aditivo (`"additive"`)
Trata la presencia/ausencia como un campo continuo $[0, 1]$ e interpola los residuales binarios linealmente.

---

## 5. Estrategias de Frontera de Decisión (`RnoRCutOff`)

CDT implementa tres funciones de transferencia para transformar la probabilidad $P(s)$ en el factor multiplicativo final:

### Opción 1: Corte Binario Duro (*Hard Threshold*)
$$\text{Mask}(s) = \begin{cases} 0 & \text{si } P(s) < 0.5 \\ 1 & \text{si } P(s) \geq 0.5 \end{cases}$$
- *Comportamiento:* Genera límites muy definidos entre lluvia y no lluvia. Puede crear gradientes abruptos en los bordes de tormentas.

### Opción 2: Supresión de Baja Probabilidad
$$\text{Mask}(s) = \begin{cases} 0 & \text{si } P(s) < 0.1 \\ P(s) & \text{si } P(s) \geq 0.1 \end{cases}$$
- *Comportamiento:* Elimina lloviznas marginales por debajo del 10% de probabilidad, pero modula la intensidad de la precipitación con la probabilidad estimada.

### Opción 3: Rampa Sigmoide Suave (*Smooth Ramp*) - **Recomendada**
$$\text{Mask}(s) = \begin{cases} 0 & \text{si } P(s) < 0.25 \\ P(s) & \text{si } 0.25 \le P(s) < 0.75 \\ 1 & \text{si } P(s) \geq 0.75 \end{cases}$$
- *Comportamiento:* Ofrece el mejor equilibrio: anula con seguridad zonas secas (<25%), preserva al 100% las áreas de lluvia consolidada (>75%) y genera una transición espacial continua en el área perimetral.

---

## 6. Control de Límites Físicos

En el archivo [`R/cdtMerging_functions.R`](file:///d:/Workspace/CDT-8.0/R/cdtMerging_functions.R#L51-L59), CDT aplica límites estrictos tras la recomposición:

- **Precipitación:** $\text{Límites} = [0, 5000]\text{ mm}$.
  - Cualquier valor negativo resultante de la resta de residuales se trunca automáticamente a $0\text{ mm}$.
  - Valores que superen $5000\text{ mm}$ se truncan al máximo físico.
- Si una celda presenta valor no disponible (`NA`), se restituye el valor del NetCDF original para garantizar un producto sin huecos.
