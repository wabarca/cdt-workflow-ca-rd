# 05. Fusión de Temperatura (Temperature Data) y Modelado Topográfico

## 1. Características del Campo de Temperatura

A diferencia de la precipitación, la temperatura (Tmax, Tmin o Tmean) se caracteriza por:
1. **Continuidad espacial:** No presenta vacíos en cero ni discontinuidades abruptas en condiciones normales.
2. **Fuerte dependencia orográfica:** El factor dominante en la variación espacial de la temperatura es la **altitud** a través del gradiente adiabático o gradiente térmico vertical (*lapse rate*, típicamente entre $-5.0$ y $-6.5\ ^\circ\text{C}$ por cada $1000\text{ m}$ de ascenso).
3. **Efectos de ladera e insolación:** La orientación (*aspect*) y la pendiente (*slope*) influyen significativamente en la radiación solar recibida y por ende en las temperaturas máximas diurnas.
4. **Gradiente latitudinal / continental:** Variaciones térmicas a escala sinóptica explicadas por la latitud y longitud.

Por esta razón, en temperatura el método de fusión estándar y más recomendado en CDT es **Regression Kriging (`"RK"`) con Modelo Digital de Elevación (DEM)**.

---

## 2. Configuración de Parámetros para Temperatura

En `cdtMergingTempCMD`:

```r
cdtMergingTempCMD(
  time.step = "daily",
  dates = list(from = "range", pars = list(start = "20230101", end = "20230131")),
  station.data = list(file = "data/tmax_stn.csv", sep = ",", na.strings = "-99"),
  netcdf.data = list(
    dir = "data/era5_temp", 
    format = "tmax_era5_%s%s%s.nc",
    varid = "t2m", 
    ilon = 1, 
    ilat = 2
  ),
  merge.method = list(
    method = "RK",               # Regression Kriging
    nrun = 3, 
    pass = c(1, 0.75, 0.5)
  ),
  interp.method = list(
    method = "idw",              # o "okr" si hay suficientes estaciones
    nmin = 8, 
    nmax = 24, 
    maxdist = 3.5,               # Radio más amplio que en lluvia (3.5°)
    use.block = TRUE, 
    vargrd = FALSE
  ),
  auxvar = list(
    dem = TRUE,                  # Elevación DEM
    slope = TRUE,                # Pendiente
    aspect = FALSE,              # Orientación
    lon = TRUE,                  # Longitud
    lat = TRUE                   # Latitud
  ),
  dem.data = list(
    file = "data/dem_srtm_elevation.nc", 
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

## 3. Modelado Estadístico por Regresión (GLM en RK)

Para cada fecha, CDT ajusta un Modelo Lineal Generalizado (familia Gaussiana) con las estaciones disponibles:

$$\text{Temp}(s_i) = \beta_0 + \beta_1 \cdot \text{Reanalysis}(s_i) + \beta_2 \cdot \text{DEM}(s_i) + \beta_3 \cdot \text{Slope}(s_i) + \beta_4 \cdot \text{Lon}(s_i) + \beta_5 \cdot \text{Lat}(s_i) + \varepsilon(s_i)$$

1. **Derivación topográfica automática:**
   Si `slope = TRUE` o `aspect = TRUE`, CDT calcula internamente las matrices de pendiente y orientación a partir del archivo NetCDF del DEM mediante la función interna `raster.slope.aspect()`.
2. **Evaluación de la tendencia espacial:**
   Se evalúa la ecuación ajustada en toda la malla de alta resolución del DEM:
   $$\text{Trend}(s) = \hat{\beta}_0 + \hat{\beta}_1 \text{Reanalysis}(s) + \hat{\beta}_2 \text{DEM}(s) + \hat{\beta}_3 \text{Slope}(s) + \hat{\beta}_4 \text{Lon}(s) + \hat{\beta}_5 \text{Lat}(s)$$
3. **Interpolación de los residuales térmicos:**
   Los residuales no explicados por la topografía ni por el reanálisis ($\varepsilon_i = \text{Obs}_i - \text{Trend}_i$) representan anomalías locales (inversiones térmicas en valles, brisas costeras, islas de calor urbano) y se interpolan hacia toda la malla con el método seleccionado (`idw` u `okr`).

---

## 4. Límites Físicos y Control de Calidad

- **Límites de temperatura en CDT:** $[-40\ ^\circ\text{C}, +50\ ^\circ\text{C}]$.
- En el caso de variables derivadas (presión atmosférica, humedad relativa), CDT ajusta los rangos correspondientes:
  - Humedad Relativa (`"rh"`): $[0, 100]\%$.
  - Presión Superficial (`"pres"`): $[700, 1100]\text{ hPa}$.
  - Presión a Nivel del Mar (`"prmsl"`): $[850, 1100]\text{ hPa}$.
  - Radiación (`"rad"`): $[0, 1300]\text{ W/m}^2$.
