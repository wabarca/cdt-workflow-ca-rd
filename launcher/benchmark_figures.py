"""
CDT 8.0 - Benchmark Static Diagnostic Figures Generator
Generates high-resolution (300 DPI) diagnostic figures
for climate grid reconstruction and bias correction benchmarking in Central America.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
import re
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# Configure clean scientific matplotlib style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'axes.edgecolor': '#94a3b8',
    'axes.linewidth': 0.8,
    'grid.color': '#e2e8f0',
    'grid.linestyle': '--',
    'grid.alpha': 0.7
})


def _extract_exp_short_label(exp_id: str) -> str:
    """Extracts clean short label Exp_XX from experiment ID."""
    m = re.search(r'(?:R|TX|TN)?(\d+)', exp_id)
    if m:
        return f"Exp_{int(m.group(1)):02d}"
    return exp_id[:8]


def generate_kge_boxplots_figure(
    df_stations_var: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    winner_id: Optional[str] = None
) -> str:
    """Generates horizontal boxplot of KGE across validation stations for all experiments of a variable."""
    if df_stations_var.empty or "kge" not in df_stations_var.columns:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Order experiments by median KGE
    medians = df_stations_var.groupby("experiment_id")["kge"].median().sort_values(ascending=True)
    ordered_exps = medians.index.tolist()

    palette = {}
    ylabels = []
    for e in ordered_exps:
        is_ctrl = ("00" in e or "Raw" in e)
        is_win = (e == winner_id) if winner_id else (("R15" in e and var_type == "rainfall") or ("TX11" in e and var_type == "tmax") or ("TN10" in e and var_type == "tmin"))
        if is_win:
            palette[e] = "#059669" # Emerald
            ylabels.append(f"[OPTIMO] {e}")
        elif is_ctrl:
            palette[e] = "#1e293b" # Dark Slate
            ylabels.append(f"[REJILLA ORIGINAL] {e}")
        else:
            palette[e] = "#38bdf8" if var_type == "rainfall" else ("#ea580c" if var_type == "tmax" else "#8b5cf6")
            ylabels.append(e)

    fig_height = max(5.5, len(ordered_exps) * 0.38 + 1.8)
    fig, ax = plt.subplots(figsize=(10.5, fig_height), dpi=300)

    sns.boxplot(
        data=df_stations_var,
        y="experiment_id",
        x="kge",
        order=ordered_exps,
        palette=palette,
        hue="experiment_id",
        legend=False,
        ax=ax,
        fliersize=3,
        linewidth=1.0,
        width=0.6,
        boxprops=dict(alpha=0.85)
    )

    # Rejilla Original median reference line (without loose 00)
    ctrl_rows = df_stations_var[df_stations_var["experiment_id"].str.contains(r"00|Raw", regex=True)]
    if not ctrl_rows.empty:
        ctrl_median = ctrl_rows["kge"].median()
        ax.axvline(ctrl_median, color="#e11d48", linestyle="--", linewidth=1.2,
                   label=f"Mediana Rejilla Original (Control): {ctrl_median:.3f}")
        ax.legend(loc="upper left", frameon=True, facecolor="white", framealpha=0.9, fontsize=8.5)

    ax.set_yticks(range(len(ordered_exps)))
    ax.set_yticklabels(ylabels, fontsize=8.5)

    for tick_label in ax.get_yticklabels():
        text = tick_label.get_text()
        if "[OPTIMO]" in text:
            tick_label.set_color("#059669")
            tick_label.set_fontweight("bold")
        elif "[REJILLA ORIGINAL]" in text:
            tick_label.set_color("#0f172a")
            tick_label.set_fontweight("bold")

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ax.set_title(f"Figura 1: Distribucion de Eficiencia KGE en las 29 Estaciones Holdout\n{var_title} (1991-2020) • Ordenados por Mediana de Rendimiento", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Kling-Gupta Efficiency (KGE)", fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Experimento Evaluado", fontsize=9.5, fontweight="bold")
    ax.set_xlim(min(-0.3, df_stations_var["kge"].quantile(0.01)), max(1.02, df_stations_var["kge"].quantile(0.99)))

    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)


def generate_pareto_scatter_figure(
    df_var: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    unit: str = "mm"
) -> str:
    """
    Generates Pareto frontier scatter plot of Precision (RMSE) vs Efficiency (KGE).
    Features orthogonal dotted projection lines to X and Y axes, dynamic y-axis scaling
    tailored to the actual metric range (no large empty gaps), and collision-aware Exp_XX labels.
    """
    if df_var.empty or "rmse" not in df_var.columns or "kge" not in df_var.columns:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10.5, 7.0), dpi=300)
    base_color = "#0284c7" if var_type == "rainfall" else ("#ea580c" if var_type == "tmax" else "#7c3aed")

    candidates_df = df_var[~df_var["is_winner"] & ~df_var["is_control"]].copy()
    win_row = df_var[df_var["is_winner"]].iloc[0] if not df_var[df_var["is_winner"]].empty else None
    ctrl_row = df_var[df_var["is_control"]].iloc[0] if not df_var[df_var["is_control"]].empty else None

    # Dynamic axis limits tailored tightly to actual data range (avoids large empty top gap)
    kge_min = float(df_var["kge"].min())
    kge_max = float(df_var["kge"].max())
    kge_span = max(kge_max - kge_min, 0.12)

    y_min = kge_min - 0.08 * kge_span
    y_max = kge_max + 0.14 * kge_span

    rmse_min = float(df_var["rmse"].min())
    rmse_max = float(df_var["rmse"].max())
    rmse_span = max(rmse_max - rmse_min, 0.4)

    x_min = max(0.0, rmse_min - 0.08 * rmse_span)
    x_max = rmse_max + 0.08 * rmse_span

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)

    # 1. Orthogonal dotted projection lines to axes (RMSE horizontal to Y, KGE vertical to X)
    for _, row in df_var.iterrows():
        xi, yi = row["rmse"], row["kge"]
        is_w = row.get("is_winner", False)
        is_c = row.get("is_control", False)

        if is_w:
            line_color = "#059669"
            alpha = 0.85
            lw = 1.3
            z = 3
        elif is_c:
            line_color = "#334155"
            alpha = 0.70
            lw = 1.1
            z = 2
        else:
            line_color = "#94a3b8"
            alpha = 0.40
            lw = 0.8
            z = 1

        ax.plot([xi, xi], [y_min, yi], linestyle=":", color=line_color, alpha=alpha, linewidth=lw, zorder=z)
        ax.plot([x_min, xi], [yi, yi], linestyle=":", color=line_color, alpha=alpha, linewidth=lw, zorder=z)

    # 2. Candidate points
    if not candidates_df.empty:
        ax.scatter(
            candidates_df["rmse"], candidates_df["kge"],
            color=base_color, s=85, alpha=0.85,
            edgecolor="#ffffff", linewidth=1.0,
            zorder=5, label="Experimentos Candidatos"
        )

    # 3. Control (Rejilla Original) point
    if ctrl_row is not None:
        ax.scatter(
            ctrl_row["rmse"], ctrl_row["kge"],
            color="#1e293b", s=150, marker="s",
            edgecolor="#ffffff", linewidth=1.8,
            zorder=7, label=f"Rejilla Original [Control] (RMSE={ctrl_row['rmse']:.2f}, KGE={ctrl_row['kge']:.3f})"
        )

    # 4. Winner (Optimo) point
    if win_row is not None:
        lbl_w = _extract_exp_short_label(win_row["experiment_id"])
        ax.scatter(
            win_row["rmse"], win_row["kge"],
            color="#fbbf24", s=280, alpha=0.5,
            zorder=7
        )
        ax.scatter(
            win_row["rmse"], win_row["kge"],
            color="#059669", s=180, marker="o",
            edgecolor="#ffffff", linewidth=2.2,
            zorder=8, label=f"Ganador Físico [{lbl_w}] (RMSE={win_row['rmse']:.2f}, KGE={win_row['kge']:.3f})"
        )

    # 5. Collision-aware smart label positioning
    sorted_df = df_var.sort_values(by=["rmse", "kge"]).copy()
    offset_options = [
        (6, 6),      # top-right
        (-44, 6),    # top-left
        (6, -16),    # bottom-right
        (-44, -16),  # bottom-left
        (0, 12),     # top-center
        (0, -20),    # bottom-center
    ]
    used_positions = []

    for idx, row in sorted_df.iterrows():
        xi, yi = float(row["rmse"]), float(row["kge"])
        is_w = row.get("is_winner", False)
        is_c = row.get("is_control", False)
        lbl = _extract_exp_short_label(row["experiment_id"])

        if is_w:
            ax.annotate(
                f"{lbl} [ÓPTIMO]", (xi, yi),
                xytext=(-15, 14), textcoords="offset points",
                fontsize=8.5, color="#065f46", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#ecfdf5", edgecolor="#059669", alpha=0.95),
                zorder=10
            )
            continue

        if is_c:
            ax.annotate(
                "Exp_00 [Control]", (xi, yi),
                xytext=(8, -14), textcoords="offset points",
                fontsize=8.5, color="#0f172a", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.2", facecolor="#f1f5f9", edgecolor="#334155", alpha=0.9),
                zorder=9
            )
            continue

        best_offset = offset_options[0]
        min_clash = float("inf")

        for opt in offset_options:
            dx_pt, dy_pt = opt
            cand_x = xi + (dx_pt / 100.0) * rmse_span
            cand_y = yi + (dy_pt / 100.0) * kge_span

            dist = 9999.0
            for px, py in used_positions:
                d = np.hypot((cand_x - px) / rmse_span, (cand_y - py) / kge_span)
                if d < dist:
                    dist = d
            if dist > 0.12:
                best_offset = opt
                break
            elif dist > min_clash or min_clash == float("inf"):
                min_clash = dist
                best_offset = opt

        dx_pt, dy_pt = best_offset
        used_positions.append((xi + (dx_pt / 100.0) * rmse_span, yi + (dy_pt / 100.0) * kge_span))

        # Add thin hair pointer if offset is displaced
        use_arrow = abs(dx_pt) > 15 or abs(dy_pt) > 12
        arr_props = dict(arrowstyle="-", color="#94a3b8", lw=0.6, alpha=0.6) if use_arrow else None

        ax.annotate(
            lbl, (xi, yi),
            xytext=best_offset, textcoords="offset points",
            arrowprops=arr_props,
            fontsize=7.5, color="#1e293b", fontweight="medium",
            bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="#cbd5e1", alpha=0.88),
            zorder=6
        )

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ax.set_title(f"Figura 2: Espacio Bi-Criterio de Precision (RMSE vs. KGE)\nFrontera de Pareto con Proyecciones Ortogonales a los Ejes • {var_title}", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel(f"Raiz del Error Cuadratico Medio (RMSE en {unit}) [Menor error a la izquierda ←]", fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Kling-Gupta Efficiency (KGE) [Mayor habilidad hacia arriba ↑]", fontsize=9.5, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.92, loc="lower left", fontsize=8.5)

    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)


def generate_divergent_bars_figure(
    df_var: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall"
) -> str:
    """Generates divergent horizontal bars showing net gain in KGE vs raw grid control."""
    if df_var.empty or "kge" not in df_var.columns:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    df_copy = df_var.copy()
    ctrl_rows = df_copy[df_copy["experiment_id"].str.contains(r"00|Raw", regex=True)]
    raw_kge = ctrl_rows["kge"].values[0] if not ctrl_rows.empty else df_copy["kge"].min()

    df_copy["delta_kge"] = df_copy["kge"] - raw_kge
    df_sorted = df_copy.sort_values("delta_kge", ascending=True)

    colors = []
    for _, row in df_sorted.iterrows():
        is_ctrl = ("00" in row["experiment_id"] or "Raw" in row["experiment_id"])
        if is_ctrl:
            colors.append("#1e293b")
        elif row["delta_kge"] > 0.05:
            colors.append("#059669")
        elif row["delta_kge"] > 0:
            colors.append("#10b981")
        else:
            colors.append("#f43f5e")

    fig_height = max(5.5, len(df_sorted) * 0.38 + 1.8)
    fig, ax = plt.subplots(figsize=(10.5, fig_height), dpi=300)

    bars = ax.barh(df_sorted["experiment_id"], df_sorted["delta_kge"], color=colors, height=0.65, edgecolor="#334155", linewidth=0.5)
    ax.axvline(0, color="#0f172a", linestyle="-", linewidth=1.2)

    for bar in bars:
        w = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2
        va = "center"
        if w >= 0:
            ax.text(w + 0.005, y, f"+{w:.3f}", ha="left", va=va, fontsize=8, fontweight="bold" if w > 0.08 else "normal", color="#0f172a")
        else:
            ax.text(w - 0.005, y, f"{w:.3f}", ha="right", va=va, fontsize=8, color="#e11d48")

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ctrl_name = ctrl_rows["experiment_id"].values[0] if not ctrl_rows.empty else "Rejilla Original"
    ax.set_title(f"Figura 3: Ganancia Neta de Eficiencia (Δ KGE) respecto a la Rejilla Original [{ctrl_name}]\n{var_title} (1991-2020) • Evaluacion en 29 Estaciones Holdout", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel("Ganancia Neta en Eficiencia (Δ KGE) [> 0 indica mejora respecto a la rejilla original sin corregir]", fontsize=9.5, fontweight="bold")
    ax.set_xlim(df_sorted["delta_kge"].min() - 0.04, df_sorted["delta_kge"].max() + 0.05)

    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)


def generate_heatmap_matrix_figure(
    df_var: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall"
) -> str:
    """
    Generates an annotated multi-metric performance matrix/heatmap.
    Per user feedback: exact values printed in cells; colorbar displays qualitative
    ticks (Deficiente/Rojo to Optimo/Verde) without confusing decimal scales.
    """
    if df_var.empty:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    df_sorted = df_var.sort_values(by="rank", ascending=True).copy()

    if var_type in ("rainfall", "precip", "rain"):
        metric_cols = [
            ("global_skill_score", "GSS", True, "{:.3f}"),
            ("kge", "KGE", True, "{:.3f}"),
            ("r", "r (corr)", True, "{:.3f}"),
            ("rmse", "RMSE (mm)", False, "{:.2f}"),
            ("mae", "MAE (mm)", False, "{:.2f}"),
            ("pbias", "PBIAS (%)", "abs_zero", "{:+.1f}%"),
            ("ets", "ETS", True, "{:.3f}"),
        ]
    else:
        metric_cols = [
            ("global_skill_score", "GSS", True, "{:.3f}"),
            ("kge", "KGE", True, "{:.3f}"),
            ("r", "r (corr)", True, "{:.3f}"),
            ("rmse", "RMSE (°C)", False, "{:.2f}"),
            ("mae", "MAE (°C)", False, "{:.2f}"),
            ("pbias", "PBIAS (%)", "abs_zero", "{:+.1f}%"),
        ]

    row_labels = []
    for _, row in df_sorted.iterrows():
        is_win = bool(row.get("is_winner", False))
        is_ctrl = bool(row.get("is_control", False)) or ("00" in row["experiment_id"] or "Raw" in row["experiment_id"])
        if is_win:
            row_labels.append(f"[OPTIMO #01] {row['experiment_id']}")
        elif is_ctrl:
            row_labels.append(f"[REJILLA ORIGINAL] {row['experiment_id']}")
        else:
            row_labels.append(f"#{row['rank']:02d} {row['experiment_id']}")

    norm_matrix = []
    text_matrix = []

    for col_key, _, is_higher_better, fmt in metric_cols:
        series = df_sorted[col_key] if col_key in df_sorted.columns else pd.Series(np.nan, index=df_sorted.index)
        if is_higher_better == "abs_zero":
            abs_val = series.abs()
            max_abs = max(abs_val.max(), 1.0)
            norm_col = (1.0 - (abs_val / max_abs)).clip(0.0, 1.0)
        elif is_higher_better is True:
            min_v, max_v = series.min(), series.max()
            norm_col = (series - min_v) / (max_v - min_v + 1e-6) if max_v > min_v else pd.Series(1.0, index=series.index)
        else:
            min_v, max_v = series.min(), series.max()
            norm_col = 1.0 - ((series - min_v) / (max_v - min_v + 1e-6)) if max_v > min_v else pd.Series(1.0, index=series.index)

        norm_matrix.append(norm_col.values)
        col_texts = [("-" if pd.isna(v) else fmt.format(v)) for v in series]
        text_matrix.append(col_texts)

    norm_arr = np.array(norm_matrix).T
    text_arr = np.array(text_matrix).T

    fig_height = max(5.5, len(row_labels) * 0.42 + 2.0)
    fig_width = max(9.0, len(metric_cols) * 1.25 + 2.0)
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)

    # RdYlGn colormap (Green=1.0 Optimo, Red=0.0 Deficiente)
    heatmap_plot = sns.heatmap(
        norm_arr,
        annot=text_arr,
        fmt="",
        cmap="RdYlGn",
        linewidths=0.8,
        linecolor="#ffffff",
        cbar=False,
        xticklabels=[c[1] for c in metric_cols],
        yticklabels=row_labels,
        ax=ax,
        vmin=0.0,
        vmax=1.0
    )

    # Qualitative Colorbar with explicit text labels
    cbar = fig.colorbar(heatmap_plot.collections[0], ax=ax, shrink=0.65, pad=0.03)
    cbar.set_ticks([0.08, 0.50, 0.92])
    cbar.set_ticklabels(["Deficiente (Peor)", "Desempeno Medio", "Optimo (Mejor)"])
    cbar.ax.tick_params(labelsize=8.5)
    cbar.set_label("Rendimiento Relativo por Metrica (Escala Normalizada)", fontsize=9, fontweight="bold")

    for tick_label in ax.get_yticklabels():
        t = tick_label.get_text()
        if "[REJILLA ORIGINAL]" in t:
            tick_label.set_color("#0f172a")
            tick_label.set_fontweight("bold")
        elif "[OPTIMO" in t:
            tick_label.set_color("#059669")
            tick_label.set_fontweight("bold")

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ax.set_title(f"Figura 4: Matriz Multicriterio de Rendimiento Climatologico\nValores exactos impresos • Escala de color: Verde (Optimo) a Rojo (Deficiente) • {var_title}", fontsize=11, fontweight="bold", pad=14)
    plt.xticks(rotation=20, ha="right", fontsize=9, fontweight="bold")
    plt.yticks(fontsize=8)

    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)


def generate_spatial_gain_map(
    df_win_stn: pd.DataFrame,
    df_raw_stn: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    winner_name: str = "Experimento Optimo"
) -> str:
    """
    Generates geographic map of Central America with country borders, lat/lon axis labels,
    station delta KGE dots, and an explicit elevation circle size legend.
    """
    if df_win_stn.empty or df_raw_stn.empty:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if "elev" in df_raw_stn.columns:
        df_merged = pd.merge(df_win_stn[["station_id", "lon", "lat", "kge"]],
                             df_raw_stn[["station_id", "elev", "kge"]],
                             on="station_id", suffixes=("_win", "_raw"))
    else:
        df_merged = pd.merge(df_win_stn[["station_id", "lon", "lat", "kge"]],
                             df_raw_stn[["station_id", "kge"]],
                             on="station_id", suffixes=("_win", "_raw"))
        df_merged["elev"] = 500.0

    df_merged["delta_kge"] = df_merged["kge_win"] - df_merged["kge_raw"]

    fig = plt.figure(figsize=(11, 7.2), dpi=300)
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

    # Regional extent: Central America (Guatemala to Panama)
    ax.set_extent([-93.0, -77.0, 7.2, 18.8], crs=ccrs.PlateCarree())

    # Geographic features
    ax.add_feature(cfeature.OCEAN, facecolor="#e0f2fe", zorder=1)
    ax.add_feature(cfeature.LAND, facecolor="#f8fafc", edgecolor="none", zorder=2)
    ax.add_feature(cfeature.COASTLINE, edgecolor="#1e293b", linewidth=1.0, zorder=3)
    ax.add_feature(cfeature.BORDERS, edgecolor="#475569", linestyle="-", linewidth=0.8, zorder=3)

    # Gridlines with explicit Latitude and Longitude labels
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color="#cbd5e1", linestyle="--", alpha=0.7, zorder=4)
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = True
    gl.bottom_labels = True
    gl.xlabel_style = {"size": 8.5, "color": "#1e293b", "weight": "bold"}
    gl.ylabel_style = {"size": 8.5, "color": "#1e293b", "weight": "bold"}

    # Country names for regional orientation
    countries = [
        ("GUATEMALA", -90.3, 15.6),
        ("BELICE", -88.7, 17.2),
        ("HONDURAS", -86.5, 14.8),
        ("EL SALVADOR", -88.9, 13.7),
        ("NICARAGUA", -85.2, 12.8),
        ("COSTA RICA", -84.1, 9.8),
        ("PANAMA", -80.5, 8.6)
    ]
    for name, clon, clat in countries:
        ax.text(clon, clat, name, transform=ccrs.PlateCarree(),
                fontsize=8.5, fontweight="bold", color="#64748b", alpha=0.8, ha="center", va="center", zorder=4)

    # Station points proportional to elevation
    sc = ax.scatter(
        df_merged["lon"], df_merged["lat"],
        c=df_merged["delta_kge"],
        cmap="coolwarm_r",
        s=df_merged["elev"].clip(100, 2500) / 10 + 60,
        edgecolor="#0f172a",
        linewidth=1.3,
        alpha=0.95,
        vmin=-0.20, vmax=0.30,
        transform=ccrs.PlateCarree(),
        zorder=5
    )

    cbar = plt.colorbar(sc, ax=ax, fraction=0.032, pad=0.03, shrink=0.75)
    cbar.set_label("Ganancia Neta en Eficiencia (Δ KGE = KGE_Ganador - KGE_Rejilla_Original)", fontsize=9, fontweight="bold")

    # Dedicated Elevation Circle Size Legend on the Map
    elev_samples = [200, 1000, 2000]
    legend_handles = [
        plt.scatter([], [], s=elev / 10 + 60, color="#64748b", alpha=0.75, edgecolor="#0f172a", linewidth=1.1)
        for elev in elev_samples
    ]
    legend_labels = [f"{elev:,} msnm" for elev in elev_samples]
    leg_elev = ax.legend(
        legend_handles, legend_labels,
        title="Elevacion DEM\n(Tamano del Circulo)",
        loc="lower right",
        frameon=True,
        facecolor="white",
        framealpha=0.92,
        fontsize=8,
        title_fontsize=8.5,
        borderpad=0.6,
        labelspacing=0.8
    )
    leg_elev.set_zorder(10)
    ax.add_artist(leg_elev)

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    fig.suptitle(
        f"Figura 5: Distribucion Espacial de la Ganancia Neta (Δ KGE) en las 29 Estaciones de Validacion\n"
        f"{winner_name} vs. Rejilla Original • {var_title} en Centroamerica",
        fontsize=12.5, fontweight="bold", y=0.965, color="#0f172a"
    )
    fig.subplots_adjust(top=0.89, bottom=0.08, left=0.06, right=0.92)

    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)


def generate_elevation_strata_figure(
    df_win_stn: pd.DataFrame,
    df_raw_stn: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    winner_name: str = "Experimento Optimo"
) -> str:
    """
    Generates grouped bar chart of KGE by elevation strata: Coast (<200m), Valleys (200-800m), Mountains (>800m).
    Annotates both the mean inside the bars and standard deviation (σ = ±std) on the error whiskers.
    """
    if df_win_stn.empty or df_raw_stn.empty:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    if "elev" in df_raw_stn.columns:
        df_merged = pd.merge(df_win_stn[["station_id", "lon", "lat", "kge"]],
                             df_raw_stn[["station_id", "elev", "kge"]],
                             on="station_id", suffixes=("_win", "_raw"))
    else:
        df_merged = pd.merge(df_win_stn[["station_id", "lon", "lat", "kge"]],
                             df_raw_stn[["station_id", "kge"]],
                             on="station_id", suffixes=("_win", "_raw"))
        df_merged["elev"] = 500.0

    bins = [-1, 200, 800, 5000]
    labels = ["Tierras Bajas / Costas\n(< 200 m)", "Valles Intermedios\n(200-800 m)", "Zonas Montanosas\n(> 800 m)"]
    df_merged["stratum"] = pd.cut(df_merged["elev"], bins=bins, labels=labels)

    elev_agg = df_merged.groupby("stratum", observed=True)[["kge_raw", "kge_win"]].agg(["mean", "std"]).reset_index()

    fig, ax = plt.subplots(figsize=(9.5, 5.8), dpi=300)
    x = np.arange(len(labels))
    width = 0.35

    raw_means = elev_agg[("kge_raw", "mean")]
    raw_stds = elev_agg[("kge_raw", "std")]
    win_means = elev_agg[("kge_win", "mean")]
    win_stds = elev_agg[("kge_win", "std")]

    rects1 = ax.bar(x - width/2, raw_means, width, yerr=raw_stds,
                    label="Rejilla Original [Control 00]", color="#94a3b8", edgecolor="#475569", capsize=5)
    rects2 = ax.bar(x + width/2, win_means, width, yerr=win_stds,
                    label=f"Ganador [{winner_name}]", color="#059669", edgecolor="#065f46", capsize=5)

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ax.set_title(f"Figura 6: Eficiencia (KGE) por Estrato Topografico de Elevacion\nEvaluacion de Sesgo Orografico en Centroamerica (Media ± Desv. Estandar) • {var_title}", fontsize=11, fontweight="bold", pad=12)
    ax.set_ylabel("Kling-Gupta Efficiency (KGE)", fontsize=9.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, fontsize=9)

    max_top = max(float((win_means + win_stds).max()), float((raw_means + raw_stds).max()))
    ax.set_ylim(0, max_top * 1.18 + 0.04)

    # Annotate mean inside bar and standard deviation on whiskers
    for i, rect in enumerate(rects1):
        h = rect.get_height()
        s = float(raw_stds.iloc[i]) if pd.notna(raw_stds.iloc[i]) else 0.0
        ax.annotate(f"{h:.3f}", (rect.get_x() + rect.get_width() / 2, h / 2),
                    ha="center", va="center", color="white", fontweight="bold", fontsize=9)
        ax.annotate(f"σ=±{s:.3f}", (rect.get_x() + rect.get_width() / 2, h + s + 0.012),
                    ha="center", va="bottom", fontsize=8, color="#475569", fontweight="semibold")

    for i, rect in enumerate(rects2):
        h = rect.get_height()
        s = float(win_stds.iloc[i]) if pd.notna(win_stds.iloc[i]) else 0.0
        ax.annotate(f"{h:.3f}", (rect.get_x() + rect.get_width() / 2, h / 2),
                    ha="center", va="center", color="white", fontweight="bold", fontsize=9)
        ax.annotate(f"σ=±{s:.3f}", (rect.get_x() + rect.get_width() / 2, h + s + 0.012),
                    ha="center", va="bottom", fontsize=8, color="#065f46", fontweight="bold")

    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)
