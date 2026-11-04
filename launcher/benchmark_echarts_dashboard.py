"""
Interactive HTML Benchmark Dashboard powered by Apache ECharts.

Provides a modern, publication-grade interactive dashboard for the CDT 8.0
Central America Grid Reconstruction Suite.
Features:
- "Data-First" layout: Executive KPIs and Full Interactive Master Table & Rankings
  presented upfront before interactive visual deep-dives.
- Interactive Polar Taylor Diagram in Apache ECharts (Pearson r vs. Normalized Std Dev,
  reference holdout observation star, unit variance arc, RMS isolines).
- Multi-criteria skill radar chart containing ALL experiments with a scrollable
  interactive legend (defaulting to [ÓPTIMO] Winner and [CONTROL 0] Raw Baseline).
- Highlighting for [CONTROL 0] in slate grey (#64748b) and Winner in emerald/gold (#059669).
- Boxplots of station-level KGE distributions.
- Centro de Descargas (300 DPI): One-click download cards for all publication-ready figures
  and toolbox.saveAsImage across all interactive charts.
- Comprehensive scientific glossary defining all 9 climate evaluation metrics with KaTeX equations,
  optimal targets, acceptable ranges, and physical interpretation for Central America.
"""

from __future__ import annotations

import datetime
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


def compute_echarts_payloads(
    df_ranked: pd.DataFrame,
    df_stations: Optional[pd.DataFrame],
    var_type: str,
) -> Dict[str, Any]:
    """Generates structured data payloads for Apache ECharts charts for a specific variable."""
    df_var = df_ranked[df_ranked["variable"] == var_type].copy() if not df_ranked.empty else pd.DataFrame()
    if df_var.empty:
        return {}

    # Ensure is_control and is_winner flags exist
    if "is_control" not in df_var.columns:
        df_var["is_control"] = df_var["experiment_id"].str.contains(r"00_Raw|_Raw_", regex=True)
    if "is_winner" not in df_var.columns:
        df_var["is_winner"] = df_var["rank"] == 1

    # Identify control and winner
    raw_sub = df_var[df_var["is_control"] == True]
    raw_row = raw_sub.iloc[0] if not raw_sub.empty else None
    raw_kge = float(raw_row["kge"]) if raw_row is not None and pd.notna(raw_row.get("kge")) else 0.3
    raw_rmse = float(raw_row["rmse"]) if raw_row is not None and pd.notna(raw_row.get("rmse")) else 10.0

    # 1. Experiments Summary List for Table & Tooltips
    exps = []
    for _, r in df_var.iterrows():
        kge_v = float(r["kge"]) if pd.notna(r.get("kge")) else 0.0
        rmse_v = float(r["rmse"]) if pd.notna(r.get("rmse")) else 0.0
        r_v = float(r["r"]) if pd.notna(r.get("r")) else 0.0
        d_kge = kge_v - raw_kge
        d_rmse = rmse_v - raw_rmse
        pct_kge = (d_kge / abs(raw_kge) * 100.0) if raw_kge != 0 else 0.0
        pct_rmse = (-d_rmse / raw_rmse * 100.0) if raw_rmse != 0 else 0.0

        exps.append({
            "id": r["experiment_id"],
            "rank": int(r.get("rank", 0)),
            "is_winner": bool(r.get("is_winner", False)),
            "is_control": bool(r.get("is_control", False)),
            "desc": r.get("description", ""),
            "gss": round(float(r.get("global_skill_score", 0.0)), 3),
            "kge": round(kge_v, 3),
            "kge_median": round(float(r.get("kge_median", kge_v)), 3),
            "r": round(r_v, 3),
            "rmse": round(rmse_v, 2),
            "mae": round(float(r.get("mae", 0.0)), 2),
            "pbias": round(float(r.get("pbias", 0.0)), 1),
            "pod": round(float(r.get("pod", 0.0)), 3) if pd.notna(r.get("pod")) else None,
            "far": round(float(r.get("far", 0.0)), 3) if pd.notna(r.get("far")) else None,
            "ets": round(float(r.get("ets", 0.0)), 3) if pd.notna(r.get("ets")) else None,
            "delta_kge_raw": round(d_kge, 3),
            "pct_kge_gain": round(pct_kge, 1),
            "delta_rmse_raw": round(d_rmse, 2),
            "pct_rmse_reduction": round(pct_rmse, 1),
        })

    # Sort exps for ranking bar chart (from best rank to worst)
    exps_sorted = sorted(exps, key=lambda x: (not x["is_control"], x["rank"]))

    # 2. Scatter Points: [RMSE, KGE, ExpID, is_winner, is_control, delta_kge, r, pbias, pct_kge, desc]
    scatter_pts = []
    for e in exps:
        scatter_pts.append([
            e["rmse"],
            e["kge"],
            e["id"],
            e["is_winner"],
            e["is_control"],
            e["delta_kge_raw"],
            e["r"],
            e["pbias"],
            e["pct_kge_gain"],
            e["desc"],
        ])

    # 3. Delta Bar Chart Data
    bar_categories = [e["id"] for e in exps_sorted]
    bar_values = [e["delta_kge_raw"] for e in exps_sorted]
    bar_colors = [
        "#64748b" if e["is_control"] else ("#059669" if e["delta_kge_raw"] >= 0 else "#dc2626")
        for e in exps_sorted
    ]

    # 4. Boxplot Data per Experiment
    boxplot_categories = []
    boxplot_data = []
    boxplot_colors = []
    if df_stations is not None and not df_stations.empty:
        for e in exps_sorted:
            eid = e["id"]
            st_sub = df_stations[df_stations["experiment_id"] == eid]
            if not st_sub.empty and "kge" in st_sub.columns:
                vals = sorted(st_sub["kge"].dropna().tolist())
                if vals:
                    q1 = float(np.percentile(vals, 25))
                    med = float(np.percentile(vals, 50))
                    q3 = float(np.percentile(vals, 75))
                    low = float(min(vals))
                    high = float(max(vals))
                    boxplot_categories.append(eid)
                    boxplot_data.append([low, q1, med, q3, high])
                    if e["is_control"]:
                        boxplot_colors.append("#64748b")
                    elif e["is_winner"]:
                        boxplot_colors.append("#059669")
                    else:
                        boxplot_colors.append("#0284c7" if var_type == "rainfall" else ("#ea580c" if var_type == "tmax" else "#7c3aed"))

    # 5. Radar Chart Data (ALL EXPERIMENTS with Dynamic Legend Filter)
    radar_indicators = [
        {"name": "Eficiencia (KGE)", "max": 1.0, "min": 0.0},
        {"name": "Correlación (r)", "max": 1.0, "min": 0.0},
        {"name": "Control de Sesgo (PBIAS)", "max": 1.0, "min": 0.0},
        {"name": "Precisión (1 - RMSE/max)", "max": 1.0, "min": 0.0},
    ]
    if var_type == "rainfall":
        radar_indicators.extend([
            {"name": "Habilidad Lluvia (ETS)", "max": 1.0, "min": 0.0},
            {"name": "Detección (POD)", "max": 1.0, "min": 0.0},
        ])
    else:
        radar_indicators.append({"name": "Error Absoluto (1 - MAE/max)", "max": 1.0, "min": 0.0})

    max_rmse = max([e["rmse"] for e in exps] + [1.0])
    max_mae = max([e["mae"] for e in exps] + [1.0])
    max_ets = max([e.get("ets") or 0.1 for e in exps] + [0.1])

    radar_series = []
    radar_legend_selected = {}
    other_palette = [
        "#38bdf8", "#818cf8", "#f43f5e", "#fb923c", "#facc15", "#2dd4bf",
        "#a78bfa", "#f472b6", "#34d399", "#60a5fa", "#c084fc", "#4ade80",
        "#fb7185", "#e879f9", "#22d3ee", "#a3e635"
    ]
    other_idx = 0

    for item in exps_sorted:
        kge_n = max(0.0, min(1.0, item["kge"]))
        r_n = max(0.0, min(1.0, item["r"]))
        bias_n = max(0.0, min(1.0, 1.0 - (abs(item["pbias"]) / 30.0)))
        rmse_n = max(0.0, min(1.0, 1.0 - (item["rmse"] / (max_rmse * 1.1))))
        r_vals = [kge_n, r_n, bias_n, rmse_n]
        if var_type == "rainfall":
            ets_n = max(0.0, min(1.0, (item["ets"] or 0.0) / (max_ets * 1.1)))
            pod_n = max(0.0, min(1.0, item["pod"] or 0.0))
            r_vals.extend([ets_n, pod_n])
        else:
            mae_n = max(0.0, min(1.0, 1.0 - (item["mae"] / (max_mae * 1.1))))
            r_vals.append(mae_n)

        is_win = item["is_winner"]
        is_ctrl = item["is_control"]

        if is_win:
            col = "#059669"
            width = 3.5
            area_op = 0.25
        elif is_ctrl:
            col = "#64748b"
            width = 2.5
            area_op = 0.15
        else:
            col = other_palette[other_idx % len(other_palette)]
            other_idx += 1
            width = 1.5
            area_op = 0.04

        series_name = f"{item['id']} {'[ÓPTIMO]' if is_win else ('[CONTROL 0]' if is_ctrl else '')}"
        radar_legend_selected[series_name] = bool(is_win or is_ctrl)

        radar_series.append({
            "name": series_name,
            "value": [round(v, 3) for v in r_vals],
            "itemStyle": {"color": col},
            "lineStyle": {"width": width, "type": "dashed" if is_ctrl else "solid"},
            "areaStyle": {"opacity": area_op},
        })

    # 6. Polar Taylor Diagram Data Payload
    taylor_series = []
    # A. Reference Observation Point at [radius=1.0, angle=0.0 deg]
    taylor_series.append({
        "name": "Referencia Holdout",
        "type": "scatter",
        "coordinateSystem": "polar",
        "symbol": "pin",
        "symbolSize": 26,
        "itemStyle": {
            "color": "#ef4444",
            "borderColor": "#ffffff",
            "borderWidth": 2,
            "shadowBlur": 10,
            "shadowColor": "rgba(239, 68, 68, 0.9)",
        },
        "data": [[1.0, 0.0, "ESTACIONES HOLDOUT (OBSERVACIÓN)", False, False, 1.0, 1.0, 0.0, 0.0, 0.0]],
        "z": 25,
    })

    # B. Reference Unit Variance Arc (sigma* = 1.0)
    arc_angles = np.linspace(0, 90, 45)
    arc_data = [[1.0, round(float(a), 2)] for a in arc_angles]
    taylor_series.append({
        "name": "Varianza Observada (σ* = 1.0)",
        "type": "line",
        "coordinateSystem": "polar",
        "symbol": "none",
        "data": arc_data,
        "lineStyle": {
            "color": "#ef4444",
            "type": "dashed",
            "width": 1.5,
            "opacity": 0.65
        },
        "z": 5,
        "silent": True,
    })

    # C. All Model Points
    t_other_idx = 0
    for e in exps:
        r_val = max(0.0, min(1.0, e["r"]))
        theta_deg = float(np.degrees(np.arccos(r_val)))
        sigma_norm = 1.0 - (e["pbias"] / 100.0) if e.get("pbias") is not None else 1.0
        sigma_norm = max(0.25, min(1.55, float(sigma_norm)))
        crmse = float(np.sqrt(max(0.0, sigma_norm**2 + 1.0 - 2.0 * sigma_norm * r_val)))

        if e["is_winner"]:
            col = "#059669"
            sym = "diamond"
            sym_size = 18
            z_val = 20
            border_col = "#fbbf24"
            border_w = 2.0
        elif e["is_control"]:
            col = "#64748b"
            sym = "rect"
            sym_size = 14
            z_val = 18
            border_col = "#0f172a"
            border_w = 1.8
        else:
            col = other_palette[t_other_idx % len(other_palette)]
            t_other_idx += 1
            sym = "circle"
            sym_size = 10
            z_val = 12
            border_col = "#ffffff"
            border_w = 0.8

        taylor_series.append({
            "name": f"{e['id']} {'[ÓPTIMO]' if e['is_winner'] else ('[CONTROL 0]' if e['is_control'] else '')}",
            "type": "scatter",
            "coordinateSystem": "polar",
            "symbol": sym,
            "symbolSize": sym_size,
            "itemStyle": {
                "color": col,
                "borderColor": border_col,
                "borderWidth": border_w,
            },
            "data": [[round(sigma_norm, 3), round(theta_deg, 2), e["id"], e["is_winner"], e["is_control"], e["r"], e["kge"], e["rmse"], e["pbias"], round(crmse, 3)]],
            "z": z_val,
        })

    return {
        "experiments": exps,
        "scatter_points": scatter_pts,
        "bar_categories": bar_categories,
        "bar_values": bar_values,
        "bar_colors": bar_colors,
        "boxplot_categories": boxplot_categories,
        "boxplot_data": boxplot_data,
        "boxplot_colors": boxplot_colors,
        "radar_indicators": radar_indicators,
        "radar_series": radar_series,
        "radar_selected": radar_legend_selected,
        "taylor_series": taylor_series,
        "raw_kge": raw_kge,
        "raw_rmse": raw_rmse,
    }


