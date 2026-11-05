"""
CDT 8.0 - Static Benchmark Dashboard Generator
Generates a clean, ultra-reliable static HTML dashboard with Light Theme,
Data-First sortable tables, and high-resolution (300 DPI) embedded scientific figures for Central America.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import datetime
import json
import pandas as pd
from jinja2 import Template


def generate_static_html_dashboard(
    df_ranked: pd.DataFrame,
    figures_map: Dict[str, Dict[str, str]],
    comparison_figures: Dict[str, str],
    output_html_path: Path | str,
    df_stations: Optional[pd.DataFrame] = None
) -> str:
    """Renders the self-contained static HTML dashboard with Light Theme."""
    out_p = Path(output_html_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    # Filter by variable
    df_rain = df_ranked[df_ranked["variable"] == "rainfall"].sort_values("rank", ascending=True) if not df_ranked.empty else pd.DataFrame()
    df_tmax = df_ranked[df_ranked["variable"] == "tmax"].sort_values("rank", ascending=True) if not df_ranked.empty else pd.DataFrame()
    df_tmin = df_ranked[df_ranked["variable"] == "tmin"].sort_values("rank", ascending=True) if not df_ranked.empty else pd.DataFrame()

    win_rain = df_rain[df_rain["is_winner"]].iloc[0].to_dict() if not df_rain.empty and not df_rain[df_rain["is_winner"]].empty else (df_rain.iloc[0].to_dict() if not df_rain.empty else {})
    win_tmax = df_tmax[df_tmax["is_winner"]].iloc[0].to_dict() if not df_tmax.empty and not df_tmax[df_tmax["is_winner"]].empty else (df_tmax.iloc[0].to_dict() if not df_tmax.empty else {})
    win_tmin = df_tmin[df_tmin["is_winner"]].iloc[0].to_dict() if not df_tmin.empty and not df_tmin[df_tmin["is_winner"]].empty else (df_tmin.iloc[0].to_dict() if not df_tmin.empty else {})

    # Calculate delta KGE vs raw control for all rows
    def enrich_deltas(df_sub):
        if df_sub.empty:
            return []
        ctrl_rows = df_sub[df_sub["experiment_id"].str.contains(r"00|Raw", regex=True)]
        raw_kge = ctrl_rows["kge"].values[0] if not ctrl_rows.empty else df_sub["kge"].min()
        raw_rmse = ctrl_rows["rmse"].values[0] if not ctrl_rows.empty else df_sub["rmse"].max()

        records = []
        for r in df_sub.to_dict(orient="records"):
            delta_k = r.get("kge", 0.0) - raw_kge
            pct_gain = (delta_k / abs(raw_kge) * 100.0) if abs(raw_kge) > 1e-6 else 0.0
            r["delta_kge_raw"] = delta_k
            r["pct_kge_gain"] = pct_gain
            r["raw_rmse_diff"] = r.get("rmse", 0.0) - raw_rmse
            r["is_control"] = bool("00" in r["experiment_id"] or "Raw" in r["experiment_id"])
            records.append(r)
        return records

    list_rain = enrich_deltas(df_rain)
    list_tmax = enrich_deltas(df_tmax)
    list_tmin = enrich_deltas(df_tmin)
    list_all = enrich_deltas(df_ranked.sort_values(["variable", "rank"]))

    html_template = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CDT 8.0 • Benchmark Regional Centroamérica (1991–2020)</title>
    
    <!-- Tailwind CSS (CDN) -->
    <script src="https://cdn.tailwindcss.com"></script>
    
        <!-- KaTeX for Scientific Mathematics Typography (Synchronous Load) -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
        body { font-family: 'Inter', sans-serif; background-color: #f8fafc; color: #0f172a; }
        .font-mono { font-family: 'JetBrains Mono', monospace; }
        
        /* Light Theme Tabs */
        .tab-btn {
            color: #64748b;
            border-bottom: 2px solid transparent;
            font-weight: 600;
        }
        .tab-btn:hover {
            color: #0284c7;
        }
        .tab-btn.active {
            color: #0284c7;
            border-bottom: 2px solid #0284c7;
            background-color: #f0f9ff;
        }

        /* Sortable Table Styling */
        .sortable-th {
            cursor: pointer;
            user-select: none;
            position: relative;
            padding-right: 1.4rem !important;
            transition: background-color 0.15s;
        }
        .sortable-th:hover {
            background-color: #e2e8f0 !important;
        }
        .sort-icon {
            position: absolute;
            right: 0.35rem;
            top: 50%;
            transform: translateY(-50%);
            font-size: 0.65rem;
            color: #64748b;
        }

        .data-table th {
            background-color: #f1f5f9;
            color: #1e293b;
            font-weight: 700;
            padding: 9px 10px;
            text-align: center;
            border-bottom: 2px solid #cbd5e1;
            white-space: nowrap;
        }
        .data-table td {
            padding: 7px 10px;
            border-bottom: 1px solid #e2e8f0;
            text-align: center;
            white-space: nowrap;
        }
        .data-table tr:hover {
            background-color: #f8fafc;
        }

        /* Publication Figure Cards */
        .fig-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 1.25rem;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.06);
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .fig-card:hover {
            border-color: #0284c7;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* Modal Lightbox */
        #imgModal {
            display: none;
            position: fixed;
            z-index: 100;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(4px);
        }
    </style>
</head>
<body class="min-h-screen flex flex-col antialiased">

    <!-- Modal Lightbox for Full-Resolution Image Inspection -->
    <div id="imgModal" onclick="closeModal()">
        <div class="relative max-w-6xl mx-auto p-4 flex flex-col items-center justify-center min-h-screen">
            <button onclick="closeModal()" class="absolute top-6 right-6 bg-slate-800 hover:bg-slate-700 text-white rounded-full w-10 h-10 flex items-center justify-center font-bold text-lg shadow-lg">&times;</button>
            <img id="modalImg" src="" alt="Vista Previa de Figura" class="max-h-[85vh] max-w-full rounded-lg shadow-2xl border border-slate-700 object-contain bg-white">
            <div id="modalCaption" class="mt-4 text-xs font-semibold text-slate-200 bg-slate-900/95 px-4 py-2 rounded-lg border border-slate-700"></div>
        </div>
    </div>

    <!-- Header (Light Theme) -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-sm">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <div class="flex items-center gap-2">
                    <span class="bg-sky-600 text-white text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded">CDT 8.0</span>
                    <span class="text-xs text-sky-700 font-bold font-mono">Suite Regional de Reconstrucción de Mallas</span>
                </div>
                <h1 class="text-xl sm:text-2xl font-black tracking-tight text-slate-900 mt-1">
                    Centroamérica: Evaluación y Benchmark de Experimentos
                </h1>
                <p class="text-xs text-slate-500">
                    Validación independiente en 29 estaciones ciegas (1991–2020) • Datos Primero y Figuras de Publicación (300 DPI)
                </p>
            </div>
            <div class="flex items-center gap-3">
                <a href="benchmark_leaderboard_summary.csv" download class="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded-lg border border-slate-300 transition font-medium">
                    <span>📊 Descargar CSV</span>
                </a>
                <a href="benchmark_leaderboard.json" download class="inline-flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs px-3 py-1.5 rounded-lg border border-slate-300 transition font-medium">
                    <span>💾 JSON</span>
                </a>
                <span class="text-[11px] text-slate-400 font-mono hidden lg:inline">{{ timestamp }}</span>
            </div>
        </div>

        <!-- Navigation Tabs -->
        <nav class="max-w-7xl mx-auto px-4 sm:px-6 flex overflow-x-auto space-x-1 border-t border-slate-100">
            <button onclick="switchTab('consolidated')" id="tab-btn-consolidated" class="tab-btn active px-4 py-2.5 text-xs whitespace-nowrap transition">
                🌟 Resumen Ejecutivo Multivariable
            </button>
            <button onclick="switchTab('rainfall')" id="tab-btn-rainfall" class="tab-btn px-4 py-2.5 text-xs whitespace-nowrap transition">
                🌧️ Precipitación Diaria (CHIRPS)
            </button>
            <button onclick="switchTab('tmax')" id="tab-btn-tmax" class="tab-btn px-4 py-2.5 text-xs whitespace-nowrap transition">
                ☀️ Temperatura Máxima (CHIRTS)
            </button>
            <button onclick="switchTab('tmin')" id="tab-btn-tmin" class="tab-btn px-4 py-2.5 text-xs whitespace-nowrap transition">
                🌙 Temperatura Mínima (CHIRTS)
            </button>
            <button onclick="switchTab('glossary')" id="tab-btn-glossary" class="tab-btn px-4 py-2.5 text-xs whitespace-nowrap transition">
                📖 Definición e Interpretación
            </button>
        </nav>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 py-8 flex-1 space-y-8">

        <!-- ========================================================================= -->
        <!-- TAB 1: RESUMEN EJECUTIVO MULTIVARIABLE (42 EXPERIMENTOS) -->
        <!-- ========================================================================= -->
        <div id="tab-content-consolidated" class="tab-panel space-y-8">
            
            <!-- Executive Cross-Variable Synthesis Figure Card -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
                    <div>
                        <div class="flex items-center gap-2">
                            <span class="bg-emerald-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Síntesis Ejecutiva</span>
                            <h3 class="font-bold text-base text-slate-900">Evaluación Global: Rejilla Original vs. Malla Óptima Corregida</h3>
                        </div>
                        <p class="text-xs text-slate-600 mt-1">Comparación directa de Eficiencia KGE, correlación Pearson y reducción de error en las 29 estaciones holdout de Centroamérica.</p>
                    </div>
                    <a href="{{ comp_overview }}" download class="inline-flex items-center gap-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow-sm">
                        <span>⬇️ Descargar Síntesis (300 DPI)</span>
                    </a>
                </div>
                <div class="bg-slate-50 rounded-lg p-3 border border-slate-200 flex justify-center cursor-pointer hover:border-slate-400 transition" onclick="openModal('{{ comp_overview }}', 'Síntesis Ejecutiva Multivariable (Lluvia, Tmax, Tmin)')">
                    <img src="{{ comp_overview }}" alt="Síntesis Ejecutiva de Desempeño" class="rounded max-h-[520px] object-contain shadow-sm">
                </div>
                <p class="text-[11px] text-slate-500 text-center italic">Haga clic en la imagen para ampliar en alta definición.</p>
            </div>

            <!-- TABLA MAESTRA CONSOLIDADA: DATOS PRIMERO -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                        <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                            <span>📋 Tabla Maestra Consolidada: Los 42 Experimentos de Centroamérica</span>
                            <span class="bg-slate-100 text-slate-700 text-[10px] font-mono px-2 py-0.5 rounded border border-slate-300">42 Experimentos de Corrección</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar de forma ascendente o descendente.</p>
                    </div>
                    <input type="text" id="searchAll" onkeyup="filterTable('tableAll', 'searchAll')" placeholder="🔍 Filtrar experimento o variable..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white transition">
                </div>

                <div class="overflow-x-auto">
                    <table id="tableAll" class="data-table w-full text-xs">
                        <thead>
                            <tr>
                                <th class="sortable-th" onclick="sortTable('tableAll', 0, 'str')">Variable <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 1, 'num')">Rango <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 2, 'str')">ID Experimento <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 3, 'str')">Estado <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 4, 'num')">GSS <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 5, 'num')">KGE <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 6, 'num')">Pearson r <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 7, 'num')">RMSE <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 8, 'num')">MAE <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 9, 'num')">PBIAS (%) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableAll', 10, 'num')">Δ KGE vs Rejilla Original <span class="sort-icon">⇅</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in list_all %}
                            <tr class="{% if e.is_winner %}bg-emerald-50 text-emerald-950 font-bold{% elif e.is_control %}bg-slate-100 text-slate-800 font-semibold{% endif %}">
                                <td class="font-semibold uppercase text-sky-700">{{ e.variable }}</td>
                                <td>{{ e.rank }}</td>
                                <td class="font-mono text-left font-medium">{{ e.experiment_id }}</td>
                                <td>
                                    {% if e.is_winner %}
                                    <span class="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded border border-emerald-300 font-bold">GANADOR OFICIAL</span>
                                    {% elif "Baseline" in e.experiment_id %}
                                    <span class="bg-amber-100 text-amber-800 text-[10px] px-2 py-0.5 rounded border border-amber-300 font-bold">LÍNEA BASE 2D</span>
                                    {% elif e.is_control %}
                                    <span class="bg-slate-200 text-slate-700 text-[10px] px-2 py-0.5 rounded font-bold">REJILLA ORIGINAL</span>
                                    {% else %}
                                    <span class="text-slate-500 text-[10px]">Candidato</span>
                                    {% endif %}
                                </td>
                                <td>{{ "%.3f"|format(e.global_skill_score) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-700 font-bold{% elif e.delta_kge_raw < 0 %}text-rose-700{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 2: PRECIPITACIÓN DIARIA (CHIRPS) -->
        <!-- ========================================================================= -->
        <div id="tab-content-rainfall" class="tab-panel hidden space-y-8">
            
            <!-- Winner Highlight Card (Light Theme) -->
            {% if win_rain %}
            <div class="bg-gradient-to-r from-sky-50 via-white to-sky-50 border border-sky-300 rounded-xl p-6 shadow-sm relative overflow-hidden">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-sky-600 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Experimento Óptimo Seleccionado</span>
                            <span class="text-xs text-sky-800 font-mono font-bold">Rango #01 en Precipitación Diaria</span>
                        </div>
                        <h2 class="text-2xl font-black text-slate-900 tracking-tight">{{ win_rain.experiment_id }}</h2>
                        <p class="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">{{ win_rain.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-white rounded-lg p-3 border border-sky-200 text-center shadow-sm">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">GSS</div>
                            <div class="text-base font-bold text-sky-700">{{ "%.3f"|format(win_rain.global_skill_score) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">KGE</div>
                            <div class="text-base font-bold text-slate-900">{{ "%.3f"|format(win_rain.kge) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">Pearson r</div>
                            <div class="text-base font-bold text-slate-700">{{ "%.3f"|format(win_rain.r) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">RMSE</div>
                            <div class="text-base font-bold text-emerald-700">{{ "%.2f"|format(win_rain.rmse) }} <span class="text-[9px]">mm</span></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- 1. DATA FIRST: Master Table for Rainfall -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                        <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                            <span>📋 Tabla Maestra de Experimentos de Corrección: Precipitación Diaria</span>
                            <span class="bg-sky-100 text-sky-800 border border-sky-300 text-[10px] font-mono px-2 py-0.5 rounded">16 Experimentos de Corrección</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar ascendentemente o descendentemente.</p>
                    </div>
                    <input type="text" id="searchRain" onkeyup="filterTable('tableRain', 'searchRain')" placeholder="🔍 Filtrar experimento..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white transition">
                </div>

                <div class="overflow-x-auto">
                    <table id="tableRain" class="data-table w-full text-xs">
                        <thead>
                            <tr>
                                <th class="sortable-th" onclick="sortTable('tableRain', 0, 'num')">Rango <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 1, 'str')">ID Experimento <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 2, 'num')">GSS <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 3, 'num')">KGE Medio <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 4, 'num')">Pearson r <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 5, 'num')">RMSE (mm) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 6, 'num')">MAE (mm) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 7, 'num')">PBIAS (%) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 8, 'num')">ETS (Lluvia) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableRain', 9, 'num')">Δ KGE vs Rejilla Original <span class="sort-icon">⇅</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in list_rain %}
                            <tr class="{% if e.is_winner %}bg-emerald-50 text-emerald-950 font-bold{% elif e.is_control %}bg-slate-100 text-slate-800 font-semibold{% endif %}">
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }} [Ganador Físico]{% elif "Baseline" in e.experiment_id %}📐 #{{ e.rank }} [Línea Base]{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono text-left font-medium">{{ e.experiment_id }}</td>
                                <td>{{ "%.3f"|format(e.global_skill_score) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td>{{ "%.3f"|format(e.ets) if e.ets is defined and e.ets is not none and e.ets == e.ets else "-" }}</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-700 font-bold{% elif e.delta_kge_raw < 0 %}text-rose-700{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }} ({{ "%+.1f"|format(e.pct_kge_gain) }}%)
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- 2. GALERÍA DE FIGURAS ESTÁTICAS DE ALTA RESOLUCIÓN (300 DPI) -->
            <div class="space-y-4">
                <div class="border-b border-slate-200 pb-2 flex justify-between items-center">
                    <h3 class="text-base font-bold text-slate-900 flex items-center gap-2">
                        <span>🖼️ Galería Diagnóstica de Figuras de Publicación (300 DPI)</span>
                    </h3>
                    <span class="text-xs bg-slate-100 text-slate-700 px-2.5 py-1 rounded border border-slate-300 font-medium">PNG Alta Definición</span>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Fig 1: Boxplots -->
                    <div class="fig-card">
                        <div>
                            <div class="text-[10px] font-bold text-sky-700 uppercase tracking-wider mb-1">Figura 1 • Dispersión</div>
                            <h4 class="font-bold text-sm text-slate-900">Distribución de Eficiencia KGE en las 29 Estaciones Holdout</h4>
                            <p class="text-xs text-slate-600 mt-1">Cajas muestran percentiles 25–75, línea central la mediana. Línea discontinua indica la Rejilla Original [00].</p>
                        </div>
                        <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.kge_boxplots }}', 'Figura 1: Boxplots de KGE por Estación (Precipitación)')">
                            <img src="{{ fig_rain.kge_boxplots }}" alt="Boxplots KGE Lluvia" class="max-h-72 object-contain w-full">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • Holdout Ciego</span>
                            <a href="{{ fig_rain.kge_boxplots }}" download class="text-xs bg-slate-100 hover:bg-sky-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>

                    <!-- Fig 2: Scatter Pareto (Clean, no arrow/labels) -->
                    <div class="fig-card">
                        <div>
                            <div class="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">Figura 2 • Frontera Pareto</div>
                            <h4 class="font-bold text-sm text-slate-900">Espacio de Precisión: Error (RMSE) vs. Eficiencia (KGE)</h4>
                            <p class="text-xs text-slate-600 mt-1">El experimento óptimo se ubica en el extremo superior izquierdo (mínimo error y máxima habilidad). Identificación en leyenda.</p>
                        </div>
                        <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.pareto }}', 'Figura 2: Scatter Pareto KGE vs. RMSE (Precipitación)')">
                            <img src="{{ fig_rain.pareto }}" alt="Scatter Pareto Lluvia" class="max-h-72 object-contain w-full">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • Bi-Criterio</span>
                            <a href="{{ fig_rain.pareto }}" download class="text-xs bg-slate-100 hover:bg-emerald-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>

                    <!-- Fig 3: Barras Divergentes Δ KGE -->
                    <div class="fig-card">
                        <div>
                            <div class="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">Figura 3 • Ganancia Neta</div>
                            <h4 class="font-bold text-sm text-slate-900">Ganancia Neta (Δ KGE) respecto a la Rejilla Original [CHIRPS 00]</h4>
                            <p class="text-xs text-slate-600 mt-1">CHIRPS Rejilla Original = 0.0 de referencia. Barras verdes indican mejora sobre el dato original; barras rojas degradación.</p>
                        </div>
                        <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.divergent }}', 'Figura 3: Barras Divergentes Δ KGE (Precipitación)')">
                            <img src="{{ fig_rain.divergent }}" alt="Barras Divergentes Lluvia" class="max-h-72 object-contain w-full">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • Ganancia Neta</span>
                            <a href="{{ fig_rain.divergent }}" download class="text-xs bg-slate-100 hover:bg-emerald-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>

                    <!-- Fig 4: Matriz Heatmap con Control 00 (RdYlGn) -->
                    <div class="fig-card">
                        <div>
                            <div class="text-[10px] font-bold text-amber-700 uppercase tracking-wider mb-1">Figura 4 • Síntesis Multicriterio</div>
                            <h4 class="font-bold text-sm text-slate-900">Matriz Diagnóstica de Rendimiento Climatológico</h4>
                            <p class="text-xs text-slate-600 mt-1">Cuadrícula con valores numéricos impresos para todos los experimentos de corrección. Escala de color: Verde (Óptimo) a Rojo (Deficiente).</p>
                        </div>
                        <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.heatmap }}', 'Figura 4: Matriz Heatmap Multimétrica (Precipitación)')">
                            <img src="{{ fig_rain.heatmap }}" alt="Heatmap Multimétrica Lluvia" class="max-h-72 object-contain w-full">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • RdYlGn</span>
                            <a href="{{ fig_rain.heatmap }}" download class="text-xs bg-slate-100 hover:bg-amber-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>

                    <!-- Fig 5: Mapa Espacial Cartopy (Full Map with Lat/Lon) -->
                    <div class="fig-card">
                        <div>
                            <div class="text-[10px] font-bold text-sky-700 uppercase tracking-wider mb-1">Figura 5 • Geografía Regional</div>
                            <h4 class="font-bold text-sm text-slate-900">Distribución Espacial de la Ganancia Neta (Δ KGE) en Centroamérica</h4>
                            <p class="text-xs text-slate-600 mt-1">Mapa geográfico completo con fronteras, costas y coordenadas Lat/Lon explícitas. Puntos limpios coloreados por ganancia.</p>
                        </div>
                        <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.map }}', 'Figura 5: Mapa Espacial Regional de Ganancia (Precipitación)')">
                            <img src="{{ fig_rain.map }}" alt="Mapa Espacial Lluvia" class="max-h-72 object-contain w-full">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • Cartopy GIS</span>
                            <a href="{{ fig_rain.map }}" download class="text-xs bg-slate-100 hover:bg-sky-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>

                    <!-- Fig 6: Estratos de Elevación -->
                    <div class="fig-card">
                        <div>
                            <div class="text-[10px] font-bold text-violet-700 uppercase tracking-wider mb-1">Figura 6 • Orografía</div>
                            <h4 class="font-bold text-sm text-slate-900">Rendimiento por Estratos Topográficos de Elevación</h4>
                            <p class="text-xs text-slate-600 mt-1">Evaluación estratificada (Costas &lt;200m, Valles 200–800m, Montañas &gt;800m) comparando Rejilla Original vs. Ganador.</p>
                        </div>
                        <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.strata }}', 'Figura 6: Estratos de Elevación (Precipitación)')">
                            <img src="{{ fig_rain.strata }}" alt="Estratos Elevación Lluvia" class="max-h-72 object-contain w-full">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • Topografía</span>
                            <a href="{{ fig_rain.strata }}" download class="text-xs bg-slate-100 hover:bg-violet-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>

                    <!-- Fig 7: Taylor Polar Diagram (Span 2) -->
                    <div class="fig-card lg:col-span-2">
                        <div>
                            <div class="text-[10px] font-bold text-rose-700 uppercase tracking-wider mb-1">Figura 7 • Espacio Polar</div>
                            <h4 class="font-bold text-sm text-slate-900">Diagrama Polar Clásico de Taylor: Precipitación Diaria</h4>
                            <p class="text-xs text-slate-600 mt-1">Experimento óptimo claramente destacado con llamada y aureola dorada. Eje base explicativo de RMSE y ángulo de correlación en 2 líneas.</p>
                        </div>
                        <div class="mt-3 cursor-pointer flex justify-center bg-slate-50 p-3 rounded-lg border border-slate-200" onclick="openModal('{{ fig_rain.taylor }}', 'Figura 7: Diagrama Polar de Taylor (Precipitación)')">
                            <img src="{{ fig_rain.taylor }}" alt="Taylor Diagram Lluvia" class="max-h-84 object-contain">
                        </div>
                        <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                            <span class="text-[10px] text-slate-500 font-mono">300 DPI • Taylor (2001)</span>
                            <a href="{{ fig_rain.taylor }}" download class="text-xs bg-slate-100 hover:bg-rose-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                        </div>
                    </div>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 3: TEMPERATURA MÁXIMA (CHIRTS) -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmax" class="tab-panel hidden space-y-8">
            
            {% if win_tmax %}
            <div class="bg-gradient-to-r from-amber-50 via-white to-amber-50 border border-amber-300 rounded-xl p-6 shadow-sm relative overflow-hidden">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-amber-600 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Experimento Óptimo Seleccionado</span>
                            <span class="text-xs text-amber-800 font-mono font-bold">Rango #01 en Temp. Máxima</span>
                        </div>
                        <h2 class="text-2xl font-black text-slate-900 tracking-tight">{{ win_tmax.experiment_id }}</h2>
                        <p class="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">{{ win_tmax.description }}</p>
                        <div class="mt-3 inline-block bg-emerald-100 text-emerald-900 text-[11px] font-bold px-3 py-1 rounded border border-emerald-300">
                            ✓ Ganador Físico Oficial de CDT • Validación Topográfica Ciega en 29 Estaciones
                        </div>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-white rounded-lg p-3 border border-amber-200 text-center shadow-sm">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">GSS</div>
                            <div class="text-base font-bold text-amber-700">{{ "%.3f"|format(win_tmax.global_skill_score) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">KGE</div>
                            <div class="text-base font-bold text-slate-900">{{ "%.3f"|format(win_tmax.kge) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">Pearson r</div>
                            <div class="text-base font-bold text-slate-700">{{ "%.3f"|format(win_tmax.r) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">RMSE</div>
                            <div class="text-base font-bold text-emerald-700">{{ "%.2f"|format(win_tmax.rmse) }} <span class="text-[9px]">°C</span></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Nota Metodológica de Selección de Ganador -->
            <div class="bg-amber-50/80 border-l-4 border-amber-500 p-4 rounded-r-xl text-xs text-amber-950 space-y-1.5 shadow-sm">
                <div class="flex items-center gap-2 font-bold text-amber-900">
                    <span>⚠️</span>
                    <span>Dictamen Metodológico sobre la Línea Base vs. Experimento Ganador en Temperatura Máxima</span>
                </div>
                <p class="leading-relaxed">
                    Aunque la línea base plana bidimensional (<code class="bg-white/80 px-1 py-0.5 rounded font-mono font-bold text-slate-800">EXP_TX01_SBA_IDW_Baseline</code>) reporta un puntaje estadístico puntual alto en estaciones de validación debido a que la gran mayoría de estaciones meteorológicas se encuentran en valles y planicies bajas, <b>carece de acoplamiento orográfico con el DEM continental</b>. En terrenos montañosos no monitoreados (Sierra Madre, Cordillera de Talamanca, Cordillera Central de RD), este método genera un severo <i>aplanamiento orográfico</i> (+4 a +8 °C de sobreestimación artificial en cumbres). Conforme a las conclusiones del Documento 10, <code class="bg-white/80 px-1 py-0.5 rounded font-mono font-bold text-slate-800">EXP_TX01</code> fue rechazado como producto operativo y <b><code class="bg-emerald-100 text-emerald-950 px-1.5 py-0.5 rounded font-mono font-bold border border-emerald-300">EXP_TX11_RK_Barnes_Hybrid</code></b> es adoptado como el <b>Ganador Físico Oficial</b>.
                </p>
            </div>

            <!-- Table for Tmax -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                        <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                            <span>📋 Tabla Maestra de Experimentos de Corrección: Temperatura Máxima</span>
                            <span class="bg-amber-100 text-amber-800 border border-amber-300 text-[10px] font-mono px-2 py-0.5 rounded">13 Experimentos de Corrección</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar ascendentemente o descendentemente.</p>
                    </div>
                    <input type="text" id="searchTmax" onkeyup="filterTable('tableTmax', 'searchTmax')" placeholder="🔍 Filtrar experimento..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-amber-500 focus:bg-white transition">
                </div>

                <div class="overflow-x-auto">
                    <table id="tableTmax" class="data-table w-full text-xs">
                        <thead>
                            <tr>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 0, 'num')">Rango <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 1, 'str')">ID Experimento <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 2, 'num')">GSS <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 3, 'num')">KGE Medio <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 4, 'num')">Pearson r <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 5, 'num')">RMSE (°C) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 6, 'num')">MAE (°C) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 7, 'num')">PBIAS (%) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmax', 8, 'num')">Δ KGE vs Rejilla Original <span class="sort-icon">⇅</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in list_tmax %}
                            <tr class="{% if e.is_winner %}bg-emerald-50 text-emerald-950 font-bold{% elif e.is_control %}bg-slate-100 text-slate-800 font-semibold{% endif %}">
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }} [Ganador Físico]{% elif "Baseline" in e.experiment_id %}📐 #{{ e.rank }} [Línea Base]{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono text-left font-medium">{{ e.experiment_id }}</td>
                                <td>{{ "%.3f"|format(e.global_skill_score) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-700 font-bold{% elif e.delta_kge_raw < 0 %}text-rose-700{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }} ({{ "%+.1f"|format(e.pct_kge_gain) }}%)
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Static Figures Grid for Tmax -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-amber-700 uppercase tracking-wider mb-1">Figura 1 • Dispersión</div>
                        <h4 class="font-bold text-sm text-slate-900">Distribución de KGE en Estaciones (Temp. Máxima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Dispersión de eficiencia en las 29 estaciones para los 13 experimentos de corrección de temperatura máxima.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.kge_boxplots }}', 'Figura 1: Boxplots de KGE (Temp. Máxima)')">
                        <img src="{{ fig_tmax.kge_boxplots }}" alt="Boxplots Tmax" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmax.kge_boxplots }}" download class="text-xs bg-slate-100 hover:bg-amber-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">Figura 2 • Pareto</div>
                        <h4 class="font-bold text-sm text-slate-900">Espacio de Precisión: RMSE vs. KGE (Temp. Máxima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Convergencia de experimentos hacia el óptimo en temperatura máxima.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.pareto }}', 'Figura 2: Scatter Pareto (Temp. Máxima)')">
                        <img src="{{ fig_tmax.pareto }}" alt="Scatter Pareto Tmax" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmax.pareto }}" download class="text-xs bg-slate-100 hover:bg-emerald-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-amber-700 uppercase tracking-wider mb-1">Figura 3 • Ganancia Neta</div>
                        <h4 class="font-bold text-sm text-slate-900">Ganancia Neta (Δ KGE) vs. Rejilla Original [TX00]</h4>
                        <p class="text-xs text-slate-600 mt-1">Comparación directa frente a la rejilla original sin corrección.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.divergent }}', 'Figura 3: Barras Divergentes Δ KGE (Temp. Máxima)')">
                        <img src="{{ fig_tmax.divergent }}" alt="Barras Divergentes Tmax" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmax.divergent }}" download class="text-xs bg-slate-100 hover:bg-amber-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-amber-700 uppercase tracking-wider mb-1">Figura 4 • Heatmap</div>
                        <h4 class="font-bold text-sm text-slate-900">Matriz Multicriterio de Desempeño (Temp. Máxima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Matriz con valores exactos impresos en escala Verde a Rojo.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.heatmap }}', 'Figura 4: Heatmap Multimétrica (Temp. Máxima)')">
                        <img src="{{ fig_tmax.heatmap }}" alt="Heatmap Tmax" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI • RdYlGn</span>
                        <a href="{{ fig_tmax.heatmap }}" download class="text-xs bg-slate-100 hover:bg-amber-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-sky-700 uppercase tracking-wider mb-1">Figura 5 • Geografía</div>
                        <h4 class="font-bold text-sm text-slate-900">Distribución Espacial de la Ganancia en Centroamérica</h4>
                        <p class="text-xs text-slate-600 mt-1">Mapa geográfico completo con coordenadas Lat/Lon y fronteras.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.map }}', 'Figura 5: Mapa Espacial Regional (Temp. Máxima)')">
                        <img src="{{ fig_tmax.map }}" alt="Mapa Espacial Tmax" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmax.map }}" download class="text-xs bg-slate-100 hover:bg-sky-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-violet-700 uppercase tracking-wider mb-1">Figura 6 • Orografía</div>
                        <h4 class="font-bold text-sm text-slate-900">Rendimiento por Estratos de Elevación (Temp. Máxima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Comportamiento en costas (&lt;200m), valles (200–800m) y montañas (&gt;800m).</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.strata }}', 'Figura 6: Estratos Elevación (Temp. Máxima)')">
                        <img src="{{ fig_tmax.strata }}" alt="Estratos Tmax" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmax.strata }}" download class="text-xs bg-slate-100 hover:bg-violet-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <!-- Fig 7: Taylor Tmax (Span 2) -->
                <div class="fig-card lg:col-span-2">
                    <div>
                        <div class="text-[10px] font-bold text-rose-700 uppercase tracking-wider mb-1">Figura 7 • Espacio Polar</div>
                        <h4 class="font-bold text-sm text-slate-900">Diagrama Polar Clásico de Taylor: Temperatura Máxima</h4>
                        <p class="text-xs text-slate-600 mt-1">Experimento óptimo claramente destacado con llamada y aureola dorada.</p>
                    </div>
                    <div class="mt-3 cursor-pointer flex justify-center bg-slate-50 p-3 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmax.taylor }}', 'Figura 7: Diagrama Polar de Taylor (Temp. Máxima)')">
                        <img src="{{ fig_tmax.taylor }}" alt="Taylor Diagram Tmax" class="max-h-84 object-contain">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI • Taylor (2001)</span>
                        <a href="{{ fig_tmax.taylor }}" download class="text-xs bg-slate-100 hover:bg-rose-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 4: TEMPERATURA MÍNIMA (CHIRTS) -->
        <!-- ========================================================================= -->
        <div id="tab-content-tmin" class="tab-panel hidden space-y-8">
            
            {% if win_tmin %}
            <div class="bg-gradient-to-r from-violet-50 via-white to-violet-50 border border-violet-300 rounded-xl p-6 shadow-sm relative overflow-hidden">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 relative z-10">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-violet-600 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Experimento Óptimo Seleccionado</span>
                            <span class="text-xs text-violet-800 font-mono font-bold">Rango #01 en Temp. Mínima</span>
                        </div>
                        <h2 class="text-2xl font-black text-slate-900 tracking-tight">{{ win_tmin.experiment_id }}</h2>
                        <p class="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">{{ win_tmin.description }}</p>
                    </div>
                    <div class="grid grid-cols-4 gap-3 bg-white rounded-lg p-3 border border-violet-200 text-center shadow-sm">
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">GSS</div>
                            <div class="text-base font-bold text-violet-700">{{ "%.3f"|format(win_tmin.global_skill_score) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">KGE</div>
                            <div class="text-base font-bold text-slate-900">{{ "%.3f"|format(win_tmin.kge) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">Pearson r</div>
                            <div class="text-base font-bold text-slate-700">{{ "%.3f"|format(win_tmin.r) }}</div>
                        </div>
                        <div class="px-2">
                            <div class="text-[10px] uppercase text-slate-500 font-semibold">RMSE</div>
                            <div class="text-base font-bold text-emerald-700">{{ "%.2f"|format(win_tmin.rmse) }} <span class="text-[9px]">°C</span></div>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Table for Tmin -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                        <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                            <span>📋 Tabla Maestra de Experimentos de Corrección: Temperatura Mínima</span>
                            <span class="bg-violet-100 text-violet-800 border border-violet-300 text-[10px] font-mono px-2 py-0.5 rounded">13 Experimentos de Corrección</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar ascendentemente o descendentemente.</p>
                    </div>
                    <input type="text" id="searchTmin" onkeyup="filterTable('tableTmin', 'searchTmin')" placeholder="🔍 Filtrar experimento..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-violet-500 focus:bg-white transition">
                </div>

                <div class="overflow-x-auto">
                    <table id="tableTmin" class="data-table w-full text-xs">
                        <thead>
                            <tr>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 0, 'num')">Rango <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 1, 'str')">ID Experimento <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 2, 'num')">GSS <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 3, 'num')">KGE Medio <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 4, 'num')">Pearson r <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 5, 'num')">RMSE (°C) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 6, 'num')">MAE (°C) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 7, 'num')">PBIAS (%) <span class="sort-icon">⇅</span></th>
                                <th class="sortable-th" onclick="sortTable('tableTmin', 8, 'num')">Δ KGE vs Rejilla Original <span class="sort-icon">⇅</span></th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for e in list_tmin %}
                            <tr class="{% if e.is_winner %}bg-emerald-50 text-emerald-950 font-bold{% elif e.is_control %}bg-slate-100 text-slate-800 font-semibold{% endif %}">
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }} [Ganador Físico]{% elif "Baseline" in e.experiment_id %}📐 #{{ e.rank }} [Línea Base]{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
                                <td class="font-mono text-left font-medium">{{ e.experiment_id }}</td>
                                <td>{{ "%.3f"|format(e.global_skill_score) }}</td>
                                <td>{{ "%.3f"|format(e.kge) }}</td>
                                <td>{{ "%.3f"|format(e.r) }}</td>
                                <td>{{ "%.2f"|format(e.rmse) }}</td>
                                <td>{{ "%.2f"|format(e.mae) }}</td>
                                <td>{{ "%+.1f"|format(e.pbias) }}%</td>
                                <td class="{% if e.delta_kge_raw > 0 %}text-emerald-700 font-bold{% elif e.delta_kge_raw < 0 %}text-rose-700{% else %}text-slate-500{% endif %}">
                                    {{ "%+.3f"|format(e.delta_kge_raw) }} ({{ "%+.1f"|format(e.pct_kge_gain) }}%)
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Static Figures Grid for Tmin -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-violet-700 uppercase tracking-wider mb-1">Figura 1 • Dispersión</div>
                        <h4 class="font-bold text-sm text-slate-900">Distribución de KGE en Estaciones (Temp. Mínima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Dispersión de eficiencia en las 29 estaciones holdout para los 13 experimentos de corrección de temperatura mínima.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.kge_boxplots }}', 'Figura 1: Boxplots de KGE (Temp. Mínima)')">
                        <img src="{{ fig_tmin.kge_boxplots }}" alt="Boxplots Tmin" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmin.kge_boxplots }}" download class="text-xs bg-slate-100 hover:bg-violet-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-emerald-700 uppercase tracking-wider mb-1">Figura 2 • Pareto</div>
                        <h4 class="font-bold text-sm text-slate-900">Espacio de Precisión: RMSE vs. KGE (Temp. Mínima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Frontera de Pareto destacando a Empirical ECDF frente a la rejilla original.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.pareto }}', 'Figura 2: Scatter Pareto (Temp. Mínima)')">
                        <img src="{{ fig_tmin.pareto }}" alt="Scatter Pareto Tmin" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmin.pareto }}" download class="text-xs bg-slate-100 hover:bg-emerald-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-violet-700 uppercase tracking-wider mb-1">Figura 3 • Ganancia Neta</div>
                        <h4 class="font-bold text-sm text-slate-900">Ganancia Neta (Δ KGE) vs. Rejilla Original [TN00]</h4>
                        <p class="text-xs text-slate-600 mt-1">Mejora neta sobre la rejilla original en temperatura mínima.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.divergent }}', 'Figura 3: Barras Divergentes Δ KGE (Temp. Mínima)')">
                        <img src="{{ fig_tmin.divergent }}" alt="Barras Divergentes Tmin" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmin.divergent }}" download class="text-xs bg-slate-100 hover:bg-violet-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-violet-700 uppercase tracking-wider mb-1">Figura 4 • Heatmap</div>
                        <h4 class="font-bold text-sm text-slate-900">Matriz Multicriterio de Desempeño (Temp. Mínima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Matriz con valores exactos impresos en escala Verde a Rojo.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.heatmap }}', 'Figura 4: Heatmap Multimétrica (Temp. Mínima)')">
                        <img src="{{ fig_tmin.heatmap }}" alt="Heatmap Tmin" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI • RdYlGn</span>
                        <a href="{{ fig_tmin.heatmap }}" download class="text-xs bg-slate-100 hover:bg-violet-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-sky-700 uppercase tracking-wider mb-1">Figura 5 • Geografía</div>
                        <h4 class="font-bold text-sm text-slate-900">Distribución Espacial de la Ganancia en Centroamérica</h4>
                        <p class="text-xs text-slate-600 mt-1">Mapa geográfico completo con coordenadas Lat/Lon y fronteras.</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.map }}', 'Figura 5: Mapa Espacial Regional (Temp. Mínima)')">
                        <img src="{{ fig_tmin.map }}" alt="Mapa Espacial Tmin" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmin.map }}" download class="text-xs bg-slate-100 hover:bg-sky-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <div class="fig-card">
                    <div>
                        <div class="text-[10px] font-bold text-violet-700 uppercase tracking-wider mb-1">Figura 6 • Orografía</div>
                        <h4 class="font-bold text-sm text-slate-900">Rendimiento por Estratos de Elevación (Temp. Mínima)</h4>
                        <p class="text-xs text-slate-600 mt-1">Comportamiento en costas (&lt;200m), valles (200–800m) y montañas (&gt;800m).</p>
                    </div>
                    <div class="mt-3 cursor-pointer bg-slate-50 p-2 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.strata }}', 'Figura 6: Estratos Elevación (Temp. Mínima)')">
                        <img src="{{ fig_tmin.strata }}" alt="Estratos Tmin" class="max-h-72 object-contain w-full">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI</span>
                        <a href="{{ fig_tmin.strata }}" download class="text-xs bg-slate-100 hover:bg-violet-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>

                <!-- Fig 7: Taylor Tmin (Span 2) -->
                <div class="fig-card lg:col-span-2">
                    <div>
                        <div class="text-[10px] font-bold text-rose-700 uppercase tracking-wider mb-1">Figura 7 • Espacio Polar</div>
                        <h4 class="font-bold text-sm text-slate-900">Diagrama Polar Clásico de Taylor: Temperatura Mínima</h4>
                        <p class="text-xs text-slate-600 mt-1">Experimento óptimo claramente destacado con llamada y aureola dorada.</p>
                    </div>
                    <div class="mt-3 cursor-pointer flex justify-center bg-slate-50 p-3 rounded-lg border border-slate-200" onclick="openModal('{{ fig_tmin.taylor }}', 'Figura 7: Diagrama Polar de Taylor (Temp. Mínima)')">
                        <img src="{{ fig_tmin.taylor }}" alt="Taylor Diagram Tmin" class="max-h-84 object-contain">
                    </div>
                    <div class="mt-3 pt-2 border-t border-slate-100 flex justify-between items-center">
                        <span class="text-[10px] text-slate-500 font-mono">300 DPI • Taylor (2001)</span>
                        <a href="{{ fig_tmin.taylor }}" download class="text-xs bg-slate-100 hover:bg-rose-600 hover:text-white text-slate-700 px-3 py-1.5 rounded transition font-medium border border-slate-300">📥 Descargar</a>
                    </div>
                </div>
            </div>

        </div>

        <!-- ========================================================================= -->
        <!-- TAB 5: GUÍA METODOLÓGICA COMPLETA DE EVALUACIÓN Y VALIDACIÓN (DOCUMENTO 12) -->
        <!-- ========================================================================= -->
        <div id="tab-content-glossary" class="tab-panel hidden space-y-8">
            
            <!-- Document Header Banner -->
            <div class="bg-gradient-to-r from-sky-50 via-white to-sky-50 border border-sky-300 rounded-xl p-6 shadow-sm">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <div class="flex items-center gap-2 mb-1">
                            <span class="bg-sky-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Manual Técnico Integrado</span>
                            <span class="text-xs text-sky-800 font-mono font-bold">Documento Oficial 12</span>
                        </div>
                        <h2 class="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">Metodología de Evaluación Estadística, Métricas y Validación Cruzada en CDT 8.0</h2>
                        <p class="text-xs text-slate-600 max-w-3xl mt-1 leading-relaxed">
                            Marco metodológico, formulaciones matemáticas rigurosas e interpretación física de las métricas estadísticas implementadas para la validación ciega de los experimentos de corrección de precipitación y temperatura en América Central y República Dominicana (1991–2020).
                        </p>
                    </div>
                    <div class="flex items-center gap-2 bg-white px-3 py-2 rounded-lg border border-sky-200 shadow-sm text-xs text-slate-700">
                        <span class="text-emerald-600 font-bold">✓ 29 Estaciones Holdout</span>
                        <span class="text-slate-300">|</span>
                        <span class="text-sky-600 font-bold">30 Años (10,958 Días)</span>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 1: ESQUEMA DE VALIDACIÓN -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="border-b border-slate-100 pb-3">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 1</span>
                    <h3 class="text-base font-bold text-slate-900">1. Esquema de Validación Cruzada Ciega (Holdout Validation)</h3>
                </div>
                <p class="text-xs text-slate-600 leading-relaxed">
                    Para garantizar una evaluación científica imparcial, reproducible y evitar el sobreajuste (<i>overfitting</i> o memorización de datos), el pipeline implementa una partición estricta de las redes de estaciones meteorológicas:
                </p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 my-3">
                    <div class="bg-slate-50 border border-slate-200 p-4 rounded-lg">
                        <div class="font-bold text-xs text-slate-800 flex items-center gap-1.5 mb-1">
                            <span class="text-sky-600">●</span> Estaciones de Entrenamiento (Training Stations)
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Utilizadas activamente por CDT para el cálculo de coeficientes de sesgo (<i>bias coefficients</i>), regresiones multivariadas contra el DEM y la fusión espacial (<i>merging</i>).
                        </p>
                    </div>
                    <div class="bg-sky-50 border border-sky-200 p-4 rounded-lg">
                        <div class="font-bold text-xs text-sky-900 flex items-center gap-1.5 mb-1">
                            <span class="text-emerald-600">★</span> Estaciones de Validación Ciega (Holdout Stations)
                        </div>
                        <p class="text-[11px] text-sky-800 leading-relaxed">
                            Estaciones reservadas que <b>nunca intervienen</b> en ninguna fase del ajuste de sesgo ni de la interpolación. La grilla reconstruida se evalúa a ciegas contra estas estaciones.
                        </p>
                    </div>
                </div>

                <div class="overflow-x-auto mt-4">
                    <table class="data-table w-full text-xs">
                        <thead>
                            <tr>
                                <th>Variable Climática</th>
                                <th>Total Red de Superficie</th>
                                <th>Estaciones de Entrenamiento</th>
                                <th>Estaciones Holdout (Ciegas)</th>
                                <th>Porcentaje de Reserva</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="font-semibold text-slate-800">Precipitación Diaria (CHIRPS)</td>
                                <td>266</td>
                                <td>237</td>
                                <td class="font-bold text-sky-700">29</td>
                                <td>~11%</td>
                            </tr>
                            <tr>
                                <td class="font-semibold text-slate-800">Temperatura Máxima (CHIRTS)</td>
                                <td>266</td>
                                <td>237</td>
                                <td class="font-bold text-amber-700">29</td>
                                <td>~11%</td>
                            </tr>
                            <tr>
                                <td class="font-semibold text-slate-800">Temperatura Mínima (CHIRTS)</td>
                                <td>266</td>
                                <td>237</td>
                                <td class="font-bold text-purple-700">29</td>
                                <td>~11%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="bg-slate-50 border-l-4 border-sky-500 p-3 rounded-r text-xs text-slate-700 mt-2">
                    <b>Criterios Geográficos de Representatividad:</b> Las 29 estaciones de validación cubren sistemáticamente: (1) Vertientes contrastantes Pacífico vs. Mar Caribe / Golfo de México; (2) Gradientes altitudinales desde el nivel del mar (0 m) hasta alta montaña (>2,000 msnm); (3) Regímenes del Corredor Seco Centroamericano (<i>Dry Corridor</i>) y selvas tropicales húmedas.
                </div>
            </div>

            <!-- SECCIÓN 2: NIVELES DE CÁLCULO PUNTUAL VS REGIONAL -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="border-b border-slate-100 pb-3">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 2</span>
                    <h3 class="text-base font-bold text-slate-900">2. Niveles de Cálculo: Puntual vs. Agregación Regional</h3>
                </div>
                <p class="text-xs text-slate-600 leading-relaxed">
                    Una consulta fundamental en la auditoría climatológica es cómo se calculan las métricas y si el resultado reportado es un promedio por estación o una evaluación agregada:
                </p>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 my-2">
                    <div class="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-xs text-slate-900">Nivel 1: Métricas Puntuales por Estación</span>
                            <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">validation_metrics_by_station.csv</span>
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Para cada una de las 29 estaciones independientes ($i = 1, \dots, 29$), se extrae la serie temporal diaria de la celda de la grilla más cercana ($S_{i,t}$) y se compara directamente contra la serie observada en superficie ($O_{i,t}$) durante los 10,958 días del periodo 1991–2020. Todas las fórmulas estadísticas (KGE, RMSE, MAE, r, PBIAS, ETS, HSS) se evalúan <b>primero de forma individual e independiente en cada estación</b>.
                        </p>
                    </div>

                    <div class="border border-sky-200 rounded-lg p-4 bg-sky-50/40 space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="font-bold text-xs text-sky-950">Nivel 2: Agregación Regional Centroamericana</span>
                            <span class="text-[10px] bg-sky-200 text-sky-800 px-2 py-0.5 rounded font-mono">Leaderboard & Resumen</span>
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            El valor escalar que figura en la tabla principal de cada experimento representa el <b>promedio aritmético regional</b> de las 29 estaciones:
                        </p>
                        <div class="bg-white p-2 rounded border border-sky-200 text-center font-mono text-xs text-sky-900 my-1">
                            $$\overline{M} = \frac{1}{N} \sum_{i=1}^{N} M_i \quad (N = 29)$$
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Para evaluar la dispersión geográfica (si la corrección funciona homogéneamente en toda Centroamérica o solo en algunas estaciones), se emplean los <b>diagramas de caja y bigotes (Boxplots, Figura 1)</b> y la <b>mediana regional</b>.
                        </p>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 3: FORMULACIÓN MATEMÁTICA DE MÉTRICAS CONTINUAS -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-6">
                <div class="border-b border-slate-100 pb-3">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 3</span>
                    <h3 class="text-base font-bold text-slate-900">3. Formulación Matemática de las Métricas Continuas</h3>
                </div>

                <!-- KGE Detailed -->
                <div class="border border-sky-200 rounded-xl p-5 bg-sky-50/20 space-y-3">
                    <div class="flex items-center justify-between">
                        <h4 class="font-bold text-sm text-sky-950">3.1. Eficiencia de Kling-Gupta (KGE, Gupta et al. 2009; Kling et al. 2012)</h4>
                        <span class="text-[10px] bg-sky-600 text-white font-bold px-2 py-0.5 rounded">Métrica Primaria de Optimización</span>
                    </div>
                    <p class="text-xs text-slate-700 leading-relaxed">
                        Es el índice integrador estándar en hidroclimatología. A diferencia del Nash-Sutcliffe (NSE), el KGE descompone el error cuadrático medio en tres componentes físicamente ortogonales e independientes (correlación, sesgo medio y dispersión relativa):
                    </p>
                    <div class="bg-white p-3 rounded-lg border border-sky-200 text-center text-sm font-mono text-sky-900 shadow-sm">
                        $$\text{KGE} = 1 - \sqrt{(r - 1)^2 + (\beta - 1)^2 + (\gamma - 1)^2}$$
                    </div>
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                        <div class="bg-white p-3 rounded border border-slate-200 space-y-1">
                            <span class="font-bold text-slate-800">1. Correlación de Pearson ($r$):</span>
                            <div class="font-mono text-[11px] text-slate-700">$$r = \frac{\sum (O_t - \mu_o)(S_t - \mu_s)}{\sqrt{\sum (O_t - \mu_o)^2 \sum (S_t - \mu_s)^2}}$$</div>
                            <p class="text-[11px] text-slate-500">Mide la sincronía temporal y el ciclo estacional.</p>
                        </div>
                        <div class="bg-white p-3 rounded border border-slate-200 space-y-1">
                            <span class="font-bold text-slate-800">2. Razón de Sesgo ($\beta$):</span>
                            <div class="font-mono text-[11px] text-slate-700">$$\beta = \frac{\mu_s}{\mu_o}$$</div>
                            <p class="text-[11px] text-slate-500">Evalúa la conservación de la media observada (óptimo = 1.0).</p>
                        </div>
                        <div class="bg-white p-3 rounded border border-slate-200 space-y-1">
                            <span class="font-bold text-slate-800">3. Razón de Dispersión ($\gamma$):</span>
                            <div class="font-mono text-[11px] text-slate-700">$$\gamma = \frac{\text{CV}_s}{\text{CV}_o} = \frac{\sigma_s / \mu_s}{\sigma_o / \mu_o}$$</div>
                            <p class="text-[11px] text-slate-500">Mide la variabilidad relativa sin confundirla con el sesgo.</p>
                        </div>
                    </div>
                    <div class="bg-white p-3 rounded border border-sky-200 text-[11px] text-slate-600 space-y-1">
                        <div>• <b>Interpretación:</b> $\text{KGE} = 1.0$ (concordancia perfecta); $\text{KGE} &gt; 0.30$ (habilidad diagnóstica superior al promedio climatológico en series diarias out-of-sample); $\text{KGE} &lt; -0.41$ (el promedio histórico observado supera en habilidad a la grilla).</div>
                    </div>
                </div>

                <!-- Grid for RMSE, MAE, PBIAS, r -->
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <!-- RMSE -->
                    <div class="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                        <div class="flex items-center justify-between">
                            <h4 class="font-bold text-xs text-slate-900">3.2. Raíz del Error Cuadrático Medio (RMSE)</h4>
                            <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">mm/día o °C</span>
                        </div>
                        <div class="bg-white p-2.5 rounded border border-slate-200 text-center text-xs font-mono text-slate-800">
                            $$\text{RMSE} = \sqrt{\frac{1}{T} \sum_{t=1}^T (S_t - O_t)^2}$$
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Cuantifica la magnitud absoluta del error promedio, penalizando cuadráticamente los errores de gran magnitud. Sensible a eventos meteorológicos extremos (tormentas tropicales y olas de calor).
                        </p>
                    </div>

                    <!-- MAE -->
                    <div class="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                        <div class="flex items-center justify-between">
                            <h4 class="font-bold text-xs text-slate-900">3.3. Error Absoluto Medio (MAE)</h4>
                            <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">mm/día o °C</span>
                        </div>
                        <div class="bg-white p-2.5 rounded border border-slate-200 text-center text-xs font-mono text-slate-800">
                            $$\text{MAE} = \frac{1}{T} \sum_{t=1}^T |S_t - O_t|$$
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Ofrece una lectura lineal intuitiva de la incertidumbre cotidiana habitual del producto en superficie, sin sobrerreaccionar a valores atípicos aislados.
                        </p>
                    </div>

                    <!-- PBIAS -->
                    <div class="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                        <div class="flex items-center justify-between">
                            <h4 class="font-bold text-xs text-slate-900">3.4. Sesgo Porcentual Relativo (PBIAS)</h4>
                            <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">%</span>
                        </div>
                        <div class="bg-white p-2.5 rounded border border-slate-200 text-center text-xs font-mono text-slate-800">
                            $$\text{PBIAS} = 100 \times \frac{\sum_{t=1}^T (S_t - O_t)}{\sum_{t=1}^T O_t}$$
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Mide la tendencia volumétrica acumulada a sobreestimar ($&gt;0$) o subestimar ($&lt;0$) el volumen hídrico o térmico total. Rango excelente en balances de cuencas: $[-10\%, +10\%]$.
                        </p>
                    </div>

                    <!-- Pearson r -->
                    <div class="border border-slate-200 rounded-lg p-4 bg-slate-50/50 space-y-2">
                        <div class="flex items-center justify-between">
                            <h4 class="font-bold text-xs text-slate-900">3.5. Coeficiente de Correlación de Pearson (r)</h4>
                            <span class="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-mono">Adimensional [-1, 1]</span>
                        </div>
                        <div class="bg-white p-2.5 rounded border border-slate-200 text-center text-xs font-mono text-slate-800">
                            $$r = \frac{\text{Cov}(S, O)}{\sigma_s \sigma_o}$$
                        </div>
                        <p class="text-[11px] text-slate-600 leading-relaxed">
                            Mide la asociación lineal y coherencia de fase temporal. En Centroamérica, captura la alternancia entre la época seca (noviembre-abril) y lluviosa (mayo-octubre).
                        </p>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 4: MÉTRICAS CATEGÓRICAS DE LLUVIA (MATRIZ DE CONTINGENCIA) -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="border-b border-slate-100 pb-3">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 4</span>
                    <h3 class="text-base font-bold text-slate-900">4. Formulación de Métricas Categóricas de Lluvia Diaria (Matriz de Contingencia)</h3>
                </div>
                <p class="text-xs text-slate-600 leading-relaxed">
                    Para la precipitación diaria, un experimento de corrección puede presentar buena correlación pero fallar al discriminar cuándo llueve y cuándo no. Se aplica un umbral físico de lluvia de $1.0\text{ mm/día}$ para construir la matriz de contingencia $2 \times 2$:
                </p>

                <div class="overflow-x-auto my-2">
                    <table class="data-table w-full text-xs max-w-2xl mx-auto">
                        <thead>
                            <tr>
                                <th>Evento de Lluvia ($\ge 1.0\text{ mm}$)</th>
                                <th class="text-center">Observado = SÍ</th>
                                <th class="text-center">Observado = NO</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="font-semibold text-slate-800">Simulado / Grilla = SÍ</td>
                                <td class="text-center bg-emerald-50 text-emerald-900 font-bold">Aciertos ($a$, <i>Hits</i>)</td>
                                <td class="text-center bg-rose-50 text-rose-900 font-semibold">Falsas Alarmas ($b$, <i>False Alarms</i>)</td>
                            </tr>
                            <tr>
                                <td class="font-semibold text-slate-800">Simulado / Grilla = NO</td>
                                <td class="text-center bg-amber-50 text-amber-900 font-semibold">Omisiones ($c$, <i>Misses</i>)</td>
                                <td class="text-center bg-slate-50 text-slate-800 font-semibold">Negativos Correctos ($d$, <i>Correct Rejections</i>)</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
                        <div class="font-bold text-xs text-slate-900">POD (Prob. de Detección)</div>
                        <div class="font-mono text-xs text-sky-800 text-center py-1">$$\text{POD} = \frac{a}{a + c}$$</div>
                        <p class="text-[10px] text-slate-500">Fracción de días lluviosos reales capturados por la malla (óptimo = 1.0).</p>
                    </div>
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
                        <div class="font-bold text-xs text-slate-900">FAR (Falsa Alarma)</div>
                        <div class="font-mono text-xs text-rose-800 text-center py-1">$$\text{FAR} = \frac{b}{a + b}$$</div>
                        <p class="text-[10px] text-slate-500">Fracción de días que la malla reportó lluvia pero en tierra estuvo seco (óptimo = 0.0).</p>
                    </div>
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
                        <div class="font-bold text-xs text-slate-900">ETS (Equitable Threat)</div>
                        <div class="font-mono text-xs text-sky-800 text-center py-1">$$\text{ETS} = \frac{a - a_{\text{azar}}}{a + b + c - a_{\text{azar}}}$$</div>
                        <p class="text-[10px] text-slate-500">Habilidad neta descontando aciertos esperados por puro azar $a_{\text{azar}}$.</p>
                    </div>
                    <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
                        <div class="font-bold text-xs text-slate-900">HSS (Heidke Skill Score)</div>
                        <div class="font-mono text-xs text-emerald-800 text-center py-1">$$\text{HSS} = \frac{2(ad - bc)}{(a+c)(c+d) + (a+b)(b+d)}$$</div>
                        <p class="text-[10px] text-slate-500">Exactitud global sobre el pronóstico aleatorio ($\text{HSS} &gt; 0.40$ es destreza alta).</p>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 5: EL DIAGRAMA DE TAYLOR -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="border-b border-slate-100 pb-3">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 5</span>
                    <h3 class="text-base font-bold text-slate-900">5. El Diagrama de Taylor: Síntesis Geométrica Polar</h3>
                </div>
                <p class="text-xs text-slate-600 leading-relaxed">
                    El Diagrama de Taylor (Taylor, 2001) resume en un solo gráfico polar la correspondencia geométrica tridimensional entre la correlación de Pearson ($r$), la desviación estándar normalizada ($\sigma^*$) y el error cuadrático medio centrado ($E'^*$):
                </p>
                <div class="bg-slate-50 p-3 rounded-lg border border-slate-200 text-center text-xs font-mono text-slate-800 my-2">
                    $${E'}^2 = \sigma_{\text{sim}}^2 + \sigma_{\text{obs}}^2 - 2 \sigma_{\text{sim}} \sigma_{\text{obs}} r \quad \implies \quad {E'^*}^2 = {\sigma^*}^2 + 1 - 2 \sigma^* r$$
                </div>
                <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
                    <div class="border border-slate-200 rounded p-3 bg-white">
                        <span class="font-bold text-slate-800">1. Coordenada Radial ($R = \sigma^*$):</span>
                        <p class="text-[11px] text-slate-600 mt-1">Razón $\sigma_{\text{sim}} / \sigma_{\text{obs}}$. $\sigma^* = 1.0$ indica amplitud idéntica a las estaciones. $\sigma^* &lt; 1.0$ representa subestimación de picos (malla suavizada); $\sigma^* &gt; 1.0$ ruido excesivo.</p>
                    </div>
                    <div class="border border-slate-200 rounded p-3 bg-white">
                        <span class="font-bold text-slate-800">2. Coordenada Angular ($\theta = \arccos r$):</span>
                        <p class="text-[11px] text-slate-600 mt-1">El ángulo respecto a la base horizontal representa la correlación. $\theta = 0^\circ \implies r = 1.0$; $\theta = 60^\circ \implies r = 0.5$; $\theta = 90^\circ \implies r = 0.0$.</p>
                    </div>
                    <div class="border border-slate-200 rounded p-3 bg-white">
                        <span class="font-bold text-slate-800">3. Distancia al Punto Observado:</span>
                        <p class="text-[11px] text-slate-600 mt-1">La distancia euclidiana entre el experimento y el punto $(1.0, 0^\circ)$ equivale directamente al error centrado RMS ($E'^*$). El experimento ganador es el más cercano al objetivo.</p>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 6: INTERPRETACIÓN FÍSICA CENTROAMERICANA -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="border-b border-slate-100 pb-3">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 6</span>
                    <h3 class="text-base font-bold text-slate-900">6. Interpretación Física en el Contexto Centroamericano</h3>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs text-slate-700">
                    <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-2">
                        <div class="font-bold text-sm text-slate-900">Efecto de "Doble Penalización" (Double Penalty) en Lluvia</div>
                        <p class="text-[11px] leading-relaxed text-slate-600">
                            En el istmo centroamericano, gran parte de la precipitación proviene de sistemas convectivos de mesoescala (tormentas locales vespertinas de 3 a 10 km de diámetro) y ondas tropicales del este. Si una tormenta descarga $60\text{ mm}$ sobre la estación, pero el satélite la ubicó a solo $8\text{ km}$ (en la celda contigua): la estación reporta omisión ($0\text{ mm}$) y la celda vecina falsa alarma ($60\text{ mm}$). Este fenómeno penaliza fuertemente el KGE y RMSE diario puntual. Por tanto, un $\text{KGE}$ diario de $0.35$ a $0.40$ en validación independiente representa un producto de <b>altísima fidelidad física</b>.
                        </p>
                    </div>

                    <div class="bg-slate-50 p-4 rounded-lg border border-slate-200 space-y-2">
                        <div class="font-bold text-sm text-slate-900">Factor Orográfico y Filtro Lluvia-No-Lluvia (RnoR)</div>
                        <p class="text-[11px] leading-relaxed text-slate-600">
                            En relieves montañosos escarpados (Cordillera de Talamanca, Sierra Madre, Sierra de Sulaco, Cordillera Central de RD), los satélites infrarrojos confunden los topes fríos de nubes estratiformes orográficas con núcleos de lluvia convectiva, sobreestimando los días lluviosos. El algoritmo $RnoR$ con umbral logit calibrado elimina las lloviznas espurias (<i>drizzle</i>), contrayendo el sesgo volumétrico (PBIAS) a niveles cercanos a cero.
                        </p>
                    </div>
                </div>
            </div>

            <!-- SECCIÓN 7: REFERENCIAS BIBLIOGRÁFICAS -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-3">
                <div class="border-b border-slate-100 pb-2">
                    <span class="text-[10px] font-bold text-sky-700 uppercase tracking-wider">Sección 7</span>
                    <h3 class="text-sm font-bold text-slate-900">7. Referencias Bibliográficas Oficiales</h3>
                </div>
                <ol class="list-decimal list-inside text-[11px] text-slate-600 space-y-1.5 leading-relaxed">
                    <li><b>Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).</b> <i>Decomposition of the mean squared error and NSE performance criteria: Implications for improving hydrological modelling.</i> Journal of Hydrology, 377(1-2), 80-91.</li>
                    <li><b>Kling, H., Fuchs, M., & Paulin, M. (2012).</b> <i>Runoff conditions in the upper Danube basin under an ensemble of climate change scenarios.</i> Journal of Hydrology, 424-425, 264-277.</li>
                    <li><b>Taylor, K. E. (2001).</b> <i>Summarizing multiple aspects of model performance in a single diagram.</i> Journal of Geophysical Research: Atmospheres, 106(D7), 7183-7192.</li>
                    <li><b>Dinku, T., et al. (2018).</b> <i>Validation of the CHIRP and CHIRPS precipitation estimates over eastern Africa.</i> International Journal of Climatology, 38(7), 2928-2942.</li>
                    <li><b>Faniriantsoa, R., & Dinku, T. (2022).</b> <i>Climate Data Tools (CDT): An R package for data quality control, homogenization and merging station data with satellite and reanalysis data.</i> IRI Technical Report, Columbia University.</li>
                </ol>
            </div>

        </div>

</main>

    <!-- Footer (Light Theme) -->
    <footer class="bg-slate-100 border-t border-slate-200 py-6 text-center text-xs text-slate-600 mt-12">
        <div class="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-2">
            <div>CDT 8.0 Climate Data Tools • Suite Regional de Centroamérica (1991–2020)</div>
            <div>Validación Holdout Ciega en 29 Estaciones • Dashboard Estático de Publicación (300 DPI)</div>
        </div>
    </footer>

    <!-- Interactive Vanilla Logic: Tab Switching, Sorting, Filtering, Modal Lightbox -->
    <script>
        // Tab Switching
        function switchTab(tabId) {
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            
            const targetPanel = document.getElementById('tab-content-' + tabId);
            const targetBtn = document.getElementById('tab-btn-' + tabId);
            if (targetPanel) targetPanel.classList.remove('hidden');
            if (targetBtn) targetBtn.classList.add('active');
            setTimeout(renderMath, 20);

            if (window.MathJax && window.MathJax.typesetPromise) {
                setTimeout(() => { window.MathJax.typesetPromise(); }, 50);
            }
        }

        // Table Column Sorter (Works on any table by column index)
        const sortDirections = {};
        function sortTable(tableId, colIdx, type) {
            const table = document.getElementById(tableId);
            if (!table) return;
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle direction
            const key = tableId + '_' + colIdx;
            const isAsc = !sortDirections[key];
            sortDirections[key] = isAsc;

            // Update header icons
            const headers = table.querySelectorAll('th');
            headers.forEach((th, idx) => {
                const icon = th.querySelector('.sort-icon');
                if (icon) {
                    if (idx === colIdx) {
                        icon.textContent = isAsc ? '▲' : '▼';
                        icon.style.color = '#0284c7';
                    } else {
                        icon.textContent = '⇅';
                        icon.style.color = '#94a3b8';
                    }
                }
            });

            rows.sort((a, b) => {
                const cellA = a.children[colIdx]?.innerText.trim() || '';
                const cellB = b.children[colIdx]?.innerText.trim() || '';
                
                if (type === 'num') {
                    // Extract number
                    const cleanA = cellA.replace(/[^0-9.-]/g, '');
                    const cleanB = cellB.replace(/[^0-9.-]/g, '');
                    const numA = cleanA !== '' ? parseFloat(cleanA) : -999999;
                    const numB = cleanB !== '' ? parseFloat(cleanB) : -999999;
                    return isAsc ? numA - numB : numB - numA;
                } else {
                    return isAsc ? cellA.localeCompare(cellB) : cellB.localeCompare(cellA);
                }
            });

            // Re-append sorted rows
            rows.forEach(r => tbody.appendChild(r));
        }

        // Table Instant Filter
        function filterTable(tableId, inputId) {
            const query = (document.getElementById(inputId)?.value || '').toLowerCase();
            const table = document.getElementById(tableId);
            if (!table) return;
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(r => {
                const text = r.innerText.toLowerCase();
                r.style.display = text.includes(query) ? '' : 'none';
            });
        }

        // Modal Lightbox
        function openModal(imgSrc, caption) {
            const modal = document.getElementById('imgModal');
            const modalImg = document.getElementById('modalImg');
            const modalCaption = document.getElementById('modalCaption');
            if (modal && modalImg) {
                modalImg.src = imgSrc;
                if (modalCaption) modalCaption.textContent = caption || 'Figura de Publicación (300 DPI)';
                modal.style.display = 'block';
            }
        }
        function closeModal() {
            const modal = document.getElementById('imgModal');
            if (modal) modal.style.display = 'none';
        }
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') closeModal();
        });

        // KaTeX Math Rendering Engine
        function renderMath() {
            if (window.renderMathInElement) {
                try {
                    renderMathInElement(document.body, {
                        delimiters: [
                            {left: '$$', right: '$$', display: true},
                            {left: '\\[', right: '\\]', display: true},
                            {left: '$', right: '$', display: false},
                            {left: '\\(', right: '\\)', display: false}
                        ],
                        ignoredTags: ["script", "noscript", "style", "textarea", "pre", "code", "option"],
                        throwOnError: false
                    });
                } catch(e) {
                    console.error('KaTeX error:', e);
                }
            }
        }

        // Render on page load
        document.addEventListener('DOMContentLoaded', renderMath);
        window.addEventListener('load', renderMath);
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
        list_rain=list_rain,
        list_tmax=list_tmax,
        list_tmin=list_tmin,
        list_all=list_all,
        fig_rain=figures_map.get("rainfall", {}),
        fig_tmax=figures_map.get("tmax", {}),
        fig_tmin=figures_map.get("tmin", {}),
        comp_overview=comparison_figures.get("overview", "figures/comparisons_winner_vs_raw/comparison_all_variables_executive_summary.png"),
    )

    with open(out_p, "w", encoding="utf-8") as f:
        f.write(rendered_html)
    print(f"  [DASHBOARD] Clean Light-Theme Static Publication Dashboard generated: {out_p}")
    return str(out_p)
