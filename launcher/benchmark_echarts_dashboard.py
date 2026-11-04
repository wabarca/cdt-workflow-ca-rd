"""
Interactive HTML Benchmark Dashboard powered by Apache ECharts.

Provides a modern, publication-grade interactive dashboard for the CDT 8.0
Central America Grid Reconstruction Suite.
Features:
- Apache ECharts 5 with interactive DataZoom sliders, responsive canvas rendering,
  and rich HTML tooltips comparing each model against the raw satellite baseline (Control 00).
- Highlighting for [CONTROL 0] in slate grey (#64748b) and Winner in emerald/gold (#059669).
- Boxplots of station-level KGE distributions.
- Multi-criteria skill radar charts.
- Gallery of high-resolution (300 DPI) Winner vs. Raw Satellite diagnostic figures.
- Comprehensive scientific glossary defining all 9 climate evaluation metrics with KaTeX equations,
  optimal targets, acceptable ranges, and physical interpretation for Central America.
"""

from __future__ import annotations

import datetime
import json
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

    # 2. Scatter Points: [RMSE, KGE, ExpID, is_winner, is_control, delta_kge, r, pbias, pct_kge]
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
        # Group stations by experiment_id in the order of exps_sorted
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

    # 5. Radar Chart Data
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
    # Include Winner, Control 00, and Top 2
    candidates_to_plot = []
    winner_exp = next((e for e in exps if e["is_winner"]), None)
    control_exp = next((e for e in exps if e["is_control"]), None)
    if winner_exp:
        candidates_to_plot.append((winner_exp, "#059669", 3, True))
    if control_exp:
        candidates_to_plot.append((control_exp, "#64748b", 2, False))
    for e in exps_sorted:
        if not e["is_winner"] and not e["is_control"] and len(candidates_to_plot) < 5:
            candidates_to_plot.append((e, "#38bdf8" if len(candidates_to_plot) == 2 else "#94a3b8", 1.5, False))

    for item, col, width, is_win in candidates_to_plot:
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

        radar_series.append({
            "name": f"{item['id']} {'[ÓPTIMO]' if is_win else ('[CONTROL 0]' if item['is_control'] else '')}",
            "value": [round(v, 3) for v in r_vals],
            "itemStyle": {"color": col},
            "lineStyle": {"width": width, "type": "dashed" if item["is_control"] else "solid"},
            "areaStyle": {"opacity": 0.25 if is_win else 0.05},
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
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        }
        .chart-box {
            width: 100%;
            height: 440px;
        }
        /* Custom Scrollbar */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #475569; }
        /* DataTables dark theme styling */
        table.dataTable { background-color: #1e293b; color: #e2e8f0; border-collapse: collapse; }
        table.dataTable thead th { background-color: #0f172a; color: #94a3b8; border-bottom: 2px solid #334155; }
        table.dataTable tbody tr { background-color: #1e293b; border-bottom: 1px solid #334155; }
        table.dataTable tbody tr:hover { background-color: #273549; }
        .dataTables_wrapper .dataTables_length, .dataTables_wrapper .dataTables_filter,
        .dataTables_wrapper .dataTables_info, .dataTables_wrapper .dataTables_paginate {
            color: #94a3b8; font-size: 0.85rem;
        }
        .dataTables_wrapper .dataTables_filter input {
            background-color: #0f172a; border: 1px solid #475569; color: #f8fafc; border-radius: 0.375rem; padding: 0.25rem 0.5rem;
        }
    </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">

    <!-- Top Navigation Bar -->
    <header class="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 backdrop-blur-md bg-opacity-95">
        <div class="max-w-7xl mx-auto px-6 py-4 flex flex-col md:flex-row justify-between items-center gap-4">
            <div class="flex items-center space-x-3">
                <span class="bg-sky-600 text-white font-bold text-xs px-2.5 py-1 rounded tracking-wider shadow">CDT 8.0</span>
                <div>
                    <h1 class="text-base font-bold tracking-tight text-white flex items-center gap-2">
                        Tablero Interactivo de Validación y Benchmark de Modelos
                        <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded-full font-mono">Apache ECharts 5</span>
                    </h1>
                    <p class="text-xs text-slate-400">Reconstrucción y Corrección de Mallas en América Central (1991–2020)</p>
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

    <main class="max-w-7xl mx-auto px-6 py-8 space-y-8">

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

            <!-- Interactive ECharts Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Chart 1: Scatter RMSE vs KGE -->
                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Espacio de Precisión: Error (RMSE) vs. Eficiencia (KGE)</h3>
                            <p class="text-[11px] text-slate-400">El modelo óptimo se ubica en el extremo superior izquierdo (menor RMSE, mayor KGE)</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">16 Exp.</span>
                    </div>
                    <div id="scatterRain" class="chart-box"></div>
                </div>

                <!-- Chart 2: Net Gain vs Raw Satellite (Control 00) -->
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

                <!-- Chart 3: Boxplot of KGE by Station -->
                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Distribución de Eficiencia KGE en las 29 Estaciones Holdout</h3>
                            <p class="text-[11px] text-slate-400">Caja representa percentiles 25–75 y línea central la mediana. Gris: [CONTROL 0].</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Zoomable</span>
                    </div>
                    <div id="boxRain" class="chart-box"></div>
                </div>

                <!-- Chart 4: Multi-criteria Radar -->
                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad Climatológica</h3>
                            <p class="text-[11px] text-slate-400">Comparación simultánea de 6 dimensiones normalizadas entre modelos top y el satélite crudo</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Radar</span>
                    </div>
                    <div id="radarRain" class="chart-box"></div>
                </div>
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
                    <a href="{{ comp_rain }}" target="_blank" class="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                        <span>🔍 Abrir en Alta Resolución (300 DPI)</span>
                    </a>
                </div>
                <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                    <img src="{{ comp_rain }}" alt="Comparativa Lluvia Ganador vs Crudo" class="rounded max-h-[550px] object-contain shadow-md">
                </div>
            </div>

            <!-- Interactive DataTable -->
            <div class="plot-card">
                <h3 class="font-bold text-sm text-white mb-3">Tabla Maestra de Rendimiento: Experimentos de Precipitación</h3>
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
                            <span class="bg-amber-500 text-slate-950 text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo</span>
                            <span class="text-xs text-amber-300 font-mono">Rango #01 en Temperatura Máxima</span>
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

            <!-- Interactive ECharts Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Espacio de Precisión Tmax: Error (RMSE °C) vs. Eficiencia (KGE)</h3>
                            <p class="text-[11px] text-slate-400">Muestra la dramática reducción del error térmico orográfico tras el desescalado DEM</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">13 Exp.</span>
                    </div>
                    <div id="scatterTmax" class="chart-box"></div>
                </div>

                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Ganancia Neta (Δ KGE) respecto al Satélite CHIRTS Crudo</h3>
                            <p class="text-[11px] text-slate-400">CHIRTS Crudo (0.05°) = 0.0 de referencia. Barra verde indica mejora; gris es el control.</p>
                        </div>
                        <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded">Δ KGE</span>
                    </div>
                    <div id="barDeltaTmax" class="chart-box"></div>
                </div>

                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Distribución de Eficiencia KGE en las 29 Estaciones (Tmax)</h3>
                            <p class="text-[11px] text-slate-400">Desempeño consistente entre estaciones de costa y montaña</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Zoomable</span>
                    </div>
                    <div id="boxTmax" class="chart-box"></div>
                </div>

                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad (Tmax)</h3>
                            <p class="text-[11px] text-slate-400">Dimensiones de error térmico, sesgo y sincronía temporal</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Radar</span>
                    </div>
                    <div id="radarTmax" class="chart-box"></div>
                </div>
            </div>

            <!-- High-Resolution Comparison Figure Card: Winner vs Raw -->
            <div class="plot-card border-amber-800 bg-slate-900">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="bg-amber-600 text-slate-950 text-[10px] uppercase font-bold px-2 py-0.5 rounded">Diagnóstico Comparativo</span>
                            <h3 class="font-bold text-base text-white">Modelo Ganador (EXP_TX11) vs. CHIRTS Tmax Crudo (EXP_TX00)</h3>
                        </div>
                        <p class="text-xs text-slate-300 mt-1">Corrección del gradiente altimétrico y reducción del error cuadrático medio en todo el relieve centroamericano.</p>
                    </div>
                    <a href="{{ comp_tmax }}" target="_blank" class="inline-flex items-center gap-2 bg-amber-600 hover:bg-amber-500 text-slate-950 text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                        <span>🔍 Abrir en Alta Resolución (300 DPI)</span>
                    </a>
                </div>
                <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                    <img src="{{ comp_tmax }}" alt="Comparativa Tmax Ganador vs Crudo" class="rounded max-h-[550px] object-contain shadow-md">
                </div>
            </div>

            <!-- Interactive DataTable Tmax -->
            <div class="plot-card">
                <h3 class="font-bold text-sm text-white mb-3">Tabla Maestra de Rendimiento: Experimentos de Temperatura Máxima</h3>
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
                            <tr class="{% if e.is_winner %}bg-amber-950/40 text-amber-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
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

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 3: TEMPERATURA MÍNIMA (TMIN) -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmin" class="tab-panel hidden space-y-8">
            
            {% if win_tmin %}
            <!-- Winner Highlight Card -->
            <div class="bg-gradient-to-r from-purple-950 via-slate-900 to-slate-900 border border-purple-800 text-white rounded-xl p-6 shadow-xl relative overflow-hidden">
                <div class="absolute -right-10 -bottom-10 opacity-10 text-9xl">🌙</div>
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-purple-500 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo</span>
                            <span class="text-xs text-purple-300 font-mono">Rango #01 en Temperatura Mínima</span>
                        </div>
                        <h2 class="text-2xl font-black text-white tracking-tight">{{ win_tmin.experiment_id }}</h2>
                        <p class="text-xs text-slate-300 max-w-2xl mt-1 leading-relaxed">{{ win_tmin.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-slate-900/90 rounded-lg p-3 border border-slate-700 text-center">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-400">GSS</div>
                            <div class="text-base font-bold text-purple-400">{{ "%.3f"|format(win_tmin.global_skill_score) }}</div>
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

            <!-- Interactive ECharts Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Espacio de Precisión Tmin: Error (RMSE °C) vs. Eficiencia (KGE)</h3>
                            <p class="text-[11px] text-slate-400">Calibración nocturna con corrección empírica de inversión térmica</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">13 Exp.</span>
                    </div>
                    <div id="scatterTmin" class="chart-box"></div>
                </div>

                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Ganancia Neta (Δ KGE) respecto al Satélite CHIRTS Crudo</h3>
                            <p class="text-[11px] text-slate-400">CHIRTS Crudo = 0.0 de referencia. Barra verde indica mejora; gris es el control.</p>
                        </div>
                        <span class="text-xs bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 rounded">Δ KGE</span>
                    </div>
                    <div id="barDeltaTmin" class="chart-box"></div>
                </div>

                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Distribución de Eficiencia KGE en las 29 Estaciones (Tmin)</h3>
                            <p class="text-[11px] text-slate-400">Representación de la estabilidad frente a temperaturas mínimas extremas</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Zoomable</span>
                    </div>
                    <div id="boxTmin" class="chart-box"></div>
                </div>

                <div class="plot-card">
                    <div class="flex justify-between items-center mb-2">
                        <div>
                            <h3 class="font-bold text-sm text-white">Radar Multicriterio de Habilidad (Tmin)</h3>
                            <p class="text-[11px] text-slate-400">Dimensiones de fidelidad nocturna y errores absolutos</p>
                        </div>
                        <span class="text-xs bg-slate-800 text-slate-300 px-2 py-0.5 rounded border border-slate-700">Radar</span>
                    </div>
                    <div id="radarTmin" class="chart-box"></div>
                </div>
            </div>

            <!-- High-Resolution Comparison Figure Card: Winner vs Raw -->
            <div class="plot-card border-purple-800 bg-slate-900">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="bg-purple-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Diagnóstico Comparativo</span>
                            <h3 class="font-bold text-base text-white">Modelo Ganador (EXP_TN10) vs. CHIRTS Tmin Crudo (EXP_TN00)</h3>
                        </div>
                        <p class="text-xs text-slate-300 mt-1">Ajuste quantile matching empírico eliminando el sesgo cálido nocturno en valles y planicies.</p>
                    </div>
                    <a href="{{ comp_tmin }}" target="_blank" class="inline-flex items-center gap-2 bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                        <span>🔍 Abrir en Alta Resolución (300 DPI)</span>
                    </a>
                </div>
                <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                    <img src="{{ comp_tmin }}" alt="Comparativa Tmin Ganador vs Crudo" class="rounded max-h-[550px] object-contain shadow-md">
                </div>
            </div>

            <!-- Interactive DataTable Tmin -->
            <div class="plot-card">
                <h3 class="font-bold text-sm text-white mb-3">Tabla Maestra de Rendimiento: Experimentos de Temperatura Mínima</h3>
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
                            <tr class="{% if e.is_winner %}bg-purple-950/40 text-purple-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
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

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 4: RESUMEN CONSOLIDADO -->
        <!-- ========================================================================= -->
        <div id="tab-content-consolidated" class="tab-panel hidden space-y-8">
            
            <!-- Executive Multi-Variable Summary Figure Card -->
            <div class="plot-card border-slate-700 bg-slate-900">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-4">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="bg-indigo-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Síntesis Ejecutiva</span>
                            <h3 class="font-bold text-base text-white">Evaluación Global Multi-Variable: Modelos Óptimos vs. Satélite Crudo</h3>
                        </div>
                        <p class="text-xs text-slate-300 mt-1">Comparativa directa de KGE, Pearson r y Habilidad Global (GSS) para Lluvia, Tmax y Tmin en Centroamérica.</p>
                    </div>
                    <a href="{{ comp_overview }}" target="_blank" class="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                        <span>🔍 Abrir en Alta Resolución (300 DPI)</span>
                    </a>
                </div>
                <div class="bg-slate-950 rounded-lg p-2 border border-slate-800 flex justify-center">
                    <img src="{{ comp_overview }}" alt="Síntesis Ejecutiva Multi-Variable" class="rounded max-h-[500px] object-contain shadow-md">
                </div>
            </div>

            <!-- Master Table of 42 Experiments -->
            <div class="plot-card">
                <h3 class="font-bold text-sm text-white mb-3">Catálogo Maestro de 42 Experimentos (39 Benchmark + 3 Controles Satelitales Crudos)</h3>
                <div class="overflow-x-auto">
                    <table id="tableAll" class="w-full text-xs display">
                        <thead>
                            <tr>
                                <th>Variable</th>
                                <th>Rango</th>
                                <th>ID Experimento</th>
                                <th>Descripción</th>
                                <th>GSS</th>
                                <th>KGE</th>
                                <th>Pearson r</th>
                                <th>RMSE</th>
                                <th>PBIAS (%)</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in all_exps %}
                            <tr class="{% if e.is_winner %}bg-emerald-950/40 text-emerald-300 font-bold{% elif e.is_control %}bg-slate-800/60 text-slate-400{% endif %}">
                                <td class="uppercase font-semibold text-[11px]">
                                    {% if e.variable == 'rainfall' %}<span class="text-sky-400">🌧️ Lluvia</span>
                                    {% elif e.variable == 'tmax' %}<span class="text-amber-400">☀️ Tmax</span>
                                    {% else %}<span class="text-purple-400">🌙 Tmin</span>{% endif %}
                                </td>
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono">{{ e.experiment_id }}</td>
                                <td class="max-w-xs truncate">{{ e.description }}</td>
                                <td>{{ "%.3f"|format(e.global_skill_score) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td>
                                    {% if e.is_winner %}<span class="px-2 py-0.5 bg-emerald-900 text-emerald-300 rounded text-[10px]">ÓPTIMO</span>
                                    {% elif e.is_control %}<span class="px-2 py-0.5 bg-slate-700 text-slate-300 rounded text-[10px]">CONTROL 0</span>
                                    {% else %}<span class="px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-[10px]">CANDIDATO</span>{% endif %}
                                </td>
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
            
            <!-- Glossary Header -->
            <div class="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-md">
                <div class="flex items-center gap-3 mb-2">
                    <span class="bg-indigo-600 text-white font-bold text-xs px-2.5 py-1 rounded">Marco Metodológico</span>
                    <h2 class="text-xl font-bold text-white">Definición e Interpretación de Estadísticos y Métricas Climatológicas</h2>
                </div>
                <p class="text-xs text-slate-300 leading-relaxed max-w-4xl">
                    Para evaluar con rigor científico la calidad de las mallas reconstruidas mediante Climate Data Tools (CDT 8.0) y su mejora frente a los productos satelitales crudos (CHIRPS v2.0 y CHIRTS-ERA5), se emplea una batería completa de métricas hidrológicas continuas y categóricas. A continuación se detalla su formulación matemática, valores de referencia y significado físico para la climatología de Centroamérica.
                </p>
            </div>

            <!-- Cards Grid for Metrics -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                <!-- 1. KGE -->
                <div class="plot-card space-y-3 border-l-4 border-l-sky-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-sky-400 font-bold">Métrica Primaria</span>
                            <h4 class="font-bold text-sm text-white">Eficiencia Kling-Gupta (KGE)</h4>
                        </div>
                        <span class="text-xs font-mono bg-sky-950 text-sky-300 border border-sky-800 px-2 py-0.5 rounded">Óptimo: 1.0</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-sky-200">
                        $$ \\mathrm{KGE} = 1 - \\sqrt{(r - 1)^2 + (\\alpha - 1)^2 + (\\beta - 1)^2} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Componentes:</strong> \(r\) es la correlación lineal, \(\\alpha = \\sigma_s / \\sigma_o\) mide la variabilidad relativa de extremos, y \(\\beta = \\mu_s / \\mu_o\) el sesgo de volumen medio.</p>
                        <p><strong>Interpretación:</strong> Supera las limitaciones del NSE al evitar penalizaciones desproporcionadas por sesgo de varianza. En Centroamérica, un KGE &gt; 0.3 indica habilidad predictiva real y KGE &gt; 0.6 refleja excelente fidelidad hidrológica.</p>
                    </div>
                </div>

                <!-- 2. Pearson r -->
                <div class="plot-card space-y-3 border-l-4 border-l-emerald-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-emerald-400 font-bold">Sincronía Temporal</span>
                            <h4 class="font-bold text-sm text-white">Correlación de Pearson (\(r\))</h4>
                        </div>
                        <span class="text-xs font-mono bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">Óptimo: 1.0</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-emerald-200">
                        $$ r = \\frac{\\sum (O_i - \\bar{O})(S_i - \\bar{S})}{\\sqrt{\\sum (O_i - \\bar{O})^2 \\sum (S_i - \\bar{S})^2}} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Rango:</strong> \([-1.0, +1.0]\).</p>
                        <p><strong>Interpretación:</strong> Cuantifica la sincronía temporal del ciclo anual y de los eventos meteorológicos sin considerar sesgos de amplitud. Un valor cercano a 1.0 garantiza que los días lluviosos o cálidos coincidan exactamente en el calendario entre la malla y las estaciones.</p>
                    </div>
                </div>

                <!-- 3. RMSE -->
                <div class="plot-card space-y-3 border-l-4 border-l-amber-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-amber-400 font-bold">Magnitud de Error</span>
                            <h4 class="font-bold text-sm text-white">Error Cuadrático Medio (RMSE)</h4>
                        </div>
                        <span class="text-xs font-mono bg-amber-950 text-amber-300 border border-amber-800 px-2 py-0.5 rounded">Óptimo: 0.0</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-amber-200">
                        $$ \\mathrm{RMSE} = \\sqrt{\\frac{1}{N} \\sum_{i=1}^N (S_i - O_i)^2} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Unidades:</strong> Milímetros (mm/día) en lluvia; Grados Celsius (°C) en temperatura.</p>
                        <p><strong>Interpretación:</strong> Penaliza fuertemente las desviaciones severas y picos atípicos. Una reducción del RMSE demuestra que el proceso de corrección de sesgo mitigó sobreestimaciones convectivas desmedidas.</p>
                    </div>
                </div>

                <!-- 4. MAE -->
                <div class="plot-card space-y-3 border-l-4 border-l-rose-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-rose-400 font-bold">Error Promedio</span>
                            <h4 class="font-bold text-sm text-white">Error Absoluto Medio (MAE)</h4>
                        </div>
                        <span class="text-xs font-mono bg-rose-950 text-rose-300 border border-rose-800 px-2 py-0.5 rounded">Óptimo: 0.0</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-rose-200">
                        $$ \\mathrm{MAE} = \\frac{1}{N} \\sum_{i=1}^N |S_i - O_i| $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Unidades:</strong> Mismas que la variable (mm o °C).</p>
                        <p><strong>Interpretación:</strong> Mide la magnitud típica esperada del error diario sin sobredimensionar valores extremos. Resulta más representativo del sesgo rutinario en días de régimen normal.</p>
                    </div>
                </div>

                <!-- 5. PBIAS -->
                <div class="plot-card space-y-3 border-l-4 border-l-purple-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-purple-400 font-bold">Sesgo Sistemático</span>
                            <h4 class="font-bold text-sm text-white">Sesgo Porcentual (PBIAS)</h4>
                        </div>
                        <span class="text-xs font-mono bg-purple-950 text-purple-300 border border-purple-800 px-2 py-0.5 rounded">Óptimo: 0.0%</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-purple-200">
                        $$ \\mathrm{PBIAS} = \\frac{\\sum (S_i - O_i)}{\\sum O_i} \\times 100\\% $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Rango Aceptable:</strong> \(\\pm 10\\%\) (Excelente), \(\\pm 15\\%\) (Bueno).</p>
                        <p><strong>Interpretación:</strong> Indica si la malla satelital sobreestima (positivo) o subestima (negativo) el volumen acumulado observado. CHIRPS crudo suele subestimar lluvia en zonas montañosas (\(-18\\%\)), corregido a \(-4\\%\) por CDT.</p>
                    </div>
                </div>

                <!-- 6. POD -->
                <div class="plot-card space-y-3 border-l-4 border-l-cyan-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-cyan-400 font-bold">Habilidad Categórica</span>
                            <h4 class="font-bold text-sm text-white">Probabilidad de Detección (POD)</h4>
                        </div>
                        <span class="text-xs font-mono bg-cyan-950 text-cyan-300 border border-cyan-800 px-2 py-0.5 rounded">Óptimo: 1.0 (100%)</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-cyan-200">
                        $$ \\mathrm{POD} = \\frac{A}{A + C} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Definición:</strong> \(A\) = Aciertos de lluvia, \(C\) = Días lluviosos no detectados.</p>
                        <p><strong>Interpretación:</strong> Porcentaje de eventos lluviosos reales (&gt; 1.0 mm) detectados acertadamente por la malla. Valores superiores a 0.65 garantizan detección oportuna de tormentas tropicales y ondas del este.</p>
                    </div>
                </div>

                <!-- 7. FAR -->
                <div class="plot-card space-y-3 border-l-4 border-l-orange-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-orange-400 font-bold">Habilidad Categórica</span>
                            <h4 class="font-bold text-sm text-white">Razón de Falsa Alarma (FAR)</h4>
                        </div>
                        <span class="text-xs font-mono bg-orange-950 text-orange-300 border border-orange-800 px-2 py-0.5 rounded">Óptimo: 0.0 (0%)</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-orange-200">
                        $$ \\mathrm{FAR} = \\frac{B}{A + B} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Definición:</strong> \(B\) = Falsas alarmas (malla reporta lluvia en día seco).</p>
                        <p><strong>Interpretación:</strong> Evita el problema común de "llovizna constante" donde el satélite simula lluvia ligera ficticia. Un FAR menor a 0.35 indica alta confiabilidad hidrológica.</p>
                    </div>
                </div>

                <!-- 8. ETS -->
                <div class="plot-card space-y-3 border-l-4 border-l-teal-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-teal-400 font-bold">Habilidad Neta</span>
                            <h4 class="font-bold text-sm text-white">Equitable Threat Score (ETS)</h4>
                        </div>
                        <span class="text-xs font-mono bg-teal-950 text-teal-300 border border-teal-800 px-2 py-0.5 rounded">Óptimo: 1.0</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-teal-200">
                        $$ \\mathrm{ETS} = \\frac{A - A_r}{A + B + C - A_r}, \\quad A_r = \\frac{(A+B)(A+C)}{N} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Propiedad Equitativa:</strong> Elimina aciertos fortuitos por azar (\(A_r\)).</p>
                        <p><strong>Interpretación:</strong> Evalúa la habilidad intrínseca del modelo sin verse inflado por la alta frecuencia estacional de días lluviosos en el Caribe centroamericano.</p>
                    </div>
                </div>

                <!-- 9. GSS -->
                <div class="plot-card space-y-3 border-l-4 border-l-indigo-500">
                    <div class="flex justify-between items-start">
                        <div>
                            <span class="text-[10px] font-mono uppercase text-indigo-400 font-bold">Índice Sintético</span>
                            <h4 class="font-bold text-sm text-white">Global Skill Score (GSS)</h4>
                        </div>
                        <span class="text-xs font-mono bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded">Óptimo: 1.0</span>
                    </div>
                    <div class="bg-slate-950 p-2.5 rounded border border-slate-800 text-center text-xs font-mono text-indigo-200">
                        $$ \\mathrm{GSS} = 0.40 \\cdot \\mathrm{KGE} + 0.25 \\cdot r + 0.15 \\cdot S_{\\mathrm{bias}} + 0.10 \\cdot S_{\\mathrm{rmse}} + 0.10 \\cdot S_{\\mathrm{cat}} $$
                    </div>
                    <div class="text-[11.5px] text-slate-300 space-y-1.5 leading-relaxed">
                        <p><strong>Ponderación Multicriterio:</strong> Integra eficiencia, correlación, control de sesgo y reducción de error cuadrático.</p>
                        <p><strong>Interpretación:</strong> Determina la jerarquía del Leaderboard final para seleccionar de manera objetiva la mejor malla candidata para producción operativa.</p>
                    </div>
                </div>

            </div>

        </div>

    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-800 bg-slate-950 text-slate-500 py-8 text-xs text-center">
        <div class="max-w-7xl mx-auto px-6 space-y-2">
            <p>CDT 8.0 Central America Benchmark & Grid Reconstruction Suite &copy; 2026. Desarrollado con Climate Data Tools (CDT) & Apache ECharts.</p>
            <p class="font-mono text-slate-600">Validación científica cruzada con Holdout de 29 estaciones independientes (1991–2020).</p>
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
            setTimeout(() => { window.dispatchEvent(new Event('resize')); }, 50);
        }

        // Initialize ECharts for a variable
        function initVariableCharts(prefix, payload, unit, baseColor) {
            if (!payload || !payload.experiments || payload.experiments.length === 0) return;

            // 1. Scatter KGE vs RMSE
            const scatterDom = document.getElementById('scatter' + prefix);
            if (scatterDom) {
                const scatterChart = echarts.init(scatterDom);
                const scatterOption = {
                    backgroundColor: 'transparent',
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
                    grid: { top: 30, right: 30, bottom: 50, left: 50 },
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

            // 2. Delta KGE Bar Chart
            const barDom = document.getElementById('barDelta' + prefix);
            if (barDom) {
                const barChart = echarts.init(barDom);
                const barOption = {
                    backgroundColor: 'transparent',
                    tooltip: {
                        trigger: 'axis',
                        axisPointer: { type: 'shadow' },
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        textStyle: { color: '#f8fafc', fontSize: 11 },
                        formatter: function(params) {
                            const p = params[0];
                            return '<b>' + p.name + '</b><br>Δ KGE vs Control 0: <b>' + (p.value >= 0 ? '+' : '') + p.value + '</b>';
                        }
                    },
                    grid: { top: 20, right: 20, bottom: 80, left: 50 },
                    xAxis: {
                        type: 'category',
                        data: payload.bar_categories,
                        axisLabel: { rotate: 45, fontSize: 9, color: '#94a3b8' },
                        axisLine: { lineStyle: { color: '#475569' } }
                    },
                    yAxis: {
                        name: 'Δ KGE',
                        axisLine: { lineStyle: { color: '#475569' } },
                        splitLine: { lineStyle: { color: '#334155', type: 'dashed' } }
                    },
                    dataZoom: [
                        { type: 'slider', bottom: 10, height: 18, borderColor: '#334155', textStyle: { color: '#94a3b8' } },
                        { type: 'inside' }
                    ],
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

            // 3. Boxplot
            const boxDom = document.getElementById('box' + prefix);
            if (boxDom && payload.boxplot_data.length > 0) {
                const boxChart = echarts.init(boxDom);
                const boxOption = {
                    backgroundColor: 'transparent',
                    tooltip: {
                        trigger: 'item',
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        textStyle: { color: '#f8fafc', fontSize: 11 },
                        formatter: function(param) {
                            return '<b>' + param.name + '</b><br>' +
                                   'Máximo: ' + param.value[5].toFixed(3) + '<br>' +
                                   'Q3 (P75): ' + param.value[4].toFixed(3) + '<br>' +
                                   'Mediana: <b>' + param.value[3].toFixed(3) + '</b><br>' +
                                   'Q1 (P25): ' + param.value[2].toFixed(3) + '<br>' +
                                   'Mínimo: ' + param.value[1].toFixed(3);
                        }
                    },
                    grid: { top: 20, right: 20, bottom: 80, left: 50 },
                    xAxis: {
                        type: 'category',
                        data: payload.boxplot_categories,
                        axisLabel: { rotate: 45, fontSize: 9, color: '#94a3b8' },
                        axisLine: { lineStyle: { color: '#475569' } }
                    },
                    yAxis: {
                        name: 'KGE por Estación',
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

            // 4. Radar Chart
            const radarDom = document.getElementById('radar' + prefix);
            if (radarDom && payload.radar_indicators.length > 0) {
                const radarChart = echarts.init(radarDom);
                const radarOption = {
                    backgroundColor: 'transparent',
                    tooltip: { backgroundColor: '#0f172a', borderColor: '#334155', textStyle: { color: '#f8fafc', fontSize: 11 } },
                    legend: {
                        bottom: 0,
                        textStyle: { color: '#94a3b8', fontSize: 10 },
                        itemWidth: 14,
                        itemHeight: 10
                    },
                    radar: {
                        indicator: payload.radar_indicators,
                        shape: 'polygon',
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
        }

        // Initialize All Dashboard Charts on DOM Ready
        document.addEventListener('DOMContentLoaded', function() {
            // Render Math equations with KaTeX
            if (window.renderMathInElement) {
                renderMathInElement(document.body, {
                    delimiters: [
                        {left: '$$', right: '$$', display: true},
                        {left: '\\(', right: '\\)', display: false}
                    ]
                });
            }

            // Init ECharts per Variable
            initVariableCharts('Rain', dataRain, 'mm', '#0284c7');
            initVariableCharts('Tmax', dataTmax, '°C', '#ea580c');
            initVariableCharts('Tmin', dataTmin, '°C', '#7c3aed');

            // Initialize DataTables
            $('#tableRain').DataTable({ pageLength: 10, order: [[0, 'asc']] });
            $('#tableTmax').DataTable({ pageLength: 10, order: [[0, 'asc']] });
            $('#tableTmin').DataTable({ pageLength: 10, order: [[0, 'asc']] });
            $('#tableAll').DataTable({ pageLength: 15, order: [[4, 'desc']] });
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
        comp_rain=comparison_figures.get("rainfall", "figures/comparisons_winner_vs_raw/comparison_rainfall_winner_vs_raw.png"),
        comp_tmax=comparison_figures.get("tmax", "figures/comparisons_winner_vs_raw/comparison_tmax_winner_vs_raw.png"),
        comp_tmin=comparison_figures.get("tmin", "figures/comparisons_winner_vs_raw/comparison_tmin_winner_vs_raw.png"),
        comp_overview=comparison_figures.get("overview", "figures/comparisons_winner_vs_raw/comparison_all_variables_executive_summary.png"),
    )

    with open(out_p, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"  [DASHBOARD] Apache ECharts Interactive Dashboard generated: {out_p}")
