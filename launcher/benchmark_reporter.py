"""Benchmark Evaluation, Leaderboard Ranking, and Publication-Ready Diagnostic Reporter.

This module consolidates validation metrics across all executed CDT experiments
(Rainfall, Tmax, Tmin), computes multi-criteria skill scores (Global Skill Score),
ranks the experiments to identify the optimal grid correction candidate,
generates publication-ready static figures (300 DPI) segregated by variable,
and compiles a standalone interactive HTML dashboard powered entirely by Plotly.js
with tabbed navigation, hover diagnostics, and neutral scientific presentation.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Setup matplotlib for headless server environments
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns


# =============================================================================
# 1. METRICS HARVESTER & DATA CONSOLIDATION
# =============================================================================

def enrich_stations_with_elevation(df_stations: pd.DataFrame) -> pd.DataFrame:
    """Enriches df_stations with elevation (elev) by cross-referencing station files or DEM."""
    if df_stations.empty:
        return df_stations

    df = df_stations.copy()
    need_elev = "elev" not in df.columns or df["elev"].isna().all()
    if not need_elev:
        return df

    elev_map: Dict[str, float] = {}
    station_dir = Path("data/stations")
    if station_dir.exists():
        for csv_f in station_dir.glob("*.csv"):
            if "holdout" in csv_f.name.lower():
                continue
            try:
                from launcher.station_manager import parse_cdt_station_file
                _, meta, _ = parse_cdt_station_file(csv_f)
                if meta.get("has_elev", False):
                    for sid, el in zip(meta["id"], meta["elev"]):
                        if pd.notna(el) and sid not in elev_map:
                            elev_map[sid] = float(el)
            except Exception:
                pass

    if "elev" not in df.columns:
        df["elev"] = df["station_id"].map(elev_map)
    else:
        df["elev"] = df["elev"].fillna(df["station_id"].map(elev_map))

    return df


def harvest_experiment_metrics(experiments_root: Path | str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Collects validation summaries and station-level metrics from all experiment outputs.

    Returns:
        Tuple containing:
            - df_summaries: DataFrame with one row per experiment summary.
            - df_stations: DataFrame with station-level metrics across all experiments.
    """
    root = Path(experiments_root)
    if not root.exists():
        return pd.DataFrame(), pd.DataFrame()

    summary_rows = []
    station_rows = []

    for exp_dir in sorted(root.iterdir()):
        if not exp_dir.is_dir():
            continue

        sum_json_path = exp_dir / "validation_summary.json"
        st_csv_path = exp_dir / "validation_metrics_by_station.csv"
        manifest_path = exp_dir / "manifest.json"

        exp_id = exp_dir.name
        var_type = "rainfall" if "R0" in exp_id or "R1" in exp_id or "rain" in exp_id.lower() else (
            "tmax" if "TX" in exp_id or "tmax" in exp_id.lower() else "tmin"
        )
        desc = exp_id.replace("_", " ")

        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as mf:
                    mdata = json.load(mf)
                    var_type = mdata.get("variable_type", var_type).lower()
                    desc = mdata.get("description", desc)
            except Exception:
                pass

        if sum_json_path.exists():
            try:
                with open(sum_json_path, "r", encoding="utf-8") as sf:
                    sdata = json.load(sf)
                    row = {
                        "experiment_id": exp_id,
                        "variable": var_type,
                        "description": desc,
                        "total_stations": sdata.get("total_stations_evaluated", 0),
                        "kge": sdata.get("mean_kge", np.nan),
                        "kge_median": sdata.get("median_kge", sdata.get("mean_kge", np.nan)),
                        "r": sdata.get("mean_r", np.nan),
                        "r2": sdata.get("mean_r2", np.nan),
                        "rmse": sdata.get("mean_rmse", np.nan),
                        "mae": sdata.get("mean_mae", np.nan),
                        "pbias": sdata.get("mean_pbias", np.nan),
                        "pod": sdata.get("mean_pod", np.nan),
                        "far": sdata.get("mean_far", np.nan),
                        "ets": sdata.get("mean_ets", np.nan),
                        "hss": sdata.get("mean_hss", np.nan),
                        "output_dir": str(exp_dir),
                    }
                    summary_rows.append(row)
            except Exception as e:
                print(f"[!] Warning reading {sum_json_path}: {e}")

        if st_csv_path.exists():
            try:
                df_st = pd.read_csv(st_csv_path)
                df_st["experiment_id"] = exp_id
                df_st["variable"] = var_type
                station_rows.append(df_st)
            except Exception as e:
                print(f"[!] Warning reading {st_csv_path}: {e}")

    df_summaries = pd.DataFrame(summary_rows)
    df_stations = pd.concat(station_rows, ignore_index=True) if station_rows else pd.DataFrame()
    if not df_stations.empty:
        df_stations = enrich_stations_with_elevation(df_stations)
    return df_summaries, df_stations


# =============================================================================
# 2. MULTI-CRITERIA SCORING & LEADERBOARD RANKING
# =============================================================================

def compute_leaderboard_ranking(df_summaries: pd.DataFrame) -> pd.DataFrame:
    """Computes Global Skill Score (GSS), ranks experiments within each variable suite,
    and calculates delta improvements relative to the baseline experiment.
    """
    if df_summaries.empty:
        return df_summaries

    ranked_dfs = []

    for var, df_var in df_summaries.groupby("variable"):
        df = df_var.copy()

        # Fill NaNs for scoring robustness
        kge = df["kge"].fillna(-1.0).clip(lower=-1.0, upper=1.0)
        r = df["r"].fillna(0.0).clip(lower=0.0, upper=1.0)
        rmse = df["rmse"].fillna(df["rmse"].max() if not df["rmse"].empty else 10.0)
        pbias = df["pbias"].fillna(100.0).abs()

        # Normalized RMSE score (1 = perfect, 0 = poor)
        max_rmse = rmse.max() if rmse.max() > 0 else 1.0
        nrmse_score = (1.0 - (rmse / max_rmse)).clip(lower=0.0, upper=1.0)
        
        # PBIAS penalty score (1 = 0% bias, 0 = >=50% bias)
        pbias_score = (1.0 - (pbias / 50.0)).clip(lower=0.0, upper=1.0)

        if var in ("rainfall", "precip", "rain"):
            ets = df["ets"].fillna(0.0).clip(lower=0.0, upper=1.0)
            df["global_skill_score"] = (
                0.35 * kge +
                0.25 * r +
                0.20 * ets +
                0.20 * pbias_score
            )
        else:
            df["global_skill_score"] = (
                0.40 * kge +
                0.30 * r +
                0.15 * nrmse_score +
                0.15 * pbias_score
            )

        # Sort by GSS descending
        df = df.sort_values(by="global_skill_score", ascending=False).reset_index(drop=True)
        df["rank"] = df.index + 1

        baseline_mask = df["experiment_id"].str.contains("01", regex=False)
        if baseline_mask.any():
            base_row = df[baseline_mask].iloc[0]
        else:
            base_row = df.iloc[-1]

        base_kge = base_row["kge"]
        base_rmse = base_row["rmse"]
        base_ets = base_row.get("ets", np.nan)

        df["delta_kge_vs_base"] = df["kge"] - base_kge
        df["delta_rmse_vs_base"] = base_rmse - df["rmse"]
        if "ets" in df.columns:
            df["delta_ets_vs_base"] = df["ets"] - base_ets

        df["is_winner"] = df["rank"] == 1
        ranked_dfs.append(df)

    final_df = pd.concat(ranked_dfs, ignore_index=True)
    return final_df


# =============================================================================
# 3. PUBLICATION-READY STATIC SCIENTIFIC FIGURES (300 DPI)
# =============================================================================

def generate_taylor_diagram(
    df_summaries: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    title: Optional[str] = None
):
    """Generates a polar Taylor Diagram for a specific variable."""
    df_var = df_summaries[df_summaries["variable"] == var_type].copy() if not df_summaries.empty else pd.DataFrame()
    if df_var.empty:
        return

    var_titles = {
        "rainfall": "Diagrama Polar de Taylor: Precipitación (CHIRPS)",
        "tmax": "Diagrama Polar de Taylor: Temperatura Máxima (Tmax)",
        "tmin": "Diagrama Polar de Taylor: Temperatura Mínima (Tmin)"
    }
    plot_title = title or var_titles.get(var_type, f"Diagrama Polar de Taylor: {var_type.upper()}")

    plt.figure(figsize=(8.5, 8.0), dpi=300)
    ax = plt.subplot(111, projection="polar")

    ax.set_thetamin(0)
    ax.set_thetamax(90)

    r_ticks = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0])
    angles = np.arccos(r_ticks)

    ax.set_xticks(angles)
    ax.set_xticklabels([f"{v:.2f}" for v in r_ticks], fontsize=8, color="#334155")
    ax.tick_params(pad=8)

    plt.text(
        np.pi / 4, 1.45, "Coeficiente de Correlación de Pearson (r)",
        horizontalalignment="center", verticalalignment="bottom",
        rotation=-45, fontsize=10, fontweight="bold", color="#1e293b"
    )

    ax.plot(0, 1.0, marker="*", markersize=14, color="#dc2626", label="Estaciones Holdout (Referencia)", zorder=10)

    radii = np.linspace(0, 1.5, 100)
    theta = np.linspace(0, np.pi / 2, 100)
    R, TH = np.meshgrid(radii, theta)
    X = R * np.sin(TH)
    Y = R * np.cos(TH)
    E_rms = np.sqrt(X ** 2 + (Y - 1.0) ** 2)
    contours = ax.contour(TH, R, E_rms, levels=[0.25, 0.5, 0.75, 1.0, 1.25], colors="#94a3b8", linestyles="--", linewidths=0.75)
    ax.clabel(contours, inline=True, fontsize=7, fmt="RMS=%.2f")

    var_colors = {
        "rainfall": ["#0369a1", "#0284c7", "#38bdf8", "#0891b2", "#0d9488", "#16a34a"],
        "tmax": ["#b45309", "#d97706", "#f59e0b", "#ea580c", "#c2410c", "#9a3412"],
        "tmin": ["#4338ca", "#6366f1", "#818cf8", "#7c3aed", "#a855f7", "#6b21a8"]
    }
    palette = var_colors.get(var_type, ["#1e293b", "#334155", "#475569"])
    markers = ["o", "s", "^", "D", "v", "P", "X", "<", ">", "h"]

    for idx, (_, row) in enumerate(df_var.iterrows()):
        r_val = max(0.0, min(1.0, row["r"])) if pd.notna(row["r"]) else 0.0
        theta_pt = np.arccos(r_val)
        
        std_norm = 1.0 - (row["pbias"] / 100.0) if pd.notna(row["pbias"]) else 1.0
        std_norm = max(0.4, min(1.4, std_norm))

        color = palette[idx % len(palette)]
        marker = markers[idx % len(markers)]
        is_win = row.get("is_winner", False)
        
        ax.plot(
            theta_pt, std_norm,
            marker=marker, markersize=11 if is_win else 7,
            color="#e11d48" if is_win else color,
            markeredgecolor="#fbbf24" if is_win else "#ffffff",
            markeredgewidth=2.2 if is_win else 0.8,
            label=f"{row['experiment_id']}{' [ÓPTIMO]' if is_win else ''}",
            zorder=9 if is_win else 5
        )

    ax.set_ylim(0, 1.5)
    ax.set_ylabel("Desviación Estándar Normalizada ($\\sigma_s / \\sigma_o$)", labelpad=30, fontsize=10, fontweight="bold", color="#1e293b")
    ax.grid(True, linestyle=":", color="#cbd5e1", alpha=0.8)

    plt.title(plot_title, fontsize=11, fontweight="bold", color="#0f172a", pad=20)
    plt.legend(bbox_to_anchor=(1.32, 1.0), loc="upper left", frameon=True, fontsize=8)
    plt.tight_layout()

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()


