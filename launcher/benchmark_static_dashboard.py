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
    
    <!-- KaTeX for Mathematics -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

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
                            <span class="bg-slate-100 text-slate-700 text-[10px] font-mono px-2 py-0.5 rounded border border-slate-300">42 Modelos</span>
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
                                    <span class="bg-emerald-100 text-emerald-800 text-[10px] px-2 py-0.5 rounded border border-emerald-300 font-bold">ÓPTIMO</span>
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
                            <span class="bg-sky-600 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo Seleccionado</span>
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
                            <span>📋 Tabla Maestra de Rendimiento: Precipitación Diaria</span>
                            <span class="bg-sky-100 text-sky-800 border border-sky-300 text-[10px] font-mono px-2 py-0.5 rounded">16 Modelos</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar ascendentemente o descendentemente.</p>
                    </div>
                    <input type="text" id="searchRain" onkeyup="filterTable('tableRain', 'searchRain')" placeholder="🔍 Filtrar modelo..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-sky-500 focus:bg-white transition">
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
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
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
                            <p class="text-xs text-slate-600 mt-1">El modelo óptimo se ubica en el extremo superior izquierdo (mínimo error y máxima habilidad). Identificación en leyenda.</p>
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
                            <p class="text-xs text-slate-600 mt-1">Cuadrícula con valores numéricos impresos para todos los modelos. Escala de color: Verde (Óptimo) a Rojo (Deficiente).</p>
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
                            <p class="text-xs text-slate-600 mt-1">Modelo óptimo claramente destacado con llamada y aureola dorada. Eje base explicativo de RMSE y ángulo de correlación en 2 líneas.</p>
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
                            <span class="bg-amber-600 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo Seleccionado</span>
                            <span class="text-xs text-amber-800 font-mono font-bold">Rango #01 en Temp. Máxima</span>
                        </div>
                        <h2 class="text-2xl font-black text-slate-900 tracking-tight">{{ win_tmax.experiment_id }}</h2>
                        <p class="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">{{ win_tmax.description }}</p>
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

            <!-- Table for Tmax -->
            <div class="bg-white border border-slate-200 rounded-xl p-6 shadow-sm space-y-4">
                <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
                    <div>
                        <h3 class="font-bold text-sm text-slate-900 flex items-center gap-2">
                            <span>📋 Tabla Maestra de Rendimiento: Temperatura Máxima</span>
                            <span class="bg-amber-100 text-amber-800 border border-amber-300 text-[10px] font-mono px-2 py-0.5 rounded">13 Modelos</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar ascendentemente o descendentemente.</p>
                    </div>
                    <input type="text" id="searchTmax" onkeyup="filterTable('tableTmax', 'searchTmax')" placeholder="🔍 Filtrar modelo..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-amber-500 focus:bg-white transition">
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
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
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
                        <p class="text-xs text-slate-600 mt-1">Dispersión de eficiencia en las 29 estaciones para los 13 modelos de temperatura máxima.</p>
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
                        <p class="text-xs text-slate-600 mt-1">Convergencia de modelos hacia el óptimo en temperatura máxima.</p>
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
                        <p class="text-xs text-slate-600 mt-1">Modelo óptimo claramente destacado con llamada y aureola dorada.</p>
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
                            <span class="bg-violet-600 text-white text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded">Candidato Óptimo Seleccionado</span>
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
                            <span>📋 Tabla Maestra de Rendimiento: Temperatura Mínima</span>
                            <span class="bg-violet-100 text-violet-800 border border-violet-300 text-[10px] font-mono px-2 py-0.5 rounded">13 Modelos</span>
                        </h3>
                        <p class="text-[11px] text-slate-500">Haga clic en el encabezado de cualquier columna para ordenar ascendentemente o descendentemente.</p>
                    </div>
                    <input type="text" id="searchTmin" onkeyup="filterTable('tableTmin', 'searchTmin')" placeholder="🔍 Filtrar modelo..." class="bg-slate-50 border border-slate-300 rounded px-3 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-violet-500 focus:bg-white transition">
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
                                <td>{% if e.is_winner %}🏆 #{{ e.rank }}{% elif e.is_control %}⚡ [00]{% else %}#{{ e.rank }}{% endif %}</td>
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
                        <p class="text-xs text-slate-600 mt-1">Dispersión de eficiencia en las 29 estaciones holdout para los 13 modelos de temperatura mínima.</p>
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
                        <p class="text-xs text-slate-600 mt-1">Modelo óptimo claramente destacado con llamada y aureola dorada.</p>
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
        <!-- TAB 5: DEFINICIÓN E INTERPRETACIÓN DE ESTADÍSTICOS -->
        <!-- ========================================================================= -->
        <div id="tab-content-glossary" class="tab-panel hidden space-y-8">
            <div class="bg-gradient-to-r from-sky-50 via-white to-sky-50 border border-sky-300 rounded-xl p-6 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <span class="bg-sky-600 text-white text-[10px] uppercase font-bold px-2 py-0.5 rounded">Documentación Oficial</span>
                    <h3 class="text-xl font-bold text-slate-900 mt-1">Guía Metodológica Completa de Evaluación y Validación</h3>
                    <p class="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">
                        Consulte el documento técnico oficial para el desglose exhaustivo de las formulaciones matemáticas en KaTeX,
                        la partición espacial de las 29 estaciones holdout y los criterios físicos para Centroamérica.
                    </p>
                </div>
                <a href="docs/12_metodologia_evaluacion_metricas_y_validacion.md" target="_blank" class="inline-flex items-center gap-2 bg-sky-600 hover:bg-sky-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition shadow-sm">
                    <span>📖 Ver Documento 12 en Markdown</span>
                </a>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                <!-- KGE -->
                <div class="fig-card border-sky-300">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-slate-900">Eficiencia de Kling-Gupta (KGE)</h4>
                        <span class="text-[10px] bg-sky-100 text-sky-800 border border-sky-300 px-2 py-0.5 rounded font-bold">Métrica Principal</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded border border-slate-200 my-2 text-xs font-mono text-center text-sky-800">
                        $$KGE = 1 - \sqrt{(r - 1)^2 + (\beta - 1)^2 + (\gamma - 1)^2}$$
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Descompone el error en tres componentes ortogonales: correlación lineal (\(r\)), sesgo medio (\(\beta = \mu_s / \mu_o\)) y dispersión relativa (\(\gamma = \text{CV}_s / \text{CV}_o\)).
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-100 text-[11px] space-y-1 text-slate-500">
                        <div>• <b>Rango Óptimo:</b> 1.0 (KGE &gt; 0.3 indica habilidad superior al promedio climatológico).</div>
                        <div>• <b>En Centroamérica:</b> Penaliza el desplazamiento temporal de frentes fríos y la sobreestimación orográfica.</div>
                    </div>
                </div>

                <!-- Pearson r -->
                <div class="fig-card">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-slate-900">Coeficiente de Correlación (r)</h4>
                        <span class="text-[10px] bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded font-bold">Dinámica Temporal</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded border border-slate-200 my-2 text-xs font-mono text-center text-slate-800">
                        $$r = \frac{\sum (S_i - \bar{S})(O_i - \bar{O})}{\sqrt{\sum (S_i - \bar{S})^2 \sum (O_i - \bar{O})^2}}$$
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Mide la covariación temporal y sincronía de fase entre las observaciones de estaciones y las mallas diarias.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-100 text-[11px] space-y-1 text-slate-500">
                        <div>• <b>Rango Óptimo:</b> 1.0 (\(r &gt; 0.45\) en lluvia; \(r &gt; 0.85\) en temperatura).</div>
                        <div>• <b>En Centroamérica:</b> Refleja la capacidad de capturar el ciclo anual y las ondas tropicales del este.</div>
                    </div>
                </div>

                <!-- RMSE -->
                <div class="fig-card">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-slate-900">Raíz del Error Cuadrático Medio (RMSE)</h4>
                        <span class="text-[10px] bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded font-bold">Magnitud de Error</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded border border-slate-200 my-2 text-xs font-mono text-center text-slate-800">
                        $$RMSE = \sqrt{\frac{1}{N} \sum_{i=1}^N (S_i - O_i)^2}$$
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Pondera fuertemente los errores de gran magnitud. Expresado en unidades físicas de la variable (mm o °C).
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-100 text-[11px] space-y-1 text-slate-500">
                        <div>• <b>Rango Óptimo:</b> 0.0 (Menor es mejor).</div>
                        <div>• <b>En Centroamérica:</b> Sensible al efecto de doble penalización en tormentas convectivas tropicales.</div>
                    </div>
                </div>

                <!-- PBIAS -->
                <div class="fig-card">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-slate-900">Sesgo Porcentual Relativo (PBIAS)</h4>
                        <span class="text-[10px] bg-slate-100 text-slate-700 border border-slate-300 px-2 py-0.5 rounded font-bold">Balance de Masa</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded border border-slate-200 my-2 text-xs font-mono text-center text-slate-800">
                        $$PBIAS = 100 \times \frac{\sum (S_i - O_i)}{\sum O_i}$$
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Indica la tendencia sistemática de la malla a sobreestimar (\(&gt;0\)) o subestimar (\(&lt;0\)) los acumulados totales.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-100 text-[11px] space-y-1 text-slate-500">
                        <div>• <b>Rango Óptimo:</b> 0.0% (Aceptable entre \(-15\%\) y \(+15\%\)).</div>
                        <div>• <b>En Centroamérica:</b> Vital para la conservación de la masa de precipitación en balances de cuencas.</div>
                    </div>
                </div>

                <!-- Taylor Identity -->
                <div class="fig-card border-rose-300">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-slate-900">Identidad Geométrica de Taylor</h4>
                        <span class="text-[10px] bg-rose-100 text-rose-800 border border-rose-300 px-2 py-0.5 rounded font-bold">Espacio Polar</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded border border-slate-200 my-2 text-xs font-mono text-center text-rose-800">
                        $$E'^2 = \sigma_s^2 + \sigma_o^2 - 2\sigma_s\sigma_o r$$
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Vincula el error centrado RMS (\(E'\)), las desviaciones estándar de simulación y observación, y la correlación Pearson.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-100 text-[11px] space-y-1 text-slate-500">
                        <div>• <b>Punto Óptimo:</b> Radio \(\sigma^* = 1.0\) y Ángulo \(\theta = 0^\circ\) (\(r = 1.0\)).</div>
                        <div>• <b>En Centroamérica:</b> Muestra qué modelos reproducen la variabilidad estacional sin amortiguar picos.</div>
                    </div>
                </div>

                <!-- ETS -->
                <div class="fig-card border-sky-300">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-bold text-sm text-slate-900">Equitable Threat Score (ETS)</h4>
                        <span class="text-[10px] bg-sky-100 text-sky-800 border border-sky-300 px-2 py-0.5 rounded font-bold">Habilidad de Lluvia</span>
                    </div>
                    <div class="bg-slate-50 p-2.5 rounded border border-slate-200 my-2 text-xs font-mono text-center text-sky-800">
                        $$ETS = \frac{Hits - Hits_{random}}{Hits + FalseAlarms + Misses - Hits_{random}}$$
                    </div>
                    <p class="text-xs text-slate-600 leading-relaxed">
                        Mide la habilidad de la malla para discriminar días lluviosos (&gt;1 mm/día) penalizando aciertos al azar.
                    </p>
                    <div class="mt-3 pt-2 border-t border-slate-100 text-[11px] space-y-1 text-slate-500">
                        <div>• <b>Rango Óptimo:</b> 1.0 (Valores &gt; 0.20 indican destreza real en lluvia diaria tropical).</div>
                        <div>• <b>En Centroamérica:</b> Discrimina días secos y lluviosos en el Corredor Seco Centroamericano.</div>
                    </div>
                </div>
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

        // Initialize KaTeX math rendering safely
        document.addEventListener('DOMContentLoaded', function() {
            if (window.renderMathInElement) {
                try {
                    renderMathInElement(document.body, {
                        delimiters: [
                            {left: '$$', right: '$$', display: true},
                            {left: '\\\\(', right: '\\\\)', display: false}
                        ],
                        throwOnError: false
                    });
                } catch(e) {
                    console.warn('KaTeX skipped:', e);
                }
            }
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
