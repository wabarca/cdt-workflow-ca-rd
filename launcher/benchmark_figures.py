"""
CDT 8.0 - Benchmark Static Publication Figures Generator
Generates high-resolution (300 DPI) publication-ready diagnostic figures
for climate grid reconstruction and bias correction benchmarking in Central America.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import os
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
        is_win = (e == winner_id) or ("R15" in e and var_type == "rainfall") or ("TX01" in e and var_type == "tmax") or ("TN10" in e and var_type == "tmin")
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

    # Rejilla Original median reference line
    ctrl_rows = df_stations_var[df_stations_var["experiment_id"].str.contains(r"00|Raw", regex=True)]
    if not ctrl_rows.empty:
        ctrl_median = ctrl_rows["kge"].median()
        ax.axvline(ctrl_median, color="#e11d48", linestyle="--", linewidth=1.2,
                   label=f"Mediana Rejilla Original [00]: {ctrl_median:.3f}")
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
    Per user feedback: all marker text labels and arrows are removed; only markers and legend are kept.
    """
    if df_var.empty or "rmse" not in df_var.columns or "kge" not in df_var.columns:
        return ""

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(9.5, 6.2), dpi=300)
    base_color = "#0284c7" if var_type == "rainfall" else ("#ea580c" if var_type == "tmax" else "#7c3aed")

    candidates_df = df_var[~df_var["is_winner"] & ~df_var["is_control"]]
    win_row = df_var[df_var["is_winner"]].iloc[0] if not df_var[df_var["is_winner"]].empty else None
    ctrl_row = df_var[df_var["is_control"]].iloc[0] if not df_var[df_var["is_control"]].empty else None

    # 1. Candidate points
    if not candidates_df.empty:
        ax.scatter(
            candidates_df["rmse"], candidates_df["kge"],
            color=base_color, s=70, alpha=0.75,
            edgecolor="#ffffff", linewidth=0.8,
            zorder=4, label="Experimentos Candidatos"
        )

    # 2. Control (Rejilla Original) point
    if ctrl_row is not None:
        ax.scatter(
            ctrl_row["rmse"], ctrl_row["kge"],
            color="#1e293b", s=150, marker="s",
            edgecolor="#ffffff", linewidth=1.8,
            zorder=6, label=f"Rejilla Original [{ctrl_row['experiment_id']}] (RMSE={ctrl_row['rmse']:.2f}, KGE={ctrl_row['kge']:.3f})"
        )

    # 3. Winner (Optimo) point
    if win_row is not None:
        ax.scatter(
            win_row["rmse"], win_row["kge"],
            color="#fbbf24", s=280, alpha=0.5,
            zorder=7
        )
        ax.scatter(
            win_row["rmse"], win_row["kge"],
            color="#059669", s=180, marker="o",
            edgecolor="#ffffff", linewidth=2.2,
            zorder=8, label=f"Experimento Optimo [{win_row['experiment_id']}] (RMSE={win_row['rmse']:.2f}, KGE={win_row['kge']:.3f})"
        )

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ax.set_title(f"Figura 2: Espacio Bi-Criterio de Precision (RMSE vs. KGE)\nFrontera de Pareto en 29 Estaciones Holdout • {var_title}", fontsize=11, fontweight="bold", pad=12)
    ax.set_xlabel(f"Raiz del Error Cuadratico Medio (RMSE en {unit}) [Menor es mejor]", fontsize=9.5, fontweight="bold")
    ax.set_ylabel("Kling-Gupta Efficiency (KGE) [Mayor es mejor]", fontsize=9.5, fontweight="bold")
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
    ctrl_name = ctrl_rows["experiment_id"].values[0] if not ctrl_rows.empty else "Rejilla Original [00]"
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
    Per user feedback: colormap is RdYlGn (green = best, red = worst).
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
            norm_col = np.clip(1.0 - (abs_val / (abs_val.max() + 1e-6)), 0.0, 1.0)
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
    sns.heatmap(
        norm_arr,
        annot=text_arr,
        fmt="",
        cmap="RdYlGn",
        linewidths=0.8,
        linecolor="#ffffff",
        cbar_kws={"label": "Rendimiento Normalizado (Verde = Optimo, Rojo = Deficiente)", "shrink": 0.65},
        xticklabels=[c[1] for c in metric_cols],
        yticklabels=row_labels,
        ax=ax,
        vmin=0.0,
        vmax=1.0
    )

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
    and station delta KGE dots.
    NOTE: bbox_inches='tight' MUST NOT be used on Cartopy GeoAxes as it crops out the map.
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

    # Station points without text clutter
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

    var_title = "Precipitación Diaria" if var_type == "rainfall" else ("Temperatura Máxima" if var_type == "tmax" else "Temperatura Mínima")
    fig.suptitle(
        f"Figura 5: Distribución Espacial de la Ganancia Neta (Δ KGE) en las 29 Estaciones de Validación\n"
        f"{winner_name} vs. Rejilla Original • {var_title} en Centroamérica",
        fontsize=12.5, fontweight="bold", y=0.965, color="#0f172a"
    )
    fig.subplots_adjust(top=0.89, bottom=0.08, left=0.06, right=0.92)

    # Save without bbox_inches='tight' so the map is preserved at 3300x2160
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
    """Generates grouped bar chart of KGE by elevation strata: Coast (<200m), Valleys (200-800m), Mountains (>800m)."""
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

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    x = np.arange(len(labels))
    width = 0.35

    rects1 = ax.bar(x - width/2, elev_agg[("kge_raw", "mean")], width, yerr=elev_agg[("kge_raw", "std")],
                    label="Rejilla Original [Control 00]", color="#94a3b8", edgecolor="#475569", capsize=5)
    rects2 = ax.bar(x + width/2, elev_agg[("kge_win", "mean")], width, yerr=elev_agg[("kge_win", "std")],
                    label=f"Ganador [{winner_name}]", color="#059669", edgecolor="#065f46", capsize=5)

    var_title = "Precipitacion Diaria" if var_type == "rainfall" else ("Temperatura Maxima" if var_type == "tmax" else "Temperatura Minima")
    ax.set_title(f"Figura 6: Eficiencia (KGE) por Estrato Topografico de Elevacion\nEvaluacion de Sesgo Orografico en Centroamerica (Media ± Desv. Estandar) • {var_title}", fontsize=11, fontweight="bold", pad=12)
    ax.set_ylabel("Kling-Gupta Efficiency (KGE)", fontsize=9.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9.5, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", framealpha=0.9, fontsize=9)
    ax.set_ylim(0, max(0.55, float(df_merged["kge_win"].max() * 1.15)))

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.3f}", (rect.get_x() + rect.get_width() / 2, h / 2),
                    ha="center", va="center", color="white", fontweight="bold", fontsize=9)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.3f}", (rect.get_x() + rect.get_width() / 2, h / 2),
                    ha="center", va="center", color="white", fontweight="bold", fontsize=9)

    plt.tight_layout()
    plt.savefig(out_p, dpi=300)
    plt.close()
    return str(out_p)
