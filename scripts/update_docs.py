import os

def update_03_metodos():
    doc_path = os.path.join("docs", "03_metodos_interpolacion_residuales.md")
    with open(doc_path, "r", encoding="utf-8") as f:
        text = f.read()

    replacement_methods = """### C. Modified Shepard Interpolation (`"shepard"`)
Es una variante local de IDW que utiliza una función de influencia suave y corrige la ponderación mediante derivadas directas de primer orden para evitar el efecto de "ojo de buey" (*bull's-eye*) característico del IDW clásico.

$$\\text{Peso base: } w_i = \\left( \\frac{\\max(0, R_w - d_i)}{R_w \\cdot d_i} \\right)^p$$

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

$$W_i = \\begin{cases} \\dfrac{R_c^2 - d_i^2}{R_c^2 + d_i^2}, & d_i < R_c \\\\ 0, & d_i \\ge R_c \\end{cases}$$

- **Mecanismo iterativo:** Se ejecuta en múltiples pasadas (típicamente 4 pasadas con radios decrecientes: $1.0 R_c, 0.75 R_c, 0.50 R_c, 0.25 R_c$), capturando primero anomalías de escala sinóptica y ajustando progresivamente las celdas convectivas o núcleos orográficos locales.

---

### F. Barnes Objective Analysis (`"BSc"` / `"barnes"`)
Análisis objetivo de dos o más pasadas con filtro de ponderación Gaussiano en el dominio espacial continuo:

$$w_i = \\exp\\left( -\\frac{d_i^2}{4 c_k} \\right)$$

donde $c_k$ es el parámetro de escala espacial ($c_2 = \\gamma c_1$, con $\\gamma \\in (0, 1)$, típicamente $\\gamma = 0.35$ a $0.5$).
- **Respuesta espectral:** Actúa como un filtro pasabajas riguroso con respuesta analítica conocida en el dominio de números de onda. Filtra ruidos instrumentales de alta frecuencia mientras retiene y reconstruye frentes térmicos, brisas marinas e inversiones térmicas sin oscilaciones numéricas espurias.

---

### G. 3D Nearest Neighbor / Elevation-Weighted (`"nn3d"`)
Esquema de interpolación tridimensional que acopla las coordenadas geográficas horizontales $(\\lambda, \\phi)$ con la cota topográfica vertical $z$ (DEM):

$$d_{3D}(s_0, s_i) = \\sqrt{\\left(\\frac{\\Delta x}{s_x}\\right)^2 + \\left(\\frac{\\Delta y}{s_y}\\right)^2 + \\left(\\frac{\\Delta z}{s_z}\\right)^2}$$

- **Mapeo hipsométrico:** Implementado en CDT a través del motor `gstat::krige(bs ~ 1, locations = ~lon+lat+elv, data = locbs, newdata = interp.grid, nmax = 1)`.
- **Ventaja en temperatura:** Permite que las estaciones montañosas proyecten su corrección a cotas similares a lo largo de cadenas montañosas (p. ej. Cordillera de Talamanca, Sierra de los Cuchumatanes, Cordillera Central de RD) en lugar de proyectarse indebidamente a estaciones de fondo de valle situadas a corta distancia horizontal.

---

### H. Regression Kriging (`"RK"`)
Descompone el campo térmico o de precipitación en una tendencia determinista explicada por covariables fisiográficas (DEM, pendiente, orientación/aspecto, latitud, longitud) y un residual estocástico interpolado espacialmente:

$$\\hat{Z}(s_0) = \\sum_{k=0}^{P} \\hat{\\beta}_k q_k(s_0) + \\sum_{i=1}^{n} w_i \\left[ Z(s_i) - \\sum_{k=0}^{P} \\hat{\\beta}_k q_k(s_i) \\right]$$

donde $q_k(s_0)$ son los predictores en el punto no muestreado (elevación del DEM, pendiente, etc.) y los residuales se interpolan mediante Kriging Ordinario (`"okr"`) o esquemas deterministas según la matriz experimental."""

    references_section = """

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
"""

    target_old = """### C. Modified Shepard Interpolation (`"shepard"`)
Es una variante local de IDW que utiliza una función de influencia suave y corrige la ponderación mediante derivadas directas de primer orden para evitar el efecto de "ojo de buey" (*bull's-eye*) característico del IDW clásico.

$$\\text{Peso base: } w_i = \\left( \\frac{\\max(0, R_w - d_i)}{R_w \\cdot d_i} \\right)^p$$

- Potencia por defecto: `powerWeightShepard = 0.7`.

---

### D. Spheremap Interpolation (`"sphere"`)
Diseñado para compensar el **agrupamiento espacial (*clustering*)** de estaciones:
- Si varias estaciones están muy juntas en una misma subcuenca, una interpolación convencional sobreponderaría esa región.
- Spheremap calcula pesos angulares que reparten la influencia entre cuadrantes alrededor del punto objetivo, evitando que estaciones redundantes distorsionen la estimación."""

    norm_text = text.replace("\r\n", "\n")
    norm_target = target_old.replace("\r\n", "\n")

    if norm_target in norm_text:
        norm_text = norm_text.replace(norm_target, replacement_methods)
        norm_text = norm_text + references_section
        with open(doc_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(norm_text)
        print("Updated 03_metodos_interpolacion_residuales.md successfully.")
    else:
        print("Target not found!")

if __name__ == "__main__":
    update_03_metodos()
