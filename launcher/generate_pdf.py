"""PDF Document Generator for CDT Experiments Matrix (Central America & Dominican Republic).

Generates a publication-grade scientific technical document in PORTRAIT format (8.5 x 11 inches),
with standard readable font sizes, harmonious spacing, elegant card containers, numbered pages (Página X de Y),
professional running headers/footers, complete step-by-step CDT architecture tables (Rainfall: 3 steps;
Temperature: 5 steps), comprehensive matrices for all 31 experiments (15 Rainfall: Fase 1 & Fase 2, 8 Tmax, 8 Tmin)
with detailed per-step parameter breakdowns and physical rationales, full validation leaderboard ranking (29 blind holdout stations),
typographically rendered mathematical equations, calibrated hardware benchmarks (Ubuntu 24.04.5 LTS, i9-10850K, 32GB RAM, 400GB NVMe),
and 21 annotated scientific references.
"""

from __future__ import annotations

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count and headers/footers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 7.8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(0.50 * inch, 10.45 * inch, 8.00 * inch, 10.45 * inch)
            self.drawString(0.50 * inch, 10.50 * inch, "Matriz de Experimentos y Diseño Metodológico con CDT (1991–2020)")
            self.drawRightString(8.00 * inch, 10.50 * inch, "Centroamérica y República Dominicana")

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(0.50 * inch, 0.42 * inch, 8.00 * inch, 0.42 * inch)
        self.drawString(0.50 * inch, 0.30 * inch, "Climate Data Tools (CDT v8.0) • CHIRPS / CHIRTS • Estándar CF-1.8")
        page_text = f"Página {self._pageNumber} de {page_count}"
        self.drawRightString(8.00 * inch, 0.30 * inch, page_text)
        self.restoreState()