def generate_kge_boxplots(
    df_stations: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    title: Optional[str] = None
):
    """Generates comparative boxplots of KGE across holdout stations for a specific variable."""
    if df_stations.empty or "kge" not in df_stations.columns:
        return
    
    df_var = df_stations[df_stations["variable"] == var_type].copy()
    if df_var.empty:
        return

    var_titles = {
        "rainfall": "Distribución Espacial de Eficiencia KGE en Estaciones Holdout: Precipitación",
        "tmax": "Distribución Espacial de Eficiencia KGE en Estaciones Holdout: Tmax",
        "tmin": "Distribución Espacial de Eficiencia KGE en Estaciones Holdout: Tmin"
    }
    plot_title = title or var_titles.get(var_type, f"Distribución Espacial KGE: {var_type.upper()}")

    plt.figure(figsize=(12, 6), dpi=300)
    sns.set_theme(style="whitegrid")

    exp_order = (
        df_var.groupby("experiment_id")["kge"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )

    palette_map = {"rainfall": "Blues_r", "tmax": "YlOrRd_r", "tmin": "Purples_r"}
    palette = sns.color_palette(palette_map.get(var_type, "Blues_r"), len(exp_order))
    
    ax = sns.boxplot(
        data=df_var,
        x="experiment_id",
        y="kge",
        hue="experiment_id",
        legend=False,
        order=exp_order,
        palette=palette,
        fliersize=3,
        linewidth=1.2,
    )
    
    plt.axhline(0.75, color="#16a34a", linestyle="--", linewidth=1.2, label="Umbral Óptimo (KGE >= 0.75)")
    plt.axhline(0.50, color="#d97706", linestyle=":", linewidth=1.0, label="Umbral Aceptable (KGE >= 0.50)")
    plt.axhline(0.00, color="#dc2626", linestyle="-", linewidth=0.8, alpha=0.6, label="Sin Habilidad vs Media (KGE <= 0.0)")

    plt.title(plot_title, fontsize=12, fontweight="bold", color="#0f172a", pad=15)
    plt.xlabel("Configuración de Experimento (Ordenado por KGE Mediano)", fontsize=10, fontweight="bold", labelpad=10)
    plt.ylabel("Eficiencia Kling-Gupta (KGE)", fontsize=10, fontweight="bold", labelpad=10)
    plt.xticks(rotation=45, ha="right", fontsize=9)
    plt.ylim(-0.2, 1.0)
    plt.legend(loc="lower left", frameon=True, fontsize=8)
    plt.tight_layout()

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()


def generate_strata_performance_chart(
    df_stations: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    title: Optional[str] = None
):
    """Evaluates how top experiments behave across relief strata (<500m, 500-1500m, >1500m)."""
    if df_stations.empty or "kge" not in df_stations.columns:
        return

    df_enriched = enrich_stations_with_elevation(df_stations)
    if "elev" not in df_enriched.columns or df_enriched["elev"].dropna().empty:
        print(f"  [Fig] Aviso: No se encontraron cotas de elevación válidas para estratificar {var_type}.")
        return

    df_var = df_enriched[df_enriched["variable"] == var_type].copy()
    if df_var.empty or df_var["elev"].dropna().empty:
        return

    bins = [-np.inf, 500, 1500, np.inf]
    labels = ["Tierras Bajas (<500 m)", "Transición Premontana (500–1500 m)", "Tierras Altas (>1500 m)"]
    df = df_var.copy()
    df["stratum"] = pd.cut(df["elev"], bins=bins, labels=labels)

    top_exps = (
        df.groupby("experiment_id")["kge"]
        .median()
        .sort_values(ascending=False)
        .head(6)
        .index.tolist()
    )
    df_sub = df[df["experiment_id"].isin(top_exps)]

    plt.figure(figsize=(11, 5.5), dpi=300)
    sns.set_theme(style="whitegrid")

    palette_map = {"rainfall": "crest", "tmax": "flare", "tmin": "mako"}
    ax = sns.barplot(
        data=df_sub,
        x="stratum",
        y="kge",
        hue="experiment_id",
        palette=palette_map.get(var_type, "crest"),
        errorbar=None,
        edgecolor="black",
        linewidth=0.8,
    )

    plot_title = title or f"Desempeño por Estratos Orográficos: {var_type.upper()}"
    plt.title(plot_title, fontsize=12, fontweight="bold", color="#0f172a", pad=15)
    plt.xlabel("Estrato Altitudinal / Topográfico", fontsize=10, fontweight="bold", labelpad=10)
    plt.ylabel("Eficiencia KGE Promedio", fontsize=10, fontweight="bold", labelpad=10)
    plt.ylim(0.0, 1.0)
    plt.legend(title="Configuración CDT", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True, fontsize=8)
    plt.tight_layout()

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()


def generate_radar_skill_chart(
    df_summaries: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    title: Optional[str] = None
):
    """Generates a multi-criteria Radar (Spider) chart showing multidimensional skill."""
    df_var = df_summaries[df_summaries["variable"] == var_type].copy() if not df_summaries.empty else pd.DataFrame()
    if df_var.empty:
        return

    df_sorted = df_var.sort_values(by="global_skill_score", ascending=False)
    top_candidates = df_sorted.head(4).copy()
    base_candidates = df_sorted[df_sorted["experiment_id"].str.contains("01", regex=False)]
    
    combined = pd.concat([top_candidates, base_candidates]).drop_duplicates(subset=["experiment_id"])
    combined = combined.sort_values(by="global_skill_score", ascending=False)

    if var_type in ("rainfall", "precip", "rain"):
        dimensions = [
            ("Eficiencia\n(KGE)", lambda d: np.clip((d["kge"] - 0.2) / 0.8, 0.0, 1.0)),
            ("Correlación\n(r)", lambda d: np.clip(d["r"], 0.0, 1.0)),
            ("Control Sesgo\n(1 - |PBIAS|)", lambda d: np.clip(1.0 - (abs(d["pbias"]) / 40.0), 0.0, 1.0)),
            ("Precisión Error\n(1 - RMSE norm)", lambda d: np.clip(1.0 - (d["rmse"] / (d["rmse"].max() * 1.1 + 1e-6)), 0.0, 1.0)),
            ("Habilidad Lluvia\n(ETS)", lambda d: np.clip(d["ets"] / max(0.01, d["ets"].max()), 0.0, 1.0)),
            ("Detección Eventos\n(POD)", lambda d: np.clip(d["pod"], 0.0, 1.0)),
        ]
    else:
        dimensions = [
            ("Eficiencia\n(KGE)", lambda d: np.clip((d["kge"] - 0.4) / 0.6, 0.0, 1.0)),
            ("Correlación\n(r)", lambda d: np.clip(d["r"], 0.0, 1.0)),
            ("Control Sesgo\n(1 - |PBIAS|)", lambda d: np.clip(1.0 - (abs(d["pbias"]) / 15.0), 0.0, 1.0)),
            ("Precisión RMSE\n(1 - RMSE norm)", lambda d: np.clip(1.0 - (d["rmse"] / (d["rmse"].max() * 1.1 + 1e-6)), 0.0, 1.0)),
            ("Error Absoluto\n(1 - MAE norm)", lambda d: np.clip(1.0 - (d["mae"] / (d["mae"].max() * 1.1 + 1e-6)), 0.0, 1.0)),
        ]

    num_vars = len(dimensions)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    plt.figure(figsize=(8.0, 7.5), dpi=300)
    ax = plt.subplot(111, polar=True)
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    labels = [d[0] for d in dimensions]
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9, fontweight="bold", color="#1e293b")
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["0.2", "0.4", "0.6", "0.8", "1.0 (Óptimo)"], fontsize=7, color="#64748b")
    ax.grid(color="#cbd5e1", linestyle="--", linewidth=0.7)

    plot_colors = ["#dc2626", "#0284c7", "#16a34a", "#8b5cf6", "#64748b"]
    for idx, (_, row) in enumerate(combined.iterrows()):
        is_win = row.get("is_winner", False)
        is_base = "01" in row["experiment_id"]
        
        values = [float(dim_fn(pd.DataFrame([row])).iloc[0]) for _, dim_fn in dimensions]
        values += values[:1]

        c = "#ea580c" if is_win else (plot_colors[idx % len(plot_colors)] if not is_base else "#475569")
        lw = 2.8 if is_win else (1.5 if not is_base else 1.2)
        ls = "-" if not is_base else "--"
        alpha = 0.22 if is_win else 0.06

        label_text = f"{row['experiment_id']}{' [ÓPTIMO]' if is_win else (' [BASE]' if is_base else '')}"
        ax.plot(angles, values, color=c, linewidth=lw, linestyle=ls, label=label_text, zorder=10 if is_win else 4)
        ax.fill(angles, values, color=c, alpha=alpha)

    plot_title = title or f"Diagrama Radial Multicriterio (Radar Skill): {var_type.upper()}"
    plt.title(plot_title, fontsize=12, fontweight="bold", color="#0f172a", pad=25)
    plt.legend(bbox_to_anchor=(1.35, 1.05), loc="upper left", frameon=True, fontsize=8)
    plt.tight_layout()

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()


