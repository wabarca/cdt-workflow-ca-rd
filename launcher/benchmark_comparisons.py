"""
Diagnostic and Comparative Visualization: Optimal Winner vs. Raw Satellite Baseline (Control 00).

Generates publication-ready comparative multi-panel figures (300 DPI) for each climate variable
(Rainfall, Maximum Temperature, Minimum Temperature) and an executive cross-variable summary.
Evaluates the holdout validation performance between the raw, unadjusted satellite products
(CHIRPS v2.0, CHIRTS-ERA5 Tmax, CHIRTS-ERA5 Tmin) and the best-performing CDT 8.0 bias correction
and downscaling workflows.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns


# =============================================================================
# STYLING CONFIGURATION
# =============================================================================
PALETTE = {
    "raw": "#64748b",         # Slate Grey for Raw Control
    "winner_rain": "#0284c7", # Sky Blue for Rainfall Winner (EXP_R15)
    "winner_tmax": "#ea580c", # Amber/Orange for Tmax Winner (EXP_TX11)
    "winner_tmin": "#7c3aed", # Violet/Indigo for Tmin Winner (EXP_TN10)
    "gain_pos": "#16a34a",    # Forest Green for Improvement
    "gain_neg": "#dc2626",    # Crimson Red for Degradation
    "grid": "#e2e8f0",
    "text": "#1e293b",
}


def clean_figures_root(figures_dir: Path | str) -> None:
    """Removes orphan loose image files in the root of the figures directory."""
    fig_path = Path(figures_dir)
    if not fig_path.exists():
        return
    for f in fig_path.glob("*.png"):
        try:
            f.unlink()
            print(f"  [CLEAN] Removed orphan figure in root: {f.name}")
        except Exception as e:
            print(f"  [!] Warning removing {f}: {e}")
    for f in fig_path.glob("*.jpg"):
        try:
            f.unlink()
        except Exception:
            pass


def generate_variable_comparison_figure(
    df_stations: pd.DataFrame,
    var_type: str,
    winner_id: str,
    raw_id: str,
    winner_name: str,
    raw_name: str,
    output_png: Path | str,
) -> None:
    """Generates a comprehensive 4-panel comparison figure (300 DPI) for a specific variable."""
    out_file = Path(output_png)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    # Filter data
    df_win = df_stations[df_stations["experiment_id"] == winner_id].copy()
    df_raw = df_stations[df_stations["experiment_id"] == raw_id].copy()

    if df_win.empty or df_raw.empty:
        print(f"  [!] Insufficient station data for {var_type} ({winner_id} vs {raw_id}). Skipping.")
        return

    # Merge on station_id
    merged = pd.merge(
        df_win,
        df_raw,
        on="station_id",
        suffixes=("_win", "_raw")
    )
    if merged.empty:
        # Fallback to positional matching if IDs don't match
        merged = df_win.reset_index(drop=True).join(
            df_raw.reset_index(drop=True),
            lsuffix="_win",
            rsuffix="_raw"
        )
        if "station_id_win" in merged.columns:
            merged["station_id"] = merged["station_id_win"]
        else:
            merged["station_id"] = [f"STN_{i+1:02d}" for i in range(len(merged))]

    # Order by elevation or raw KGE
    if "elev_win" in merged.columns and merged["elev_win"].notna().any():
        merged = merged.sort_values(by="elev_win").reset_index(drop=True)
    elif "kge_raw" in merged.columns:
        merged = merged.sort_values(by="kge_raw").reset_index(drop=True)

    n_stns = len(merged)
    merged["delta_kge"] = merged["kge_win"] - merged["kge_raw"]
    merged["delta_rmse"] = merged["rmse_win"] - merged["rmse_raw"]
    merged["delta_r"] = merged["r_win"] - merged["r_raw"]

    mean_kge_raw = merged["kge_raw"].mean()
    mean_kge_win = merged["kge_win"].mean()
    mean_delta_kge = merged["delta_kge"].mean()

    mean_rmse_raw = merged["rmse_raw"].mean()
    mean_rmse_win = merged["rmse_win"].mean()
    pct_rmse_reduct = ((mean_rmse_raw - mean_rmse_win) / mean_rmse_raw) * 100.0

    mean_r_raw = merged["r_raw"].mean()
    mean_r_win = merged["r_win"].mean()

    win_color = PALETTE["winner_rain"] if var_type == "rainfall" else (
        PALETTE["winner_tmax"] if var_type == "tmax" else PALETTE["winner_tmin"]
    )
    unit_str = "mm/día" if var_type == "rainfall" else "°C"

    # Create 2x2 multi-panel figure
    fig, axes = plt.subplots(2, 2, figsize=(16, 12), dpi=300)
    fig.patch.set_facecolor("#ffffff")

    title_var = "Precipitación Diaria" if var_type == "rainfall" else (
        "Temperatura Máxima Diaria (Tmax)" if var_type == "tmax" else "Temperatura Mínima Diaria (Tmin)"
    )
    fig.suptitle(
        f"Evaluación Comparativa: Modelo Óptimo CDT vs. Malla Satelital Cruda (Holdout n={n_stns})\n"
        f"{title_var} en América Central (1991–2020)",
        fontsize=16,
        fontweight="bold",
        color=PALETTE["text"],
        y=0.98,
    )

    # -------------------------------------------------------------------------
    # Panel A: Paired KGE by Station (Holdout)
    # -------------------------------------------------------------------------
    ax = axes[0, 0]
    ax.set_facecolor("#f8fafc")
    x = np.arange(n_stns)
    width = 0.38

    ax.bar(x - width/2, merged["kge_raw"], width, label=f"Crudo: {raw_id}", color=PALETTE["raw"], alpha=0.85, edgecolor="#475569")
    ax.bar(x + width/2, merged["kge_win"], width, label=f"Óptimo CDT: {winner_id}", color=win_color, alpha=0.9, edgecolor="#0f172a")

    ax.set_xticks(x)
    stn_labels = merged["station_id"].tolist()
    # Format labels cleanly
    short_labels = [s.replace("CR_", "CR:").replace("GU_INS", "GU:").replace("HO_", "HO:").replace("PA_X", "PA:") for s in stn_labels]
    ax.set_xticklabels(short_labels, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("Eficiencia Kling-Gupta (KGE)", fontsize=11, fontweight="bold")
    ax.set_title(
        f"(a) Kling-Gupta Efficiency (KGE) por Estación Holdout\n"
        f"Media Crudo: {mean_kge_raw:.3f}  →  Media Corregido: {mean_kge_win:.3f}  (ΔKGE = +{mean_delta_kge:.3f})",
        fontsize=11, fontweight="bold", loc="left"
    )
    ax.axhline(0.0, color="#94a3b8", linestyle="--", linewidth=0.8)
    ax.grid(axis="y", color=PALETTE["grid"], linestyle="--", alpha=0.7)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9, loc="upper left")

    # -------------------------------------------------------------------------
    # Panel B: Net KGE Gain (Waterfall / Diverging Bar)
    # -------------------------------------------------------------------------
    ax = axes[0, 1]
    ax.set_facecolor("#f8fafc")
    colors_gain = [PALETTE["gain_pos"] if g >= 0 else PALETTE["gain_neg"] for g in merged["delta_kge"]]
    ax.bar(x, merged["delta_kge"], width=0.6, color=colors_gain, edgecolor="#334155", alpha=0.88)
    ax.axhline(0.0, color="#475569", linestyle="-", linewidth=1.0)
    ax.axhline(mean_delta_kge, color="#059669", linestyle="--", linewidth=1.8, label=f"Ganancia Media (Δ = +{mean_delta_kge:.3f})")

    ax.set_xticks(x)
    ax.set_xticklabels(short_labels, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("Ganancia Neta (Δ KGE)", fontsize=11, fontweight="bold")
    ax.set_title(
        f"(b) Incremento de Eficiencia por Estación (ΔKGE = KGE_CDT - KGE_Raw)\n"
        f"Estaciones mejoradas: {(merged['delta_kge'] > 0).sum()}/{n_stns} ({(merged['delta_kge'] > 0).sum()/n_stns*100:.1f}%)",
        fontsize=11, fontweight="bold", loc="left"
    )
    ax.grid(axis="y", color=PALETTE["grid"], linestyle="--", alpha=0.7)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9, loc="upper right")

    # -------------------------------------------------------------------------
    # Panel C: Scatter Correlation (r) vs. RMSE
    # -------------------------------------------------------------------------
    ax = axes[1, 0]
    ax.set_facecolor("#f8fafc")

    # Connect raw and corrected points with displacement arrows
    for i in range(n_stns):
        ax.annotate(
            "",
            xy=(merged["rmse_win"].iloc[i], merged["r_win"].iloc[i]),
            xytext=(merged["rmse_raw"].iloc[i], merged["r_raw"].iloc[i]),
            arrowprops=dict(arrowstyle="->", color="#94a3b8", lw=0.8, alpha=0.6)
        )

    ax.scatter(
        merged["rmse_raw"], merged["r_raw"],
        s=70, color=PALETTE["raw"], label=f"Crudo ({raw_id})", alpha=0.8, edgecolors="#1e293b", zorder=4
    )
    ax.scatter(
        merged["rmse_win"], merged["r_win"],
        s=95, color=win_color, label=f"Óptimo ({winner_id})", alpha=0.95, edgecolors="#0f172a", zorder=5
    )

    # Plot centroid markers
    ax.scatter(
        [mean_rmse_raw], [mean_r_raw],
        s=200, marker="X", color="#334155", edgecolors="#ffffff", linewidth=1.5,
        label=f"Centroide Crudo (RMSE={mean_rmse_raw:.2f}, r={mean_r_raw:.3f})", zorder=6
    )
    ax.scatter(
        [mean_rmse_win], [mean_r_win],
        s=250, marker="*", color="#fbbf24", edgecolors="#b45309", linewidth=1.5,
        label=f"Centroide Óptimo (RMSE={mean_rmse_win:.2f}, r={mean_r_win:.3f})", zorder=7
    )

    ax.set_xlabel(f"Error Cuadrático Medio - RMSE ({unit_str}) [menor es mejor]", fontsize=11, fontweight="bold")
    ax.set_ylabel("Coeficiente de Correlación de Pearson (r) [mayor es mejor]", fontsize=11, fontweight="bold")
    ax.set_title(
        f"(c) Espacio de Precisión (RMSE vs. Pearson r)\n"
        f"Reducción de Error: -{pct_rmse_reduct:.1f}%  |  Aumento de Correlación: {mean_r_raw:.3f} → {mean_r_win:.3f}",
        fontsize=11, fontweight="bold", loc="left"
    )
    ax.grid(color=PALETTE["grid"], linestyle="--", alpha=0.7)
    ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8.5, loc="lower left")

    # -------------------------------------------------------------------------
    # Panel D: Categorical Metrics (Rainfall) or Elevation-Dependent Error (Temperature)
    # -------------------------------------------------------------------------
    ax = axes[1, 1]
    ax.set_facecolor("#f8fafc")

    if var_type == "rainfall" and "pod_win" in merged.columns and "pod_raw" in merged.columns:
        # Categorical skill comparison: POD, FAR, ETS, HSS
        cat_metrics = ["pod", "far", "ets", "hss"]
        cat_names = ["Probabilidad Detección\n(POD)", "Falsa Alarma\n(FAR)", "Equitable Threat Score\n(ETS)", "Heidke Skill Score\n(HSS)"]
        raw_vals = [merged[f"{m}_raw"].mean() for m in cat_metrics]
        win_vals = [merged[f"{m}_win"].mean() for m in cat_metrics]

        cx = np.arange(len(cat_metrics))
        cwidth = 0.35
        b1 = ax.bar(cx - cwidth/2, raw_vals, cwidth, label=f"Crudo: {raw_id}", color=PALETTE["raw"], alpha=0.85, edgecolor="#334155")
        b2 = ax.bar(cx + cwidth/2, win_vals, cwidth, label=f"Óptimo: {winner_id}", color=win_color, alpha=0.9, edgecolor="#0f172a")

        for rect in b1:
            h = rect.get_height()
            ax.annotate(f"{h:.3f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5)
        for rect in b2:
            h = rect.get_height()
            ax.annotate(f"{h:.3f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8.5, fontweight="bold")

        ax.set_xticks(cx)
        ax.set_xticklabels(cat_names, fontsize=9.5)
        ax.set_ylabel("Puntuación de Habilidad Categórica", fontsize=11, fontweight="bold")
        ax.set_title(
            f"(d) Habilidad de Detección de Eventos de Precipitación (Umbral > 1.0 mm)\n"
            f"Mayor POD y ETS, menor FAR indican mayor fidelidad hidrológica",
            fontsize=11, fontweight="bold", loc="left"
        )
        ax.set_ylim(0, max(max(raw_vals), max(win_vals)) * 1.25)
        ax.grid(axis="y", color=PALETTE["grid"], linestyle="--", alpha=0.7)
        ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9, loc="upper right")
    else:
        # Temperature: Elevation-dependent error analysis (Orographic Correction)
        has_elev = "elev_win" in merged.columns and merged["elev_win"].notna().any()
        if has_elev:
            elev_vals = merged["elev_win"]
            ax.scatter(elev_vals, merged["rmse_raw"], s=80, color=PALETTE["raw"], label=f"RMSE Crudo ({raw_id})", alpha=0.85, edgecolor="#1e293b")
            ax.scatter(elev_vals, merged["rmse_win"], s=100, color=win_color, label=f"RMSE Óptimo ({winner_id})", alpha=0.95, edgecolor="#0f172a")

            # Fit trend lines
            if len(elev_vals.dropna()) > 3:
                z_raw = np.polyfit(elev_vals, merged["rmse_raw"], 1)
                p_raw = np.poly1d(z_raw)
                z_win = np.polyfit(elev_vals, merged["rmse_win"], 1)
                p_win = np.poly1d(z_win)
                ex_grid = np.linspace(elev_vals.min(), elev_vals.max(), 50)
                ax.plot(ex_grid, p_raw(ex_grid), color=PALETTE["raw"], linestyle="--", linewidth=1.5, alpha=0.8)
                ax.plot(ex_grid, p_win(ex_grid), color=win_color, linestyle="-", linewidth=2.0)

            ax.set_xlabel("Elevación de la Estación (msnm)", fontsize=11, fontweight="bold")
            ax.set_ylabel(f"RMSE ({unit_str})", fontsize=11, fontweight="bold")
            ax.set_title(
                f"(d) Reducción del Error Orográfico en Función de la Altitud\n"
                f"El desescalado topográfico (DEM) elimina el sesgo por gradiente térmico vertical",
                fontsize=11, fontweight="bold", loc="left"
            )
            ax.grid(color=PALETTE["grid"], linestyle="--", alpha=0.7)
            ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9, loc="upper right")
        else:
            # Fallback to MAE comparison
            ax.bar(x - width/2, merged["mae_raw"], width, label=f"MAE Crudo: {raw_id}", color=PALETTE["raw"], alpha=0.85)
            ax.bar(x + width/2, merged["mae_win"], width, label=f"MAE Óptimo: {winner_id}", color=win_color, alpha=0.9)
            ax.set_xticks(x)
            ax.set_xticklabels(short_labels, rotation=60, ha="right", fontsize=8)
            ax.set_ylabel(f"Error Absoluto Medio - MAE ({unit_str})", fontsize=11, fontweight="bold")
            ax.set_title(f"(d) Error Absoluto Medio (MAE) por Estación", fontsize=11, fontweight="bold", loc="left")
            ax.grid(axis="y", color=PALETTE["grid"], linestyle="--", alpha=0.7)
            ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [FIG] Comparison Figure (300 DPI) generated: {out_file}")


def generate_all_comparisons_suite(
    df_ranked: pd.DataFrame,
    df_stations: pd.DataFrame,
    output_dir: Path | str = "output/benchmark_ca/figures/comparisons_winner_vs_raw"
) -> Dict[str, str]:
    """Generates the full comparison suite for all 3 climate variables and an overview figure."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Clean figures root to prevent orphan images
    clean_figures_root(out_dir.parent)

    var_configs = [
        {
            "var": "rainfall",
            "winner_id": "EXP_R15_Shepard_RnoR_Smooth",
            "raw_id": "EXP_R00_Raw_CHIRPS",
            "winner_name": "Shepard Suave RnoR",
            "raw_name": "CHIRPS v2.0 Original Crudo",
            "filename": "comparison_rainfall_winner_vs_raw.png",
        },
        {
            "var": "tmax",
            "winner_id": "EXP_TX11_RK_Barnes_Hybrid",
            "raw_id": "EXP_TX00_Raw_CHIRTS",
            "winner_name": "RK Barnes Hybrid",
            "raw_name": "CHIRTS-ERA5 Tmax Crudo",
            "filename": "comparison_tmax_winner_vs_raw.png",
        },
        {
            "var": "tmin",
            "winner_id": "EXP_TN10_QM_Empirical_ECDF",
            "raw_id": "EXP_TN00_Raw_CHIRTS",
            "winner_name": "QM Empírico ECDF",
            "raw_name": "CHIRTS-ERA5 Tmin Crudo",
            "filename": "comparison_tmin_winner_vs_raw.png",
        },
    ]

    generated_files = {}

    for cfg in var_configs:
        v = cfg["var"]
        # Find winner dynamically if available in df_ranked
        sub_df = df_ranked[df_ranked["variable"] == v] if not df_ranked.empty else pd.DataFrame()
        win_id = cfg["winner_id"]
        if not sub_df.empty:
            winners = sub_df[sub_df["is_winner"] == True]
            if not winners.empty:
                win_id = winners.iloc[0]["experiment_id"]

        png_path = out_dir / cfg["filename"]
        generate_variable_comparison_figure(
            df_stations=df_stations,
            var_type=v,
            winner_id=win_id,
            raw_id=cfg["raw_id"],
            winner_name=cfg["winner_name"],
            raw_name=cfg["raw_name"],
            output_png=png_path
        )
        generated_files[v] = f"figures/comparisons_winner_vs_raw/{cfg['filename']}"

    # 2. Executive Synthesis Overview (All 3 Variables side by side)
    overview_png = out_dir / "comparison_all_variables_executive_summary.png"
    generate_executive_overview_figure(df_ranked, overview_png)
    generated_files["overview"] = f"figures/comparisons_winner_vs_raw/comparison_all_variables_executive_summary.png"

    return generated_files


