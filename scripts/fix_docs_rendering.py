import os
import shutil
import re

def fix_all():
    print("Fixing LaTeX and Mermaid rendering issues across docs...")

    # 1. Fix docs/02_gridding_merging_fundamentos.md
    f02 = os.path.join("docs", "02_gridding_merging_fundamentos.md")
    with open(f02, "r", encoding="utf-8") as fp:
        t02 = fp.read()

    old_cressman = r"$$W_{ij} = \begin{cases} \dfrac{R^2 - d_{ij}^2}{R^2 + d_{ij}^2} & \text{si } d_{ij} < R \\ 0 & \text{si } d_{ij} \ge R \end{cases}$$"
    new_cressman = """$$
W_{ij} = \\begin{cases} 
\\dfrac{R^2 - d_{ij}^2}{R^2 + d_{ij}^2} & \\text{si } d_{ij} < R \\\\
0 & \\text{si } d_{ij} \\ge R 
\\end{cases}
$$"""
    if old_cressman in t02:
        t02 = t02.replace(old_cressman, new_cressman)
        with open(f02, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(t02)
        print("Fixed docs/02_gridding_merging_fundamentos.md")
    else:
        # Regex replacement in case of whitespace
        t02 = re.sub(
            r"\$\$W_\{ij\}\s*=\s*\\begin\{cases\}.*?\\end\{cases\}\$\$",
            new_cressman.replace("\\", "\\\\"),
            t02,
            flags=re.DOTALL
        )
        with open(f02, "w", encoding="utf-8", newline="\n") as fp:
            fp.write(t02)
        print("Fixed docs/02 (regex)")

    # 2. Fix docs/03_metodos_interpolacion_residuales.md
    f03 = os.path.join("docs", "03_metodos_interpolacion_residuales.md")
    with open(f03, "r", encoding="utf-8") as fp:
        t03 = fp.read()
    
    t03 = re.sub(
        r"\$\$W_i\s*=\s*\\begin\{cases\}.*?\\end\{cases\}\$\$",
        """$$
W_i = \\begin{cases} 
\\dfrac{R_c^2 - d_i^2}{R_c^2 + d_i^2}, & d_i < R_c \\\\
0, & d_i \\ge R_c 
\\end{cases}
$$""".replace("\\", "\\\\"),
        t03,
        flags=re.DOTALL
    )
    with open(f03, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(t03)
    print("Fixed docs/03_metodos_interpolacion_residuales.md")

    # 3. Fix docs/04_merging_precipitacion_rnor.md
    f04 = os.path.join("docs", "04_merging_precipitacion_rnor.md")
    with open(f04, "r", encoding="utf-8") as fp:
        t04 = fp.read()

    t04 = re.sub(
        r"\$\$\\text\{Mask\}\(s\)\s*=\s*\\begin\{cases\}\s*0\s*&\s*\\text\{si \}\s*P\(s\)\s*<\s*0\.5\s*\\\\\s*1\s*&\s*\\text\{si \}\s*P\(s\)\s*\\geq\s*0\.5\s*\\end\{cases\}\$\$",
        """$$
\\text{Mask}(s) = \\begin{cases} 
0 & \\text{si } P(s) < 0.5 \\\\
1 & \\text{si } P(s) \\geq 0.5 
\\end{cases}
$$""".replace("\\", "\\\\"),
        t04
    )

    t04 = re.sub(
        r"\$\$\\text\{Mask\}\(s\)\s*=\s*\\begin\{cases\}\s*0\s*&\s*\\text\{si \}\s*P\(s\)\s*<\s*0\.1\s*\\\\\s*P\(s\)\s*&\s*\\text\{si \}\s*P\(s\)\s*\\geq\s*0\.1\s*\\end\{cases\}\$\$",
        """$$
\\text{Mask}(s) = \\begin{cases} 
0 & \\text{si } P(s) < 0.1 \\\\
P(s) & \\text{si } P(s) \\geq 0.1 
\\end{cases}
$$""".replace("\\", "\\\\"),
        t04
    )

    t04 = re.sub(
        r"\$\$\\text\{Mask\}\(s\)\s*=\s*\\begin\{cases\}\s*0\s*&\s*\\text\{si \}\s*P\(s\)\s*<\s*0\.25\s*\\\\\s*P\(s\)\s*&\s*\\text\{si \}\s*0\.25\s*\\le\s*P\(s\)\s*<\s*0\.75\s*\\\\\s*1\s*&\s*\\text\{si \}\s*P\(s\)\s*\\geq\s*0\.75\s*\\end\{cases\}\$\$",
        """$$
\\text{Mask}(s) = \\begin{cases} 
0 & \\text{si } P(s) < 0.25 \\\\
P(s) & \\text{si } 0.25 \\le P(s) < 0.75 \\\\
1 & \\text{si } P(s) \\geq 0.75 
\\end{cases}
$$""".replace("\\", "\\\\"),
        t04
    )
    with open(f04, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(t04)
    print("Fixed docs/04_merging_precipitacion_rnor.md")

    # 4. Fix docs/05_merging_temperatura_dem.md
    f05 = os.path.join("docs", "05_merging_temperatura_dem.md")
    with open(f05, "r", encoding="utf-8") as fp:
        t05 = fp.read()

    # Isolate display math with clear newlines
    old_formula_05 = r"$$T_{\text{downscaled}}(s_{\text{fine}}) = \beta_0 + \beta_{\text{elv}} \cdot \text{DEM}_{\text{fine}}(s_{\text{fine}}) + \hat{R}_{\text{fine}}(s_{\text{fine}})$$"
    new_formula_05 = """

$$
T_{\\text{downscaled}}(s_{\\text{fine}}) = \\beta_0 + \\beta_{\\text{elv}} \\cdot \\text{DEM}_{\\text{fine}}(s_{\\text{fine}}) + \\hat{R}_{\\text{fine}}(s_{\\text{fine}})
$$

"""
    if old_formula_05 in t05:
        t05 = t05.replace(old_formula_05, new_formula_05)
    else:
        t05 = re.sub(
            r"\$\$T_\{?\\text\{downscaled\}\}?\(s_\{?\\text\{fine\}\}?\)\s*=.*?\$\$",
            new_formula_05.strip().replace("\\", "\\\\"),
            t05
        )

    old_formula_05b = r"$$T_{\text{downscaled}} = \beta_0 + \beta_{\text{elv}} \cdot \text{DEM}_{\text{fino}} + \hat{R}$$"
    new_formula_05b = """

$$
T_{\\text{downscaled}} = \\beta_0 + \\beta_{\\text{elv}} \\cdot \\text{DEM}_{\\text{fino}} + \\hat{R}
$$

"""
    if old_formula_05b in t05:
        t05 = t05.replace(old_formula_05b, new_formula_05b)

    with open(f05, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(t05)
    print("Fixed docs/05_merging_temperatura_dem.md")

    # 5. Fix docs/07_flujo_completo_temperatura_chirts.md
    f07 = os.path.join("docs", "07_flujo_completo_temperatura_chirts.md")
    with open(f07, "r", encoding="utf-8") as fp:
        t07 = fp.read()

    # Line 57 and line 84
    old_07_a = r"$$T_{\text{downscaled}}(s_{\text{fino}}) = f_m(\text{DEM}_{\text{fino}}) + \hat{R}_{\text{fino}}(s_{\text{fino}})$$"
    new_07_a = """

$$
T_{\\text{downscaled}}(s_{\\text{fino}}) = f_m(\\text{DEM}_{\\text{fino}}) + \\hat{R}_{\\text{fino}}(s_{\\text{fino}})
$$

"""
    if old_07_a in t07:
        t07 = t07.replace(old_07_a, new_07_a)
    else:
        t07 = re.sub(
            r"\s*\$\$T_\{?\\text\{downscaled\}\}?\(s_\{?\\text\{fino\}\}?\)\s*=.*?\$\$",
            new_07_a.replace("\\", "\\\\"),
            t07
        )

    old_07_b = r"$$\hat{T}_{\text{corrected}}(s) = F_{\text{stn}}^{-1}\left( F_{\text{proxy}}(T_{\text{downscaled}}(s)) \right)$$"
    new_07_b = """

$$
\\hat{T}_{\\text{corrected}}(s) = F_{\\text{stn}}^{-1}\\left( F_{\\text{proxy}}(T_{\\text{downscaled}}(s)) \\right)
$$

"""
    if old_07_b in t07:
        t07 = t07.replace(old_07_b, new_07_b)
    else:
        t07 = re.sub(
            r"\s*\$\$\\hat\{T\}_\{?\\text\{corrected\}\}?\(s\)\s*=.*?\$\$",
            new_07_b.replace("\\", "\\\\"),
            t07
        )

    with open(f07, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(t07)
    print("Fixed docs/07_flujo_completo_temperatura_chirts.md")

    # 6. Fix docs/13_influencia_dem_batimetria_desescalado_temperatura.md
    f13 = os.path.join("docs", "13_influencia_dem_batimetria_desescalado_temperatura.md")
    with open(f13, "r", encoding="utf-8") as fp:
        t13 = fp.read()

    # Block 1 edge labels
    t13 = t13.replace(
        "A -.->|Picos: 3,820 m (Chirripó)| C[\"Δz = z_real - z_modelo <br> (hasta +1,800 m)\"]",
        "A -.->|\"Picos: 3,820 m Chirripó\"| C[\"Δz = z_real - z_modelo <br> (hasta +1,800 m)\"]"
    )
    t13 = t13.replace(
        "A -.->|Picos: 3,820 m (Chirrip)| C[\"Δz = z_real - z_modelo <br> (hasta +1,800 m)\"]",
        "A -.->|\"Picos: 3,820 m Chirripó\"| C[\"Δz = z_real - z_modelo <br> (hasta +1,800 m)\"]"
    )
    t13 = t13.replace(
        "B -.->|Promedio de Celda: ~2,000 m| C",
        "B -.->|\"Promedio de Celda: 2,000 m\"| C"
    )

    # Block 2 edge labels
    t13 = t13.replace(
        "DEM -->|GEBCO con Batimetría Negativa <br> -8,390 m <= z <= +5,611 m| Bati[\"Inclusión de cotas submarinas en la regresión\"]",
        "DEM -->|\"GEBCO con Batimetria Negativa (-8,390 m a +5,611 m)\"| Bati[\"Inclusión de cotas submarinas en la regresión\"]"
    )
    t13 = t13.replace(
        "DEM -->|GEBCO con Batimetra Negativa <br> -8,390 m <= z <= +5,611 m| Bati[\"Inclusin de cotas submarinas en la regresin\"]",
        "DEM -->|\"GEBCO con Batimetria Negativa (-8,390 m a +5,611 m)\"| Bati[\"Inclusión de cotas submarinas en la regresión\"]"
    )
    t13 = t13.replace(
        "DEM -->|DEM Continental Terrestre <br> z >= 0.0 m (Nivel del mar / Máscara)| Cont[\"Física Confinada a la Troposfera Emergida\"]",
        "DEM -->|\"DEM Continental Terrestre (z >= 0.0 m)\"| Cont[\"Física Confinada a la Troposfera Emergida\"]"
    )
    t13 = t13.replace(
        "DEM -->|DEM Continental Terrestre <br> z >= 0.0 m (Nivel del mar / Mscara)| Cont[\"Fsica Confinada a la Troposfera Emergida\"]",
        "DEM -->|\"DEM Continental Terrestre (z >= 0.0 m)\"| Cont[\"Física Confinada a la Troposfera Emergida\"]"
    )

    with open(f13, "w", encoding="utf-8", newline="\n") as fp:
        fp.write(t13)
    print("Fixed docs/13_influencia_dem_batimetria_desescalado_temperatura.md")

    # 7. Move docs/10_matriz_maestra_experimentos_y_guia_metodologica.md to docs-private/
    src_10 = os.path.join("docs", "10_matriz_maestra_experimentos_y_guia_metodologica.md")
    dst_10 = os.path.join("docs-private", "10_matriz_maestra_experimentos_y_guia_metodologica.md")
    if os.path.exists(src_10):
        shutil.copy2(src_10, dst_10)
        os.remove(src_10)
        print("Moved docs/10_matriz_maestra_experimentos_y_guia_metodologica.md to docs-private/")

    # 8. Check docs/README.md to update any reference to doc 10
    readme_path = os.path.join("docs", "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as fp:
            r_text = fp.read()
        if "10_matriz_maestra_experimentos_y_guia_metodologica.md" in r_text:
            r_text = r_text.replace(
                "10_matriz_maestra_experimentos_y_guia_metodologica.md",
                "../docs-private/10_matriz_maestra_experimentos_y_guia_metodologica.md (privado/interno)"
            )
            with open(readme_path, "w", encoding="utf-8", newline="\n") as fp:
                fp.write(r_text)
            print("Updated docs/README.md references")

if __name__ == "__main__":
    fix_all()