def generate_metrics_heatmap(
    df_summaries: pd.DataFrame,
    output_png: Path | str,
    var_type: str = "rainfall",
    title: Optional[str] = None
):
    """Generates an annotated performance matrix/heatmap of experiments vs quantitative metrics."""
    df_var = df_summaries[df_summaries["variable"] == var_type].copy() if not df_summaries.empty else pd.DataFrame()
    if df_var.empty:
        return

    df_sorted = df_var.sort_values(by="rank", ascending=True).copy()

    if var_type in ("rainfall", "precip", "rain"):
        metric_cols = [
            ("global_skill_score", "GSS", True, "{:.3f}"),
            ("kge", "KGE", True, "{:.3f}"),
            ("r", "r (corr)", True, "{:.3f}"),
            ("rmse", "RMSE", False, "{:.2f}"),
            ("mae", "MAE", False, "{:.2f}"),
            ("pbias", "PBIAS (%)", "abs_zero", "{:+.1f}%"),
            ("pod", "POD", True, "{:.3f}"),
            ("far", "FAR", False, "{:.3f}"),
            ("ets", "ETS", True, "{:.3f}"),
            ("hss", "HSS", True, "{:.3f}"),
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

    norm_matrix = []
    text_matrix = []
    row_labels = []

    for _, row in df_sorted.iterrows():
        is_win = row.get("is_winner", False)
        prefix = "★ " if is_win else ""
        row_labels.append(f"{prefix}#{row['rank']:02d} {row['experiment_id']}")

    for col_key, _, is_higher_better, fmt in metric_cols:
        series = df_sorted[col_key] if col_key in df_sorted.columns else pd.Series(np.nan, index=df_sorted.index)
        
        if is_higher_better == "abs_zero":
            abs_val = series.abs()
            norm_col = np.clip(1.0 - (abs_val / (abs_val.max() + 1e-6)), 0.0, 1.0)
        elif is_higher_better is True:
            min_v = series.min()
            max_v = series.max()
            norm_col = (series - min_v) / (max_v - min_v + 1e-6) if max_v > min_v else pd.Series(1.0, index=series.index)
        else:
            min_v = series.min()
            max_v = series.max()
            norm_col = 1.0 - ((series - min_v) / (max_v - min_v + 1e-6)) if max_v > min_v else pd.Series(1.0, index=series.index)

        norm_matrix.append(norm_col.values)
        
        col_texts = []
        for v in series:
            if pd.isna(v):
                col_texts.append("-")
            else:
                col_texts.append(fmt.format(v))
        text_matrix.append(col_texts)

    norm_df = pd.DataFrame(np.array(norm_matrix).T, index=row_labels, columns=[c[1] for c in metric_cols])
    text_arr = np.array(text_matrix).T

    fig_height = max(5.0, len(row_labels) * 0.45 + 2.0)
    fig_width = max(8.5, len(metric_cols) * 1.1 + 2.0)
    plt.figure(figsize=(fig_width, fig_height), dpi=300)

    ax = sns.heatmap(
        norm_df,
        annot=text_arr,
        fmt="",
        cmap="RdYlGn",
        linewidths=1.0,
        linecolor="#ffffff",
        cbar_kws={"label": "Rendimiento Relativo Normalizado (0 = Mínimo, 1 = Óptimo)"},
        vmin=0.0,
        vmax=1.0,
    )
    ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9, fontweight="medium")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha="right", fontsize=9, fontweight="bold")

    plot_title = title or f"Heatmap Diagnóstico de Rendimiento Multimétrica: {var_type.upper()}"
    plt.title(plot_title, fontsize=12, fontweight="bold", color="#0f172a", pad=15)
    plt.tight_layout()

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()


def generate_roc_pod_vs_far(
    df_summaries: pd.DataFrame,
    output_png: Path | str,
    title: Optional[str] = None
):
    """Generates a categorical ROC space diagram (POD vs FAR) with Critical Success Index (CSI) isolines."""
    df_rain = df_summaries[df_summaries["variable"] == "rainfall"].copy() if not df_summaries.empty else pd.DataFrame()
    if df_rain.empty or "pod" not in df_rain.columns or "far" not in df_rain.columns:
        return

    plt.figure(figsize=(8.0, 7.5), dpi=300)
    ax = plt.subplot(111)

    far_vals = np.linspace(0.001, 0.7, 200)
    pod_vals = np.linspace(0.4, 1.0, 200)
    FAR_grid, POD_grid = np.meshgrid(far_vals, pod_vals)
    CSI_grid = 1.0 / ( (1.0 / POD_grid) + (1.0 / (1.0 - FAR_grid)) - 1.0 )

    cs = ax.contour(FAR_grid, POD_grid, CSI_grid, levels=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8], colors="#cbd5e1", linestyles="--", linewidths=0.9)
    ax.clabel(cs, inline=True, fontsize=8, fmt="CSI=%.2f")

    ax.plot(0.0, 1.0, marker="*", markersize=14, color="#16a34a", label="Detección Perfecta (FAR=0, POD=1)", zorder=10)

    winner_row = None
    for _, row in df_rain.iterrows():
        pod_val = row["pod"]
        far_val = row["far"]
        if pd.isna(pod_val) or pd.isna(far_val):
            continue

        is_win = row.get("is_winner", False)
        if is_win:
            winner_row = row
            ax.scatter(
                far_val, pod_val,
                s=180, color="#dc2626", edgecolors="#fbbf24", linewidth=2.5,
                zorder=12, label=f"{row['experiment_id']} [ÓPTIMO]"
            )
        else:
            is_base = "01" in row["experiment_id"]
            ax.scatter(
                far_val, pod_val,
                s=70 if is_base else 50,
                color="#475569" if is_base else "#0284c7",
                edgecolors="#ffffff", linewidth=0.8,
                alpha=0.9, zorder=5,
                label=f"{row['experiment_id']}" if is_base else None
            )

    if winner_row is not None and pd.notna(winner_row["pod"]) and pd.notna(winner_row["far"]):
        ax.annotate(
            f"  {winner_row['experiment_id']}\n  (POD: {winner_row['pod']:.2f}, FAR: {winner_row['far']:.2f})\n  [Mayor captura y menor falsa alarma]",
            xy=(winner_row["far"], winner_row["pod"]),
            xytext=(winner_row["far"] + 0.05, winner_row["pod"] - 0.08),
            arrowprops=dict(facecolor="#dc2626", shrink=0.08, width=1.5, headwidth=7),
            fontsize=9, fontweight="bold", color="#991b1b",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="#fee2e2", edgecolor="#f87171", alpha=0.9)
        )

    ax.set_xlim(-0.02, 0.65)
    ax.set_ylim(0.40, 1.02)
    ax.set_xlabel("Razón de Falsa Alarma (FAR) [Menor es mejor]", fontsize=10, fontweight="bold", labelpad=10)
    ax.set_ylabel("Probabilidad de Detección (POD) [Mayor es mejor]", fontsize=10, fontweight="bold", labelpad=10)
    
    plot_title = title or "Espacio ROC Categórico: Detección vs Falsa Alarma (Precipitación)"
    plt.title(plot_title, fontsize=12, fontweight="bold", color="#0f172a", pad=15)
    plt.grid(True, linestyle=":", color="#e2e8f0")
    plt.legend(loc="lower left", frameon=True, fontsize=8)
    plt.tight_layout()

    out_p = Path(output_png)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, dpi=300, bbox_inches="tight")
    plt.close()


# =============================================================================
# 4. PLOTLY INTERACTIVE CHART PAYLOAD GENERATOR
# =============================================================================