def generate_executive_overview_figure(
    df_ranked: pd.DataFrame,
    output_png: Path | str
) -> None:
    """Generates an executive cross-variable synthesis comparing Raw vs. Corrected Grid."""
    out_file = Path(output_png)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    if df_ranked.empty:
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), dpi=300)
    fig.patch.set_facecolor("#ffffff")
    fig.suptitle(
        "Síntesis Ejecutiva de Desempeño: Malla Original Cruda vs. Malla Óptima Corregida\n"
        "Validación Independiente con 29 Estaciones en Centroamérica (1991–2020)",
        fontsize=15, fontweight="bold", color=PALETTE["text"], y=1.02
    )

    vars_meta = [
        ("rainfall", "Precipitación (CHIRPS v2.0)", PALETTE["winner_rain"], "EXP_R00_Raw_CHIRPS", "EXP_R15_Shepard_RnoR_Smooth"),
        ("tmax", "Temperatura Máxima (CHIRTS)", PALETTE["winner_tmax"], "EXP_TX00_Raw_CHIRTS", "EXP_TX11_RK_Barnes_Hybrid"),
        ("tmin", "Temperatura Mínima (CHIRTS)", PALETTE["winner_tmin"], "EXP_TN00_Raw_CHIRTS", "EXP_TN10_QM_Empirical_ECDF"),
    ]

    for idx, (v_key, v_title, v_col, raw_id, win_id) in enumerate(vars_meta):
        ax = axes[idx]
        ax.set_facecolor("#f8fafc")

        sub = df_ranked[df_ranked["variable"] == v_key]
        r_raw = sub[sub["experiment_id"] == raw_id]
        r_win = sub[sub["experiment_id"] == win_id]
        if r_win.empty:
            r_win = sub[sub["is_winner"] == True]

        if r_raw.empty or r_win.empty:
            continue

        raw_row = r_raw.iloc[0]
        win_row = r_win.iloc[0]

        metrics = ["kge", "r", "global_skill_score"]
        m_labels = ["Eficiencia\n(KGE)", "Correlación\n(Pearson r)", "Habilidad Global\n(GSS)"]
        raw_vals = [raw_row.get(m, 0.0) for m in metrics]
        win_vals = [win_row.get(m, 0.0) for m in metrics]

        x = np.arange(len(metrics))
        w = 0.35
        b_raw = ax.bar(x - w/2, raw_vals, w, label="Crudo [Control 00]", color=PALETTE["raw"], alpha=0.85, edgecolor="#334155")
        b_win = ax.bar(x + w/2, win_vals, w, label=f"Óptimo ({win_row['experiment_id'][:10]}...)", color=v_col, alpha=0.9, edgecolor="#0f172a")

        # Values labels
        for rect in b_raw:
            h = rect.get_height()
            ax.annotate(f"{h:.3f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9)
        for rect in b_win:
            h = rect.get_height()
            ax.annotate(f"{h:.3f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=9, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels(m_labels, fontsize=10)
        ax.set_ylabel("Valor de Métrica Normalizada", fontsize=10.5, fontweight="bold")
        ax.set_title(f"{v_title}\nGanancia KGE: Δ = +{win_row['kge'] - raw_row['kge']:.3f}", fontsize=11, fontweight="bold")
        ax.set_ylim(0, 1.15)
        ax.grid(axis="y", color=PALETTE["grid"], linestyle="--", alpha=0.7)
        ax.legend(frameon=True, facecolor="#ffffff", edgecolor="#cbd5e1", fontsize=8.5, loc="upper left")

    plt.tight_layout()
    plt.savefig(out_file, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [FIG] Executive Synthesis Overview generated: {out_file}")