def generate_echarts_html_dashboard(
    df_ranked: pd.DataFrame,
    figures_map: Dict[str, Dict[str, str]],
    comparison_figures: Dict[str, str],
    output_html_path: Path | str,
    df_stations: Optional[pd.DataFrame] = None,
) -> None:
    """Generates the modern Apache ECharts interactive dashboard."""
    from jinja2 import Template

    out_p = Path(output_html_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Compute payloads for each variable
    payloads_rain = compute_echarts_payloads(df_ranked, df_stations, "rainfall")
    payloads_tmax = compute_echarts_payloads(df_ranked, df_stations, "tmax")
    payloads_tmin = compute_echarts_payloads(df_ranked, df_stations, "tmin")

    # Winner dicts
    def get_win(var_name: str):
        sub = df_ranked[df_ranked["variable"] == var_name]
        if not sub.empty:
            return sub[sub["is_winner"] == True].iloc[0].to_dict()
        return None

    win_rain = get_win("rainfall")
    win_tmax = get_win("tmax")
    win_tmin = get_win("tmin")

    html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDT 8.0 Central America Benchmark & Validation Dashboard</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Apache ECharts 5 -->
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
    <!-- KaTeX for Scientific Formula Rendering -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
    <!-- DataTables -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #0f172a; color: #f8fafc; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        .tab-btn.active {
            border-bottom: 3px solid #38bdf8;
            color: #ffffff;
            font-weight: 700;
        }
        .plot-card {
            background-color: #1e293b;
            border-radius: 0.75rem;
            border: 1px solid #334155;
            padding: 1.25rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
        }
        .chart-box {
            width: 100%;
            height: 380px;
        }
        .chart-box-large {
            width: 100%;
            height: 420px;
        }
        /* Custom styling for DataTables in Dark Theme */
        .dataTables_wrapper { color: #cbd5e1; font-size: 11px; }
        .dataTables_length, .dataTables_filter, .dataTables_info, .dataTables_paginate { color: #94a3b8 !important; }
        .dataTables_filter input {
            background-color: #0f172a;
            border: 1px solid #475569;
            color: #f8fafc;
            border-radius: 6px;
            padding: 4px 10px;
            outline: none;
        }
        .dataTables_length select {
            background-color: #0f172a;
            border: 1px solid #475569;
            color: #f8fafc;
            border-radius: 6px;
            padding: 4px;
        }
        table.dataTable tbody tr { background-color: transparent !important; border-bottom: 1px solid #334155; }
        table.dataTable tbody tr:hover { background-color: rgba(51, 65, 85, 0.5) !important; }
        table.dataTable thead th {
            border-bottom: 1px solid #475569 !important;
            color: #38bdf8 !important;
            font-size: 11px;
            font-weight: 600;
            background-color: #0f172a;
        }
        .paginate_button { color: #94a3b8 !important; }
        .paginate_button.current { background: #38bdf8 !important; color: #0f172a !important; border-radius: 4px; border: none !important; }
    </style>
</head>
<body class="min-h-screen flex flex-col">

    <!-- Top Header -->
    <header class="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-md">
        <div class="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div class="flex items-center space-x-3">
                <span class="text-3xl">🌍</span>
                <div>
                    <h1 class="text-xl font-bold tracking-tight text-white flex items-center gap-2">
                        CDT 8.0 Central America Benchmark Dashboard
                        <span class="bg-sky-500/20 text-sky-400 text-xs px-2 py-0.5 rounded border border-sky-500/30 font-mono">v8.0-ECharts</span>
                    </h1>
                    <p class="text-xs text-slate-400">Plataforma Científica de Validación Cruzada Holdout &amp; Reconstrucción de Malla (1991–2020)</p>
                </div>
            </div>
            <div class="text-xs text-slate-400 text-right">
                <div>Fecha: <span class="font-mono text-slate-200">{{ timestamp }}</span></div>
                <div>Validación Independiente Holdout: <span class="text-sky-400 font-semibold">29 Estaciones</span> (10,958 días)</div>
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
                <span>📊 Resumen Consolidado (42 Exp.)</span>
            </button>
            <button onclick="switchTab('glossary')" id="tab-btn-glossary" class="tab-btn py-3 px-2 text-slate-300 hover:text-white flex items-center space-x-2 whitespace-nowrap">
                <span>📐 Definición e Interpretación de Estadísticos</span>
            </button>
        </div>
    </header>

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-8 flex-1">

        <!-- ========================================================================= -->
        <!-- TAB 1: PRECIPITACIÓN -->
        <!-- ========================================================================= -->
        <div id="tab-content-rainfall" class="tab-panel space-y-8">
            
            {% if win_rain %}
            <!-- Winner Highlight Card -->
            <div class="bg-gradient-to-r from-sky-950 via-slate-900 to-slate-900 border border-sky-800 text-white rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div class="absolute -right-10 -bottom-10 opacity-10 text-9xl">🌧️</div>
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-sky-500 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo</span>
                            <span class="text-xs text-sky-300 font-mono">Rango #01 en Precipitación</span>
                        </div>
                        <h2 class="text-2xl font-black text-white tracking-tight">{{ win_rain.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">{{ win_rain.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-900/90 rounded-lg p-3 border border-slate-700 text-center">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-sky-400">{{ "%.3f"|format(win_rain.global_skill_score) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">KGE</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_rain.kge) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">Pearson r</div>
                            <div class="text-base font-bold text-slate-200">{{ "%.3f"|format(win_rain.r) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">RMSE</div>
                            <div class="text-base font-bold text-emerald-400">{{ "%.2f"|format(win_rain.rmse) }} <span class="text-[9px]">mm</span></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- 1. DATA FIRST: Interactive Master DataTable -->
            <div class="plot-card">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                    <div>
                        <h3 class="font-bold text-sm text-white flex items-center gap-2">
                            <span>📋 Tabla Maestra de Rendimiento y Ranking: Precipitación</span>
                            <span class="bg-sky-950 text-sky-400 border border-sky-800 text-[10px] font-mono px-2 py-0.5 rounded">16 Modelos</span>
                        </h3>
                        <p class="text-[11px] text-slate-400">Resultados numéricos exactos de validación independiente en 29 estaciones holdout. Ordene o filtre por cualquier métrica.</p>
                    </div>
                    <span class="text-[11px] text-slate-400">Datos Primero • Holdout Ciego</span>
                </div>
                <div class="overflow-x-auto">
                    <table id="tableRain" class="w-full text-xs display">
                        <thead>
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>GSS</th>
                                <th>KGE Medio</th>
                                <th>KGE Mediana</th>
                                <th>Pearson r</th>
                                <th>RMSE (mm)</th>
                                <th>PBIAS (%)</th>
                                <th>POD</th>
                                <th>FAR</th>
                                <th>ETS</th>
                                <th>Δ KGE vs Crudo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in pay_rain.experiments %}
                            <tr class="{% if e.is_winner %}bg-emerald-950/40 text-emerald-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono">{{ e.id }}</td>
                                <td>{{ "%.3f"|format(e.gss) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.kge_median) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td>{{ "%.3f"|format(e.pod) if e.pod is not none else "-" }}</td>
                                <td>{{ "%.3f"|format(e.far) if e.far is not none else "-" }}</td>
                                <td>{{ "%.3f"|format(e.ets) if e.ets is not none else "-" }}</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-400{% elif e.delta_kge_raw < 0 %}text-rose-400{% else %}text-slate-400{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }} ({{ "%+.1f"|format(e.pct_kge_gain) }}%)
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 2. EXPLORACIÓN GRÁFICA INTERACTIVA -->
            <div class="space-y-4">
                <div class="border-b border-slate-800 pb-2 flex justify-between items-center">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📈 Exploración Gráfica Interactiva</span>
                        <span class="text-xs font-normal text-slate-400">(Herramientas dinámicas de zoom, selección y descarga)</span>
                    </h3>
                    <span class="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded border border-slate-700">Apache ECharts 5</span>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Chart 1: Polar Taylor Diagram -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Diagrama Polar de Taylor: Precipitación</h3>
                                <p class="text-[11px] text-slate-400">Coordenadas: Ángulo = arccos(r), Radio = σ*. Referencia Holdout en (1.0, 0°).</p>
                            </div>
                            <span class="text-xs bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">Taylor Polar</span>
                        </div>
                        <div id="taylorRain" class="chart-box"></div>
                    </div>

                    <!-- Chart 2: Multi-criteria Radar (ALL EXPERIMENTS) -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad Climatológica</h3>
                                <p class="text-[11px] text-slate-400">Haga clic en la leyenda superior para activar/desactivar cualquier experimento.</p>
                            </div>
                            <span class="text-xs bg-sky-950 text-sky-300 border border-sky-800 px-2 py-0.5 rounded">16 Modelos</span>
                        </div>
                        <div id="radarRain" class="chart-box"></div>
                    </div>

                    <!-- Chart 3: Scatter RMSE vs KGE -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Espacio de Precisión: Error (RMSE) vs. Eficiencia (KGE)</h3>
                                <p class="text-[11px] text-slate-400">El modelo óptimo se ubica en el extremo superior izquierdo (menor RMSE, mayor KGE)</p>
                            </div>
                            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Pareto</span>
                        </div>
                        <div id="scatterRain" class="chart-box"></div>
                    </div>

                    <!-- Chart 4: Net Gain vs Raw Satellite (Control 00) -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Ganancia Neta (Δ KGE) respecto al Satélite Crudo [Control 00]</h3>
                                <p class="text-[11px] text-slate-400">CHIRPS Crudo = 0.0 de referencia. Barra verde indica mejora; gris es el control.</p>
                            </div>
                            <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded">Δ KGE</span>
                        </div>
                        <div id="barDeltaRain" class="chart-box"></div>
                    </div>

                    <!-- Chart 5: Boxplot of KGE by Station (Full Width) -->
                    <div class="plot-card lg:col-span-2">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Distribución de Eficiencia KGE en las 29 Estaciones Holdout</h3>
                                <p class="text-[11px] text-slate-400">Caja representa percentiles 25–75 y línea central la mediana. Use el control inferior para desplazarse.</p>
                            </div>
                            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Zoomable</span>
                        </div>
                        <div id="boxRain" class="chart-box"></div>
                    </div>
                </div>
            </div>

            <!-- 3. DIAGNÓSTICO COMPARATIVO Y CENTRO DE DESCARGAS (300 DPI) -->
            <div class="space-y-4">
                <div class="border-b border-slate-800 pb-2">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📥 Centro de Descargas y Diagnóstico Comparativo (300 DPI)</span>
                        <span class="text-xs font-normal text-slate-400">(Figuras estáticas de alta resolución listas para publicación)</span>
                    </h3>
                </div>

                <!-- High-Resolution Comparison Figure Card: Winner vs Raw -->
                <div class="plot-card border-sky-800 bg-slate-900">
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="bg-sky-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Diagnóstico Comparativo</span>
                                <h3 class="font-bold text-base text-white">Modelo Ganador (EXP_R15) vs. CHIRPS v2.0 Crudo (EXP_R00)</h3>
                            </div>
                            <p class="text-xs text-slate-300 mt-1">Evaluación estación por estación: ganancia de KGE, correlación dual y habilidad categórica de lluvia.</p>
                        </div>
                        <a href="{{ comp_rain }}" download target="_blank" class="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                            <span>⬇️ Descargar Comparativa 4 Paneles (300 DPI)</span>
                        </a>
                    </div>
                    <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                        <img src="{{ comp_rain }}" alt="Comparativa Lluvia Ganador vs Crudo" class="rounded max-h-[500px] object-contain shadow-md">
                    </div>
                </div>

                <!-- Static Figure Download Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-sky-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Diagrama Polar de Taylor Estático</h4>
                            <p class="text-xs text-slate-400 mt-1">Diagrama polar con isolíneas de error centrado RMS, varianza normalizada y correlación Pearson.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_rain.taylor }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-sky-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Distribución de KGE por Estación</h4>
                            <p class="text-xs text-slate-400 mt-1">Boxplots de dispersión en las 29 estaciones holdout independientes para todos los modelos.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_rain.boxplots }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-sky-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Desempeño por Estratos de Elevación</h4>
                            <p class="text-xs text-slate-400 mt-1">Evaluación estratificada (Costas &lt;200m, Valles 200–800m, Montañas &gt;800m).</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_rain.elevation }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-sky-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad</h4>
                            <p class="text-xs text-slate-400 mt-1">Comparación vectorial de 6 métricas climatológicas simultáneas.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_rain.radar }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-sky-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Matriz de Rendimiento (Heatmap)</h4>
                            <p class="text-xs text-slate-400 mt-1">Mapa de calor tabular normalizado que condensa todas las dimensiones estadísticas.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_rain.heatmap }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-sky-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Detección de Lluvia (POD vs. FAR)</h4>
                            <p class="text-xs text-slate-400 mt-1">Evaluación de contingencia en el espacio de aciertos vs falsa alarma con umbrales de lluvia.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_rain.roc }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-sky-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 2: TEMPERATURA MÁXIMA (TMAX) -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmax" class="tab-panel hidden space-y-8">
            
            {% if win_tmax %}
            <!-- Winner Highlight Card -->
            <div class="bg-gradient-to-r from-amber-950 via-slate-900 to-slate-900 border border-amber-800 text-white rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div class="absolute -right-10 -bottom-10 opacity-10 text-9xl">☀️</div>
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-amber-500 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo</span>
                            <span class="text-xs text-amber-300 font-mono">Rango #01 en Temp. Máxima</span>
                        </div>
                        <h2 class="text-2xl font-black text-white tracking-tight">{{ win_tmax.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">{{ win_tmax.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-900/90 rounded-lg p-3 border border-slate-700 text-center">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-amber-400">{{ "%.3f"|format(win_tmax.global_skill_score) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">KGE</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_tmax.kge) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">Pearson r</div>
                            <div class="text-base font-bold text-slate-200">{{ "%.3f"|format(win_tmax.r) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">RMSE</div>
                            <div class="text-base font-bold text-emerald-400">{{ "%.2f"|format(win_tmax.rmse) }} <span class="text-[9px]">°C</span></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- 1. DATA FIRST: Interactive Master DataTable -->
            <div class="plot-card">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                    <div>
                        <h3 class="font-bold text-sm text-white flex items-center gap-2">
                            <span>📋 Tabla Maestra de Rendimiento y Ranking: Temperatura Máxima</span>
                            <span class="bg-amber-950 text-amber-400 border border-amber-800 text-[10px] font-mono px-2 py-0.5 rounded">13 Modelos</span>
                        </h3>
                        <p class="text-[11px] text-slate-400">Resultados numéricos exactos de validación independiente en 29 estaciones holdout. Ordene o filtre por cualquier métrica.</p>
                    </div>
                    <span class="text-[11px] text-slate-400">Datos Primero • Holdout Ciego</span>
                </div>
                <div class="overflow-x-auto">
                    <table id="tableTmax" class="w-full text-xs display">
                        <thead>
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>GSS</th>
                                <th>KGE Medio</th>
                                <th>KGE Mediana</th>
                                <th>Pearson r</th>
                                <th>RMSE (°C)</th>
                                <th>MAE (°C)</th>
                                <th>PBIAS (%)</th>
                                <th>Δ KGE vs Crudo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in pay_tmax.experiments %}
                            <tr class="{% if e.is_winner %}bg-emerald-950/40 text-emerald-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono">{{ e.id }}</td>
                                <td>{{ "%.3f"|format(e.gss) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.kge_median) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-400{% elif e.delta_kge_raw < 0 %}text-rose-400{% else %}text-slate-400{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }} ({{ "%+.1f"|format(e.pct_kge_gain) }}%)
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 2. EXPLORACIÓN GRÁFICA INTERACTIVA -->
            <div class="space-y-4">
                <div class="border-b border-slate-800 pb-2 flex justify-between items-center">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📈 Exploración Gráfica Interactiva</span>
                        <span class="text-xs font-normal text-slate-400">(Herramientas dinámicas de zoom, selección y descarga)</span>
                    </h3>
                    <span class="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded border border-slate-700">Apache ECharts 5</span>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Chart 1: Polar Taylor Diagram -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Diagrama Polar de Taylor: Temperatura Máxima</h3>
                                <p class="text-[11px] text-slate-400">Coordenadas: Ángulo = arccos(r), Radio = σ*. Referencia Holdout en (1.0, 0°).</p>
                            </div>
                            <span class="text-xs bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">Taylor Polar</span>
                        </div>
                        <div id="taylorTmax" class="chart-box"></div>
                    </div>

                    <!-- Chart 2: Multi-criteria Radar (ALL EXPERIMENTS) -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad Climatológica</h3>
                                <p class="text-[11px] text-slate-400">Haga clic en la leyenda superior para activar/desactivar cualquier experimento.</p>
                            </div>
                            <span class="text-xs bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded">13 Modelos</span>
                        </div>
                        <div id="radarTmax" class="chart-box"></div>
                    </div>

                    <!-- Chart 3: Scatter RMSE vs KGE -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Espacio de Precisión: Error (RMSE) vs. Eficiencia (KGE)</h3>
                                <p class="text-[11px] text-slate-400">El modelo óptimo se ubica en el extremo superior izquierdo (menor RMSE, mayor KGE)</p>
                            </div>
                            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Pareto</span>
                        </div>
                        <div id="scatterTmax" class="chart-box"></div>
                    </div>

                    <!-- Chart 4: Net Gain vs Raw Satellite (Control 00) -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Ganancia Neta (Δ KGE) respecto al Satélite Crudo [Control 00]</h3>
                                <p class="text-[11px] text-slate-400">CHIRTS Crudo = 0.0 de referencia. Barra verde indica mejora; gris es el control.</p>
                            </div>
                            <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded">Δ KGE</span>
                        </div>
                        <div id="barDeltaTmax" class="chart-box"></div>
                    </div>

                    <!-- Chart 5: Boxplot of KGE by Station (Full Width) -->
                    <div class="plot-card lg:col-span-2">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Distribución de Eficiencia KGE en las 29 Estaciones Holdout</h3>
                                <p class="text-[11px] text-slate-400">Caja representa percentiles 25–75 y línea central la mediana. Use el control inferior para desplazarse.</p>
                            </div>
                            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Zoomable</span>
                        </div>
                        <div id="boxTmax" class="chart-box"></div>
                    </div>
                </div>
            </div>

            <!-- 3. DIAGNÓSTICO COMPARATIVO Y CENTRO DE DESCARGAS (300 DPI) -->
            <div class="space-y-4">
                <div class="border-b border-slate-800 pb-2">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📥 Centro de Descargas y Diagnóstico Comparativo (300 DPI)</span>
                        <span class="text-xs font-normal text-slate-400">(Figuras estáticas de alta resolución listas para publicación)</span>
                    </h3>
                </div>

                <!-- High-Resolution Comparison Figure Card: Winner vs Raw -->
                <div class="plot-card border-amber-800 bg-slate-900">
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="bg-amber-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Diagnóstico Comparativo</span>
                                <h3 class="font-bold text-base text-white">Modelo Ganador (EXP_TX11) vs. CHIRTS-ERA5 Crudo (EXP_TX00)</h3>
                            </div>
                            <p class="text-xs text-slate-300 mt-1">Evaluación estación por estación: ganancia de KGE, correlación dual y precisión térmica.</p>
                        </div>
                        <a href="{{ comp_tmax }}" download target="_blank" class="inline-flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                            <span>⬇️ Descargar Comparativa 4 Paneles (300 DPI)</span>
                        </a>
                    </div>
                    <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                        <img src="{{ comp_tmax }}" alt="Comparativa Tmax Ganador vs Crudo" class="rounded max-h-[500px] object-contain shadow-md">
                    </div>
                </div>

                <!-- Static Figure Download Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Diagrama Polar de Taylor Estático</h4>
                            <p class="text-xs text-slate-400 mt-1">Diagrama polar con isolíneas de error centrado RMS, varianza normalizada y correlación Pearson.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmax.taylor }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-amber-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Distribución de KGE por Estación</h4>
                            <p class="text-xs text-slate-400 mt-1">Boxplots de dispersión en las 29 estaciones holdout independientes para todos los modelos.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmax.boxplots }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-amber-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Desempeño por Estratos de Elevación</h4>
                            <p class="text-xs text-slate-400 mt-1">Evaluación estratificada (Costas &lt;200m, Valles 200–800m, Montañas &gt;800m).</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmax.elevation }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-amber-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad</h4>
                            <p class="text-xs text-slate-400 mt-1">Comparación vectorial de métricas climatológicas simultáneas.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmax.radar }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-amber-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-amber-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Matriz de Rendimiento (Heatmap)</h4>
                            <p class="text-xs text-slate-400 mt-1">Mapa de calor tabular normalizado que condensa todas las dimensiones estadísticas.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmax.heatmap }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-amber-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 3: TEMPERATURA MÍNIMA (TMIN) -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmin" class="tab-panel hidden space-y-8">
            
            {% if win_tmin %}
            <!-- Winner Highlight Card -->
            <div class="bg-gradient-to-r from-violet-950 via-slate-900 to-slate-900 border border-violet-800 text-white rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div class="absolute -right-10 -bottom-10 opacity-10 text-9xl">🌙</div>
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-violet-500 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo</span>
                            <span class="text-xs text-violet-300 font-mono">Rango #01 en Temp. Mínima</span>
                        </div>
                        <h2 class="text-2xl font-black text-white tracking-tight">{{ win_tmin.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">{{ win_tmin.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-900/90 rounded-lg p-3 border border-slate-700 text-center">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-violet-400">{{ "%.3f"|format(win_tmin.global_skill_score) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">KGE</div>
                            <div class="text-base font-bold text-white">{{ "%.3f"|format(win_tmin.kge) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">Pearson r</div>
                            <div class="text-base font-bold text-slate-200">{{ "%.3f"|format(win_tmin.r) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">RMSE</div>
                            <div class="text-base font-bold text-emerald-400">{{ "%.2f"|format(win_tmin.rmse) }} <span class="text-[9px]">°C</span></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- 1. DATA FIRST: Interactive Master DataTable -->
            <div class="plot-card">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                    <div>
                        <h3 class="font-bold text-sm text-white flex items-center gap-2">
                            <span>📋 Tabla Maestra de Rendimiento y Ranking: Temperatura Mínima</span>
                            <span class="bg-violet-950 text-violet-400 border border-violet-800 text-[10px] font-mono px-2 py-0.5 rounded">13 Modelos</span>
                        </h3>
                        <p class="text-[11px] text-slate-400">Resultados numéricos exactos de validación independiente en 29 estaciones holdout. Ordene o filtre por cualquier métrica.</p>
                    </div>
                    <span class="text-[11px] text-slate-400">Datos Primero • Holdout Ciego</span>
                </div>
                <div class="overflow-x-auto">
                    <table id="tableTmin" class="w-full text-xs display">
                        <thead>
                            <tr>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>GSS</th>
                                <th>KGE Medio</th>
                                <th>KGE Mediana</th>
                                <th>Pearson r</th>
                                <th>RMSE (°C)</th>
                                <th>MAE (°C)</th>
                                <th>PBIAS (%)</th>
                                <th>Δ KGE vs Crudo</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in pay_tmin.experiments %}
                            <tr class="{% if e.is_winner %}bg-emerald-950/40 text-emerald-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono">{{ e.id }}</td>
                                <td>{{ "%.3f"|format(e.gss) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.kge_median) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-400{% elif e.delta_kge_raw < 0 %}text-rose-400{% else %}text-slate-400{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }} ({{ "%+.1f"|format(e.pct_kge_gain) }}%)
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 2. EXPLORACIÓN GRÁFICA INTERACTIVA -->
            <div class="space-y-4">
                <div class="border-b border-slate-800 pb-2 flex justify-between items-center">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📈 Exploración Gráfica Interactiva</span>
                        <span class="text-xs font-normal text-slate-400">(Herramientas dinámicas de zoom, selección y descarga)</span>
                    </h3>
                    <span class="text-xs bg-slate-800 text-slate-300 px-2.5 py-1 rounded border border-slate-700">Apache ECharts 5</span>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Chart 1: Polar Taylor Diagram -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Diagrama Polar de Taylor: Temperatura Mínima</h3>
                                <p class="text-[11px] text-slate-400">Coordenadas: Ángulo = arccos(r), Radio = σ*. Referencia Holdout en (1.0, 0°).</p>
                            </div>
                            <span class="text-xs bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">Taylor Polar</span>
                        </div>
                        <div id="taylorTmin" class="chart-box"></div>
                    </div>

                    <!-- Chart 2: Multi-criteria Radar (ALL EXPERIMENTS) -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad Climatológica</h3>
                                <p class="text-[11px] text-slate-400">Haga clic en la leyenda superior para activar/desactivar cualquier experimento.</p>
                            </div>
                            <span class="text-xs bg-violet-950 text-violet-300 border border-violet-800 px-2 py-0.5 rounded">13 Modelos</span>
                        </div>
                        <div id="radarTmin" class="chart-box"></div>
                    </div>

                    <!-- Chart 3: Scatter RMSE vs KGE -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Espacio de Precisión: Error (RMSE) vs. Eficiencia (KGE)</h3>
                                <p class="text-[11px] text-slate-400">El modelo óptimo se ubica en el extremo superior izquierdo (menor RMSE, mayor KGE)</p>
                            </div>
                            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Pareto</span>
                        </div>
                        <div id="scatterTmin" class="chart-box"></div>
                    </div>

                    <!-- Chart 4: Net Gain vs Raw Satellite (Control 00) -->
                    <div class="plot-card">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Ganancia Neta (Δ KGE) respecto al Satélite Crudo [Control 00]</h3>
                                <p class="text-[11px] text-slate-400">CHIRTS Crudo = 0.0 de referencia. Barra verde indica mejora; gris es el control.</p>
                            </div>
                            <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded">Δ KGE</span>
                        </div>
                        <div id="barDeltaTmin" class="chart-box"></div>
                    </div>

                    <!-- Chart 5: Boxplot of KGE by Station (Full Width) -->
                    <div class="plot-card lg:col-span-2">
                        <div class="flex justify-between items-center mb-2">
                            <div>
                                <h3 class="font-bold text-sm text-white">Distribución de Eficiencia KGE en las 29 Estaciones Holdout</h3>
                                <p class="text-[11px] text-slate-400">Caja representa percentiles 25–75 y línea central la mediana. Use el control inferior para desplazarse.</p>
                            </div>
                            <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Zoomable</span>
                        </div>
                        <div id="boxTmin" class="chart-box"></div>
                    </div>
                </div>
            </div>

            <!-- 3. DIAGNÓSTICO COMPARATIVO Y CENTRO DE DESCARGAS (300 DPI) -->
            <div class="space-y-4">
                <div class="border-b border-slate-800 pb-2">
                    <h3 class="text-base font-bold text-white flex items-center gap-2">
                        <span>📥 Centro de Descargas y Diagnóstico Comparativo (300 DPI)</span>
                        <span class="text-xs font-normal text-slate-400">(Figuras estáticas de alta resolución listas para publicación)</span>
                    </h3>
                </div>

                <!-- High-Resolution Comparison Figure Card: Winner vs Raw -->
                <div class="plot-card border-violet-800 bg-slate-900">
                    <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                        <div>
                            <div class="flex items-center gap-2">
                                <span class="bg-violet-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Diagnóstico Comparativo</span>
                                <h3 class="font-bold text-base text-white">Modelo Ganador (EXP_TN10) vs. CHIRTS-ERA5 Crudo (EXP_TN00)</h3>
                            </div>
                            <p class="text-xs text-slate-300 mt-1">Evaluación estación por estación: ganancia de KGE, correlación dual y precisión térmica nocturna.</p>
                        </div>
                        <a href="{{ comp_tmin }}" download target="_blank" class="inline-flex items-center gap-2 bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                            <span>⬇️ Descargar Comparativa 4 Paneles (300 DPI)</span>
                        </a>
                    </div>
                    <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                        <img src="{{ comp_tmin }}" alt="Comparativa Tmin Ganador vs Crudo" class="rounded max-h-[500px] object-contain shadow-md">
                    </div>
                </div>

                <!-- Static Figure Download Grid -->
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-violet-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Diagrama Polar de Taylor Estático</h4>
                            <p class="text-xs text-slate-400 mt-1">Diagrama polar con isolíneas de error centrado RMS, varianza normalizada y correlación Pearson.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmin.taylor }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-violet-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Distribución de KGE por Estación</h4>
                            <p class="text-xs text-slate-400 mt-1">Boxplots de dispersión en las 29 estaciones holdout independientes para todos los modelos.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmin.boxplots }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-violet-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Desempeño por Estratos de Elevación</h4>
                            <p class="text-xs text-slate-400 mt-1">Evaluación estratificada (Costas &lt;200m, Valles 200–800m, Montañas &gt;800m).</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmin.elevation }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-violet-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad</h4>
                            <p class="text-xs text-slate-400 mt-1">Comparación vectorial de métricas climatológicas simultáneas.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmin.radar }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>

                    <div class="bg-slate-800/80 border border-slate-700 rounded-lg p-4 flex flex-col justify-between">
                        <div>
                            <div class="text-[11px] font-bold text-violet-400 uppercase tracking-wider mb-1">Figura de Publicación</div>
                            <h4 class="font-bold text-sm text-white">Matriz de Rendimiento (Heatmap)</h4>
                            <p class="text-xs text-slate-400 mt-1">Mapa de calor tabular normalizado que condensa todas las dimensiones estadísticas.</p>
                        </div>
                        <div class="mt-4 pt-3 border-t border-slate-700/60 flex items-center justify-between">
                            <span class="text-[10px] text-slate-400 font-mono">PNG • 300 DPI</span>
                            <a href="{{ fig_tmin.heatmap }}" download target="_blank" class="text-xs bg-slate-700 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition font-medium flex items-center gap-1">
                                <span>📥 Descargar</span>
                            </a>
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 4: RESUMEN CONSOLIDADO (42 EXPERIMENTOS) -->
        <!-- ========================================================================= -->
        <div id="tab-content-consolidated" class="tab-panel hidden space-y-8">
            
            <!-- Executive Cross-Variable Synthesis Figure -->
            <div class="plot-card border-slate-700 bg-slate-900">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="bg-emerald-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Síntesis Ejecutiva</span>
                            <h3 class="font-bold text-base text-white">Evaluación Global: Malla Original Cruda vs. Malla Óptima Corregida</h3>
                        </div>
                        <p class="text-xs text-slate-300 mt-1">Comparación multi-variable de KGE, correlación Pearson y habilidad global en las 29 estaciones holdout de Centroamérica.</p>
                    </div>
                    <a href="{{ comp_overview }}" download target="_blank" class="inline-flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                        <span>⬇️ Descargar Síntesis Ejecutiva (300 DPI)</span>
                    </a>
                </div>
                <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                    <img src="{{ comp_overview }}" alt="Síntesis Ejecutiva de Desempeño" class="rounded max-h-[500px] object-contain shadow-md">
                </div>
            </div>

            <!-- Master Consolidated Table -->
            <div class="plot-card">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-3">
                    <div>
                        <h3 class="font-bold text-sm text-white">Tabla Maestra de los 42 Experimentos Evaluados</h3>
                        <p class="text-[11px] text-slate-400">Catálogo completo de la suite regional de Centroamérica: Precipitación, Temperatura Máxima y Mínima.</p>
                    </div>
                    <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700 font-mono">42 Experimentos</span>
                </div>
                <div class="overflow-x-auto">
                    <table id="tableAll" class="w-full text-xs display">
                        <thead>
                            <tr>
                                <th>Variable</th>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>Estado</th>
                                <th>GSS</th>
                                <th>KGE</th>
                                <th>Pearson r</th>
                                <th>RMSE</th>
                                <th>MAE</th>
                                <th>PBIAS (%)</th>
                                <th>ETS</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in all_exps %}
                            <tr class="{% if e.is_winner %}bg-emerald-950/40 text-emerald-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
                                <td class="font-semibold uppercase text-sky-400">{{ e.variable }}</td>
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono">{{ e.experiment_id }}</td>
                                <td>
                                    {% if e.is_winner %}
                                    <span class="bg-emerald-500/20 text-emerald-400 text-[10px] px-1.5 py-0.5 rounded border border-emerald-500/30 font-bold">ÓPTIMO</span>
                                    {% elif e.is_control %}
                                    <span class="bg-slate-700 text-slate-300 text-[10px] px-1.5 py-0.5 rounded font-bold">CONTROL 0</span>
                                    {% else %}
                                    <span class="text-slate-400 text-[10px]">Candidato</span>
                                    {% endif %}
                                </td>
                                <td>{{ "%.3f"|format(e.global_skill_score) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td>{{ "%.3f"|format(e.ets) if e.ets is defined and e.ets is not none and e.ets == e.ets else "-" }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 5: DEFINICIÓN E INTERPRETACIÓN DE ESTADÍSTICOS -->
        <!-- ========================================================================= -->
        <div id="tab-content-glossary" class="tab-panel hidden space-y-8">
            
            <!-- Callout linking to full documentation -->
            <div class="bg-gradient-to-r from-sky-950 via-slate-900 to-slate-900 border border-sky-700 text-white rounded-xl p-6 shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <span class="bg-sky-500 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Documentación Oficial</span>
                    <h3 class="text-xl font-bold text-white mt-1">Guía Metodológica Completa de Evaluación y Validación</h3>
                    <p class="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">
                        Consulte el documento técnico oficial para un desglose exhaustivo de las formulaciones matemáticas en KaTeX,
                        la partición espacial de 29 estaciones holdout y los criterios físicos para Centroamérica.
                    </p>
                </div>
                <a href="docs/12_metodologia_evaluacion_metricas_y_validacion.md" target="_blank" class="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition shadow">
                    <span>📖 Ver Documento 12 en Markdown</span>
                </a>
            </div>

            <!-- Metric Cards Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                <!-- 1. KGE -->
                <div class="plot-card border-sky-800">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-white">Eficiencia de Kling-Gupta (KGE)</h4>
                        <span class="text-[10px] bg-sky-950 text-sky-400 border border-sky-800 px-2 py-0.5 rounded">Métrica Principal</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 my-2 text-xs font-mono text-center text-sky-300">
                        $$KGE = 1 - \sqrt{(r - 1)^2 + (\beta - 1)^2 + (\gamma - 1)^2}$$
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Descompone el error en tres componentes ortogonales: correlación lineal (\(r\)), sesgo medio (\(\beta = \mu_s / \mu_o\)) y dispersión relativa (\(\gamma = \text{CV}_s / \text{CV}_o\)).
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-700/60 text-[11px] space-y-1">
                        <div>• <b>Rango Óptimo:</b> 1.0 (KGE &gt; 0.3 indica habilidad superior al promedio climatológico).</div>
                        <div>• <b>Interpretación en CA:</b> Penaliza adecuadamente el desplazamiento temporal de frentes fríos y la sobreestimación orográfica.</div>
                    </div>
                </div>

                <!-- 2. Pearson r -->
                <div class="plot-card border-slate-700">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-white">Coeficiente de Correlación (r)</h4>
                        <span class="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded">Dinámica Temporal</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 my-2 text-xs font-mono text-center text-slate-300">
                        $$r = \frac{\sum (S_i - \bar{S})(O_i - \bar{O})}{\sqrt{\sum (S_i - \bar{S})^2 \sum (O_i - \bar{O})^2}}$$
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Mide la covariación temporal y concordancia de fase entre las observaciones diarias de estaciones y las estimaciones grilladas.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-700/60 text-[11px] space-y-1">
                        <div>• <b>Rango Óptimo:</b> 1.0 (\(r &gt; 0.40\) en lluvia diaria; \(r &gt; 0.85\) en temperatura).</div>
                        <div>• <b>Interpretación en CA:</b> Refleja la capacidad de capturar la marcha del ciclo anual y las ondas tropicales del este.</div>
                    </div>
                </div>

                <!-- 3. RMSE -->
                <div class="plot-card border-slate-700">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-white">Raíz del Error Cuadrático Medio (RMSE)</h4>
                        <span class="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded">Magnitud de Error</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 my-2 text-xs font-mono text-center text-slate-300">
                        $$RMSE = \sqrt{\frac{1}{N} \sum_{i=1}^N (S_i - O_i)^2}$$
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Pondera fuertemente los errores de gran magnitud. Expresado en las unidades físicas de la variable (mm o °C).
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-700/60 text-[11px] space-y-1">
                        <div>• <b>Rango Óptimo:</b> 0.0 (Menor es mejor).</div>
                        <div>• <b>Interpretación en CA:</b> Muy sensible al efecto de doble penalización en tormentas convectivas tropicales localizadas.</div>
                    </div>
                </div>

                <!-- 4. PBIAS -->
                <div class="plot-card border-slate-700">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-white">Sesgo Porcentual Relativo (PBIAS)</h4>
                        <span class="text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-2 py-0.5 rounded">Balance de Masa</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 my-2 text-xs font-mono text-center text-slate-300">
                        $$PBIAS = 100 \times \frac{\sum_{i=1}^N (S_i - O_i)}{\sum_{i=1}^N O_i}$$
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Indica la tendencia sistemática de la malla a sobreestimar (\(PBIAS &gt; 0\)) o subestimar (\(PBIAS &lt; 0\)) el volumen o temperatura total.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-700/60 text-[11px] space-y-1">
                        <div>• <b>Rango Óptimo:</b> 0.0% (Aceptable entre \(-15\%\) y \(+15\%\)).</div>
                        <div>• <b>Interpretación en CA:</b> Vital para la conservación de la masa de precipitación en balances hidrológicos de cuencas.</div>
                    </div>
                </div>

                <!-- 5. Taylor Diagram Dynamics -->
                <div class="plot-card border-rose-800">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-white">Identidad Geométrica de Taylor</h4>
                        <span class="text-[10px] bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">Espacio Polar</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 my-2 text-xs font-mono text-center text-rose-300">
                        $$E'^2 = \sigma_s^2 + \sigma_o^2 - 2\sigma_s\sigma_o r$$
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Vincula analíticamente el error centrado cuadrático medio (\(E'\)), las desviaciones estándar de simulación y observación, y la correlación Pearson.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-700/60 text-[11px] space-y-1">
                        <div>• <b>Punto Óptimo:</b> Radio \(\sigma^* = 1.0\) y Ángulo \(\theta = 0^\circ\) (\(r = 1.0\)).</div>
                        <div>• <b>Interpretación en CA:</b> Muestra qué modelos reproducen fielmente la variabilidad estacional sin atenuar picos extremos.</div>
                    </div>
                </div>

                <!-- 6. ETS & Categorical Metrics -->
                <div class="plot-card border-sky-800">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-white">Equitable Threat Score (ETS)</h4>
                        <span class="text-[10px] bg-sky-950 text-sky-400 border border-sky-800 px-2 py-0.5 rounded">Habilidad de Lluvia</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 my-2 text-xs font-mono text-center text-sky-300">
                        $$ETS = \frac{Hits - Hits_{random}}{Hits + FalseAlarms + Misses - Hits_{random}}$$
                    </div>
                    <p class="text-xs text-slate-300 leading-relaxed">
                        Mide la habilidad de la malla para discriminar eventos de lluvia (&gt;1.0 mm/día) penalizando aciertos debidos al azar.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-700/60 text-[11px] space-y-1">
                        <div>• <b>Rango Óptimo:</b> 1.0 (Valores &gt; 0.20 indican destreza real en lluvia diaria tropical).</div>
                        <div>• <b>Interpretación en CA:</b> Discrimina eficazmente entre días secos y lluviosos en el Corredor Seco Centroamericano.</div>
                    </div>
                </div>

            </div>
        </div>

    </main>

    <!-- Footer -->
    <footer class="bg-slate-900 border-t border-slate-800 py-6 text-center text-xs text-slate-400 mt-12">
        <div class="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-2">
            <div>CDT 8.0 Climate Data Tools • Suite de Reconstrucción de Mallas para Centroamérica</div>
            <div>Validación Holdout en 29 Estaciones Ciega (1991–2020) • Generado con Apache ECharts 5</div>
        </div>
    </footer>

    <!-- Chart Initializer & Script Logic -->
    <script>
        // Data Payloads from Jinja
        const dataRain = {{ pay_rain_json | safe }};
        const dataTmax = {{ pay_tmax_json | safe }};
        const dataTmin = {{ pay_tmin_json | safe }};

        // Tab Switching Logic
        function switchTab(tabId) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            const targetPanel = document.getElementById('tab-content-' + tabId);
            const targetBtn = document.getElementById('tab-btn-' + tabId);
            if (targetPanel) targetPanel.classList.remove('hidden');
            if (targetBtn) targetBtn.classList.add('active');

            // Trigger window resize to render ECharts smoothly
            setTimeout(() => { window.dispatchEvent(new Event('resize')); }, 60);
        }

        // Initialize ECharts for a variable
        function initVariableCharts(prefix, payload, unit, baseColor) {
            if (!payload || !payload.experiments || payload.experiments.length === 0) return;

            // Common Toolbox Configuration for Image Download
            const commonToolbox = {
                feature: {
                    saveAsImage: {
                        title: 'Descargar Gráfica',
                        pixelRatio: 2,
                        backgroundColor: '#0f172a'
                    }
                },
                iconStyle: { borderColor: '#94a3b8' },
                right: 15,
                top: 5
            };

            // 1. Polar Taylor Diagram
            const taylorDom = document.getElementById('taylor' + prefix);
            if (taylorDom && payload.taylor_series) {
                const taylorChart = echarts.init(taylorDom);
                const taylorOption = {
                    backgroundColor: 'transparent',
                    toolbox: commonToolbox,
                    tooltip: {
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        textStyle: { color: '#f8fafc', fontSize: 11 },
                        formatter: function(params) {
                            if (params.seriesName === 'Referencia Holdout') {
                                return '<div class="font-bold text-rose-400">Estaciones Holdout (Referencia)</div>' +
                                       '<div class="text-xs text-slate-300">r = 1.000 | σ* = 1.00 | E\'* = 0.00</div>';
                            }
                            const d = params.value;
                            if (!d || d.length < 10) return params.seriesName;
                            const id = d[2];
                            const is_win = d[3];
                            const is_ctrl = d[4];
                            const r = d[5];
                            const kge = d[6];
                            const rmse = d[7];
                            const pbias = d[8];
                            const crmse = d[9];
                            const sigma = d[0];
                            const tag = is_win ? '<span style="background-color:#059669;color:#fff;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;">🏆 ÓPTIMO</span>' :
                                        (is_ctrl ? '<span style="background-color:#64748b;color:#fff;font-size:10px;padding:2px 6px;border-radius:4px;font-weight:bold;">⚡ CONTROL 0</span>' : '');
                            return '<div style="font-weight:bold;margin-bottom:4px;">' + id + ' ' + tag + '</div>' +
                                   '<div style="font-size:11px;color:#cbd5e1;line-height:1.6;">' +
                                   '<div>• Pearson r: <b style="color:#38bdf8;">' + Number(r).toFixed(3) + '</b></div>' +
                                   '<div>• Desv. Estándar Norm. (σ*): <b>' + Number(sigma).toFixed(3) + '</b></div>' +
                                   '<div>• Error Centrado (E\'*): <b style="color:#fbbf24;">' + Number(crmse).toFixed(3) + '</b></div>' +
                                   '<div>• Eficiencia KGE: <b style="color:#34d399;">' + Number(kge).toFixed(3) + '</b></div>' +
                                   '<div>• RMSE: <b>' + Number(rmse).toFixed(2) + ' ' + unit + '</b></div>' +
                                   '<div>• PBIAS: <b>' + (pbias > 0 ? '+' : '') + Number(pbias).toFixed(1) + '%</b></div>' +
                                   '</div>';
                        }
                    },
                    polar: {
                        center: ['50%', '52%'],
                        radius: '72%'
                    },
                    angleAxis: {
                        type: 'value',
                        startAngle: 0,
                        clockwise: false,
                        min: 0,
                        max: 90,
                        interval: 15,
                        axisLine: { lineStyle: { color: '#64748b' } },
                        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
                        axisLabel: {
                            color: '#94a3b8',
                            fontSize: 10,
                            formatter: function(val) {
                                const rad = val * Math.PI / 180;
                                const r = Math.cos(rad);
                                return r.toFixed(2);
                            }
                        }
                    },
                    radiusAxis: {
                        type: 'value',
                        min: 0,
                        max: 1.6,
                        interval: 0.2,
                        axisLine: { lineStyle: { color: '#64748b' } },
                        splitLine: { lineStyle: { color: '#334155', type: 'dotted' } },
                        axisLabel: { color: '#94a3b8', fontSize: 10 }
                    },
                    series: payload.taylor_series
                };
                taylorChart.setOption(taylorOption);
                window.addEventListener('resize', () => taylorChart.resize());
            }

            // 2. Multi-criteria Radar Chart (ALL EXPERIMENTS with Dynamic Legend)
            const radarDom = document.getElementById('radar' + prefix);
            if (radarDom && payload.radar_indicators.length > 0) {
                const radarChart = echarts.init(radarDom);
                const radarOption = {
                    backgroundColor: 'transparent',
                    toolbox: commonToolbox,
                    tooltip: { backgroundColor: '#0f172a', borderColor: '#334155', textStyle: { color: '#f8fafc', fontSize: 11 } },
                    legend: {
                        type: 'scroll',
                        orient: 'horizontal',
                        top: 5,
                        selected: payload.radar_selected,
                        textStyle: { color: '#cbd5e1', fontSize: 10 },
                        pageTextStyle: { color: '#94a3b8' },
                        pageIconColor: '#38bdf8',
                        pageIconInactiveColor: '#475569',
                        itemWidth: 14,
                        itemHeight: 10
                    },
                    radar: {
                        indicator: payload.radar_indicators,
                        shape: 'polygon',
                        center: ['50%', '55%'],
                        radius: '65%',
                        splitNumber: 4,
                        axisName: { color: '#cbd5e1', fontSize: 10 },
                        splitLine: { lineStyle: { color: '#334155' } },
                        splitArea: { show: true, areaStyle: { color: ['#0f172a', '#1e293b'] } },
                        axisLine: { lineStyle: { color: '#475569' } }
                    },
                    series: [{
                        type: 'radar',
                        data: payload.radar_series
                    }]
                };
                radarChart.setOption(radarOption);
                window.addEventListener('resize', () => radarChart.resize());
            }

            // 3. Scatter KGE vs RMSE
            const scatterDom = document.getElementById('scatter' + prefix);
            if (scatterDom) {
                const scatterChart = echarts.init(scatterDom);
                const scatterOption = {
                    backgroundColor: 'transparent',
                    toolbox: commonToolbox,
                    tooltip: {
                        trigger: 'item',
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        textStyle: { color: '#f8fafc', fontSize: 11 },
                        formatter: function(params) {
                            const d = params.value;
                            const isWin = d[3];
                            const isCtrl = d[4];
                            const badge = isWin ? '<span style="color:#34d399;font-weight:bold;">🏆 ÓPTIMO</span>' : (isCtrl ? '<span style="color:#94a3b8;font-weight:bold;">⚡ CONTROL 0</span>' : '');
                            return '<div style="font-weight:bold;margin-bottom:4px;">' + d[2] + ' ' + badge + '</div>' +
                                   '<div style="color:#94a3b8;font-size:10px;margin-bottom:6px;">' + d[9] + '</div>' +
                                   '<div>RMSE: <b>' + d[0] + ' ' + unit + '</b></div>' +
                                   '<div>KGE: <b>' + d[1] + '</b></div>' +
                                   '<div>Pearson r: <b>' + d[6] + '</b></div>' +
                                   '<div>PBIAS: <b>' + (d[7] > 0 ? '+' : '') + d[7] + '%</b></div>' +
                                   '<hr style="border-color:#334155;margin:4px 0;">' +
                                   '<div style="color:' + (d[5] >= 0 ? '#34d399' : '#f87171') + ';">Δ KGE vs Crudo: <b>' + (d[5] >= 0 ? '+' : '') + d[5] + ' (' + (d[8] >= 0 ? '+' : '') + d[8] + '%)</b></div>';
                        }
                    },
                    grid: { top: 35, right: 30, bottom: 50, left: 50 },
                    xAxis: {
                        name: 'RMSE (' + unit + ') [Menor es mejor]',
                        nameLocation: 'middle',
                        nameGap: 30,
                        axisLine: { lineStyle: { color: '#475569' } },
                        splitLine: { lineStyle: { color: '#1e293b' } }
                    },
                    yAxis: {
                        name: 'KGE [Mayor es mejor]',
                        axisLine: { lineStyle: { color: '#475569' } },
                        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } },
                        min: 0,
                        max: 1.05
                    },
                    series: [{
                        type: 'scatter',
                        data: payload.scatter_points,
                        symbolSize: function(data) {
                            return data[3] ? 18 : (data[4] ? 14 : 11);
                        },
                        itemStyle: {
                            color: function(params) {
                                if (params.value[3]) return '#059669'; // Winner
                                if (params.value[4]) return '#64748b'; // Control 00
                                return baseColor;
                            },
                            borderColor: function(params) {
                                if (params.value[3]) return '#fbbf24';
                                return '#ffffff';
                            },
                            borderWidth: function(params) {
                                return params.value[3] ? 2 : 1;
                            }
                        }
                    }]
                };
                scatterChart.setOption(scatterOption);
                window.addEventListener('resize', () => scatterChart.resize());
            }

            // 4. Delta KGE Bar Chart
            const barDom = document.getElementById('barDelta' + prefix);
            if (barDom) {
                const barChart = echarts.init(barDom);
                const barOption = {
                    backgroundColor: 'transparent',
                    toolbox: commonToolbox,
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: { type: 'shadow' },
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        textStyle: { color: '#f8fafc', fontSize: 11 },
                        formatter: function(params) {
                            const p = params[0];
                            const val = p.value;
                            const isCtrl = p.name.includes('00_Raw');
                            return '<div style="font-weight:bold;">' + p.name + '</div>' +
                                   '<div>' + (isCtrl ? 'Referencia Satélite Crudo' : 'Ganancia Neta') + ': <b>' + (val >= 0 ? '+' : '') + val + ' KGE</b></div>';
                        }
                    },
                    grid: { top: 35, right: 20, bottom: 90, left: 50 },
                    xAxis: {
                        type: 'category',
                        data: payload.bar_categories,
                        axisLabel: {
                            rotate: 45,
                            interval: 0,
                            color: '#94a3b8',
                            fontSize: 9,
                            formatter: function(val) {
                                return val.length > 18 ? val.substring(0, 16) + '..' : val;
                            }
                        },
                        axisLine: { lineStyle: { color: '#475569' } }
                    },
                    yAxis: {
                        name: 'Δ KGE vs Satélite Crudo',
                        axisLine: { lineStyle: { color: '#475569' } },
                        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
                    },
                    series: [{
                        type: 'bar',
                        data: payload.bar_values.map((v, i) => ({
                            value: v,
                            itemStyle: { color: payload.bar_colors[i] }
                        }))
                    }]
                };
                barChart.setOption(barOption);
                window.addEventListener('resize', () => barChart.resize());
            }

            // 5. Boxplot of Station KGE
            const boxDom = document.getElementById('box' + prefix);
            if (boxDom && payload.boxplot_data.length > 0) {
                const boxChart = echarts.init(boxDom);
                const boxOption = {
                    backgroundColor: 'transparent',
                    toolbox: commonToolbox,
                    tooltip: {
                        trigger: 'item',
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        textStyle: { color: '#f8fafc', fontSize: 11 },
                        formatter: function(params) {
                            const v = params.value;
                            return '<div style="font-weight:bold;margin-bottom:4px;">' + params.name + '</div>' +
                                   '<div>Máximo: <b>' + v[5] + '</b></div>' +
                                   '<div>Percentil 75 (Q3): <b>' + v[4] + '</b></div>' +
                                   '<div>Mediana: <b style="color:#38bdf8;">' + v[3] + '</b></div>' +
                                   '<div>Percentil 25 (Q1): <b>' + v[2] + '</b></div>' +
                                   '<div>Mínimo: <b>' + v[1] + '</b></div>';
                        }
                    },
                    grid: { top: 35, right: 20, bottom: 100, left: 50 },
                    xAxis: {
                        type: 'category',
                        data: payload.boxplot_categories,
                        axisLabel: {
                            rotate: 45,
                            interval: 0,
                            color: '#94a3b8',
                            fontSize: 9,
                            formatter: function(val) {
                                return val.length > 18 ? val.substring(0, 16) + '..' : val;
                            }
                        },
                        axisLine: { lineStyle: { color: '#475569' } }
                    },
                    yAxis: {
                        name: 'Eficiencia KGE en Estaciones Holdout',
                        axisLine: { lineStyle: { color: '#475569' } },
                        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
                    },
                    dataZoom: [
                        { type: 'slider', bottom: 10, height: 18, borderColor: '#334155', textStyle: { color: '#94a3b8' } },
                        { type: 'inside' }
                    ],
                    series: [{
                        type: 'boxplot',
                        data: payload.boxplot_data.map((d, i) => ({
                            value: d,
                            itemStyle: {
                                borderColor: payload.boxplot_colors[i],
                                color: payload.boxplot_colors[i] + '44'
                            }
                        }))
                    }]
                };
                boxChart.setOption(boxOption);
                window.addEventListener('resize', () => boxChart.resize());
            }
        }

        // Initialize All Dashboard Charts on DOM Ready
        document.addEventListener('DOMContentLoaded', function() {
            // Render Math equations with KaTeX
            if (window.renderMathInElement) {
                renderMathInElement(document.body, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '\(', right: '\)', display: false}
                    ]
                });
            }

            // Init ECharts per Variable
            initVariableCharts('Rain', dataRain, 'mm', '#0284c7');
            initVariableCharts('Tmax', dataTmax, '°C', '#ea580c');
            initVariableCharts('Tmin', dataTmin, '°C', '#7c3aed');

            // Initialize DataTables (Page length 25 so all experiments fit on one page)
            $('#tableRain').DataTable({ pageLength: 25, order: [[0, 'asc']] });
            $('#tableTmax').DataTable({ pageLength: 25, order: [[0, 'asc']] });
            $('#tableTmin').DataTable({ pageLength: 25, order: [[0, 'asc']] });
            $('#tableAll').DataTable({ pageLength: 25, order: [[4, 'desc']] });
        });
    </script>