def build_interactive_chart_payloads(
    df_ranked: pd.DataFrame,
    df_stations: Optional[pd.DataFrame],
    var_type: str
) -> Dict[str, Any]:
    """Prepares structured Plotly.js JSON payloads for all diagnostic charts of a variable."""
    df_var = df_ranked[df_ranked["variable"] == var_type].copy() if not df_ranked.empty else pd.DataFrame()
    if df_var.empty:
        return {}

    payloads = {}

    # 1. Taylor Diagram (Polar Scatter)
    taylor_traces = [{
        "type": "scatterpolar",
        "mode": "markers+text",
        "r": [1.0],
        "theta": [0.0],
        "text": ["Referencia (Holdout)"],
        "textposition": "top right",
        "marker": {"symbol": "star", "size": 14, "color": "#dc2626"},
        "name": "Estaciones Holdout",
        "hoverinfo": "text",
    }]

    for _, row in df_var.iterrows():
        r_val = float(np.clip(row["r"], 0.0, 1.0)) if pd.notna(row["r"]) else 0.0
        theta_deg = float(math.acos(r_val) * 180.0 / math.pi)
        std_norm = float(np.clip(1.0 - (row["pbias"] / 100.0) if pd.notna(row["pbias"]) else 1.0, 0.4, 1.4))
        is_win = bool(row.get("is_winner", False))
        
        hover_txt = (
            f"<b>{row['experiment_id']}</b><br>"
            f"Correlación (r): {r_val:.3f}<br>"
            f"Desv. Est. Normalizada: {std_norm:.3f}<br>"
            f"KGE: {row['kge']:.3f}<br>"
            f"RMSE: {row['rmse']:.2f}"
        )
        taylor_traces.append({
            "type": "scatterpolar",
            "mode": "markers",
            "r": [std_norm],
            "theta": [theta_deg],
            "name": f"{row['experiment_id']}{' [ÓPTIMO]' if is_win else ''}",
            "text": [hover_txt],
            "hoverinfo": "text",
            "marker": {
                "size": 12 if is_win else 9,
                "color": "#e11d48" if is_win else ("#0284c7" if var_type == "rainfall" else ("#d97706" if var_type == "tmax" else "#7c3aed")),
                "line": {"color": "#fbbf24" if is_win else "#ffffff", "width": 2 if is_win else 1}
            }
        })

    taylor_layout = {
        "polar": {
            "radialaxis": {"visible": True, "range": [0, 1.5], "title": {"text": "Desv. Estándar Normalizada (σs/σo)"}},
            "angularaxis": {
                "direction": "counterclockwise",
                "period": 360,
                "min": 0,
                "max": 90,
                "tickmode": "array",
                "tickvals": [0, 18.2, 25.8, 36.9, 45.6, 53.1, 60.0, 66.4, 72.5, 78.5, 84.3, 90.0],
                "ticktext": ["1.00", "0.95", "0.90", "0.80", "0.70", "0.60", "0.50", "0.40", "0.30", "0.20", "0.10", "0.00"]
            }
        },
        "margin": {"t": 30, "b": 30, "l": 40, "r": 40},
        "showlegend": True,
        "legend": {"orientation": "h", "y": -0.15}
    }
    payloads["taylor"] = {"data": taylor_traces, "layout": taylor_layout}

    # 2. Boxplots KGE
    box_traces = []
    if df_stations is not None and not df_stations.empty and "kge" in df_stations.columns:
        st_var = df_stations[df_stations["variable"] == var_type]
        if not st_var.empty:
            med_order = st_var.groupby("experiment_id")["kge"].median().sort_values(ascending=False).index
            for exp_id in med_order:
                vals = [float(v) for v in st_var[st_var["experiment_id"] == exp_id]["kge"].dropna()]
                box_traces.append({
                    "type": "box",
                    "name": exp_id,
                    "y": vals,
                    "boxpoints": "outliers",
                    "jitter": 0.2,
                })
    box_layout = {
        "yaxis": {"title": "Kling-Gupta Efficiency (KGE)", "range": [-0.2, 1.05]},
        "xaxis": {"tickangle": -45},
        "shapes": [
            {"type": "line", "y0": 0.75, "y1": 0.75, "x0": 0, "x1": 1, "xref": "paper", "line": {"color": "#16a34a", "dash": "dash", "width": 1.2}},
            {"type": "line", "y0": 0.50, "y1": 0.50, "x0": 0, "x1": 1, "xref": "paper", "line": {"color": "#d97706", "dash": "dot", "width": 1.2}},
            {"type": "line", "y0": 0.00, "y1": 0.00, "x0": 0, "x1": 1, "xref": "paper", "line": {"color": "#dc2626", "width": 0.8}}
        ],
        "margin": {"t": 30, "b": 100, "l": 50, "r": 20},
        "showlegend": False
    }
    payloads["boxplots"] = {"data": box_traces, "layout": box_layout}

    # 3. Strata Performance
    strata_traces = []
    if df_stations is not None and not df_stations.empty and "kge" in df_stations.columns:
        df_st_enriched = enrich_stations_with_elevation(df_stations)
        st_var = df_st_enriched[df_st_enriched["variable"] == var_type].copy()
        if not st_var.empty and "elev" in st_var.columns and not st_var["elev"].dropna().empty:
            bins = [-np.inf, 500, 1500, np.inf]
            labels = ["Tierras Bajas (<500 m)", "Transición (500–1500 m)", "Tierras Altas (>1500 m)"]
            st_var["stratum"] = pd.cut(st_var["elev"], bins=bins, labels=labels)
            
            top_exps = st_var.groupby("experiment_id")["kge"].median().sort_values(ascending=False).head(5).index
            for exp_id in top_exps:
                exp_df = st_var[st_var["experiment_id"] == exp_id]
                means = []
                for s in labels:
                    m = exp_df[exp_df["stratum"] == s]["kge"].mean()
                    means.append(float(round(m, 3)) if pd.notna(m) else 0.0)
                strata_traces.append({
                    "type": "bar",
                    "name": exp_id,
                    "x": labels,
                    "y": means,
                })
    strata_layout = {
        "barmode": "group",
        "yaxis": {"title": "KGE Promedio", "range": [0, 1.05]},
        "xaxis": {"title": "Estrato Altitudinal"},
        "margin": {"t": 30, "b": 50, "l": 50, "r": 20},
        "legend": {"orientation": "h", "y": -0.25}
    }
    payloads["strata"] = {"data": strata_traces, "layout": strata_layout}

    # 4. Radar Skill Chart
    df_sorted = df_var.sort_values(by="global_skill_score", ascending=False)
    top_exps = pd.concat([df_sorted.head(4), df_sorted[df_sorted["experiment_id"].str.contains("01", regex=False)]]).drop_duplicates(subset=["experiment_id"])
    
    if var_type in ("rainfall", "precip", "rain"):
        dims = ["Eficiencia (KGE)", "Correlación (r)", "Control Sesgo", "Precisión (1-RMSE)", "Habilidad Lluvia (ETS)", "Detección (POD)"]
        def calc_vals(r):
            return [
                float(np.clip((r["kge"] - 0.2) / 0.8, 0, 1)),
                float(np.clip(r["r"], 0, 1)),
                float(np.clip(1.0 - (abs(r["pbias"]) / 40.0), 0, 1)),
                float(np.clip(1.0 - (r["rmse"] / (df_var["rmse"].max() * 1.1 + 1e-6)), 0, 1)),
                float(np.clip(r["ets"] / max(0.01, df_var["ets"].max()), 0, 1)),
                float(np.clip(r["pod"], 0, 1))
            ]
    else:
        dims = ["Eficiencia (KGE)", "Correlación (r)", "Control Sesgo", "Precisión (1-RMSE)", "Error Absoluto (1-MAE)"]
        def calc_vals(r):
            return [
                float(np.clip((r["kge"] - 0.4) / 0.6, 0, 1)),
                float(np.clip(r["r"], 0, 1)),
                float(np.clip(1.0 - (abs(r["pbias"]) / 15.0), 0, 1)),
                float(np.clip(1.0 - (r["rmse"] / (df_var["rmse"].max() * 1.1 + 1e-6)), 0, 1)),
                float(np.clip(1.0 - (r["mae"] / (df_var["mae"].max() * 1.1 + 1e-6)), 0, 1))
            ]

    radar_traces = []
    for _, row in top_exps.iterrows():
        v = calc_vals(row)
        v_loop = v + [v[0]]
        dims_loop = dims + [dims[0]]
        is_win = bool(row.get("is_winner", False))
        radar_traces.append({
            "type": "scatterpolar",
            "r": v_loop,
            "theta": dims_loop,
            "fill": "toself",
            "name": f"{row['experiment_id']}{' [ÓPTIMO]' if is_win else ''}",
            "line": {"width": 2.5 if is_win else 1.2},
            "opacity": 0.85 if is_win else 0.5
        })
    radar_layout = {
        "polar": {"radialaxis": {"visible": True, "range": [0, 1], "tickvals": [0.2, 0.4, 0.6, 0.8, 1.0]}},
        "margin": {"t": 40, "b": 40, "l": 40, "r": 40},
        "legend": {"orientation": "h", "y": -0.2}
    }
    payloads["radar"] = {"data": radar_traces, "layout": radar_layout}

    # 5. Metrics Heatmap
    if var_type in ("rainfall", "precip", "rain"):
        m_keys = [
            ("global_skill_score", "GSS", True, "{:.3f}"),
            ("kge", "KGE", True, "{:.3f}"),
            ("r", "r", True, "{:.3f}"),
            ("rmse", "RMSE", False, "{:.2f}"),
            ("mae", "MAE", False, "{:.2f}"),
            ("pbias", "PBIAS (%)", "abs_zero", "{:+.1f}%"),
            ("pod", "POD", True, "{:.3f}"),
            ("far", "FAR", False, "{:.3f}"),
            ("ets", "ETS", True, "{:.3f}"),
        ]
    else:
        m_keys = [
            ("global_skill_score", "GSS", True, "{:.3f}"),
            ("kge", "KGE", True, "{:.3f}"),
            ("r", "r", True, "{:.3f}"),
            ("rmse", "RMSE (°C)", False, "{:.2f}"),
            ("mae", "MAE (°C)", False, "{:.2f}"),
            ("pbias", "PBIAS (%)", "abs_zero", "{:+.1f}%"),
        ]
    
    df_hm = df_var.sort_values(by="rank", ascending=False)
    y_labels = [f"#{r['rank']:02d} {r['experiment_id']}" for _, r in df_hm.iterrows()]
    x_labels = [m[1] for m in m_keys]
    
    z_norm = []
    text_vals = []
    for _, row in df_hm.iterrows():
        row_z = []
        row_txt = []
        for k, name, is_high, fmt in m_keys:
            val = row.get(k, np.nan)
            if pd.isna(val):
                row_z.append(0.5)
                row_txt.append("-")
            else:
                row_txt.append(fmt.format(val))
                s = df_var[k]
                min_v, max_v = s.min(), s.max()
                if is_high == "abs_zero":
                    norm = 1.0 - (abs(val) / (abs(s).max() + 1e-6))
                elif is_high is True:
                    norm = (val - min_v) / (max_v - min_v + 1e-6) if max_v > min_v else 1.0
                else:
                    norm = 1.0 - ((val - min_v) / (max_v - min_v + 1e-6)) if max_v > min_v else 1.0
                row_z.append(float(round(norm, 3)))
        z_norm.append(row_z)
        text_vals.append(row_txt)

    heatmap_traces = [{
        "type": "heatmap",
        "z": z_norm,
        "x": x_labels,
        "y": y_labels,
        "text": text_vals,
        "texttemplate": "%{text}",
        "textfont": {"size": 10, "color": "#0f172a"},
        "colorscale": [[0, "#fca5a5"], [0.5, "#fef08a"], [1, "#86efac"]],
        "showscale": True,
        "colorbar": {"title": "Rendimiento Normalizado", "len": 0.8}
    }]
    heatmap_layout = {
        "xaxis": {"tickangle": -30},
        "margin": {"t": 30, "b": 60, "l": 160, "r": 20}
    }
    payloads["heatmap"] = {"data": heatmap_traces, "layout": heatmap_layout}

    # 6. ROC Space (Only rainfall)
    if var_type in ("rainfall", "precip", "rain"):
        roc_traces = []
        far_grid = np.linspace(0.01, 0.65, 50)
        for csi in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            line_x, line_y = [], []
            for far_val in far_grid:
                denom = (1.0 / csi) + 1.0 - (1.0 / (1.0 - far_val))
                if denom > 0:
                    pod_val = 1.0 / denom
                    if 0.4 <= pod_val <= 1.0:
                        line_x.append(float(round(far_val, 3)))
                        line_y.append(float(round(pod_val, 3)))
            if line_x:
                roc_traces.append({
                    "type": "scatter",
                    "mode": "lines",
                    "x": line_x,
                    "y": line_y,
                    "line": {"dash": "dot", "color": "#cbd5e1", "width": 1},
                    "name": f"CSI = {csi:.1f}",
                    "hoverinfo": "name",
                    "showlegend": False
                })
        roc_traces.append({
            "type": "scatter",
            "mode": "markers+text",
            "x": [0.0],
            "y": [1.0],
            "text": ["Punto Ideal (FAR=0, POD=1)"],
            "textposition": "top right",
            "marker": {"symbol": "star", "size": 14, "color": "#16a34a"},
            "name": "Detección Perfecta",
            "hoverinfo": "name"
        })
        exp_x, exp_y, exp_txt = [], [], []
        for _, row in df_var.iterrows():
            if pd.notna(row["far"]) and pd.notna(row["pod"]):
                exp_x.append(float(row["far"]))
                exp_y.append(float(row["pod"]))
                exp_txt.append(f"<b>{row['experiment_id']}</b><br>POD: {row['pod']:.3f}<br>FAR: {row['far']:.3f}<br>ETS: {row['ets']:.3f}")
        roc_traces.append({
            "type": "scatter",
            "mode": "markers+text",
            "x": exp_x,
            "y": exp_y,
            "text": [r["experiment_id"] for _, r in df_var.iterrows() if pd.notna(r["far"])],
            "textposition": "bottom center",
            "textfont": {"size": 9},
            "hovertext": exp_txt,
            "hoverinfo": "text",
            "marker": {"size": 11, "color": "#0284c7"},
            "name": "Experimentos"
        })
        roc_layout = {
            "xaxis": {"title": "Razón de Falsa Alarma (FAR) [Menor es mejor]", "range": [-0.02, 0.65]},
            "yaxis": {"title": "Probabilidad de Detección (POD) [Mayor es mejor]", "range": [0.4, 1.02]},
            "margin": {"t": 30, "b": 50, "l": 50, "r": 20},
            "showlegend": True,
            "legend": {"orientation": "h", "y": -0.2}
        }
        payloads["roc"] = {"data": roc_traces, "layout": roc_layout}

    # 7. Scatter KGE vs RMSE per variable
    scatter_traces = [{
        "type": "scatter",
        "mode": "markers+text",
        "x": [float(v) for v in df_var["rmse"]],
        "y": [float(v) for v in df_var["kge"]],
        "text": [r["experiment_id"] for _, r in df_var.iterrows()],
        "textposition": "top center",
        "marker": {"size": 11, "color": "#0284c7" if var_type == "rainfall" else ("#ea580c" if var_type == "tmax" else "#7c3aed")},
        "hoverinfo": "text",
        "hovertext": [f"<b>{r['experiment_id']}</b><br>RMSE: {r['rmse']:.2f}<br>KGE: {r['kge']:.3f}" for _, r in df_var.iterrows()]
    }]
    unit = "mm/día" if var_type == "rainfall" else "°C"
    scatter_layout = {
        "xaxis": {"title": f"RMSE ({unit}) [Menor es mejor]"},
        "yaxis": {"title": "KGE [Mayor es mejor]", "range": [0, 1.05]},
        "margin": {"t": 30, "b": 50, "l": 50, "r": 20}
    }
    payloads["scatter_kge_rmse"] = {"data": scatter_traces, "layout": scatter_layout}

    # 8. Delta KGE vs Base per variable
    bar_traces = [{
        "type": "bar",
        "x": [r["experiment_id"] for _, r in df_var.iterrows()],
        "y": [float(round(r["delta_kge_vs_base"], 3)) if pd.notna(r["delta_kge_vs_base"]) else 0.0 for _, r in df_var.iterrows()],
        "marker": {"color": ["#16a34a" if (r["delta_kge_vs_base"] or 0) >= 0 else "#dc2626" for _, r in df_var.iterrows()]}
    }]
    delta_layout = {
        "yaxis": {"title": "Δ KGE vs Línea Base"},
        "xaxis": {"tickangle": -45},
        "margin": {"t": 30, "b": 100, "l": 50, "r": 20}
    }
    payloads["delta_kge"] = {"data": bar_traces, "layout": delta_layout}

    return payloads