def generate_experiments_pdf(output_path: Path | str = "docs/Matriz_Experimentos_CDT_Centroamerica_Dominicana.pdf") -> Path:
    output_pdf = Path(output_path).resolve()
    output_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Documento en formato vertical (Portrait Letter: 8.5 x 11 pulgadas)
    doc = SimpleDocTemplate(
        str(output_pdf),
        pagesize=letter,
        leftMargin=0.50 * inch,
        rightMargin=0.50 * inch,
        topMargin=0.60 * inch,
        bottomMargin=0.55 * inch,
    )

    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#1A365D")   # Deep Navy
    SECONDARY = colors.HexColor("#0D9488") # Teal
    DARK_TEXT = colors.HexColor("#0F172A") # Slate Dark
    LIGHT_BG = colors.HexColor("#F8FAFC")  # Table Alt Row
    BORDER_COLOR = colors.HexColor("#CBD5E1")
    BOX_BG_TEAL = colors.HexColor("#F0FDFA")
    BOX_BORDER_TEAL = colors.HexColor("#99F6E4")

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14.5,
        leading=18.0,
        textColor=PRIMARY,
        alignment=1,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.0,
        leading=13.0,
        textColor=SECONDARY,
        alignment=1,
        spaceAfter=5,
    )

    h1_style = ParagraphStyle(
        "H1Style",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11.0,
        leading=14.0,
        textColor=PRIMARY,
        spaceBefore=5.0,
        spaceAfter=3.0,
    )

    h2_style = ParagraphStyle(
        "H2Style",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=9.8,
        leading=12.5,
        textColor=SECONDARY,
        spaceBefore=4.0,
        spaceAfter=2.0,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.0,
        leading=12.2,
        textColor=DARK_TEXT,
        spaceAfter=3.5,
    )

    formula_style = ParagraphStyle(
        "FormulaBox",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11.2,
        textColor=DARK_TEXT,
    )

    ref_style = ParagraphStyle(
        "RefText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=6.6,
        leading=8.3,
        textColor=DARK_TEXT,
        spaceAfter=0.8,
        leftIndent=10,
        firstLineIndent=-10,
    )

    th_style = ParagraphStyle(
        "TableHeader",
        fontName="Helvetica-Bold",
        fontSize=8.0,
        leading=10.2,
        textColor=colors.white,
        alignment=1,
    )

    td_style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.0,
        textColor=DARK_TEXT,
    )

    td_bold = ParagraphStyle(
        "TableCellBold",
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10.0,
        textColor=PRIMARY,
        alignment=1,
    )

    # Estilos compactos para tablas de experimentos
    th_sm = ParagraphStyle(
        "TableHeaderSm",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white,
        alignment=1,
    )

    th_xs = ParagraphStyle(
        "TableHeaderXs",
        fontName="Helvetica-Bold",
        fontSize=7.0,
        leading=9.0,
        textColor=colors.white,
        alignment=1,
    )

    td_sm = ParagraphStyle(
        "TableCellSm",
        fontName="Helvetica",
        fontSize=7.1,
        leading=8.8,
        textColor=DARK_TEXT,
    )

    td_sm_bold = ParagraphStyle(
        "TableCellSmBold",
        fontName="Helvetica-Bold",
        fontSize=7.1,
        leading=8.8,
        textColor=PRIMARY,
        alignment=1,
    )

    td_xs = ParagraphStyle(
        "TableCellXs",
        fontName="Helvetica",
        fontSize=6.7,
        leading=8.2,
        textColor=DARK_TEXT,
    )

    td_xs_bold = ParagraphStyle(
        "TableCellXsBold",
        fontName="Helvetica-Bold",
        fontSize=6.7,
        leading=8.2,
        textColor=PRIMARY,
        alignment=1,
    )

    th_lb = ParagraphStyle(
        "TableHeaderLb",
        fontName="Helvetica-Bold",
        fontSize=6.2,
        leading=7.8,
        textColor=colors.white,
        alignment=1,
    )

    td_lb = ParagraphStyle(
        "TableCellLb",
        fontName="Helvetica",
        fontSize=6.0,
        leading=7.4,
        textColor=DARK_TEXT,
        alignment=1,
    )

    td_lb_bold = ParagraphStyle(
        "TableCellLbBold",
        fontName="Helvetica-Bold",
        fontSize=6.0,
        leading=7.4,
        textColor=PRIMARY,
        alignment=1,
    )

    td_lb_winner = ParagraphStyle(
        "TableCellLbWinner",
        fontName="Helvetica-Bold",
        fontSize=6.0,
        leading=7.4,
        textColor=colors.HexColor("#065F46"), # Emerald dark
        alignment=1,
    )

    # Estilos para tablas de validación cuantitativa
    th_val = ParagraphStyle(
        "TableHeaderVal",
        fontName="Helvetica-Bold",
        fontSize=6.4,
        leading=8.0,
        textColor=colors.white,
        alignment=1,
    )

    td_val = ParagraphStyle(
        "TableCellVal",
        fontName="Helvetica",
        fontSize=5.8,
        leading=7.2,
        textColor=DARK_TEXT,
    )

    td_val_bold = ParagraphStyle(
        "TableCellValBold",
        fontName="Helvetica-Bold",
        fontSize=5.8,
        leading=7.2,
        textColor=PRIMARY,
        alignment=1,
    )

    story = []

    # =========================================================================
    # PÁGINA 1: PORTADA, PROBLEMA CIENTÍFICO Y GLOSARIO
    # =========================================================================
    story.append(Paragraph("MATRIZ DE EXPERIMENTOS Y DISEÑO METODOLÓGICO CON CLIMATE DATA TOOLS (CDT)", title_style))
    story.append(Paragraph("Reconstrucción y Fusión Gridded de Alta Resolución (1991–2020) para <b>Centroamérica y República Dominicana</b>", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=5))

    story.append(Paragraph("1. Justificación Científica del Problema y Objetivos de la Fusión", h1_style))
    story.append(Paragraph(
        "Los conjuntos de datos climáticos satelitales y de reanálisis global presentan discrepancias sistemáticas e importantes con respecto a la realidad observada en superficie en regiones tropicales complejas: "
        "<br/><br/>"
        "• <b>Precipitación (CHIRPS):</b> Sobreestimación de lloviznas espurias (<i>drizzle effect</i>) debida a la reflectividad infrarroja de cirros fríos durante la <i>Canícula</i> en el Corredor Seco y Azua (Funk et al., 2015; Maldonado et al., 2016); subestimación de picos ciclónicos (&gt;100 mm/día) por alisado espacial del píxel de 5.5 km (Dinku et al., 2018); y falta de resolución del forzamiento orográfico fino en barlovento/sotavento (Daly et al., 2008). "
        "<br/><br/>"
        "• <b>Temperatura Máxima (CHIRTS Tmax):</b> No modela la radiación solar directa según la orientación de ladera (<i>aspect</i>: calentamiento matutino este vs máximo vespertino oeste) ni captura olas de calor (&gt;38 &deg;C) en depresiones áridas (Azua, Enriquillo a -40 msnm, Golfo de Fonseca) (Coles, 2001; Funk et al., 2019). "
        "<br/><br/>"
        "• <b>Temperatura Mínima (CHIRTS Tmin):</b> No modela inversiones térmicas nocturnas ni drenaje catabático en valles intramontanos cerrados (Constanza, Valle Nuevo, Quetzaltenango) con heladas (&lt;0 &deg;C), ni caídas térmicas bruscas asimétricas por frentes fríos invernales (<i>Nortes</i>) (Alfaro et al., 2018). "
        "<br/><br/>"
        "<b>Objetivo:</b> Ejecutar una matriz de <b>31 experimentos controlados</b> (15 de Precipitación organizados en Fase 1 y Fase 2, 8 de Tmax y 8 de Tmin) estructurados estrictamente según las etapas de procesamiento de CDT para determinar la configuración óptima de fusión espacial.",
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Glosario de Siglas y Acrónimos Técnicos", h1_style))
    th_glo = [Paragraph("Sigla", th_style), Paragraph("Nombre Completo", th_style), Paragraph("Definición y Rol en el Procesamiento", th_style)]
    rows_glo = [
        [Paragraph("<b>CDT</b>", td_bold), Paragraph("Climate Data Tools (IRI Columbia)", td_style), Paragraph("Paquete R para control de calidad, homogeneización, corrección de sesgo y fusión espacial.", td_style)],
        [Paragraph("<b>CHIRPS / CHIRTS</b>", td_bold), Paragraph("CHG Infrared Precipitation / Temp. with Stations", td_style), Paragraph("Bases de datos satelitales cuasi-globales a 0.05° (~5.5 km) de precipitación y temperatura diaria.", td_style)],
        [Paragraph("<b>DEM SRTM</b>", td_bold), Paragraph("Shuttle Radar Topography Mission (90m)", td_style), Paragraph("Modelo Digital de Elevación para gradiente vertical (&part;<i>T</i>/&part;<i>z</i> &approx; -6.5 &deg;C/km) y sombras orográficas.", td_style)],
        [Paragraph("<b>SBA / RK</b>", td_bold), Paragraph("Simple Bias Adjustment / Regression Kriging", td_style), Paragraph("SBA aplica ajuste residual directo. RK combina regresión lineal multivariada con Kriging de residuos.", td_style)],
        [Paragraph("<b>BSc / CSc</b>", td_bold), Paragraph("Barnes Scheme / Cressman Scheme", td_style), Paragraph("Análisis objetivo: Barnes aplica decaimiento gaussiano continuo; Cressman usa radio esférico finito.", td_style)],
        [Paragraph("<b>NN-3D / RnoR</b>", td_bold), Paragraph("Nearest Neighbor 3D / Rain-No-Rain Mask", td_style), Paragraph("NN-3D pondera distancia y cota altimétrica (&Delta;<i>z</i>). RnoR es un filtro logístico para días secos.", td_style)],
        [Paragraph("<b>QM / KGE</b>", td_bold), Paragraph("Quantile Mapping / Kling-Gupta Efficiency", td_style), Paragraph("QM iguala funciones acumuladas de probabilidad. KGE evalúa correlación, sesgo y variabilidad.", td_style)],
    ]
    t_glo = Table([th_glo] + rows_glo, colWidths=[0.90 * inch, 2.30 * inch, 4.30 * inch])
    t_glo.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.0),
    ]))
    story.append(t_glo)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 2: ARQUITECTURA SECUENCIAL DE PASOS EN CDT
    # =========================================================================
    story.append(Paragraph("3. Arquitectura de Flujo Secuencial por Pasos en CDT", h1_style))
    story.append(Paragraph(
        "La metodología de fusión en CDT se estructura en etapas analíticas secuenciales independientes que permiten aislar y evaluar rigurosamente el impacto de cada técnica en el modelado climático regional:",
        body_style
    ))
    story.append(Spacer(1, 2))

    story.append(Paragraph("3.1. Cadena de Procesamiento para Precipitación (3 Etapas en CDT)", h2_style))
    story.append(Paragraph("<font size=7.5 color='#475569'><i>Ruta en CDT GUI: Gridding > Merging Climate Data > Rainfall Data</i></font>", body_style))

    th_arch_r = [
        Paragraph("Paso en CDT", th_sm),
        Paragraph("Acción en CDT", th_sm),
        Paragraph("Opciones y Parámetros que se Varían (Detalle Exhaustivo)", th_sm),
    ]
    rows_arch_r = [
        [
            Paragraph("<b>Paso 1:<br/>Compute Bias Coefficients</b><br/><i>(Cálculo de Coefs. de Sesgo)</i>", td_sm_bold),
            Paragraph("Modela estadísticamente las discrepancias espaciales y distribucionales entre satélite y observaciones de estaciones de superficie.", td_sm),
            Paragraph("• <b>Métodos de Estimación de Sesgo:</b> Multiplicativo móvil (<code>mbvar</code>, ventana temporal móvil de &plusmn;5 días), Mensual climatológico fijo (<code>mbmon</code>), Quantile Mapping paramétrico (<code>qmdist</code> con función analítica teórica), Quantile Mapping empírico no paramétrico (<code>qmecdf</code> directamente sobre la curva observada).<br/>• <b>Distribuciones de Probabilidad:</b> Bernoulli-Gamma, Bernoulli-Weibull, Bernoulli-LogNormal (modelado mixto: probabilidad de ocurrencia binaria <i>wet &ge; 1.0 mm</i> y distribución de intensidad continua).<br/>• <b>Interpolación Espacial de Coeficientes:</b> IDW (<i>p</i>=2.0, radios de búsqueda 0.9° a 1.5°, nmin=3–4, nmax=8–12), Kriging Ordinario (<code>okr</code>), Kriging por Bloques (<code>use_block=TRUE</code> con integración numérica sobre celda de 5.5 km y semivariogramas esférico, exponencial y gaussiano).<br/>• <b>Opciones Avanzadas de CDT:</b> Función de agregación del sesgo (<code>mulBiasFunction: 'mean'</code> aritmética vs <code>'median'</code> robusta para neutralizar tormentas convectivas severas aisladas); contención marina costera mediante malla gruesa (<code>addCoarseGrid: true</code>, <code>resCoarseGrid: 1.0°</code>) que atenúa residuos a cero en el océano.", td_sm),
        ],
        [
            Paragraph("<b>Paso 2:<br/>Apply Bias Correction</b><br/><i>(Aplicación del Ajuste de Sesgo)</i>", td_sm_bold),
            Paragraph("Transforma y calibra las 10,958 grillas diarias crudas de satélite aplicando los coeficientes calculados en el Paso 1.", td_sm),
            Paragraph("• <b>Rango Temporal de Procesamiento:</b> Serie histórica continua 1991–2020 (10,958 días / 30 años climatológicos estándar).<br/>• <b>Archivos de Entrada:</b> Parámetros estructurados en archivo binario <code>.rds</code> generado en el Paso 1 (coeficientes espaciales o funciones acumuladas de cuantiles).<br/>• <b>Grillas Satelitales Objetivo:</b> CHIRPS v2.0 diario en formato NetCDF a resolución nativa de 0.05° (~5.5 km) con patrón <code>chirps-v2.0.%s.%s.%s.nc</code>.<br/>• <b>Optimización Algorítmica y Paralelismo:</b> Despacho multihilo en clúster local (<code>parsL <- doparallel.cond(...)</code>); evaluación cuantil acelerada mediante interpolación vectorial sobre <code>stats::knots()</code> en <code>qmecdf</code> (reducción de latencia de 30 h a 12 min).<br/>• <b>Formato de Salida:</b> Grillas diarias NetCDF ajustadas <code>rr_adj_%s%s%s.nc</code>.", td_sm),
        ],
        [
            Paragraph("<b>Paso 3:<br/>Merging Data</b><br/><i>(Fusión Espacial de Datos)</i>", td_sm_bold),
            Paragraph("Combina las grillas satelitales corregidas (<i>first guess</i>) con las observaciones de estaciones meteorológicas de superficie.", td_sm),
            Paragraph("• <b>Métodos Geoestadísticos de Fusión:</b> Spatio-Temporal Bias Adjustment (<b>SBA</b>), Regression Kriging (<b>RK</b>), Barnes Objective Analysis (<b>BSc</b>), Cressman Scheme (<b>CSc</b>).<br/>• <b>Esquemas Multi-Pasada:</b> 3 o 4 pasadas con radios decrecientes (ej. regional 1.0°, 0.75°, 0.50°; local anti-cruce 1.0°, 0.67°, 0.33°; o Cressman 1.0°, 0.75°, 0.50°, 0.25°).<br/>• <b>Máscara Lluvia/No-Lluvia (RnoR):</b> Clasificación probabilística binomial (<code>logit</code>, <i>wet</i> = 1.0 mm); corte binario rígido (<code>CutOff=3</code> a 0.5 mm) vs <b>transición continua suave</b> (<code>RnoRCutOff = 2</code> entre 0.1 y 1.0 mm); suavizado espacial gaussiano (<code>smooth: true</code>).<br/>• <b>Interpolación de Residuales:</b> Modified Shepard con control de derivadas locales y ponderación direccional; Spheremap en esfera terrestre real (distancia de gran círculo); IDW (<i>p</i>=2.0); OKR por bloques; Vecino 3D (NN-3D) acoplado a elevación.<br/>• <b>Covariables Físicas y Recorte:</b> DEM SRTM, pendiente (<i>slope</i>), orientación (<i>aspect</i>) y lat/lon en RK; recorte cartográfico con shapefile y buffer de 10 km.", td_sm),
        ],
    ]
    t_arch_r = Table([th_arch_r] + rows_arch_r, colWidths=[1.40 * inch, 2.10 * inch, 4.00 * inch])
    t_arch_r.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_arch_r)
    story.append(PageBreak())

    story.append(Paragraph("3.2. Cadena de Procesamiento para Temperatura (5 Etapas en CDT)", h2_style))
    story.append(Paragraph("<font size=7.5 color='#475569'><i>Ruta en CDT GUI: Gridding > Merging Climate Data > Temperatures Data</i></font>", body_style))

    th_arch_t = [
        Paragraph("Paso en CDT", th_xs),
        Paragraph("Acción en CDT", th_xs),
        Paragraph("Opciones y Parámetros que se Varían (Detalle Exhaustivo)", th_xs),
    ]
    rows_arch_t = [
        [
            Paragraph("<b>Paso 1:<br/>Compute Downscaling Coeffs</b><br/><i>(Coefs. Desescalado)</i>", td_xs_bold),
            Paragraph("Modela empíricamente el gradiente térmico vertical ambiental (<i>lapse rate</i>, &part;<i>T</i>/&part;<i>z</i>) entre estaciones y elevación.", td_xs),
            Paragraph("• <b>Paso Temporal:</b> Coeficientes diarios móviles (&plusmn;5 días), mensuales fijos o estacionales.<br/>• <b>Topografía Base:</b> DEM SRTM de 90 m remuestreado a 0.05° o resolución nativa de 0.01° (~1.1 km).<br/>• <b>Modelado Estadístico:</b> Regresión lineal univariada estación–altitud o GLM multivariado con pendiente (<i>slope</i>) y orientación de ladera (<i>aspect</i>).<br/>• <b>Salida:</b> Archivo binario <code>.rds</code> estructurado con la matriz de coeficientes altimétricos por periodo.", td_xs),
        ],
        [
            Paragraph("<b>Paso 2:<br/>Downscaling Data</b><br/><i>(Desescalado Espacial Grillas)</i>", td_xs_bold),
            Paragraph("Proyecta y remuestrea las grillas térmicas satelitales/reanálisis sobre la malla topográfica fina del DEM.", td_xs),
            Paragraph("• <b>Métodos de Interpolación Espacial:</b> Bilineal (<code>blin</code>), IDW local o Kriging Ordinario (<code>okr</code>).<br/>• <b>Resolución y Malla Objetivo:</b> Grilla regular a 0.05° (~5.5 km) o 0.01° (~1.1 km) sincronizada con el DEM regional.<br/>• <b>Rango Temporal:</b> Procesamiento continuo de los 10,958 días (1991–2020).<br/>• <b>Salida Estandarizada:</b> NetCDF desescalados topográficamente <code>tmax_down_%s%s%s.nc</code> / <code>tmin_down_%s%s%s.nc</code>.", td_xs),
        ],
        [
            Paragraph("<b>Paso 3:<br/>Compute Bias Coefficients</b><br/><i>(Cálculo Coefs. Sesgo)</i>", td_xs_bold),
            Paragraph("Calcula las discrepancias espaciales y distribucionales entre las temperaturas desescaladas y las estaciones observadas.", td_xs),
            Paragraph("• <b>Métodos de Sesgo Térmico:</b> Multiplicativo móvil (<code>mbvar</code> &plusmn;5 días), Sesgo mensual fijo (<code>mbmon</code>), Quantile Mapping paramétrico (<code>qmdist</code>), QM empírico no paramétrico (<code>qmecdf</code>).<br/>• <b>Distribuciones Teóricas Continuas:</b> Normal gaussiana (<code>norm</code>), Asimétrica Skew-Normal (<code>snorm</code> para descensos bruscos por frentes fríos <i>Nortes</i> en Tmin u olas de calor en Tmax), Valores extremos Gumbel (<code>gumbel</code> para colas de eventos extremos >P95 en Tmax o heladas <P05 en Tmin), Log-Normal.<br/>• <b>Interpolación Espacial de Coeficientes:</b> IDW (<i>p</i>=2.0, radio sinóptico de 3.5°, nmin=4, nmax=12), OKR con variogramas Sph, Exp, Gau y Pen, Ponderación tridimensional NN-3D considerando diferencia altimétrica &Delta;<i>z</i>.", td_xs),
        ],
        [
            Paragraph("<b>Paso 4:<br/>Apply Bias Correction</b><br/><i>(Aplicación Ajuste Sesgo)</i>", td_xs_bold),
            Paragraph("Aplica las funciones de ajuste calculadas en el Paso 3 a las 10,958 grillas diarias desescaladas.", td_xs),
            Paragraph("• <b>Rango Temporal:</b> Serie 1991–2020 continua.<br/>• <b>Archivo de Entrada:</b> Parámetros estructurados y curvas CDF en archivo <code>.rds</code> del Paso 3.<br/>• <b>Transformación:</b> Corrección multiplicativa proporcional o traslación no lineal cuantil a cuantil celda por celda.<br/>• <b>Salida:</b> Grillas NetCDF calibradas <code>tmax_adj_%s%s%s.nc</code> / <code>tmin_adj_%s%s%s.nc</code>.", td_xs),
        ],
        [
            Paragraph("<b>Paso 5:<br/>Merging Data</b><br/><i>(Fusión Espacial de Residuales)</i>", td_xs_bold),
            Paragraph("Fusión final entre las grillas desescaladas/ajustadas (<i>first guess</i>) y las observaciones puntuales de estaciones.", td_xs),
            Paragraph("• <b>Métodos de Fusión:</b> Regression Kriging (<b>RK</b>) multivariado vs SBA.<br/>• <b>Covariables Físicas Acopladas:</b> DEM (elevación sobre el nivel del mar), pendiente del terreno, orientación de ladera (<i>aspect</i>), coordenadas lat/lon.<br/>• <b>Esquemas Multi-Pasada:</b> 3 pasadas decrecientes (1.0°, 0.75°, 0.50°) o Cressman 4 pasadas (1.0°, 0.75°, 0.50°, 0.25°).<br/>• <b>Interpolación de Residuales Térmicos:</b> IDW (3.5°), OKR por bloques, <b>NN-3D con restricción vertical estricta</b> (&Delta;<i>z</i> con el DEM para resolver inversiones térmicas y drenaje de aire frío nocturno), Barnes (<b>BSc</b>) gaussiano continuo para amortiguamiento marino costero.<br/>• <b>Salida Final:</b> NetCDF diarios fusionados y ensamblados en archivo 3D multitemporal conforme a CF-1.8.", td_xs),
        ],
    ]
    t_arch_t = Table([th_arch_t] + rows_arch_t, colWidths=[1.40 * inch, 2.10 * inch, 4.00 * inch])
    t_arch_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_arch_t)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 3: SUITE A - PRECIPITACIÓN FASE 1 (CRIBADO EXPLORATORIO: EXP-R01 A R10)
    # =========================================================================
    story.append(Paragraph("4.1. Suite A: Precipitación Diaria — Fase 1 (Cribado Exploratorio: 10 Experimentos)", h1_style))
    story.append(Paragraph(
        "Batería experimental estructurada según los 3 pasos de CDT para aislar efectos de corrección de sesgo, filtro RnoR y métodos de interpolación:",
        body_style
    ))
    story.append(Spacer(1, 2))

    th_r = [
        Paragraph("ID Exp.", th_sm),
        Paragraph("Paso 1: Compute Bias Coeffs", th_sm),
        Paragraph("Paso 2: Apply Bias", th_sm),
        Paragraph("Paso 3: Merging Data (Fusión)", th_sm),
        Paragraph("Hipótesis Física y Climatológica Regional", th_sm),
    ]
    rows_r = [
        [
            Paragraph("<b>EXP-R01</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (móvil &plusmn;5 d)<br/>• Interp: IDW (<i>p</i>=2.0, radio 1.5°, nmin=4, nmax=12)", td_sm),
            Paragraph("• Ajuste multiplicativo sobre grillas CHIRPS 1991–2020<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA</b> monocapa (1 pasada a 1.0°)<br/>• Interp: IDW (1.5°)<br/>• RnoR: <b>Desactivada</b> (<code>use=false</code>)<br/>• Covariables: Ninguna", td_sm),
            Paragraph("<b>Control Nulo Determinista (Línea Base):</b> Mide discrepancia satelital pura sin control de lloviznas espurias (<i>drizzle</i>) ni esquemas multiescala.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R02</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: IDW (<i>p</i>=2.0, radio 1.5°)", td_sm),
            Paragraph("• Ajuste multiplicativo sobre grillas CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• Interp: IDW (1.5°)<br/>• RnoR: <b>Activada</b> (Logit GLM, wet=1.0 mm, CutOff=3)", td_sm),
            Paragraph("<b>Impacto del Filtro RnoR:</b> Evalúa la restauración de rachas secas reales durante la <b>Canícula</b> en Corredor Seco y Azua, eliminando falsa lluvia satelital.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R03</b>", td_sm_bold),
            Paragraph("• Método: <code>qmdist</code> (Quantile Mapping)<br/>• Distribución: <b>Bernoulli-Gamma</b><br/>• Interp: OKR por Bloques (Sph/Exp/Gau, radio 2.0°)", td_sm),
            Paragraph("• Corrección cuantil a cuantil de la CDF sobre CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• Interp: OKR por Bloques (<code>use_block=TRUE</code>)<br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Régimen Convectivo Tropical Típico:</b> Gamma modela asimetría convectiva; Kriging por bloques corrige error de soporte espacial (estación puntual vs píxel 5.5 km).", td_sm),
        ],
        [
            Paragraph("<b>EXP-R04</b>", td_sm_bold),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Bernoulli-Weibull</b><br/>• Interp: OKR por Bloques (radio 2.0°)", td_sm),
            Paragraph("• Mapeo no lineal enfocado en cuantiles extremos (&gt;P95)<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• Interp: OKR por Bloques<br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Extremos Ciclónicos y Tormentas Severas:</b> Weibull captura colas pesadas (&gt;150 mm/día) provocadas por ondas del este, ciclones en el Caribe y giros monzónicos (CAG).", td_sm),
        ],
        [
            Paragraph("<b>EXP-R05</b>", td_sm_bold),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: Bernoulli-Weibull<br/>• Interp: OKR por Bloques (radio 2.0°)", td_sm),
            Paragraph("• Corrección de extremos sobre grillas CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>Regression Kriging (RK)</b> (3 pasadas)<br/>• <b>Covariables: DEM + Pendiente + Lat + Lon</b><br/>• Residuos: OKR por bloques<br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Forzamiento Orográfico Vertical:</b> Acopla el relieve en regresión determinística; modela ascenso forzado por Alisios en barlovento y sombras de lluvia en sotavento.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R06</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: <b>NN-3D con elevación DEM (&Delta;<i>z</i>)</b>", td_sm),
            Paragraph("• Ajuste proporcional tridimensional sobre CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>Barnes Objective Analysis (BSc)</b> (3 pasadas gaussianas decrecientes)<br/>• RnoR: Activada (Logit GLM)<br/>• Covariables: Ninguna", td_sm),
            Paragraph("<b>Gradientes Costeros e Insulares Suaves:</b> Función gaussiana continua de Barnes evita singularidades y ojos de buey (<i>bulls-eyes</i>) en islas y franjas litorales.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R07</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: IDW (<i>p</i>=2.0, radio 1.5°)", td_sm),
            Paragraph("• Ajuste sobre grillas satelitales<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>Cressman Scheme (CSc)</b> (4 pasadas: 1.0°, 0.75°, 0.5°, 0.25°)<br/>• RnoR: Activada (Logit GLM)<br/>• Covariables: Ninguna", td_sm),
            Paragraph("<b>Celdas Convectivas Aisladas:</b> Radios estrictamente finitos en última pasada (0.25° &approx; 27 km) para ajustar núcleos de tormenta muy localizados en la costa del Pacífico.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R08</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: <b>Shepard Modificado</b>", td_sm),
            Paragraph("• Ajuste de sesgo con polinomios locales<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas)<br/>• Interp: Shepard Modificado con control de derivadas<br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Relieve Escarpado y Cañones:</b> Polinomios de Taylor de Shepard evitan sobreoscilaciones numéricas en transiciones topográficas abruptas (cañones y fallas tectónicas).", td_sm),
        ],
        [
            Paragraph("<b>EXP-R09</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: <b>Spheremap (Gran Círculo)</b>", td_sm),
            Paragraph("• Ajuste sobre CHIRPS en coordenadas esféricas<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas)<br/>• Interp: Spheremap en esfera terrestre real<br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Geometría Esférica Trans-Caribe:</b> Corrige la distorsión métrica longitudinal en distancias zonales amplias a lo largo del arco de las Antillas Mayores.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R10</b>", td_sm_bold),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: Bernoulli-Weibull<br/>• Interp: OKR por Bloques", td_sm),
            Paragraph("• Corrección distribucional de extremos ciclónicos<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>Regression Kriging (RK)</b> multiescala<br/>• <b>Covariables: DEM + Pendiente + Aspect + Lat + Lon</b><br/>• Residuos: OKR por bloques<br/>• RnoR: Activada", td_sm),
            Paragraph("<b>Máxima Complejidad Física Acoplada:</b> Incorpora orientación de ladera (<i>aspect</i>) para capturar la intercepción directa de humedad del Chorro del Caribe (CLLJ).", td_sm),
        ],
    ]
    t_table_r = Table([th_r] + rows_r, colWidths=[0.65 * inch, 1.65 * inch, 1.20 * inch, 1.80 * inch, 2.20 * inch])
    t_table_r.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
    ]))
    story.append(t_table_r)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: SUITE A - FASE 2 Y LEADERBOARD DE PRECIPITACIÓN
    # =========================================================================
    story.append(Paragraph("4.2. Suite A: Precipitación Diaria — Fase 2 (Optimización Dirigida) y Resultados del Benchmark", h1_style))
    story.append(Paragraph(
        "A partir de los resultados de la Fase 1, donde <b>Shepard Modificado (EXP_R08)</b> y <b>Spheremap (EXP_R09)</b> demostraron superioridad concluyente sobre métodos geoestadísticos rígidos y regresiones globales, la Fase 2 formuló 5 experimentos de refinamiento dirigidos a optimizar el estimador de sesgo (mediana), el confinamiento orográfico y la transición suave de lluvia:",
        body_style
    ))
    story.append(Spacer(1, 2))

    th_r2 = [
        Paragraph("ID Exp.", th_sm),
        Paragraph("Paso 1: Compute Bias Coeffs", th_sm),
        Paragraph("Paso 2: Apply Bias", th_sm),
        Paragraph("Paso 3: Merging Data (Fusión)", th_sm),
        Paragraph("Hipótesis Física y Climatológica Regional (Fase 2)", th_sm),
    ]
    rows_r2 = [
        [
            Paragraph("<b>EXP-R11</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• <b>mulBiasFunction: 'median'</b><br/>• <b>addCoarseGrid: true (1.0°)</b><br/>• Interp: IDW (1.5°)", td_sm),
            Paragraph("• Ajuste multiplicativo robusto sobre grillas CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• Interp: Shepard Modificado (1.5°)<br/>• RnoR: Activada (Logit GLM)<br/>• <b>addCoarseGrid: true</b>", td_sm),
            Paragraph("<b>Mediana Robusta y Malla Gruesa:</b> El estimador de mediana neutraliza eventos convectivos extremos atípicos que inflan el sesgo; la malla gruesa contiene anomalías espurias en áreas oceánicas y costeras sin estaciones.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R12</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• mulBiasFunction: 'median'<br/>• <b>Interp: IDW local (radio 0.9° ~100 km, nmin=3, nmax=8)</b>", td_sm),
            Paragraph("• Ajuste con aislamiento transcordillera<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala local</b> (3 pasadas: 1.0°, 0.67°, 0.33°)<br/>• <b>Interp: Shepard local (0.9°, nmin=3, nmax=8)</b><br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Aislamiento Transcordillera:</b> En Centroamérica, un radio de 1.5° (~165 km) cruza la cordillera central contaminando la vertiente seca del Pacífico con el Caribe húmedo. Acotar el radio a 0.9° preserva la sombra orográfica real.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R13</b>", td_sm_bold),
            Paragraph("• Método: <b>Quantile Mapping Empírico (<code>qmecdf</code>)</b><br/>• Ajuste no-paramétrico cuantil a cuantil libre de distribución<br/>• Interp: IDW (1.5°)", td_sm),
            Paragraph("• Mapeo cuantil empírico sobre grillas CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• Interp: Shepard Modificado (1.5°)<br/>• RnoR: Activada (Logit GLM)", td_sm),
            Paragraph("<b>Quantile Mapping No-Paramétrico (eCDF):</b> Supera la rigidez de las distribuciones teóricas (Gamma/Weibull) que colapsaron en Fase 1, modelando eventos ciclónicos extremos directamente a partir de la curva acumulada empírica observada.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R14</b>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• mulBiasFunction: 'median'<br/>• addCoarseGrid: true (1.0°)<br/>• Interp: IDW (1.5°)", td_sm),
            Paragraph("• Ajuste esférico sobre grillas CHIRPS<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• <b>Interp: Spheremap (Gran Círculo 1.5°)</b><br/>• RnoR: Activada (Logit GLM)<br/>• addCoarseGrid: true", td_sm),
            Paragraph("<b>Spheremap con Mediana y Malla Gruesa:</b> Acopla la métrica de distancia de gran círculo sobre la curvatura terrestre real con estimador robusto de mediana y contención gruesa en costas del Caribe y Antillas.", td_sm),
        ],
        [
            Paragraph("<b>EXP-R15</b><br/><font color='#065F46' size=6><b>GANADOR</b></font>", td_sm_bold),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• <b>mulBiasFunction: 'median'</b><br/>• Interp: IDW (radio 1.2°, nmin=4, nmax=10)", td_sm),
            Paragraph("• Ajuste multiplicativo sobre grillas CHIRPS 1991–2020<br/>• Salida: <code>rr_adj_*.nc</code>", td_sm),
            Paragraph("• Método: <b>SBA multiescala</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• Interp: Shepard Modificado (radio 1.2°)<br/>• <b>RnoR: Activada con RnoRCutOff = 2 (Suave)</b>", td_sm),
            Paragraph("<b>MODELO GANADOR — Transición Continua Suave:</b> Sustituye el corte binario rígido (0.5) por una función de transición lineal suave (0.1 a 1.0 mm). Elimina el subestimado seco severo (-4.39% PBIAS vs -22.15% en R02), logrando el máximo KGE y Skill.", td_sm),
        ],
    ]
    t_table_r2 = Table([th_r2] + rows_r2, colWidths=[0.65 * inch, 1.65 * inch, 1.20 * inch, 1.80 * inch, 2.20 * inch])
    t_table_r2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("BACKGROUND", (0, 5), (-1, 5), colors.HexColor("#ECFDF5")), # Subtle emerald highlight for winner
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
    ]))
    story.append(t_table_r2)
    story.append(Spacer(1, 3))

    # TABLA RESUMEN / LEADERBOARD FINAL DE LOS 15 EXPERIMENTOS
    story.append(Paragraph("<b>Ranking Consolidado del Benchmark de Precipitación (29 Estaciones de Validación Ciega Holdout)</b>", h2_style))
    th_lb_row = [
        Paragraph("#", th_lb),
        Paragraph("Experimento ID", th_lb),
        Paragraph("Método Merging y Configuración", th_lb),
        Paragraph("KGE", th_lb),
        Paragraph("r", th_lb),
        Paragraph("RMSE", th_lb),
        Paragraph("PBIAS", th_lb),
        Paragraph("POD", th_lb),
        Paragraph("FAR", th_lb),
        Paragraph("ETS", th_lb),
        Paragraph("HSS", th_lb),
        Paragraph("Skill", th_lb),
        Paragraph("Estado / Posición", th_lb),
    ]
    rows_lb_data = [
        ("1", "EXP_R15_Shepard_RnoR_Smooth", "Shepard Suave (RnoRCutOff=2, rad 1.2°)", "0.379", "0.479", "12.88", "-4.39%", "0.692", "0.304", "0.329", "0.479", "0.501", "GANADOR (Rank 1)", True),
        ("2", "EXP_R12_Shepard_Local_Orn", "Shepard Confinado Local (rad 0.9°)", "0.372", "0.469", "13.21", "-3.21%", "0.673", "0.299", "0.324", "0.474", "0.499", "Fase 2 (Rank 2)", False),
        ("3", "EXP_R08_Shepard_Complex_Relief", "Shepard Relieve Complejo (rad 1.5°)", "0.375", "0.479", "12.89", "-6.30%", "0.665", "0.304", "0.315", "0.464", "0.489", "Fase 1 (Rank 3)", False),
        ("4", "EXP_R11_Shepard_Median_Coarse", "Shepard Mediana + CoarseGrid (1.5°)", "0.375", "0.479", "12.77", "-6.70%", "0.675", "0.304", "0.321", "0.470", "0.489", "Fase 2 (Rank 4)", False),
        ("5", "EXP_R14_Spheremap_Median", "Spheremap Gran Círculo + Mediana", "0.362", "0.455", "13.56", "-4.43%", "0.654", "0.297", "0.317", "0.466", "0.486", "Fase 2 (Rank 5)", False),
        ("6", "EXP_R09_Spheremap_Trans_Caribe", "Spheremap Gran Círculo Estándar", "0.358", "0.458", "13.59", "-4.59%", "0.648", "0.296", "0.313", "0.463", "0.484", "Fase 1 (Rank 6)", False),
        ("7", "EXP_R07_Cressman_Spherical", "Cressman 4 pasadas (1.0° a 0.25°)", "0.332", "0.447", "14.44", "+3.64%", "0.630", "0.305", "0.296", "0.444", "0.472", "Fase 1 (Guía CDT)", False),
        ("8", "EXP_R13_QM_Empirical_ECDF", "QM Empírico (qmecdf) + Shepard", "0.320", "0.465", "13.08", "-5.57%", "0.639", "0.303", "0.299", "0.446", "0.466", "Fase 2 (Rank 8)", False),
        ("9", "EXP_R06_Barnes_Gauss_Coastal", "Barnes BSc Gaussiano Costero (NN-3D)", "0.309", "0.449", "14.22", "+4.08%", "0.646", "0.310", "0.298", "0.445", "0.463", "Fase 1 (Rank 9)", False),
        ("10", "EXP_R01_SBA_IDW_Baseline", "IDW Plano Monocapa (Sin RnoR)", "0.335", "0.486", "12.22", "-13.53%", "0.666", "0.338", "0.274", "0.418", "0.440", "Línea Base", False),
        ("11", "EXP_R02_SBA_IDW_RnoR", "IDW 3 pasadas + RnoR (Corte Duro)", "0.263", "0.466", "12.39", "-22.15%", "0.613", "0.315", "0.272", "0.411", "0.374", "Fase 1 (Rank 11)", False),
        ("12", "EXP_R05_RK_Topography_BW", "Regression Kriging DEM+Slope (Weibull)", "0.215", "0.417", "13.28", "-18.28%", "0.522", "0.367", "0.201", "0.322", "0.346", "Fase 1 (Rank 12)", False),
        ("13", "EXP_R03_SBA_OKR_BernoulliGamma", "QM Paramétrico Gamma + OKR Bloques", "-0.028", "0.427", "14.87", "-5.83%", "0.639", "0.348", "0.246", "0.373", "0.323", "Fase 1 (Rank 13)", False),
        ("14", "EXP_R04_SBA_OKR_BernoulliWeib", "QM Paramétrico Weibull + OKR Bloques", "0.016", "0.431", "14.51", "-11.98%", "0.636", "0.348", "0.247", "0.373", "0.315", "Fase 1 (Rank 14)", False),
        ("15", "EXP_R10_RK_FullTopography_Asp", "RK Máxima Complejidad DEM+Aspect", "0.106", "0.411", "14.11", "-18.36%", "0.508", "0.376", "0.190", "0.307", "0.305", "Fase 1 (Rank 15)", False),
    ]

    table_lb_rows = [th_lb_row]
    winner_row_idx = None
    for idx, (rk, eid, met, kge, r_val, rmse, pb, pod, far, ets, hss, sk, st, is_win) in enumerate(rows_lb_data, start=1):
        st_style = td_lb_winner if is_win else td_lb
        table_lb_rows.append([
            Paragraph(f"<b>{rk}</b>", td_lb_winner if is_win else td_lb_bold),
            Paragraph(eid, td_lb_winner if is_win else td_lb),
            Paragraph(met, td_lb),
            Paragraph(kge, td_lb_winner if is_win else td_lb),
            Paragraph(r_val, td_lb),
            Paragraph(rmse, td_lb),
            Paragraph(pb, td_lb),
            Paragraph(pod, td_lb),
            Paragraph(far, td_lb),
            Paragraph(ets, td_lb),
            Paragraph(hss, td_lb),
            Paragraph(sk, td_lb_winner if is_win else td_lb_bold),
            Paragraph(st, st_style),
        ])
        if is_win:
            winner_row_idx = idx

    t_table_lb = Table(table_lb_rows, colWidths=[0.24 * inch, 1.36 * inch, 1.40 * inch, 0.38 * inch, 0.35 * inch, 0.40 * inch, 0.44 * inch, 0.36 * inch, 0.36 * inch, 0.36 * inch, 0.36 * inch, 0.39 * inch, 1.10 * inch])
    style_lb_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.0),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.5),
    ]
    if winner_row_idx:
        style_lb_cmds.append(("BACKGROUND", (0, winner_row_idx), (-1, winner_row_idx), colors.HexColor("#D1FAE5"))) # Highlight row 1
    t_table_lb.setStyle(TableStyle(style_lb_cmds))
    story.append(t_table_lb)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 4: SUITE B - TEMPERATURA MÁXIMA (TMAX - 8 EXP)
    # =========================================================================
    story.append(Paragraph("5. Suite B: Temperatura Máxima Diurna (CHIRTS Tmax: 8 Experimentos)", h1_style))
    story.append(Paragraph(
        "Batería experimental estructurada según los 5 pasos de CDT: desescalado topográfico, ajuste de sesgo diurno y fusión con radiación solar e insolación:",
        body_style
    ))
    story.append(Spacer(1, 2))

    th_tx = [
        Paragraph("ID Exp.", th_xs),
        Paragraph("Pasos 1-2: Desescalado", th_xs),
        Paragraph("Paso 3: Compute Bias", th_xs),
        Paragraph("Paso 4: Apply Bias", th_xs),
        Paragraph("Paso 5: Merging Data", th_xs),
        Paragraph("Hipótesis Física Diurna (Tmax)", th_xs),
    ]
    rows_tx = [
        [
            Paragraph("<b>EXP-TX01</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Coefs neutros.<br/><b>[P2]</b> Bilineal a 0.05° sin DEM.<br/>Salida: <code>tmax_down_*.nc</code>", td_xs),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: IDW (3.5°, nmin=4, nmax=12)", td_xs),
            Paragraph("• Ajuste multiplicativo sobre grillas desescaladas.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>SBA monocapa</b> (1 pasada a 1.0°)<br/>• Interp: IDW (3.5°)<br/>• Covariables: Ninguna", td_xs),
            Paragraph("<b>Control Nulo Térmico Diurno:</b> Cuantifica el error sistemático al ignorar el relieve y la insolación solar diurna.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX02</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión estación–DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM 90m (0.05°).", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Normal (norm)</b><br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Mapeo cuantil gaussiano.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• <b>Covariable: DEM</b><br/>• Residuos: OKR", td_xs),
            Paragraph("<b>Gradiente Adiabático Diurno:</b> Modela enfriamiento por ascenso adiabático (&part;<i>T</i>/&part;<i>z</i> &approx; -6.5 °C/km) en Cordillera Central y Sierra Madre.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX03</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión DEM + Pendiente.<br/><b>[P2]</b> IDW local sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Skew-Normal (snorm)</b><br/>• Interp: OKR por bloques (3.5°)", td_xs),
            Paragraph("• Mapeo cuantil asimétrico.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Pend + Lat + Lon</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Asimetría por Laderas y Frentes Fríos:</b> Captura asimetría térmica por inclinación del terreno y descensos térmicos transitorios por <i>Nortes</i>.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX04</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Desescalado orográfico 3D.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: <b>NN-3D con DEM (&Delta;<i>z</i>)</b>", td_xs),
            Paragraph("• Ajuste con control altimétrico vertical.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Pend + Aspect</b><br/>• Residuos: OKR", td_xs),
            Paragraph("<b>Insolación Diferencial según Orientación:</b> Laderas este reciben calentamiento matutino; laderas oeste acumulan el máximo vespertino.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX05</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión mensual altimétrica.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Gumbel Máximos</b><br/>• Interp: OKR por bloques", td_xs),
            Paragraph("• Mapeo cuantil para extremos (&gt;P95).<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Lat + Lon</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Olas de Calor en Depresiones Áridas:</b> Ajusta picos extremos (&gt;38 °C a 40 °C) en Hoya de Enriquillo (-40 msnm), Valle de Azua y Golfo de Fonseca.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX06</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión regional con DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Ajuste proporcional estándar.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>Barnes (BSc)</b> (3 pasadas)<br/>• Residuos: Filtro gaussiano continuo<br/>• Covariables: Ninguna", td_xs),
            Paragraph("<b>Llanuras y Brisas Costeras Diurnas:</b> Transición espacial continua sin saltos abruptos a lo largo de llanuras litorales del Caribe y planicies de RD.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX07</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión altimétrica con DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>mbmon</code> (sesgo mensual fijo)<br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Ajuste por mes climatológico.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>Cressman (CSc)</b> (4 pasadas: 1.0°, 0.75°, 0.5°, 0.25°)<br/>• Covariables: Ninguna", td_xs),
            Paragraph("<b>Valles Intermontanos Confinados:</b> Radios decrecientes para evitar que estaciones cálidas de valles profundos contaminen laderas altas vecinas.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TX08</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Multivariado DEM + Slope + Aspect.<br/><b>[P2]</b> Proyección topográfica completa.", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: Skew-Normal<br/>• Interp: OKR por bloques", td_xs),
            Paragraph("• Corrección distribucional asimétrica.<br/>Salida: <code>tmax_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Slope + Aspect + Coords</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Máxima Complejidad Diurna:</b> Acoplamiento determinístico completo de topografía, insolación solar y modelación asimétrica de residuales.", td_xs),
        ],
    ]
    t_table_tx = Table([th_tx] + rows_tx, colWidths=[0.60 * inch, 1.35 * inch, 1.30 * inch, 1.05 * inch, 1.35 * inch, 1.85 * inch])
    t_table_tx.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
    ]))
    story.append(t_table_tx)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 5: SUITE C - TEMPERATURA MÍNIMA (TMIN - 8 EXP)
    # =========================================================================
    story.append(Paragraph("6. Suite C: Temperatura Mínima Nocturna (CHIRTS Tmin: 8 Experimentos)", h1_style))
    story.append(Paragraph(
        "Batería experimental estructurada según los 5 pasos de CDT: desescalado altimétrico, enfriamiento radiativo, inversiones nocturnas y frentes fríos:",
        body_style
    ))
    story.append(Spacer(1, 2))

    th_tn = [
        Paragraph("ID Exp.", th_xs),
        Paragraph("Pasos 1-2: Desescalado", th_xs),
        Paragraph("Paso 3: Compute Bias", th_xs),
        Paragraph("Paso 4: Apply Bias", th_xs),
        Paragraph("Paso 5: Merging Data", th_xs),
        Paragraph("Hipótesis Física Nocturna (Tmin)", th_xs),
    ]
    rows_tn = [
        [
            Paragraph("<b>EXP-TN01</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Coefs neutros.<br/><b>[P2]</b> Bilineal a 0.05° sin DEM.<br/>Salida: <code>tmin_down_*.nc</code>", td_xs),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Ajuste sobre grillas desescaladas 1991–2020.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>SBA monocapa</b> (1 pasada a 1.0°)<br/>• Interp: IDW (3.5°)<br/>• Covariables: Ninguna", td_xs),
            Paragraph("<b>Control Nulo Nocturno:</b> Mide el sesgo nocturno base al ignorar el enfriamiento radiativo y el drenaje de aire frío.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN02</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión estación–DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM 90m (0.05°).", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Normal (norm)</b><br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Mapeo cuantil gaussiano.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK Solo DEM</b> (3 pasadas: 1.0°, 0.75°, 0.5°)<br/>• <b>Covariable: DEM</b><br/>• Residuos: OKR", td_xs),
            Paragraph("<b>Gradiente Térmico Nocturno Ambiental:</b> Modela la tasa vertical nocturna estándar en zonas abiertas sin inversión térmica marcada.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN03</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión DEM + Pendiente.<br/><b>[P2]</b> IDW local sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Skew-Normal (snorm)</b><br/>• Interp: OKR por bloques (3.5°)", td_xs),
            Paragraph("• Mapeo cuantil en cola fría.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Pend + Lat + Lon</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Invasiones de Frentes Fríos ('Nortes'):</b> Captura las caídas abruptas y asimétricas de temperatura en la vertiente Atlántica durante el invierno boreal.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN04</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Desescalado orográfico 3D.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: <b>NN-3D con DEM (&Delta;<i>z</i>)</b>", td_xs),
            Paragraph("• Ajuste con aislamiento vertical estricto.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Pend + Lat + Lon</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Inversiones Térmicas Nocturnas (Cold-Air Pooling):</b> Evita contaminación térmica entre cimas cálidas y valles fríos (Constanza, Valle Nuevo, Quetzaltenango).", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN05</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión altimétrica con DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: <b>Gumbel Mínimos</b><br/>• Interp: OKR por bloques", td_xs),
            Paragraph("• Mapeo cuantil para colas frías (&lt;P05).<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Lat + Lon</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Heladas Agronómicas y Extremos Bajo Cero:</b> Modela eventos de temperaturas mínimas extremas (&lt;0 °C) en altiplanos y cumbres montañosas elevadas.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN06</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión regional con DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>mbvar</code> (&plusmn;5 d)<br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Ajuste proporcional estándar.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>Barnes (BSc)</b> (3 pasadas gaussianas)<br/>• Residuos: Ponderación gaussiana<br/>• Covariables: Ninguna", td_xs),
            Paragraph("<b>Amortiguamiento Marino y Llanuras Homogéneas:</b> Representa el efecto regulador térmico del océano en costas caribeñas y valles aluviales amplios.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN07</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Regresión altimétrica con DEM.<br/><b>[P2]</b> Bilineal sobre DEM SRTM.", td_xs),
            Paragraph("• Método: <code>mbmon</code> (sesgo mensual fijo)<br/>• Interp: IDW (3.5°)", td_xs),
            Paragraph("• Corrección mensual estacional.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>Cressman (CSc)</b> (4 pasadas: 1.0°, 0.75°, 0.5°, 0.25°)<br/>• Covariables: Ninguna", td_xs),
            Paragraph("<b>Pozas de Aire Frío Confinadas:</b> Radios decrecientes para evitar disipar el aire frío estancado en depresiones hacia cordilleras adyacentes.", td_xs),
        ],
        [
            Paragraph("<b>EXP-TN08</b>", td_xs_bold),
            Paragraph("<b>[P1]</b> Multivariado DEM + Slope + Aspect.<br/><b>[P2]</b> Proyección topográfica completa.", td_xs),
            Paragraph("• Método: <code>qmdist</code><br/>• Distribución: Skew-Normal<br/>• Interp: <b>NN-3D con DEM (&Delta;<i>z</i>)</b>", td_xs),
            Paragraph("• Corrección con restricción vertical &Delta;<i>z</i>.<br/>Salida: <code>tmin_adj_*.nc</code>", td_xs),
            Paragraph("• Método: <b>RK</b> (3 pasadas)<br/>• <b>Covariables: DEM + Slope + Aspect + Coords</b><br/>• Residuos: OKR por bloques", td_xs),
            Paragraph("<b>Máxima Complejidad Nocturna:</b> Acoplamiento total de drenaje catabático gravitacional en laderas inclinadas y formación de pozas frías en valles cerrados.", td_xs),
        ],
    ]
    t_table_tn = Table([th_tn] + rows_tn, colWidths=[0.60 * inch, 1.35 * inch, 1.30 * inch, 1.05 * inch, 1.35 * inch, 1.85 * inch])
    t_table_tn.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
    ]))
    story.append(t_table_tn)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 6: GRILLAS, BUFFER, HARDWARE Y RENDIMIENTO
    # =========================================================================
    story.append(Paragraph("7. Configuración Espacial, Recursos de Cómputo y Tiempos de Ejecución", h1_style))
    story.append(Paragraph(
        "• <b>Opciones de Grilla en CDT (<code>grid$from</code>):</b> <b><code>from: \"data\"</code></b> (Grilla nativa satelital 0.05° ~5.5 km) garantiza <b>coincidencia geométrica 1:1</b> con CHIRPS crudo en <code>EXP-R01</code> a <code>EXP-R06</code> y <code>EXP-R08</code> a <code>EXP-R10</code>, permitiendo diferencias directas píxel a píxel (&Delta; = Corregido - Original). <b><code>from: \"ncdf\"</code></b> (DEM SRTM 0.01° ~1.1 km) es <b>obligatorio</b> en Desescalado de Temperatura (<code>Downscaling Data</code>) para proyectar el gradiente adiabático (&part;<i>T</i>/&part;<i>z</i> &approx; -6.5 °C/km) a cumbres &gt;3,000 m (Pico Duarte, Tajumulco) y valles (Constanza, Azua), y en <code>EXP-R07</code> (RK Orográfico).<br/><br/>"
        "• <b>Recorte con Shapefile (<i>Blanking</i>) y Buffer Óptimo de 10 km:</b> Para una celda de 0.05° (diagonal = 7.73 km), un <b>buffer de 10 km (~2 celdas)</b> supera la diagonal, evita pérdidas en costas oblicuas (45°) y asegura la cobertura completa de islas (Roatán, Saona, Beata), golfos y cuencas binacionales.",
        body_style
    ))
    story.append(Spacer(1, 3))

    story.append(Paragraph("7.1. Plataforma de Cómputo Calibrada: Intel Core i9-10850K @ 3.60GHz, 32 GB RAM, NVMe 400 GB (Ubuntu 24.04.5 LTS)", h2_style))
    th_hw = [Paragraph("Componente", th_style), Paragraph("Especificación de la Plataforma", th_style), Paragraph("Evaluación de Desempeño en CDT", th_style)]
    rows_hw = [
        [Paragraph("<b>CPU</b>", td_bold), Paragraph("<b>Intel(R) Core(TM) i9-10850K CPU @ 3.60GHz</b><br/>10 Núcleos / 20 Hilos (Base 3.6 GHz, Turbo 5.2 GHz)<br/>Caché L3 Intel Smart Cache: 20 MB", td_style), Paragraph("<b>Excelente Rendimiento Multihilo:</b> 10 núcleos Comet Lake de alta frecuencia. Permite despachar <b>hasta 18 workers paralelos</b> continuos manteniendo 2 hilos reservados para el sistema operativo sin sobrecalentamiento ni contención.", td_style)],
        [Paragraph("<b>RAM</b>", td_bold), Paragraph("<b>32 GB DDR4 @ 3200 MT/s</b><br/>Dual-Channel (~51.2 GB/s)", td_style), Paragraph("<b>Capacidad Óptima (Sin Paginación / Cero OOM):</b> En mallas 0.05° consume ~2.5–4.5 GB con 18 workers (<b>&lt;15% de la RAM</b>). En mallas 0.01° consume ~8–12 GB (<b>&lt;38% de la RAM</b>). Cero swapping a disco.", td_style)],
        [Paragraph("<b>Disco</b>", td_bold), Paragraph("<b>SSD NVMe M.2 PCIe 400 GB</b><br/>Lectura/Escritura &gt; 3000 MB/s", td_style), Paragraph("<b>Elimina Cuello de Botella I/O:</b> La lectura y escritura masiva de los <b>10,958 archivos NetCDF diarios</b> por experimento (30 años) se ejecuta a máxima velocidad de bus PCIe sin latencia de cabezal.", td_style)],
        [Paragraph("<b>Sistema Operativo</b>", td_bold), Paragraph("<b>Linux Ubuntu 24.04.5 LTS (x86_64)</b><br/>Kernel Linux con POSIX Forking", td_style), Paragraph("<b>Arquitectura de Ejecución Nativa:</b> Clústeres de procesos `doParallel` / `foreach` mediante `makeCluster(type='FORK')` o sockets locales en Linux, con gestión eficiente de descriptores de archivos.", td_style)],
    ]
    t_table_hw = Table([th_hw] + rows_hw, colWidths=[0.90 * inch, 2.30 * inch, 4.30 * inch])
    t_table_hw.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4.0),
    ]))
    story.append(t_table_hw)
    story.append(Spacer(1, 3))

    story.append(Paragraph("7.2. Diagnóstico Técnico de CDT y Tiempos de Cómputo Calibrados (18 Núcleos en Linux Ubuntu)", h2_style))
    story.append(Paragraph(
        "<b>Diagnóstico de Paralelización y Rendimiento en Linux Ubuntu:</b> (1) <i>Modo Headless:</i> La orquestación en Python elimina la dependencia de Tcl/Tk e inyecta paralelismo estable en <code>.cdtData$Config$parallel</code> mediante clústeres multiproceso con 18 workers activos. "
        "(2) <i>Diferenciación de Carga:</i> Métodos algebraicos rápidos (IDW, Barnes, Shepard) procesan 30 años (10,958 días) en ~1.1–2.2 h. Regression Kriging en temperatura con DEM toma ~1.8–2.3 h. En lluvia, la optimización vectorizada en cuantiles empíricos (R13) y Shepard multiescala reducen drásticamente la latencia. "
        "(3) <i>Formato de Monitoreo:</i> El orquestador reporta duraciones formateadas (ej. <code>2h 15m 30s</code>) en consola y en el <code>manifest.json</code>.",
        body_style
    ))
    story.append(Spacer(1, 2))

    th_tm = [Paragraph("Suite de Experimentos", th_style), Paragraph("Número de Exp. y Métodos Clave", th_style), Paragraph("Tiempo Calibrado (18 Núcleos)", th_style), Paragraph("Memoria RAM", th_style)]
    rows_tm = [
        [Paragraph("<b>Precipitación (CHIRPS)</b>", td_bold), Paragraph("<b>15 Experimentos (Fase 1: R01–R10, Fase 2: R11–R15):</b> RnoR Suave, Shepard Local/Mediana, Spheremap, QM eCDF, Barnes, CSc, OKR Bloques y RK", td_style), Paragraph("<b>~35.0 a 38.0 horas</b><br/><font size=6.5 color='#64748B'>(Optimizado con R13 vectorizado)</font>", td_style), Paragraph("~2.5–4.5 GB", td_style)],
        [Paragraph("<b>Temperatura Máxima (Tmax)</b>", td_bold), Paragraph("<b>8 Experimentos (EXP-TX01 a TX08):</b> Control, RK Solo DEM, Skew-Normal, NN-3D Aspecto, Gumbel Olas Calor, Lognorm, Cressman, Barnes", td_style), Paragraph("<b>~14.0 a 15.0 horas</b>", td_style), Paragraph("~3.5–4.6 GB", td_style)],
        [Paragraph("<b>Temperatura Mínima (Tmin)</b>", td_bold), Paragraph("<b>8 Experimentos (EXP-TN01 a TN08):</b> Control, RK Solo DEM, Skew-Normal 'Nortes', NN-3D Inversiones, Gumbel Heladas, Lognorm, Cressman, Barnes", td_style), Paragraph("<b>~14.0 a 15.0 horas</b>", td_style), Paragraph("~3.5–4.6 GB", td_style)],
        [Paragraph("<b>TOTAL BATERÍA COMPLETA</b>", td_bold), Paragraph("<b>31 Experimentos Completos (15 Precipitación + 8 Tmax + 8 Tmin / 1991–2020)</b>", td_bold), Paragraph("<b>~63.0 a 68.0 horas</b><br/><font size=6.5 color='#64748B'>(~2.7 días continuos en segundo plano)</font>", td_bold), Paragraph("<b>Máx. 4.6 GB (< 15%)</b>", td_bold)],
    ]
    t_table_tm = Table([th_tm] + rows_tm, colWidths=[1.50 * inch, 3.10 * inch, 1.45 * inch, 1.45 * inch])
    t_table_tm.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.5),
    ]))
    story.append(t_table_tm)

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 9: VALIDACIÓN CRUZADA INDEPENDIENTE Y MÉTRICAS CUANTITATIVAS
    # =========================================================================
    story.append(Paragraph("8. Validación Cruzada Independiente (Holdout por CSV) y Métricas Cuantitativas", h1_style))
    story.append(Paragraph(
        "<b>Mecanismo de Evaluación de CDT y Partición Ciega (Holdout Validation):</b><br/>"
        "Climate Data Tools (CDT) cuenta con módulos de validación espacial y cruzada para evaluar la exactitud de los campos interpolados frente a observaciones de superficie. "
        "Para garantizar una evaluación <b>estrictamente independiente, ciega y no sesgada</b> (evitando el sobreajuste o <i>overfitting</i> de calibrar y validar con las mismas estaciones), "
        "el orquestador automatizado (<code>launcher/station_manager.py</code>) desacopla el catálogo de estaciones en dos grupos disjuntos antes de iniciar la corrida de CDT:<br/>"
        "• <b>Subconjunto de Entrenamiento / Calibración (~80–90%):</b> Único subconjunto asimilado por CDT en el Paso 1 (coeficientes de sesgo distribucional) y Paso 3 / Paso 5 (fusión espacial de residuales y modelos de regresión con covariables).<br/>"
        "• <b>Subconjunto de Validación Ciega / Holdout (~10–20%, 29 estaciones de prueba):</b> Omitido por completo del flujo de cómputo; CDT no tiene acceso alguno a sus datos durante el desescalado ni la interpolación.<br/>"
        "• <b>Mecanismo de Extracción y Emparejamiento:</b> Tras finalizar la reconstrucción y el ensamblado NetCDF 3D (1991–2020), se extraen automáticamente las series del píxel coincidente con las coordenadas (&lambda;, &phi;) de cada estación retenida, generando pares temporales sincronizados (<i>S<sub>k,t</sub>, O<sub>k,t</sub></i>) evaluados con las siguientes métricas cuantitativas:",
        body_style
    ))
    story.append(Spacer(1, 1))

    story.append(Paragraph("8.1. Métricas Continuas (Magnitud, Dispersión y Distribución del Error)", h2_style))
    th_val_c = [
        Paragraph("Métrica", th_val),
        Paragraph("Ecuación Matemática", th_val),
        Paragraph("Qué Cuantifica y Rango Óptimo", th_val),
        Paragraph("Interpretación Física y Climatológica Regional", th_val),
    ]
    rows_val_c = [
        [
            Paragraph("<b>KGE</b><br/><i>Kling-Gupta Efficiency</i><br/>(Gupta et al., 2009)", td_val_bold),
            Paragraph("<b>KGE</b> = 1 &minus; &radic;[(<i>r</i> &minus; 1)<sup>2</sup> + (&beta; &minus; 1)<sup>2</sup> + (&gamma; &minus; 1)<sup>2</sup>]<br/>&bull; &beta; = &mu;<sub>S</sub> / &mu;<sub>O</sub> &nbsp;(sesgo medio)<br/>&bull; &gamma; = (&sigma;<sub>S</sub>/&mu;<sub>S</sub>) / (&sigma;<sub>O</sub>/&mu;<sub>O</sub>) &nbsp;(variabilidad)", td_val),
            Paragraph("Descompone el error en 3 ejes ortogonales: dinámica temporal (<i>r</i>), sesgo de volumen (&beta;) y dispersión relativa (&gamma;).<br/><b>Rango:</b> (&minus;&infin;, 1]. <b>Óptimo: 1.0</b>.<br/><i>KGE &gt; 0.3 indica habilidad predictiva real sobre la media.</i>", td_val),
            Paragraph("<b>Métrica rectora multiobjetivo:</b> Equilibra dinámica sinóptica, conservación de masa y dispersión. Evita que modelos que alisan la varianza obtengan puntajes artificialmente altos.", td_val),
        ],
        [
            Paragraph("<b>r</b><br/><i>Correlación de Pearson</i>", td_val_bold),
            Paragraph("<i>r</i> = &Sigma;[(<i>S<sub>i</sub></i>&minus;<i>S̄</i>)(<i>O<sub>i</sub></i>&minus;<i>Ō</i>)] / [&radic;&Sigma;(<i>S<sub>i</sub></i>&minus;<i>S̄</i>)<sup>2</sup> &radic;&Sigma;(<i>O<sub>i</sub></i>&minus;<i>Ō</i>)<sup>2</sup>]", td_val),
            Paragraph("Covarianza lineal y sincronía temporal de fases de la señal.<br/><b>Rango:</b> [&minus;1, 1]. <b>Óptimo: 1.0</b>.", td_val),
            Paragraph("<b>Sincronía de eventos:</b> Mide la fidelidad para captar la llegada y ciclo estacional de ondas tropicales, frentes fríos (<i>Nortes</i>) y giros ciclónicos, independiente del sesgo de escala.", td_val),
        ],
        [
            Paragraph("<b>RMSE</b><br/><i>Root Mean Square Error</i>", td_val_bold),
            Paragraph("<b>RMSE</b> = &radic;[&Sigma;(<i>S<sub>i</sub></i> &minus; <i>O<sub>i</sub></i>)<sup>2</sup> / <i>N</i>]", td_val),
            Paragraph("Magnitud cuadrática media del error en unidades físicas (mm o &deg;C).<br/><b>Rango:</b> [0, &infin;). <b>Óptimo: 0.0</b>.", td_val),
            Paragraph("<b>Sensibilidad a extremos:</b> Penaliza desproporcionadamente errores grandes; detecta fallas severas en núcleos convectivos intensos (&gt;100 mm) u olas de calor (&gt;38 &deg;C).", td_val),
        ],
        [
            Paragraph("<b>MAE</b><br/><i>Mean Absolute Error</i>", td_val_bold),
            Paragraph("<b>MAE</b> = &Sigma;|<i>S<sub>i</sub></i> &minus; <i>O<sub>i</sub></i>| / <i>N</i>", td_val),
            Paragraph("Magnitud lineal promedio del error absoluto en unidades físicas (mm o &deg;C).<br/><b>Rango:</b> [0, &infin;). <b>Óptimo: 0.0</b>.", td_val),
            Paragraph("<b>Magnitud típica diaria:</b> Discrepancia esperada en un día cualquiera; ofrece una lectura no sesgada por valores atípicos (<i>outliers</i>) aislados.", td_val),
        ],
        [
            Paragraph("<b>PBIAS</b><br/><i>Percent Bias</i>", td_val_bold),
            Paragraph("<b>PBIAS</b> = [&Sigma;(<i>S<sub>i</sub></i> &minus; <i>O<sub>i</sub></i>) / &Sigma;<i>O<sub>i</sub></i>] &times; 100%", td_val),
            Paragraph("Desviación porcentual neta acumulada de volumen.<br/><b>Rango:</b> (&minus;&infin;, &infin;)%. <b>Óptimo: 0.0%</b>.", td_val),
            Paragraph("<b>Conservación de balance:</b> Cuantifica el déficit (&minus;) o superávit (+) acumulado total; esencial en balances hídricos para no falsear la disponibilidad de agua en cuencas.", td_val),
        ],
    ]
    t_val_c = Table([th_val_c] + rows_val_c, colWidths=[0.95 * inch, 1.90 * inch, 2.30 * inch, 2.35 * inch])
    t_val_c.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
    ]))
    story.append(t_val_c)
    story.append(Spacer(1, 2))

    story.append(Paragraph("8.2. Métricas Categóricas y Detección de Lluvia (&ge; 1.0 mm/día)", h2_style))
    story.append(Paragraph(
        "<font size=6.5 color='#475569'><i>Tabla de contingencia 2&times;2: <b>a</b> = Aciertos (S&ge;1, O&ge;1), <b>b</b> = Falsas Alarmas (S&ge;1, O&lt;1), <b>c</b> = Fallos (S&lt;1, O&ge;1), <b>d</b> = Negativos Correctos (S&lt;1, O&lt;1), <b>n</b> = total días evaluados.</i></font>",
        body_style
    ))
    th_val_k = [
        Paragraph("Métrica", th_val),
        Paragraph("Ecuación Matemática", th_val),
        Paragraph("Qué Cuantifica y Rango Óptimo", th_val),
        Paragraph("Interpretación Física y Climatológica Regional", th_val),
    ]
    rows_val_k = [
        [
            Paragraph("<b>POD</b><br/><i>Probability of Detection</i>", td_val_bold),
            Paragraph("<b>POD</b> = <i>a</i> / (<i>a</i> + <i>c</i>)", td_val),
            Paragraph("Fracción de días lluviosos observados que fueron detectados por el modelo.<br/><b>Rango:</b> [0, 1]. <b>Óptimo: 1.0</b>.", td_val),
            Paragraph("<b>Sensibilidad de lluvia:</b> Mide la eficacia del satélite fusionado para captar precipitación real sin perder eventos agronómicamente significativos.", td_val),
        ],
        [
            Paragraph("<b>FAR</b><br/><i>False Alarm Ratio</i>", td_val_bold),
            Paragraph("<b>FAR</b> = <i>b</i> / (<i>a</i> + <i>b</i>)", td_val),
            Paragraph("Fracción de lluvia simulada que resultó ser día seco en superficie.<br/><b>Rango:</b> [0, 1]. <b>Óptimo: 0.0</b>.", td_val),
            Paragraph("<b>Control de lloviznas espurias:</b> Cuantifica la persistencia del efecto <i>drizzle</i> y falsa lluvia por cirros fríos; clave para validar la máscara RnoR en la Canícula.", td_val),
        ],
        [
            Paragraph("<b>FBI</b><br/><i>Frequency Bias Index</i>", td_val_bold),
            Paragraph("<b>FBI</b> = (<i>a</i> + <i>b</i>) / (<i>a</i> + <i>c</i>)", td_val),
            Paragraph("Razón entre días lluviosos simulados vs. observados.<br/><b>Rango:</b> [0, &infin;). <b>Óptimo: 1.0</b>.", td_val),
            Paragraph("<b>Sesgo de frecuencia:</b> FBI &gt; 1 denota tendencia crónica a simular días de lluvia en exceso; FBI &lt; 1 indica subestimación en la ocurrencia de eventos.", td_val),
        ],
        [
            Paragraph("<b>ETS</b><br/><i>Equitable Threat Score</i><br/>(Gilbert Skill Score)", td_val_bold),
            Paragraph("<b>ETS</b> = (<i>a</i> &minus; <i>a<sub>r</sub></i>) / (<i>a</i> + <i>b</i> + <i>c</i> &minus; <i>a<sub>r</sub></i>)<br/>&bull; <i>a<sub>r</sub></i> = (<i>a</i>+<i>b</i>)(<i>a</i>+<i>c</i>) / <i>n</i>", td_val),
            Paragraph("Detección equitativa penalizando falsas alarmas y fallos, descontando aciertos fortuitos.<br/><b>Rango:</b> [&minus;1/3, 1]. <b>Óptimo: 1.0</b>.", td_val),
            Paragraph("<b>Destreza sobre el azar:</b> Excluye los aciertos que ocurrirían por mera probabilidad climatológica; ETS &gt; 0 certifica habilidad predictiva real de la fusión.", td_val),
        ],
        [
            Paragraph("<b>HSS</b><br/><i>Heidke Skill Score</i>", td_val_bold),
            Paragraph("<b>HSS</b> = 2(<i>ad</i> &minus; <i>bc</i>) / [(<i>a</i>+<i>c</i>)(<i>c</i>+<i>d</i>) + (<i>a</i>+<i>b</i>)(<i>b</i>+<i>d</i>)]", td_val),
            Paragraph("Exactitud de clasificación binaria (lluvia / no-lluvia) relativa al azar.<br/><b>Rango:</b> (&minus;&infin;, 1]. <b>Óptimo: 1.0</b>.", td_val),
            Paragraph("<b>Habilidad categórica global:</b> Evalúa conjuntamente el acierto en días secos (rachas sin lluvia en Corredor Seco) y días húmedos, validando la Canícula.", td_val),
        ],
    ]
    t_val_k = Table([th_val_k] + rows_val_k, colWidths=[0.95 * inch, 1.90 * inch, 2.30 * inch, 2.35 * inch])
    t_val_k.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), SECONDARY),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
        ("TOPPADDING", (0, 0), (-1, -1), 1.3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3.0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3.0),
    ]))
    story.append(t_val_k)
    story.append(Spacer(1, 2))

    story.append(Paragraph("8.3. Ensamblado Multitemporal y Cumplimiento Estricto del Estándar CF-1.8", h2_style))
    story.append(Paragraph(
        "El módulo <code>launcher/netcdf_assembler.py</code> consolida los 10,958 archivos diarios 2D en un único archivo NetCDF 3D (time, lat, lon):<br/>"
        "• <b>Ejes estándar:</b> <code>time</code> (días gregorianos estándar desde 1991-01-01, eje 'T'), <code>latitude</code> (degrees_north, eje 'Y'), <code>longitude</code> (degrees_east, eje 'X').<br/>"
        "• <b>Variables:</b> <code>precipitation_amount</code> (mm) con <i>cell_methods: \"time: sum\"</i> y <code>air_temperature</code> (°C) con <i>cell_methods: \"time: mean\"</i>.<br/>"
        "• <b>Atributos Globales y Optimización:</b> <i>Conventions = \"CF-1.8\"</i>, compresión <i>Deflate (level=4)</i> con chunking espacial optimizado para consultas temporales rápidas.",
        body_style
    ))

    story.append(PageBreak())

    # =========================================================================
    # PÁGINA 8: REFERENCIAS BIBLIOGRÁFICAS CIENTÍFICAS VERIFICADAS
    # =========================================================================
    story.append(Paragraph("9. Referencias Bibliográficas Científicas Verificadas", h1_style))
    story.append(Paragraph("Las siguientes 21 publicaciones indexadas sustentan física, estadística y metodológicamente los experimentos propuestos:", body_style))
    story.append(Spacer(1, 1))

    references_data = [
        ("Amador, J. A., Alfaro, E. J., Lizano, O. G., & Magaña, V. O. (2006).",
         "<i>Atmospheric forcing of the eastern tropical Pacific: A review.</i> Prog. Oceanogr., 69(2–4), 101–142. DOI: <a href='https://doi.org/10.1016/j.pocean.2006.03.007'>10.1016/j.pocean.2006.03.007</a>",
         "<b>Aporte:</b> Modela la interacción sinóptica del forzamiento atmosférico, vientos y orografía en Centroamérica y el Caribe para Regression Kriging (RK)."),
        
        ("Barnes, S. L. (1964).",
         "<i>A technique for maximizing details in numerical weather map analysis.</i> J. Appl. Meteorol., 3(4), 396–409. DOI: <a href='https://doi.org/10.1175/1520-0450(1964)003<0396:ATFMDI>2.0.CO;2'>10.1175/1520-0450(1964)003&lt;0396:ATFMDI&gt;2.0.CO;2</a>",
         "<b>Aporte:</b> Fundamenta el Esquema de Barnes (BSc) para análisis objetivo continuo gaussiano en zonas costeras e insulares."),
        
        ("Coles, S. (2001).",
         "<i>An Introduction to Statistical Modeling of Extreme Values.</i> Springer-Verlag, London. DOI: <a href='https://doi.org/10.1007/978-1-4471-3675-0'>10.1007/978-1-4471-3675-0</a>",
         "<b>Aporte:</b> Sustenta la aplicación de la distribución Gumbel (Valores Extremos) para olas de calor en valles áridos (Azua, Enriquillo, Fonseca)."),
        
        ("Cressman, G. P. (1959).",
         "<i>An operational objective analysis system.</i> Mon. Weather Rev., 87(10), 367–374. DOI: <a href='https://doi.org/10.1175/1520-0493(1959)087<0367:AOOAS>2.0.CO;2'>10.1175/1520-0493(1959)087&lt;0367:AOOAS&gt;2.0.CO;2</a>",
         "<b>Aporte:</b> Base teórica del método de correcciones sucesivas con radio de corte decreciente en CDT."),
        
        ("Daly, C., Halbleib, M., Smith, J. I., Gibson, W. P., Doggett, M. K., Taylor, G. H., Curtis, J., & Pasteris, P. P. (2008).",
         "<i>Physiographically sensitive mapping of temperature and precipitation across the conterminous United States.</i> Int. J. Climatol., 28(15), 2031–2064. DOI: <a href='https://doi.org/10.1002/joc.1688'>10.1002/joc.1688</a>",
         "<b>Aporte:</b> Sustenta la incorporación de pendiente, orientación de ladera (<i>aspect</i>) y DEM en GLM para gradientes térmicos y sombras orográficas."),
        
        ("Dinku, T., Thomson, M. C., Cousin, R., del Corral, J., Ceccato, P., Hansen, J., & Connor, S. J. (2018).",
         "<i>Enhancing National Climate Services (ENACTS) for development in Africa.</i> Clim. Dev., 10(7), 664–672. DOI: <a href='https://doi.org/10.1080/17565529.2017.1405784'>10.1080/17565529.2017.1405784</a>",
         "<b>Aporte:</b> Documento metodológico oficial del marco ENACTS y Climate Data Tools (CDT) para generación de mallas climáticas de alta resolución."),
        
        ("Funk, C., Peterson, P., Landsfeld, M., Pedreros, D., Verdin, J., Shukla, S., Husak, G., Rowland, J., Harrison, L., Hoell, A., & Michaelsen, J. (2015).",
         "<i>The climate hazards group infrared precipitation with stations—a new environmental record for monitoring extremes.</i> Sci. Data, 2(1), 150066. DOI: <a href='https://doi.org/10.1038/sdata.2015.66'>10.1038/sdata.2015.66</a>",
         "<b>Aporte:</b> Describe la arquitectura de CHIRPS v2.0 y documenta la sobreestimación de lloviznas espurias (<i>drizzle</i>) que motiva la máscara RnoR."),
        
        ("Verdin, A., Funk, C., Peterson, P., Landsfeld, M., Tuholske, C., & Grace, K. (2020).",
         "<i>Development and validation of the CHIRTS-daily quasi-global high-resolution daily temperature data set.</i> Sci. Data, 7(1), 303. DOI: <a href='https://doi.org/10.1038/s41597-020-00643-7'>10.1038/s41597-020-00643-7</a>",
         "<b>Aporte:</b> Presenta el producto CHIRTS-daily y justifica la necesidad de desescalado topográfico y corrección de sesgo frente a estaciones."),
        
        ("Gudmundsson, L., Bremnes, J. B., Haugen, J. E., & Engen-Skaugen, T. (2012).",
         "<i>Downscaling RCM precipitation to the station scale using statistical transformations–a comparison of methods.</i> Hydrol. Earth Syst. Sci., 16(9), 3383–3390. DOI: <a href='https://doi.org/10.5194/hess-16-3383-2012'>10.5194/hess-16-3383-2012</a>",
         "<b>Aporte:</b> Proporciona la base matemática del Mapeo de Cuantiles paramétrico (Gamma, Weibull) y empírico para corrección no lineal."),
        
        ("Gupta, H. V., Kling, H., Yilmaz, K. K., & Martinez, G. F. (2009).",
         "<i>Decomposition of the mean squared error and NSE performance measures: Implications for improving hydrological modelling.</i> J. Hydrol., 377(1-2), 80–91. DOI: <a href='https://doi.org/10.1016/j.jhydrol.2009.08.003'>10.1016/j.jhydrol.2009.08.003</a>",
         "<b>Aporte:</b> Descomposición teórica del Kling-Gupta Efficiency (KGE) evaluando correlación, sesgo y dispersión."),
        
        ("Hastenrath, S. (1967).",
         "<i>Rainfall distribution and regime in Central America.</i> Arch. Meteorol. Geophys. Bioklimatol. Ser. B, 15(3), 201–241. DOI: <a href='https://doi.org/10.1007/BF02243853'>10.1007/BF02243853</a>",
         "<b>Aporte:</b> Estudio observacional pionero que documenta y cartografía la distribución de la lluvia, el contraste orográfico Pacífico-Caribe y la estructura estacional de la Canícula (<i>Veranillo</i>)."),
        
        ("Hastenrath, S. (1991).",
         "<i>Climate Dynamics of the Tropics.</i> Atmospheric and Oceanographic Sciences Library, Vol. 8. Springer, Dordrecht. DOI: <a href='https://doi.org/10.1007/978-94-011-3156-8'>10.1007/978-94-011-3156-8</a>",
         "<b>Aporte:</b> Tratado seminal sobre la circulación general tropical, la Zona de Convergencia Intertropical (ZCIT), los vientos Alisios y los patrones de forzamiento macroclimático en Centroamérica y el Caribe."),
        
        ("Hengl, T., Heuvelink, G. B., & Rossiter, D. G. (2007).",
         "<i>About regression-kriging: From equations to case studies.</i> Comput. Geosci., 33(10), 1301–1315. DOI: <a href='https://doi.org/10.1016/j.cageo.2007.05.001'>10.1016/j.cageo.2007.05.001</a>",
         "<b>Aporte:</b> Formaliza el marco teórico de Regression Kriging (RK) híbrido utilizado en CDT para fusionar fondos satelitales con covariables continuas."),
        
        ("Hidalgo, H. G., Alfaro, E. J., & Quesada-Montano, B. (2017).",
         "<i>Observed (1970–1999) climate variability in Central America using a high-resolution meteorological dataset with implication to climate change studies.</i> Clim. Change, 141(1), 13–28. DOI: <a href='https://doi.org/10.1007/s10584-016-1786-y'>10.1007/s10584-016-1786-y</a>",
         "<b>Aporte:</b> Caracteriza la variabilidad pluviométrica y térmica en Centroamérica y valida bases observadas de alta resolución."),
        
        ("Kedem, B., Chiu, L. S., & North, G. R. (1990).",
         "<i>Estimation of mean rain rate: Application to satellite observations.</i> J. Geophys. Res., 95(D2), 1965–1972. DOI: <a href='https://doi.org/10.1029/JD095iD02p01965'>10.1029/JD095iD02p01965</a>",
         "<b>Aporte:</b> Fundamenta la aplicación de la distribución Bernoulli-Lognormal en precipitación convectiva generada por procesos multiplicativos."),
        
        ("Maldonado, T., Rutgersson, A., Amador, J. A., Alfaro, E. J., & Claremar, B. (2016).",
         "<i>Variability of the Caribbean low-level jet during boreal winter: large-scale forcings.</i> Int. J. Climatol., 36(4), 1978–1999. DOI: <a href='https://doi.org/10.1002/joc.4472'>10.1002/joc.4472</a>",
         "<b>Aporte:</b> Analiza la dinámica invernal del CLLJ y su interacción con patrones de precipitación y humedad regional."),
        
        ("Schultz, D. M., Bracken, W. E., & Bosart, L. F. (1998).",
         "<i>Planetary- and synoptic-scale signatures associated with Central American cold surges.</i> Mon. Weather Rev., 126(1), 5–27. DOI: <a href='https://doi.org/10.1175/1520-0493(1998)126<0005:PASSSA>2.0.CO;2'>10.1175/1520-0493(1998)126&lt;0005:PASSSA&gt;2.0.CO;2</a>",
         "<b>Aporte:</b> Justifica el uso de la distribución Skew-Normal en sesgo de temperatura mínima para capturar descensos asimétricos por frentes fríos (<i>Nortes</i>)."),
        
        ("Shepard, D. (1968).",
         "<i>A two-dimensional interpolation function for irregularly-spaced data.</i> Proc. 23rd ACM Nat. Conf., 517–524. DOI: <a href='https://doi.org/10.1145/800186.810616'>10.1145/800186.810616</a>",
         "<b>Aporte:</b> Fundamenta la interpolación local con polinomios de Taylor en terrenos escarpados de red irregular."),
        
        ("Themeßl, M. J., Gobiet, A., & Leuprecht, A. (2011).",
         "<i>Empirical-statistical downscaling and error correction of daily precipitation from regional climate models.</i> Int. J. Climatol., 31(10), 1530–1544. DOI: <a href='https://doi.org/10.1002/joc.2168'>10.1002/joc.2168</a>",
         "<b>Aporte:</b> Proporciona el marco matemático del Mapeo de Cuantiles Empírico (ECDF) no paramétrico para regímenes pluviométricos complejos."),
        
        ("Willmott, C. J., Rowe, C. M., & Philpot, W. D. (1985).",
         "<i>Small-scale climate maps: A sensitivity analysis of some common assumptions associated with grid-point interpolation and contouring.</i> The American Cartographer, 12(1), 5–16. DOI: <a href='https://doi.org/10.1559/152304085783914686'>10.1559/152304085783914686</a>",
         "<b>Aporte:</b> Fundamenta Spheremap para interpolación con distancias de círculo máximo sobre coordenadas esféricas."),
        
        ("WMO / CF Metadata Conventions Committee (2020).",
         "<i>NetCDF Climate and Forecast (CF) Metadata Conventions Version 1.8.</i> World Meteorological Organization. URL: <a href='https://cfconventions.org/'>cfconventions.org</a>",
         "<b>Aporte:</b> Define los estándares para nombres estándar (standard_name), unidades UDUNITS-2 y ejes temporales en NetCDFs ensamblados."),
    ]

    for auth, cit, annot in references_data:
        p_ref = Paragraph(f"• <b>{auth}</b> {cit}<br/>&nbsp;&nbsp;{annot}", ref_style)
        story.append(p_ref)

    # Build using NumberedCanvas for dynamic two-pass page numbers & headers/footers
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[OK] Documento PDF Vertical generado exitosamente en: {output_pdf}")
    return output_pdf


if __name__ == "__main__":
    generate_experiments_pdf()