</body>
</html>
"""

    tmpl = Template(html_template)
    rendered_html = tmpl.render(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        win_rain=win_rain,
        win_tmax=win_tmax,
        win_tmin=win_tmin,
        pay_rain=payloads_rain,
        pay_tmax=payloads_tmax,
        pay_tmin=payloads_tmin,
        pay_rain_json=json.dumps(payloads_rain),
        pay_tmax_json=json.dumps(payloads_tmax),
        pay_tmin_json=json.dumps(payloads_tmin),
        all_exps=df_ranked.to_dict(orient="records"),
        fig_rain=figures_map.get("rainfall", {}),
        fig_tmax=figures_map.get("tmax", {}),
        fig_tmin=figures_map.get("tmin", {}),
        comp_rain=comparison_figures.get("rainfall", "figures/comparisons_winner_vs_raw/comparison_rainfall_winner_vs_raw.png"),
        comp_tmax=comparison_figures.get("tmax", "figures/comparisons_winner_vs_raw/comparison_tmax_winner_vs_raw.png"),
        comp_tmin=comparison_figures.get("tmin", "figures/comparisons_winner_vs_raw/comparison_tmin_winner_vs_raw.png"),
        comp_overview=comparison_figures.get("overview", "figures/comparisons_winner_vs_raw/comparison_all_variables_executive_summary.png"),
    )

    with open(out_p, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"  [DASHBOARD] Apache ECharts Interactive Dashboard generated: {out_p}")