# =============================================================================
# 5. INTERACTIVE HTML DASHBOARD GENERATOR WITH PLOTLY
# =============================================================================

HTML_DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDT Grid Reconstruction Benchmark & Validation Leaderboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; }
        .tab-btn.active {
            border-bottom: 3px solid #2563eb;
            color: #ffffff;
            font-weight: 700;
        }
        .plot-card {
            background-color: #ffffff;
            border-radius: 0.75rem;
            border: 1px solid #e2e8f0;
            padding: 1.25rem;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        }
    </style>
</head>
<body class="text-slate-800">

    <!-- Top Navigation Bar -->
    <header class="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center space-x-3">
                <span class="bg-blue-600 text-white font-bold text-xs px-2.5 py-1 rounded tracking-wider">CDT 8.0</span>
                <h1 class="text-base font-bold tracking-tight text-white">Evaluación y Selección de Modelos de Malla (Benchmark)</h1>
            </div>
            <div class="text-xs text-slate-400">
                Fecha: <span class="font-mono text-slate-200">{{ timestamp }}</span> | Período: 1991–2020 | Validación Holdout
            </div>
        </div>

        <!-- Navigation Tabs Segregated by Variable -->
        <div class="max-w-7xl mx-auto px-6 flex space-x-8 border-t border-slate-800 text-sm overflow-x-auto">
            <button onclick="switchTab('rainfall')" id="tab-btn-rainfall" class="tab-btn active py-3 px-2 text-slate-300 hover:text-white flex items-center space-x-2 whitespace-nowrap">
                <span>🌧️ Precipitación (CHIRPS)</span>
            </button>
            <button onclick="switchTab('tmax')" id="tab-btn-tmax" class="tab-btn py-3 px-2 text-slate-300 hover:text-white flex items-center space-x-2 whitespace-nowrap">
                <span>☀️ Temp. Máxima (Tmax)</span>
            </button>
            <button onclick="switchTab('tmin')" id="tab-btn-tmin" class="tab-btn py-3 px-2 text-slate-300 hover:text-white flex items-center space-x-2 whitespace-nowrap">
                <span>🌙 Temp. Mínima (Tmin)</span>
            </button>
            <button onclick="switchTab('consolidated')" id="tab-btn-consolidated" class="tab-btn py-3 px-2 text-slate-300 hover:text-white flex items-center space-x-2 whitespace-nowrap">
                <span>📊 Resumen Consolidado</span>
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">

        <!-- ========================================================================= -->
        <!-- TAB 1: PRECIPITACIÓN -->
        <!-- ========================================================================= -->
        <div id="tab-content-rainfall" class="tab-panel space-y-8">
            
            {% if win_rain %}
            <div class="bg-slate-900 border border-slate-800 text-white rounded-xl p-6 shadow-md">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="text-xs text-sky-400 font-semibold uppercase tracking-wider mb-1">Configuración con Mayor Desempeño Global</div>
                        <h2 class="text-2xl font-black text-white">{{ win_rain.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1">{{ win_rain.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-800/80 rounded-lg p-3 border border-slate-700 text-center">
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-sky-400">{{ "%.3f"|format(win_rain.global_skill_score) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">KGE</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_rain.kge) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">Corr (r)</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_rain.r) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">ETS</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_rain.ets) if win_rain.ets else '-' }}</div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Interactive Diagnostic Suite: Precipitation -->
            <section class="space-y-6">
                <div>
                    <h3 class="text-base font-bold text-slate-900">Gráficos Diagnósticos Interactivos: Precipitación</h3>
                    <p class="text-xs text-slate-500">Inspeccione métricas pasando el cursor, use zoom interactivo o aísle experimentos desde la leyenda.</p>
                </div>

                <!-- Row 1: Taylor & Radar -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Diagrama Polar de Taylor</h4>
                            {% if fig_rain.taylor %}<a href="{{ fig_rain.taylor }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_taylor_rainfall" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Diagrama Radial Multicriterio</h4>
                            {% if fig_rain.radar %}<a href="{{ fig_rain.radar }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_radar_rainfall" style="height: 380px;"></div>
                    </div>
                </div>

                <!-- Row 2: Boxplots & Strata -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Distribución Espacial de Eficiencia (KGE Boxplots)</h4>
                            {% if fig_rain.kge_boxplots %}<a href="{{ fig_rain.kge_boxplots }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_box_rainfall" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Rendimiento por Estratos Topográficos</h4>
                            {% if fig_rain.strata %}<a href="{{ fig_rain.strata }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_strata_rainfall" style="height: 380px;"></div>
                    </div>
                </div>

                <!-- Row 3: Heatmap & ROC Space -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Matriz Diagnóstica de Métricas (Heatmap)</h4>
                            {% if fig_rain.heatmap %}<a href="{{ fig_rain.heatmap }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_heatmap_rainfall" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Espacio ROC Categórico (POD vs FAR)</h4>
                            {% if fig_rain.roc %}<a href="{{ fig_rain.roc }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_roc_rainfall" style="height: 380px;"></div>
                    </div>
                </div>

                <!-- Row 4: KGE vs RMSE & Delta KGE -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <h4 class="text-sm font-bold text-slate-900 mb-2">Dispersión: Precisión vs Error (KGE vs RMSE)</h4>
                        <div id="plot_scatter_rainfall" style="height: 340px;"></div>
                    </div>
                    <div class="plot-card">
                        <h4 class="text-sm font-bold text-slate-900 mb-2">Ganancia de Eficiencia frente a Línea Base (Δ KGE)</h4>
                        <div id="plot_delta_rainfall" style="height: 340px;"></div>
                    </div>
                </div>
            </section>

            <!-- Table of Experiments for Rainfall -->
            <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 class="text-sm font-bold text-slate-900 mb-4">Tabla de Evaluación Cuantitativa: Precipitación</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left datatable-var display">
                        <thead class="bg-slate-100 text-slate-700 text-xs uppercase">
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>GSS Score</th>
                                <th>KGE</th>
                                <th>Corr (r)</th>
                                <th>RMSE</th>
                                <th>PBIAS (%)</th>
                                <th>ETS</th>
                                <th>FAR</th>
                                <th>Δ KGE vs Base</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in rows_rain %}
                            <tr class="hover:bg-slate-50 border-b border-slate-100 {% if row.is_winner %}bg-sky-50/60 font-semibold{% endif %}">
                                <td class="text-center font-bold">{{ row.rank }}</td>
                                <td class="font-mono text-xs font-bold text-blue-900">{{ row.experiment_id }}</td>
                                <td class="font-bold text-emerald-700">{{ "%.3f"|format(row.global_skill_score) }}</td>
                                <td class="font-bold">{{ "%.3f"|format(row.kge) }}</td>
                                <td>{{ "%.3f"|format(row.r) }}</td>
                                <td>{{ "%.2f"|format(row.rmse) }}</td>
                                <td>{{ "%+.1f%%"|format(row.pbias) }}</td>
                                <td>{{ "%.3f"|format(row.ets) if row.ets else '-' }}</td>
                                <td>{{ "%.3f"|format(row.far) if row.far else '-' }}</td>
                                <td class="font-bold {% if row.delta_kge_vs_base > 0 %}text-emerald-600{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(row.delta_kge_vs_base) }}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 2: TEMPERATURA MÁXIMA -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmax" class="tab-panel hidden space-y-8">
            
            {% if win_tmax %}
            <div class="bg-slate-900 border border-slate-800 text-white rounded-xl p-6 shadow-md">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="text-xs text-amber-400 font-semibold uppercase tracking-wider mb-1">Configuración con Mayor Desempeño Global</div>
                        <h2 class="text-2xl font-black text-white">{{ win_tmax.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1">{{ win_tmax.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-800/80 rounded-lg p-3 border border-slate-700 text-center">
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-amber-400">{{ "%.3f"|format(win_tmax.global_skill_score) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">KGE</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_tmax.kge) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">Corr (r)</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_tmax.r) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">RMSE</div>
                            <div class="text-base font-bold text-white">{{ "%.2f °C"|format(win_tmax.rmse) }}</div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Interactive Diagnostic Suite: Tmax -->
            <section class="space-y-6">
                <div>
                    <h3 class="text-base font-bold text-slate-900">Gráficos Diagnósticos Interactivos: Temperatura Máxima</h3>
                    <p class="text-xs text-slate-500">Evaluación de gradiente adiabático y ajuste térmico diurno en estaciones independientes.</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Diagrama Polar de Taylor</h4>
                            {% if fig_tmax.taylor %}<a href="{{ fig_tmax.taylor }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_taylor_tmax" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Diagrama Radial Multicriterio</h4>
                            {% if fig_tmax.radar %}<a href="{{ fig_tmax.radar }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_radar_tmax" style="height: 380px;"></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Distribución Espacial de Eficiencia (KGE Boxplots)</h4>
                            {% if fig_tmax.kge_boxplots %}<a href="{{ fig_tmax.kge_boxplots }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_box_tmax" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Rendimiento por Estratos Topográficos</h4>
                            {% if fig_tmax.strata %}<a href="{{ fig_tmax.strata }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_strata_tmax" style="height: 380px;"></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Matriz Diagnóstica de Métricas (Heatmap)</h4>
                            {% if fig_tmax.heatmap %}<a href="{{ fig_tmax.heatmap }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_heatmap_tmax" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <h4 class="text-sm font-bold text-slate-900 mb-2">Dispersión: Precisión vs Error (KGE vs RMSE)</h4>
                        <div id="plot_scatter_tmax" style="height: 380px;"></div>
                    </div>
                </div>

                <div class="plot-card">
                    <h4 class="text-sm font-bold text-slate-900 mb-2">Ganancia de Eficiencia frente a Línea Base (Δ KGE)</h4>
                    <div id="plot_delta_tmax" style="height: 320px;"></div>
                </div>
            </section>

            <!-- Table of Experiments for Tmax -->
            <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 class="text-sm font-bold text-slate-900 mb-4">Tabla de Evaluación Cuantitativa: Temperatura Máxima</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left datatable-var display">
                        <thead class="bg-slate-100 text-slate-700 text-xs uppercase">
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>GSS Score</th>
                                <th>KGE</th>
                                <th>Corr (r)</th>
                                <th>RMSE (°C)</th>
                                <th>MAE (°C)</th>
                                <th>PBIAS (%)</th>
                                <th>Δ KGE vs Base</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in rows_tmax %}
                            <tr class="hover:bg-slate-50 border-b border-slate-100 {% if row.is_winner %}bg-amber-50/60 font-semibold{% endif %}">
                                <td class="text-center font-bold">{{ row.rank }}</td>
                                <td class="font-mono text-xs font-bold text-amber-900">{{ row.experiment_id }}</td>
                                <td class="font-bold text-emerald-700">{{ "%.3f"|format(row.global_skill_score) }}</td>
                                <td class="font-bold">{{ "%.3f"|format(row.kge) }}</td>
                                <td>{{ "%.3f"|format(row.r) }}</td>
                                <td>{{ "%.2f °C"|format(row.rmse) }}</td>
                                <td>{{ "%.2f °C"|format(row.mae) }}</td>
                                <td>{{ "%+.1f%%"|format(row.pbias) }}</td>
                                <td class="font-bold {% if row.delta_kge_vs_base > 0 %}text-emerald-600{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(row.delta_kge_vs_base) }}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 3: TEMPERATURA MÍNIMA -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmin" class="tab-panel hidden space-y-8">
            
            {% if win_tmin %}
            <div class="bg-slate-900 border border-slate-800 text-white rounded-xl p-6 shadow-md">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="text-xs text-purple-400 font-semibold uppercase tracking-wider mb-1">Configuración con Mayor Desempeño Global</div>
                        <h2 class="text-2xl font-black text-white">{{ win_tmin.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1">{{ win_tmin.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-800/80 rounded-lg p-3 border border-slate-700 text-center">
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-purple-400">{{ "%.3f"|format(win_tmin.global_skill_score) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">KGE</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_tmin.kge) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">Corr (r)</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_tmin.r) }}</div>
                        </div>
                        <div>
                            <div class="text-[10px] uppercase text-slate-400">RMSE</div>
                            <div class="text-base font-bold text-white">{{ "%.2f °C"|format(win_tmin.rmse) }}</div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Interactive Diagnostic Suite: Tmin -->
            <section class="space-y-6">
                <div>
                    <h3 class="text-base font-bold text-slate-900">Gráficos Diagnósticos Interactivos: Temperatura Mínima</h3>
                    <p class="text-xs text-slate-500">Evaluación de inversiones térmicas nocturnas y microclimas de fondo de valle.</p>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Diagrama Polar de Taylor</h4>
                            {% if fig_tmin.taylor %}<a href="{{ fig_tmin.taylor }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_taylor_tmin" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Diagrama Radial Multicriterio</h4>
                            {% if fig_tmin.radar %}<a href="{{ fig_tmin.radar }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_radar_tmin" style="height: 380px;"></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Distribución Espacial de Eficiencia (KGE Boxplots)</h4>
                            {% if fig_tmin.kge_boxplots %}<a href="{{ fig_tmin.kge_boxplots }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_box_tmin" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Rendimiento por Estratos Topográficos</h4>
                            {% if fig_tmin.strata %}<a href="{{ fig_tmin.strata }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_strata_tmin" style="height: 380px;"></div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <h4 class="text-sm font-bold text-slate-900">Matriz Diagnóstica de Métricas (Heatmap)</h4>
                            {% if fig_tmin.heatmap %}<a href="{{ fig_tmin.heatmap }}" target="_blank" class="text-[11px] text-blue-600 hover:underline">Descargar PNG (300 DPI)</a>{% endif %}
                        </div>
                        <div id="plot_heatmap_tmin" style="height: 380px;"></div>
                    </div>
                    <div class="plot-card">
                        <h4 class="text-sm font-bold text-slate-900 mb-2">Dispersión: Precisión vs Error (KGE vs RMSE)</h4>
                        <div id="plot_scatter_tmin" style="height: 380px;"></div>
                    </div>
                </div>

                <div class="plot-card">
                    <h4 class="text-sm font-bold text-slate-900 mb-2">Ganancia de Eficiencia frente a Línea Base (Δ KGE)</h4>
                    <div id="plot_delta_tmin" style="height: 320px;"></div>
                </div>
            </section>

            <!-- Table of Experiments for Tmin -->
            <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 class="text-sm font-bold text-slate-900 mb-4">Tabla de Evaluación Cuantitativa: Temperatura Mínima</h3>
                <div class="overflow-x-auto">
                    <table class="w-full text-sm text-left datatable-var display">
                        <thead class="bg-slate-100 text-slate-700 text-xs uppercase">
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>GSS Score</th>
                                <th>KGE</th>
                                <th>Corr (r)</th>
                                <th>RMSE (°C)</th>
                                <th>MAE (°C)</th>
                                <th>PBIAS (%)</th>
                                <th>Δ KGE vs Base</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in rows_tmin %}
                            <tr class="hover:bg-slate-50 border-b border-slate-100 {% if row.is_winner %}bg-purple-50/60 font-semibold{% endif %}">
                                <td class="text-center font-bold">{{ row.rank }}</td>
                                <td class="font-mono text-xs font-bold text-purple-900">{{ row.experiment_id }}</td>
                                <td class="font-bold text-emerald-700">{{ "%.3f"|format(row.global_skill_score) }}</td>
                                <td class="font-bold">{{ "%.3f"|format(row.kge) }}</td>
                                <td>{{ "%.3f"|format(row.r) }}</td>
                                <td>{{ "%.2f °C"|format(row.rmse) }}</td>
                                <td>{{ "%.2f °C"|format(row.mae) }}</td>
                                <td>{{ "%+.1f%%"|format(row.pbias) }}</td>
                                <td class="font-bold {% if row.delta_kge_vs_base > 0 %}text-emerald-600{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(row.delta_kge_vs_base) }}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 4: RESUMEN CONSOLIDADO -->
        <!-- ========================================================================= -->
        <div id="tab-content-consolidated" class="tab-panel hidden space-y-8">
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-slate-900 text-white rounded-xl p-5 border border-slate-800 shadow-sm">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-sky-400">Precipitación (CHIRPS)</div>
                    <div class="text-xl font-black mt-1">{{ win_rain.experiment_id if win_rain else 'N/A' }}</div>
                    <div class="text-xs text-slate-300 mt-1 line-clamp-2">{{ win_rain.description if win_rain else '-' }}</div>
                    <div class="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs text-slate-300">
                        <div>KGE: <b class="text-white">{{ "%.3f"|format(win_rain.kge) if win_rain else '-' }}</b></div>
                        <div>r: <b class="text-white">{{ "%.3f"|format(win_rain.r) if win_rain else '-' }}</b></div>
                        <div>ETS: <b class="text-white">{{ "%.3f"|format(win_rain.ets) if win_rain and win_rain.ets else '-' }}</b></div>
                    </div>
                </div>

                <div class="bg-slate-900 text-white rounded-xl p-5 border border-slate-800 shadow-sm">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-amber-400">Temp. Máxima (Tmax)</div>
                    <div class="text-xl font-black mt-1">{{ win_tmax.experiment_id if win_tmax else 'N/A' }}</div>
                    <div class="text-xs text-slate-300 mt-1 line-clamp-2">{{ win_tmax.description if win_tmax else '-' }}</div>
                    <div class="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs text-slate-300">
                        <div>KGE: <b class="text-white">{{ "%.3f"|format(win_tmax.kge) if win_tmax else '-' }}</b></div>
                        <div>r: <b class="text-white">{{ "%.3f"|format(win_tmax.r) if win_tmax else '-' }}</b></div>
                        <div>RMSE: <b class="text-white">{{ "%.2f °C"|format(win_tmax.rmse) if win_tmax else '-' }}</b></div>
                    </div>
                </div>

                <div class="bg-slate-900 text-white rounded-xl p-5 border border-slate-800 shadow-sm">
                    <div class="text-[10px] font-bold uppercase tracking-wider text-purple-400">Temp. Mínima (Tmin)</div>
                    <div class="text-xl font-black mt-1">{{ win_tmin.experiment_id if win_tmin else 'N/A' }}</div>
                    <div class="text-xs text-slate-300 mt-1 line-clamp-2">{{ win_tmin.description if win_tmin else '-' }}</div>
                    <div class="mt-4 pt-3 border-t border-slate-800 flex justify-between text-xs text-slate-300">
                        <div>KGE: <b class="text-white">{{ "%.3f"|format(win_tmin.kge) if win_tmin else '-' }}</b></div>
                        <div>r: <b class="text-white">{{ "%.3f"|format(win_tmin.r) if win_tmin else '-' }}</b></div>
                        <div>RMSE: <b class="text-white">{{ "%.2f °C"|format(win_tmin.rmse) if win_tmin else '-' }}</b></div>
                    </div>
                </div>
            </div>

            <!-- Master Table Across All Variables -->
            <section class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
                <h3 class="text-sm font-bold text-slate-900 mb-4">Tabla General Consolidada de Experimentos</h3>
                <div class="overflow-x-auto">
                    <table id="masterConsolidatedTable" class="w-full text-sm text-left display">
                        <thead class="bg-slate-100 text-slate-700 text-xs uppercase">
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>Variable</th>
                                <th>GSS Score</th>
                                <th>KGE</th>
                                <th>Corr (r)</th>
                                <th>RMSE</th>
                                <th>PBIAS (%)</th>
                                <th>Δ KGE vs Base</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in rows_all %}
                            <tr class="hover:bg-slate-50 border-b border-slate-100 {% if row.is_winner %}bg-slate-50 font-medium{% endif %}">
                                <td class="text-center font-bold">{{ row.rank }}</td>
                                <td class="font-mono text-xs font-bold text-slate-900">{{ row.experiment_id }}</td>
                                <td><span class="px-2 py-0.5 rounded text-[11px] font-semibold uppercase {% if row.variable == 'rainfall' %}bg-sky-100 text-sky-800{% elif row.variable == 'tmax' %}bg-amber-100 text-amber-800{% else %}bg-purple-100 text-purple-800{% endif %}">{{ row.variable }}</span></td>
                                <td class="font-bold text-emerald-700">{{ "%.3f"|format(row.global_skill_score) }}</td>
                                <td class="font-bold">{{ "%.3f"|format(row.kge) }}</td>
                                <td>{{ "%.3f"|format(row.r) }}</td>
                                <td>{{ "%.2f"|format(row.rmse) }}</td>
                                <td>{{ "%+.1f%%"|format(row.pbias) }}</td>
                                <td class="font-bold {% if row.delta_kge_vs_base > 0 %}text-emerald-600{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(row.delta_kge_vs_base) }}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- Comparative Global Scatter Plots -->
            <section class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="plot-card">
                    <h3 class="text-sm font-bold text-slate-900 mb-2">Dispersión KGE vs RMSE (Todas las Variables)</h3>
                    <div id="scatterPlotAll" style="height: 380px;"></div>
                </div>
                <div class="plot-card">
                    <h3 class="text-sm font-bold text-slate-900 mb-2">Ganancia de Eficiencia vs Línea Base (Δ KGE)</h3>
                    <div id="deltaBarPlotAll" style="height: 380px;"></div>
                </div>
            </section>

            <!-- Scientific Synthesis -->
            <section class="bg-slate-900 text-slate-200 rounded-xl p-6 border border-slate-800">
                <h3 class="text-sm font-bold text-white mb-2">Síntesis Metodológica y Regional</h3>
                <p class="text-xs leading-relaxed text-slate-300">
                    La evaluación independiente mediante validación cruzada espacial (Holdout por CSV) confirma que el ajuste no lineal mediante <b>Mapeo de Cuantiles (QM)</b> o ajuste multiplicativo acoplado a <b>Regression Kriging (RK)</b> con covariables fisiográficas (DEM, pendiente y orientación) optimiza simultáneamente la correlación de Pearson y la eficiencia de Kling-Gupta (KGE), al tiempo que minimiza la tasa de falsa alarma en precipitación y preserva el gradiente adiabático regional investigado por Hastenrath (1967, 1991).
                </p>
            </section>

        </div>

    </main>

    <script>
        function switchTab(tabId) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('active', 'text-white');
                b.classList.add('text-slate-300');
            });

            const panel = document.getElementById('tab-content-' + tabId);
            const btn = document.getElementById('tab-btn-' + tabId);
            if (panel && btn) {
                panel.classList.remove('hidden');
                btn.classList.add('active', 'text-white');
                btn.classList.remove('text-slate-300');
                // Resize Plotly plots when tab becomes visible
                setTimeout(function() {
                    window.dispatchEvent(new Event('resize'));
                }, 50);
            }
        }

        $(document).ready(function() {
            $('.datatable-var').DataTable({
                paging: false,
                searching: true,
                info: false,
                order: [[2, 'desc']]
            });

            $('#masterConsolidatedTable').DataTable({
                paging: false,
                searching: true,
                info: false,
                order: [[3, 'desc']]
            });

            // Initialize Plotly Interactive Charts for Rainfall
            var p_rain = {{ payloads_rain | safe }};
            if (p_rain.taylor) Plotly.newPlot('plot_taylor_rainfall', p_rain.taylor.data, p_rain.taylor.layout, {responsive: true});
            if (p_rain.radar) Plotly.newPlot('plot_radar_rainfall', p_rain.radar.data, p_rain.radar.layout, {responsive: true});
            if (p_rain.boxplots) Plotly.newPlot('plot_box_rainfall', p_rain.boxplots.data, p_rain.boxplots.layout, {responsive: true});
            if (p_rain.strata) Plotly.newPlot('plot_strata_rainfall', p_rain.strata.data, p_rain.strata.layout, {responsive: true});
            if (p_rain.heatmap) Plotly.newPlot('plot_heatmap_rainfall', p_rain.heatmap.data, p_rain.heatmap.layout, {responsive: true});
            if (p_rain.roc) Plotly.newPlot('plot_roc_rainfall', p_rain.roc.data, p_rain.roc.layout, {responsive: true});
            if (p_rain.scatter_kge_rmse) Plotly.newPlot('plot_scatter_rainfall', p_rain.scatter_kge_rmse.data, p_rain.scatter_kge_rmse.layout, {responsive: true});
            if (p_rain.delta_kge) Plotly.newPlot('plot_delta_rainfall', p_rain.delta_kge.data, p_rain.delta_kge.layout, {responsive: true});

            // Initialize Plotly Interactive Charts for Tmax
            var p_tmax = {{ payloads_tmax | safe }};
            if (p_tmax.taylor) Plotly.newPlot('plot_taylor_tmax', p_tmax.taylor.data, p_tmax.taylor.layout, {responsive: true});
            if (p_tmax.radar) Plotly.newPlot('plot_radar_tmax', p_tmax.radar.data, p_tmax.radar.layout, {responsive: true});
            if (p_tmax.boxplots) Plotly.newPlot('plot_box_tmax', p_tmax.boxplots.data, p_tmax.boxplots.layout, {responsive: true});
            if (p_tmax.strata) Plotly.newPlot('plot_strata_tmax', p_tmax.strata.data, p_tmax.strata.layout, {responsive: true});
            if (p_tmax.heatmap) Plotly.newPlot('plot_heatmap_tmax', p_tmax.heatmap.data, p_tmax.heatmap.layout, {responsive: true});
            if (p_tmax.scatter_kge_rmse) Plotly.newPlot('plot_scatter_tmax', p_tmax.scatter_kge_rmse.data, p_tmax.scatter_kge_rmse.layout, {responsive: true});
            if (p_tmax.delta_kge) Plotly.newPlot('plot_delta_tmax', p_tmax.delta_kge.data, p_tmax.delta_kge.layout, {responsive: true});

            // Initialize Plotly Interactive Charts for Tmin
            var p_tmin = {{ payloads_tmin | safe }};
            if (p_tmin.taylor) Plotly.newPlot('plot_taylor_tmin', p_tmin.taylor.data, p_tmin.taylor.layout, {responsive: true});
            if (p_tmin.radar) Plotly.newPlot('plot_radar_tmin', p_tmin.radar.data, p_tmin.radar.layout, {responsive: true});
            if (p_tmin.boxplots) Plotly.newPlot('plot_box_tmin', p_tmin.boxplots.data, p_tmin.boxplots.layout, {responsive: true});
            if (p_tmin.strata) Plotly.newPlot('plot_strata_tmin', p_tmin.strata.data, p_tmin.strata.layout, {responsive: true});
            if (p_tmin.heatmap) Plotly.newPlot('plot_heatmap_tmin', p_tmin.heatmap.data, p_tmin.heatmap.layout, {responsive: true});
            if (p_tmin.scatter_kge_rmse) Plotly.newPlot('plot_scatter_tmin', p_tmin.scatter_kge_rmse.data, p_tmin.scatter_kge_rmse.layout, {responsive: true});
            if (p_tmin.delta_kge) Plotly.newPlot('plot_delta_tmin', p_tmin.delta_kge.data, p_tmin.delta_kge.layout, {responsive: true});

            // Global Consolidated Plots
            var scatterData = [{
                x: {{ scatter_rmse | safe }},
                y: {{ scatter_kge | safe }},
                text: {{ scatter_labels | safe }},
                mode: 'markers+text',
                textposition: 'top center',
                marker: {
                    size: 11,
                    color: {{ scatter_colors | safe }},
                    opacity: 0.85
                },
                type: 'scatter'
            }];
            var scatterLayout = {
                xaxis: { title: 'RMSE (menor es mejor)' },
                yaxis: { title: 'Kling-Gupta Efficiency (KGE)', range: [0, 1] },
                margin: { t: 20, r: 20, l: 50, b: 50 }
            };
            Plotly.newPlot('scatterPlotAll', scatterData, scatterLayout, {responsive: true});

            var barData = [{
                x: {{ bar_labels | safe }},
                y: {{ bar_deltas | safe }},
                type: 'bar',
                marker: { color: {{ bar_colors | safe }} }
            }];
            var barLayout = {
                yaxis: { title: 'Δ KGE vs Línea Base' },
                xaxis: { tickangle: -45 },
                margin: { t: 20, r: 20, l: 50, b: 100 }
            };
            Plotly.newPlot('deltaBarPlotAll', barData, barLayout, {responsive: true});
        });
    </script>
</body>
</html>
"""


def generate_interactive_html_dashboard(
    df_ranked: pd.DataFrame,
    figures_map: Dict[str, Dict[str, str]],
    output_html_path: Path | str,
    df_stations: Optional[pd.DataFrame] = None
):
    """Compiles the interactive benchmark dashboard with segregated variable tabs, Plotly charts, and neutral styling."""
    from jinja2 import Template

    if df_ranked.empty:
        return

    def get_winner(var_name: str) -> Optional[Dict[str, Any]]:
        sub = df_ranked[df_ranked["variable"] == var_name]
        if not sub.empty:
            return sub.sort_values(by="global_skill_score", ascending=False).iloc[0].to_dict()
        return None

    win_rain = get_winner("rainfall")
    win_tmax = get_winner("tmax")
    win_tmin = get_winner("tmin")

    rows_rain = df_ranked[df_ranked["variable"] == "rainfall"].to_dict(orient="records")
    rows_tmax = df_ranked[df_ranked["variable"] == "tmax"].to_dict(orient="records")
    rows_tmin = df_ranked[df_ranked["variable"] == "tmin"].to_dict(orient="records")
    rows_all = df_ranked.to_dict(orient="records")

    # Generate interactive payloads for each variable
    payloads_rain = build_interactive_chart_payloads(df_ranked, df_stations, "rainfall")
    payloads_tmax = build_interactive_chart_payloads(df_ranked, df_stations, "tmax")
    payloads_tmin = build_interactive_chart_payloads(df_ranked, df_stations, "tmin")

    # Consolidated data arrays
    scatter_rmse = df_ranked["rmse"].tolist()
    scatter_kge = df_ranked["kge"].tolist()
    scatter_labels = df_ranked["experiment_id"].tolist()
    scatter_colors = [
        "#0284c7" if v == "rainfall" else ("#ea580c" if v == "tmax" else "#7c3aed")
        for v in df_ranked["variable"]
    ]

    bar_labels = df_ranked["experiment_id"].tolist()
    bar_deltas = [round(float(v), 3) if pd.notna(v) else 0.0 for v in df_ranked["delta_kge_vs_base"]]
    bar_colors = ["#16a34a" if d >= 0 else "#dc2626" for d in bar_deltas]

    tmpl = Template(HTML_DASHBOARD_TEMPLATE)
    html_content = tmpl.render(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        win_rain=win_rain,
        win_tmax=win_tmax,
        win_tmin=win_tmin,
        fig_rain=figures_map.get("rainfall", {}),
        fig_tmax=figures_map.get("tmax", {}),
        fig_tmin=figures_map.get("tmin", {}),
        rows_rain=rows_rain,
        rows_tmax=rows_tmax,
        rows_tmin=rows_tmin,
        rows_all=rows_all,
        payloads_rain=json.dumps(payloads_rain),
        payloads_tmax=json.dumps(payloads_tmax),
        payloads_tmin=json.dumps(payloads_tmin),
        scatter_rmse=json.dumps(scatter_rmse),
        scatter_kge=json.dumps(scatter_kge),
        scatter_labels=json.dumps(scatter_labels),
        scatter_colors=json.dumps(scatter_colors),
        bar_labels=json.dumps(bar_labels),
        bar_deltas=json.dumps(bar_deltas),
        bar_colors=json.dumps(bar_colors),
    )

    out_p = Path(output_html_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    with open(out_p, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"  [HTML] Interactive Benchmark Dashboard generated: {out_p}")


# =============================================================================
# 6. FULL BENCHMARK SUITE ORCHESTRATION
# =============================================================================

def run_full_benchmark_suite(
    experiments_dir: Path | str = "output/experiments",
    output_dir: Path | str = "output/benchmark"
) -> pd.DataFrame:
    """Executes the complete benchmark analysis, figures generation segregated by variable, and dashboard build."""
    exp_path = Path(experiments_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("       CDT GRID BENCHMARK & EXPERIMENT LEADERBOARD EVALUATION")
    print("=" * 80)

    # 1. Harvest metrics
    df_summaries, df_stations = harvest_experiment_metrics(exp_path)
    if df_summaries.empty:
        print(f"[!] No validation summaries found in {exp_path}. Run experiments first.")
        return pd.DataFrame()

    print(f"  --> Detected {len(df_summaries)} experiment summaries.")

    # 2. Compute rankings
    df_ranked = compute_leaderboard_ranking(df_summaries)

    # Save summary CSV & JSON
    csv_path = out_path / "benchmark_leaderboard_summary.csv"
    json_path = out_path / "benchmark_leaderboard.json"
    df_ranked.to_csv(csv_path, index=False)
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(df_ranked.to_dict(orient="records"), jf, indent=2)
    print(f"  [CSV] Summary table saved: {csv_path}")

    # 3. Generate static figures segregated by variable
    figures_base = out_path / "figures"
    figures_map: Dict[str, Dict[str, str]] = {}

    unique_vars = df_ranked["variable"].unique() if "variable" in df_ranked.columns else ["rainfall"]

    for var in unique_vars:
        var_fig_dir = figures_base / var
        var_fig_dir.mkdir(parents=True, exist_ok=True)

        taylor_path = var_fig_dir / "figure_1_taylor_diagram.png"
        kge_path = var_fig_dir / "figure_2_kge_boxplots_by_station.png"
        strata_path = var_fig_dir / "figure_3_elevation_strata_performance.png"
        radar_path = var_fig_dir / "figure_4_radar_skill_chart.png"
        heatmap_path = var_fig_dir / "figure_5_metrics_heatmap.png"
        roc_path = var_fig_dir / "figure_6_roc_pod_vs_far.png"

        generate_taylor_diagram(df_ranked, taylor_path, var_type=var)
        generate_radar_skill_chart(df_ranked, radar_path, var_type=var)
        generate_metrics_heatmap(df_ranked, heatmap_path, var_type=var)

        if not df_stations.empty:
            generate_kge_boxplots(df_stations, kge_path, var_type=var)
            generate_strata_performance_chart(df_stations, strata_path, var_type=var)

        if var in ("rainfall", "precip", "rain"):
            generate_roc_pod_vs_far(df_ranked, roc_path)

        figures_map[var] = {
            "taylor": f"figures/{var}/figure_1_taylor_diagram.png",
            "kge_boxplots": f"figures/{var}/figure_2_kge_boxplots_by_station.png",
            "strata": f"figures/{var}/figure_3_elevation_strata_performance.png",
            "radar": f"figures/{var}/figure_4_radar_skill_chart.png",
            "heatmap": f"figures/{var}/figure_5_metrics_heatmap.png",
            "roc": f"figures/{var}/figure_6_roc_pod_vs_far.png" if var in ("rainfall", "precip", "rain") else "",
        }

    # 4. Generate Interactive HTML Dashboard with Plotly
    html_path = out_path / "benchmark_report.html"
    generate_interactive_html_dashboard(df_ranked, figures_map, html_path, df_stations=df_stations)

    # 5. Print Leaderboard in Console
    print("\n" + "-" * 80)
    print("  LEADERBOARD RANKING (TOP CANDIDATES)")
    print("-" * 80)
    for _, r in df_ranked.iterrows():
        star = "* [MEJOR]" if r.get("is_winner") else " "
        print(f"  #{r['rank']:02d} | {r['variable'].upper():8s} | {r['experiment_id']:30s} | GSS: {r['global_skill_score']:.3f} | KGE: {r['kge']:.3f} | r: {r['r']:.3f} | RMSE: {r['rmse']:.2f} {star}")
    print("-" * 80 + "\n")

    return df_ranked


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CDT Benchmark & Grid Validation Leaderboard Reporter")
    parser.add_argument("--experiments-dir", "-e", default="output/experiments", help="Path to experiments output root")
    parser.add_argument("--output-dir", "-o", default="output/benchmark", help="Output directory for benchmark reports")
    args = parser.parse_args()

    run_full_benchmark_suite(args.experiments_dir, args.output_dir)
