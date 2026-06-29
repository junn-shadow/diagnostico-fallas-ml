import sys
from pathlib import Path
import tempfile

# Asegurar que la raíz del proyecto esté en el sys.path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

from app.config.paths import SAMPLES_DIR
from app.dashboard.anomaly_view import render_anomalies
from app.dashboard.charts import (
    render_charts,
    render_tradingview_timeline,
    render_pattern_analysis,
)
from app.dashboard.insights import build_executive_summary, top_templates
from app.dashboard.metrics_view import render_metrics, render_status_strip
from app.dashboard.rootcause_view import render_root_causes
from app.database.repositories import (
    list_incidents,
    list_runs,
    delete_run,
    search_all_incidents,
    get_incident_summary,
)
from app.config.settings import LARGE_LOG_THRESHOLD_ROWS
from app.nlp.model_manager import check_distilbert_status
from app.services.pipeline_service import PipelineService
from app.dashboard.report_generator import (
    generate_html_report,
    generate_json_report,
    generate_csv_report,
)
from app.dashboard.report_utils import generate_report


def get_distilbert_status():
    """Wrapper — runs check_distilbert_status dynamically to reflect actual env variables."""
    return check_distilbert_status()


st.set_page_config(
    page_title="DiagnosticOps ML — Diagnóstico Inteligente de Fallas",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Variables CSS dinámicas para Modo Claro / Oscuro (Sin colores Neón)
with st.sidebar:
    st.markdown(
        """
        <a href="/" target="_self" class="sidebar-brand-link" style="text-decoration: none;">
            <div class="sidebar-brand">
                <div class="sidebar-brand-icon">🔬</div>
                <span class="sidebar-brand-text">DiagnosticOps</span>
            </div>
        </a>
        <div class="sidebar-version">v2.0 · ML Pipeline</div>
        """,
        unsafe_allow_html=True,
    )
    is_dark_mode = st.toggle("🌙 Modo Oscuro", value=True, help="Alterna entre tema claro y oscuro.")
    focus_mode = st.toggle("🔍 Modo Enfoque", value=False, help="Oculta descripciones secundarias y notas para centrar la atención en los datos.")


if is_dark_mode:
    theme_vars = """
    :root {
        --bg-app:           #0f172a;
        --bg-sidebar:       #1e293b;
        --sidebar-accent:   #334155;
        --text-main:        #f1f5f9;
        --text-muted:       #64748b;
        --text-subtle:      #94a3b8;
        --text-sidebar:     #cbd5e1;
        --text-sidebar-h:   #ffffff;
        --border-color:     rgba(255, 255, 255, 0.08);
        --accent:           #0ea5e9;
        --accent-light:     rgba(14, 165, 233, 0.08);
        --accent-hover:     #38bdf8;
        --accent-glow:      rgba(14, 165, 233, 0.15);
        --success:          #10b981;
        --warning:          #f59e0b;
        --danger:           #f43f5e;
        --card-bg:          rgba(30, 41, 59, 0.7);
        --card-shadow:      0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        --card-hover-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --radius-sm:        6px;
        --radius-md:        10px;
        --radius-lg:        14px;
        --radius-xl:        18px;
        --transition:       all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-fast:  all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
        --hero-bg:          radial-gradient(circle at 90% 10%, rgba(14, 165, 233, 0.08) 0%, #1e293b 80%, #0f172a 100%);
        --sidebar-bg-gradient: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    }
    """
else:
    theme_vars = """
    :root {
        --bg-app:           #f8fafc;
        --bg-sidebar:       #0f172a;
        --sidebar-accent:   #1e293b;
        --text-main:        #0f172a;
        --text-muted:       #64748b;
        --text-subtle:      #94a3b8;
        --text-sidebar:     #e2e8f0;
        --text-sidebar-h:   #ffffff;
        --border-color:     rgba(15, 23, 42, 0.08);
        --accent:           #0284c7;
        --accent-light:     #f0f9ff;
        --accent-hover:     #0369a1;
        --accent-glow:      rgba(2, 132, 199, 0.12);
        --success:          #059669;
        --warning:          #d97706;
        --danger:           #e11d48;
        --card-bg:          rgba(255, 255, 255, 0.85);
        --card-shadow:      0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        --card-hover-shadow:0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
        --radius-sm:        6px;
        --radius-md:        10px;
        --radius-lg:        14px;
        --radius-xl:        18px;
        --transition:       all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        --transition-fast:  all 0.1s cubic-bezier(0.4, 0, 0.2, 1);
        --hero-bg:          radial-gradient(circle at 90% 10%, rgba(2, 132, 199, 0.05) 0%, #ffffff 70%, #f8fafc 100%);
        --sidebar-bg-gradient: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    """

# Cargar tema CSS premium personalizado
theme_path = Path(__file__).parent / "custom_theme.css"
if theme_path.exists():
    with open(theme_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>\n{theme_vars}\n{f.read()}</style>", unsafe_allow_html=True)

# CSS específico para Modo Enfoque
if focus_mode:
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            opacity: 0.1 !important;
            transition: opacity 0.3s ease-in-out !important;
        }
        [data-testid="stSidebar"]:hover {
            opacity: 1.0 !important;
        }
        .section-note, .perf-note, .eyebrow, .sidebar-version, .dataset-card {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Calcular métricas rápidas para el hero (si hay resultados en sesión)
_hero_anomalies = 0
_hero_errors = 0
_hero_has_result = "last_result" in st.session_state
if _hero_has_result:
    _r = st.session_state["last_result"]
    _hero_anomalies = _r.anomaly_count
    _hero_errors = int(_r.logs["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum())

_badge_color = (
    "#ef4444"
    if _hero_anomalies > 5
    else "#f59e0b" if _hero_anomalies > 0 else "#10b981"
)
_badge_label = (
    "Crítico"
    if _hero_anomalies > 5
    else "Atención" if _hero_anomalies > 0 else "Estable"
)

if _hero_has_result:
    hero_badge_html = f"""
<div style="text-align:right;min-width:130px;">
<div style="background:{_badge_color};color:#fff;border-radius:8px;padding:0.4rem 0.8rem;font-weight:700;font-size:0.8rem;letter-spacing:0.05em;margin-bottom:0.3rem;">
{_badge_label}
</div>
<div style="font-size:0.75rem;color:#64748b;">{_hero_anomalies} anomalías · {_hero_errors} errores</div>
</div>
"""
else:
    hero_badge_html = ""

st.markdown(
    f"""
<div class="hero">
<div style="display:flex;justify-content:space-between;align-items:flex-start;">
<div>
<span class="eyebrow">DiagnosticOps ML</span>
<h1>Centro de Diagnóstico de Fallas</h1>
<p>Detección de anomalías · Agrupación semántica NLP · Recomendaciones automatizadas</p>
</div>
{hero_badge_html}
</div>
</div>
""",
    unsafe_allow_html=True,
)


# Mostrar banner destacado si se carga una consulta histórica
if st.session_state.get("is_historical_view", False) and "last_result" in st.session_state:
    res = st.session_state["last_result"]
    st.markdown(
        f"""
        <div style="background-color: rgba(37, 99, 235, 0.08); border-left: 5px solid #2563eb; padding: 1.25rem; border-radius: 8px; margin-top: 1rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="color: #1e3a8a; font-family: 'Plus Jakarta Sans', sans-serif;">
                <span style="font-weight: 700; font-size: 1.05rem; display: block; margin-bottom: 0.25rem; color: #1e40af;">📂 Modo de Visualización Histórica Activo</span>
                Estás visualizando los resultados del diagnóstico guardado para el archivo <strong>{res.log_source}</strong> (ID: <code>{res.run_id}</code>). 
                Toda la información del dashboard, métricas y reportes proviene del historial persistido en SQLite.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_exit_lbl, col_exit_btn = st.columns([3, 1])
    with col_exit_btn:
        if st.button("❌ Salir de Vista Histórica", key="exit_hist_view_btn", type="secondary", use_container_width=True):
            st.session_state.pop("last_result", None)
            st.session_state.pop("last_params", None)
            st.session_state["is_historical_view"] = False
            st.rerun()


with st.sidebar:
    uploaded = st.file_uploader("📂 Fuente de logs", type=["log", "txt"])
    use_sample = st.toggle("🧪 Usar dataset de muestra", value=uploaded is None)
    persist = st.toggle("💾 Persistir incidentes", value=True)
    auto_run = st.toggle("⚡ Analizar al cargar", value=False)

    st.divider()
    st.markdown(
        '<div class="sidebar-section-label">Hiperparámetros ML</div>',
        unsafe_allow_html=True,
    )
    contamination = st.slider(
        "🎯 Contaminación (Isolation Forest)",
        min_value=0.01,
        max_value=0.50,
        value=0.15,
        step=0.01,
        help="Proporción estimada de eventos anómalos. Determina el umbral de decisión del algoritmo Isolation Forest para clasificar un log como anomalía.",
    )
    clustering_method = st.selectbox(
        "🧩 Método de Agrupamiento",
        options=["auto", "dbscan", "kmeans"],
        index=0,
        help="Selecciona el algoritmo de machine learning para agrupar las anomalías. 'auto' selecciona el más óptimo según el tamaño y dispersión de los datos.",
    )
    with st.expander("🛠️ Parámetros del Clustering"):
        clustering_eps = st.slider(
            "📏 DBSCAN Epsilon",
            min_value=0.05,
            max_value=2.00,
            value=0.80,
            step=0.05,
            help="Distancia máxima (métrica del coseno en espacio de embeddings) entre dos muestras para considerarlas en el mismo vecindario (DBSCAN).",
        )
        clustering_min_samples = st.slider(
            "🔢 DBSCAN Min Samples",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
            help="Número mínimo de muestras en un vecindario para que un punto sea considerado como punto central en el algoritmo DBSCAN.",
        )
        clustering_n_clusters = st.slider(
            "🌀 Clusters K (K-Means)",
            min_value=2,
            max_value=20,
            value=5,
            step=1,
            help="Número explícito de agrupaciones (centroides) que el algoritmo K-Means buscará identificar en el dataset de logs.",
        )

    st.divider()
    st.markdown(
        '<div class="sidebar-section-label">Motor NLP</div>', unsafe_allow_html=True
    )

    nlp_backend = st.selectbox(
        "🧠 Backend NLP",
        options=["auto", "tfidf", "distilbert"],
        format_func=lambda x: {
            "auto": "Auto (mejor disponible)",
            "tfidf": "TF-IDF (offline)",
            "distilbert": "DistilBERT (HF API)",
        }[x],
        index=0,
        help="Elige el motor para análisis de causa raíz y recomendaciones semánticas.",
    )

    # Compact NLP status pill
    model_status = get_distilbert_status()
    if model_status.available_remote:
        _pill_cls = "connected"
        _pill_txt = "● DistilBERT Remoto"
    elif model_status.available_locally:
        _pill_cls = "connected"
        _pill_txt = "● DistilBERT Local"
    else:
        _pill_cls = "fallback"
        _pill_txt = "● TF-IDF (fallback)"
    st.markdown(
        f'<div class="nlp-status-pill {_pill_cls}">{_pill_txt}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)
    run_button = st.button(
        "▶ Ejecutar diagnóstico", type="primary", use_container_width=True
    )


def resolve_log_path():
    if uploaded is not None:
        with st.spinner("Guardando archivo temporal..."):
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".log")
            temp.write(uploaded.getbuffer())
            temp.close()
            return Path(temp.name)
    if use_sample:
        return SAMPLES_DIR / "sample.log"
    return None


@st.cache_data(show_spinner=False)
def run_pipeline(
    log_path: Path,
    persist: bool,
    contamination: float,
    clustering_method: str,
    clustering_eps: float,
    clustering_min_samples: int,
    clustering_n_clusters: int,
    nlp_backend: str,
    log_source: str | None = None,
):
    with st.spinner("Procesando logs, generando features y calculando riesgo..."):
        return PipelineService().run(
            log_path,
            persist=persist,
            contamination=contamination,
            clustering_method=clustering_method,
            clustering_eps=clustering_eps,
            clustering_min_samples=clustering_min_samples,
            clustering_n_clusters=clustering_n_clusters,
            nlp_backend=nlp_backend,
            log_source=log_source,
        )


current_params = {
    "source": (
        uploaded.name if uploaded is not None else "sample.log" if use_sample else None
    ),
    "contamination": contamination,
    "clustering_method": clustering_method,
    "clustering_eps": clustering_eps,
    "clustering_min_samples": clustering_min_samples,
    "clustering_n_clusters": clustering_n_clusters,
    "nlp_backend": nlp_backend,
}
previous_params = st.session_state.get("last_params", {})

should_run = (
    run_button
    or st.session_state.get("welcome_run", False)
    or ("last_result" not in st.session_state and auto_run)
)

# Si auto_run está activo y hay resultados anteriores, detectar cambios en cualquiera de las herramientas
if auto_run and "last_result" in st.session_state:
    if current_params != previous_params:
        should_run = True

if should_run:
    st.session_state["welcome_run"] = False
    log_path = resolve_log_path()
    if log_path is None:
        st.warning("Carga un archivo log o activa el archivo de muestra.")
        st.stop()

    real_log_source = current_params["source"]
    st.session_state["last_result"] = run_pipeline(
        log_path,
        persist,
        contamination=contamination,
        clustering_method=clustering_method,
        clustering_eps=clustering_eps,
        clustering_min_samples=clustering_min_samples,
        clustering_n_clusters=clustering_n_clusters,
        nlp_backend=nlp_backend,
        log_source=real_log_source,
    )
    st.session_state["last_params"] = current_params
    st.session_state["is_historical_view"] = False


# ---------------------------------------------------------
# RENDERIZADO DE PESTAÑAS (SIEMPRE VISIBLES)
# ---------------------------------------------------------
tab_overview, tab_alerts, tab_root, tab_patterns, tab_data, tab_history = st.tabs(
    [
        "📊 Resumen",
        "🚨 Alertas",
        "🧠 Causa Raíz",
        "🔬 Patrones",
        "🗂 Explorador",
        "🗄️ Historial",
    ]
)

# Render breadcrumbs for current active context (handled via tabs context visually, but we add a subtitle)
def render_breadcrumb(title):
    st.markdown(f'<div class="eyebrow" style="margin-top:-0.5rem;margin-bottom:1rem;">Navegación / {title}</div>', unsafe_allow_html=True)


if "last_result" in st.session_state:
    result = st.session_state["last_result"]
    logs = result.logs.copy()

    with st.sidebar:
        st.divider()
        st.markdown(
            '<div class="sidebar-section-label">Filtros</div>', unsafe_allow_html=True
        )
        search_query = st.text_input(
            "Buscador (Palabras clave)",
            value="",
            help="Filtra reactivamente los logs por cualquier término.",
        )
        levels = sorted(logs["level"].dropna().unique().tolist())
        selected_levels = st.multiselect("Severidad", levels, default=levels)
        clusters = sorted(logs["semantic_cluster"].dropna().unique().tolist())
        selected_clusters = st.multiselect(
            "Cluster semantico", clusters, default=clusters
        )
        only_alerts = st.toggle("Solo alertas", value=False)
        max_rows = st.slider("Filas visibles", 200, 5000, 1000, step=200)

    # Filtrar por búsqueda
    if search_query:
        mask = (
            logs["raw_log"].astype(str).str.contains(search_query, case=False, na=False)
        )
        if "clean_log" in logs.columns:
            mask = mask | logs["clean_log"].astype(str).str.contains(
                search_query, case=False, na=False
            )
        logs = logs[mask]

    if selected_levels:
        logs = logs[logs["level"].isin(selected_levels)]
    if selected_clusters:
        logs = logs[logs["semantic_cluster"].isin(selected_clusters)]
    if only_alerts:
        logs = logs[
            logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
        ]

    visible_logs = logs.head(max_rows).copy()

    render_status_strip(logs, result.semantic_backend)
    if result.persistence_error:
        st.warning(f"SQLite no pudo guardar incidentes: {result.persistence_error}")
    if result.profile["non_empty_lines"] > LARGE_LOG_THRESHOLD_ROWS:
        st.info(
            "Modo archivo grande activo: el clustering estadistico y NLP semantico usan tecnicas escalables sobre plantillas representativas."
        )
    render_metrics(logs)
    if len(logs) > len(visible_logs):
        st.markdown(
            f'<div class="perf-note">Mostrando {len(visible_logs):,} de {len(logs):,} eventos para mantener el dashboard fluido. Ajusta "Filas visibles" en el panel lateral.</div>',
            unsafe_allow_html=True,
        )

    with tab_overview:
        render_breadcrumb("Resumen")
        st.markdown(
            '<p class="section-note">Lectura rapida del comportamiento operativo detectado.</p>',
            unsafe_allow_html=True,
        )
        profile = result.profile
        st.markdown(
            f"""
            <div class="dataset-card">
                <div><span>Archivo</span><strong>{profile["file_name"]}</strong></div>
                <div><span>Tamano</span><strong>{profile["size_mb"]} MB</strong></div>
                <div><span>Lineas utiles</span><strong>{profile["non_empty_lines"]:,}</strong></div>
                <div><span>Modo</span><strong>{"Large Log" if profile["non_empty_lines"] > LARGE_LOG_THRESHOLD_ROWS else "Interactivo"}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        semantic_label = (
            "DistilBERT Remoto"
            if "distilbert" in result.semantic_backend
            else "TF-IDF fallback"
        )
        model_status = get_distilbert_status()
        badge_class = (
            "ready"
            if (model_status.available_remote or model_status.available_locally)
            else "fallback"
        )
        badge_text = (
            "REMOTO"
            if model_status.available_remote
            else ("LOCAL" if model_status.available_locally else "FALLBACK")
        )
        st.markdown(
            f"""
            <div class="model-status">
                <span class="eyebrow">Hugging Face Transformers</span>
                <p><strong>{model_status.model_name}</strong>
                <span class="model-badge {badge_class}">{badge_text}</span></p>
                <p>{model_status.detail}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="tech-grid">
                <div class="tech-card">
                    <span>Parsing</span>
                    <strong>Drain-style Parser</strong>
                    <p>Normaliza fechas, IPs y numeros para crear plantillas de eventos.</p>
                </div>
                <div class="tech-card">
                    <span>Anomalias</span>
                    <strong>Isolation Forest</strong>
                    <p>Detecta registros estadisticamente atipicos sobre features del log.</p>
                </div>
                <div class="tech-card">
                    <span>Clustering</span>
                    <strong>{result.statistical_backend}</strong>
                    <p>DBSCAN en logs pequenos; MiniBatchKMeans para archivos grandes.</p>
                </div>
                <div class="tech-card">
                    <span>NLP</span>
                    <strong>{semantic_label}</strong>
                    <p>{result.semantic_backend} sobre {result.semantic_scope}.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("Estado del pipeline")
        pipeline_cols = st.columns(4)
        for index, stage in enumerate(result.stages):
            status_class = stage["status"].lower()
            with pipeline_cols[index % 4]:
                st.markdown(
                    f"""
                    <div class="pipeline-step">
                        <strong>{stage["stage"]}</strong>
                        <span class="{status_class}">{stage["status"]}</span>
                        <p>{stage["detail"]}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()
        st.subheader("📊 Evaluación de Calidad del Clustering")
        eval_cols = st.columns(2)
        eval_cols[0].metric(
            label="Coeficiente de Silueta (Silhouette Score)",
            value=f"{result.silhouette_score:.4f}",
            help="Mide la cohesión y separación de los clusters. Valores cercanos a 1 indican excelente agrupamiento.",
        )
        eval_cols[1].metric(
            label="Índice Davies-Bouldin",
            value=f"{result.davies_bouldin_index:.4f}",
            help="Mide la similitud promedio entre clusters. Valores más bajos indican una mejor separación.",
        )
        summary = build_executive_summary(logs)
        templates = top_templates(logs, limit=5)
        template_items = (
            "".join(
                f"<div class='signal-item'><span>{row.event_template[:88]}</span><strong>{int(row.cantidad)}</strong></div>"
                for row in templates.itertuples()
            )
            or "<p>No hay plantillas suficientes para resumir.</p>"
        )
        st.markdown(
            f"""
            <div class="insight-grid">
                <div class="insight-card">
                    <span class="eyebrow">Lectura automatica</span>
                    <h3>De que trata este log</h3>
                    <p><strong>Dominio probable:</strong> {summary["domain"]}</p>
                    <p>{summary["volume"]}</p>
                    <p>{summary["posture"]}</p>
                    <p><strong>Siguiente paso:</strong> {summary["focus"]}</p>
                </div>
                <div class="insight-card">
                    <span class="eyebrow">Patrones dominantes</span>
                    <h3>Plantillas Drain mas frecuentes</h3>
                    <div class="signal-list">{template_items}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_tradingview_timeline(logs)
        render_charts(logs)

        # Sección de exportación del reporte de diagnóstico
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📥 Exportar Diagnóstico de logs")

        with st.expander("📥 Descargar Reporte de Diagnóstico", expanded=False):
            st.markdown(
                '<p class="section-note">Genera e informa reportes del estado operativo en múltiples formatos (HTML, JSON, CSV o Excel nativo) para análisis externos.</p>',
                unsafe_allow_html=True,
            )

            # Generar una clave única para la sesión basada en run_id y longitud de logs
            run_key = f"reports_{result.run_id}_{len(logs)}"
            if run_key not in st.session_state:
                st.session_state[run_key] = None

            if st.session_state[run_key] is None:
                st.info("Haz clic en el botón de abajo para generar los reportes de descarga. Esto evita demoras y reduce el uso de memoria.")
                if st.button("⚙️ Generar Archivos de Reporte", key=f"btn_gen_{result.run_id}", use_container_width=True):
                    with st.spinner("Generando reportes (HTML, JSON, CSV, XLSX)..."):
                        html_report = generate_html_report(logs, result)
                        json_report = generate_json_report(logs, result)
                        csv_report = generate_csv_report(logs)

                        # Intentar generar reporte XLSX desde base de datos
                        try:
                            xlsx_report = generate_report("xlsx", run_id=result.run_id)
                            xlsx_available = True
                        except Exception:
                            xlsx_report = b""
                            xlsx_available = False

                        st.session_state[run_key] = {
                            "html": html_report,
                            "json": json_report,
                            "csv": csv_report,
                            "xlsx": xlsx_report,
                            "xlsx_available": xlsx_available
                        }
                        st.rerun()

            if st.session_state[run_key] is not None:
                reports = st.session_state[run_key]
                dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4)
                with dl_col1:
                    st.download_button(
                        label="📄 Reporte HTML (Ejecutivo)",
                        data=reports["html"],
                        file_name=f"reporte_diagnostico_{result.run_id}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                with dl_col2:
                    st.download_button(
                        label="💻 Datos JSON (API)",
                        data=reports["json"],
                        file_name=f"reporte_diagnostico_{result.run_id}.json",
                        mime="application/json",
                        use_container_width=True,
                    )
                with dl_col3:
                    st.download_button(
                        label="📊 Tabla CSV (Excel)",
                        data=reports["csv"],
                        file_name=f"anomalias_{result.run_id}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                with dl_col4:
                    if reports["xlsx_available"] and len(reports["xlsx"]) > 200:
                        st.download_button(
                            label="🟢 Documento XLSX (Excel)",
                            data=reports["xlsx"],
                            file_name=f"reporte_completo_{result.run_id}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                    else:
                        st.button(
                            label="🟢 XLSX no disponible",
                            disabled=True,
                            use_container_width=True,
                            help="Para descargar en XLSX, instala openpyxl en el entorno local.",
                        )
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄 Volver a generar reportes", key=f"btn_regen_{result.run_id}", use_container_width=True):
                    st.session_state[run_key] = None
                    st.rerun()

    with tab_alerts:
        render_breadcrumb("Alertas")
        render_anomalies(visible_logs)

    with tab_root:
        render_breadcrumb("Causa Raíz")
        render_root_causes(logs)

    with tab_patterns:
        render_breadcrumb("Patrones")
        render_pattern_analysis(logs)

    with tab_data:
        render_breadcrumb("Explorador")
        st.subheader("🗂 Explorador de Eventos")
        st.markdown(
            '<p class="section-note">Inspecciona todos los eventos del log con sus atributos completos. Filtra por severidad y cluster desde el panel lateral.</p>',
            unsafe_allow_html=True,
        )
        _total_shown = len(visible_logs)
        _total_all = len(logs)
        if _total_shown < _total_all:
            st.info(
                f"Mostrando **{_total_shown:,}** de **{_total_all:,}** eventos. Ajusta 'Filas visibles' en el panel lateral para ver más."
            )
        st.dataframe(
            visible_logs,
            use_container_width=True,
            hide_index=True,
            column_config={
                "line_id": st.column_config.NumberColumn("Línea", width="small"),
                "level": st.column_config.TextColumn("Severidad", width="small"),
                "is_anomaly": st.column_config.CheckboxColumn("◆ ML", width="small"),
                "raw_log": st.column_config.TextColumn("Log Original", width="large"),
                "clean_log": st.column_config.TextColumn("Log Limpio", width="large"),
                "event_template": st.column_config.TextColumn(
                    "Plantilla Drain", width="medium"
                ),
                "anomaly_score": st.column_config.NumberColumn(
                    "Score ML", format="%.4f", width="small"
                ),
                "root_cause": st.column_config.TextColumn(
                    "Causa Probable", width="medium"
                ),
                "recommendation": st.column_config.TextColumn(
                    "Acción Sugerida", width="large"
                ),
            },
        )

else:
    with tab_overview:
        st.markdown(
            """
            <div class="welcome-container">
                <div class="welcome-icon">🔬</div>
                <h2 class="welcome-title">Listo para Iniciar el Análisis</h2>
                <p class="welcome-text">
                    Carga un archivo de logs en el panel lateral o utiliza el dataset de muestra para descubrir patrones, 
                    anomalías y causas raíz operativas con inteligencia artificial.
                </p>
                <div class="welcome-steps">
                    <div class="welcome-step"><span>1</span> <div><strong>Ingesta inteligente:</strong> Carga archivos de log estructurados o crudos.</div></div>
                    <div class="welcome-step"><span>2</span> <div><strong>Detección con ML:</strong> Análisis estadístico no supervisado (Isolation Forest).</div></div>
                    <div class="welcome-step"><span>3</span> <div><strong>Enriquecimiento NLP:</strong> Clasificación semántica de errores y recomendaciones automáticas.</div></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        col_w1, col_w2, col_w3 = st.columns([1, 2, 1])
        with col_w2:
            if st.button(
                "🚀 Iniciar Diagnóstico de Logs",
                type="primary",
                use_container_width=True,
                key="welcome_run_btn",
            ):
                st.session_state["welcome_run"] = True
                st.rerun()

    with tab_alerts:
        st.info("Carga un archivo de logs en el panel lateral o usa el dataset de muestra para ver las alertas.")
    with tab_root:
        st.info("El análisis de causa raíz aparecerá aquí.")
    with tab_patterns:
        st.info("Los patrones detectados aparecerán aquí.")
    with tab_data:
        st.info("El explorador de eventos estará disponible tras cargar datos.")


with tab_history:
    render_breadcrumb("Historial")
    st.subheader("🗄️ Historial de Diagnósticos Guardados")
    st.markdown(
        '<p class="section-note">Explora análisis anteriores guardados en la base de datos local SQLite. Puedes inspeccionar las alertas, descargar sus reportes o eliminar registros antiguos.</p>',
        unsafe_allow_html=True,
    )
    try:
        runs_df = list_runs()
        if runs_df.empty:
            st.info("No hay análisis guardados en el historial SQLite.")
        else:
            # Formatear las opciones del selector
            runs_df["display_name"] = runs_df.apply(
                lambda r: f"{r['created_at']} — {r['log_source']} ({int(r['anomalies'])} anomalías, {int(r['errors'])} errores)",
                axis=1,
            )

            # Selector de modo: Individual o Comparación
            compare_mode = False
            if len(runs_df) >= 2:
                compare_mode = st.checkbox(
                    "🔍 Activar Comparador de Ejecuciones (Comparar dos logs históricos)",
                    value=False,
                )

            if compare_mode:
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    sel_a = st.selectbox(
                        "Ejecución A (Línea Base)",
                        options=runs_df["display_name"].tolist(),
                        index=1 if len(runs_df) > 1 else 0,
                    )
                with col_c2:
                    sel_b = st.selectbox(
                        "Ejecución B (Comparar)",
                        options=runs_df["display_name"].tolist(),
                        index=0,
                    )

                row_a = runs_df[runs_df["display_name"] == sel_a].iloc[0]
                row_b = runs_df[runs_df["display_name"] == sel_b].iloc[0]

                run_id_a = row_a["run_id"]
                run_id_b = row_b["run_id"]

                if run_id_a == run_id_b:
                    st.warning(
                        "⚠️ Selecciona dos ejecuciones distintas para poder compararlas."
                    )
                else:

                    def metric_delta(val_a, val_b):
                        diff = val_b - val_a
                        if val_a == 0:
                            pct = 0.0
                        else:
                            pct = (diff / val_a) * 100
                        sign = "+" if diff > 0 else ""
                        return (
                            f"{sign}{diff} ({sign}{pct:.1f}%)"
                            if diff != 0
                            else "Sin cambio"
                        )

                    st.markdown("### 📊 Comparativa de Métricas de Riesgo")
                    m_col1, m_col2, m_col3 = st.columns(3)

                    diff_events = row_b["total_events"] - row_a["total_events"]
                    diff_anom = row_b["anomalies"] - row_a["anomalies"]
                    diff_err = row_b["errors"] - row_a["errors"]

                    m_col1.metric(
                        label="Eventos Registrados",
                        value=f"{int(row_b['total_events'])}",
                        delta=metric_delta(
                            row_a["total_events"], row_b["total_events"]
                        ),
                    )
                    m_col2.metric(
                        label="Anomalías ML",
                        value=f"{int(row_b['anomalies'])}",
                        delta=metric_delta(row_a["anomalies"], row_b["anomalies"]),
                        delta_color="inverse" if diff_anom > 0 else "normal",
                    )
                    m_col3.metric(
                        label="Eventos de Error",
                        value=f"{int(row_b['errors'])}",
                        delta=metric_delta(row_a["errors"], row_b["errors"]),
                        delta_color="inverse" if diff_err > 0 else "normal",
                    )

                    # Cargar incidentes de ambos runs
                    inc_a = list_incidents(run_id=run_id_a)
                    inc_b = list_incidents(run_id=run_id_b)

                    templates_a = set(
                        inc_a["event_template"].dropna().unique().tolist()
                    )
                    templates_b = set(
                        inc_b["event_template"].dropna().unique().tolist()
                    )

                    new_templates = templates_b - templates_a
                    resolved_templates = templates_a - templates_b

                    st.markdown("### 🔍 Análisis de Patrones de Logs")

                    exp_new = st.expander(
                        f"🆕 Nuevos Patrones en Ejecución B ({len(new_templates)})",
                        expanded=True,
                    )
                    with exp_new:
                        if new_templates:
                            st.markdown(
                                "Los siguientes patrones de logs ocurrieron en la Ejecución B pero **no estaban presentes** en la Ejecución A:"
                            )
                            for t in list(new_templates)[:20]:
                                st.code(t, language="text")
                            if len(new_templates) > 20:
                                st.caption(
                                    f"... y {len(new_templates) - 20} patrones más."
                                )
                        else:
                            st.success(
                                "✅ No se encontraron patrones de error nuevos en la Ejecución B."
                            )

                    exp_res = st.expander(
                        f"✅ Patrones Resueltos/Ausentes en Ejecución B ({len(resolved_templates)})",
                        expanded=False,
                    )
                    with exp_res:
                        if resolved_templates:
                            st.markdown(
                                "Los siguientes patrones de logs ocurrieron en la Ejecución A pero **ya no están presentes** en la Ejecución B:"
                            )
                            for t in list(resolved_templates)[:20]:
                                st.code(t, language="text")
                            if len(resolved_templates) > 20:
                                st.caption(
                                    f"... y {len(resolved_templates) - 20} patrones más."
                                )
                        else:
                            st.info(
                                "Todos los patrones de error de la Ejecución A siguen ocurriendo en la Ejecución B."
                            )
            else:
                # Vista Individual con pestañas para inspección o búsqueda global
                view_tab1, view_tab2 = st.tabs(
                    ["📂 Inspeccionar Ejecución", "🔎 Buscador Global en Historial"]
                )

                with view_tab1:
                    selected_display = st.selectbox(
                        "Selecciona una ejecución histórica",
                        options=runs_df["display_name"].tolist(),
                        key="select_run_hist",
                    )

                    # Obtener la fila seleccionada
                    selected_row = runs_df[
                        runs_df["display_name"] == selected_display
                    ].iloc[0]
                    sel_run_id = selected_row["run_id"]
                    sel_source = selected_row["log_source"]
                    sel_created = selected_row["created_at"]

                    # Cargar incidentes de este run y resumen de BD
                    hist_incidents = list_incidents(run_id=sel_run_id)
                    summary_db = get_incident_summary(run_id=sel_run_id)

                    # Mostrar métricas del run seleccionado
                    h_col1, h_col2, h_col3, h_col4 = st.columns(4)
                    h_col1.metric("Archivo Analizado", sel_source)
                    h_col2.metric("Fecha de Ejecución", str(sel_created))
                    h_col3.metric("Anomalías Guardadas", summary_db["anomalies"])
                    h_col4.metric(
                        "Errores/Críticos Guardados", summary_db["errors"]
                    )
                    
                    # Mostrar detalles de incidentes
                    with st.expander("🔎 Incidentes del Run Seleccionado"):
                        if not hist_incidents.empty:
                            render_anomalies(hist_incidents)
                        else:
                            st.info("No hay incidentes para esta ejecución.")

                    # Botón para restaurar la ejecución en el dashboard principal
                    if st.button(
                        "📂 Cargar esta ejecución en el Dashboard Principal",
                        key=f"restore_btn_{sel_run_id}",
                        type="primary",
                        use_container_width=True,
                    ):
                        from app.services.pipeline_service import PipelineResult

                        # Cargar incidentes completos desde la base de datos SQLite para esta ejecución
                        from app.database.connection import get_connection
                        with st.spinner("Cargando ejecución histórica desde la base de datos..."):
                            with get_connection() as conn:
                                import pandas as pd
                                import sqlalchemy as sa
                                restore_df = pd.read_sql_query(
                                    sa.text("SELECT * FROM incidents WHERE run_id = :run_id ORDER BY line_id ASC"),
                                    conn,
                                    params={"run_id": sel_run_id},
                                )

                        if "clean_log" not in restore_df.columns:
                            restore_df["clean_log"] = restore_df["raw_log"]
                        restore_df["is_anomaly"] = restore_df["is_anomaly"].astype(
                            bool
                        )

                        stages = [
                            {
                                "stage": "Carga Histórica",
                                "status": "Completado",
                                "detail": "Restaurado desde SQLite",
                            },
                            {
                                "stage": "Incidentes",
                                "status": "Completado",
                                "detail": f"{len(restore_df):,} anomalías/errores cargados",
                            },
                        ]

                        restored_result = PipelineResult(
                            logs=restore_df,
                            semantic_backend="Historial SQLite",
                            saved_incidents=len(restore_df),
                            profile={
                                "file_name": sel_source,
                                "size_mb": "Historial",
                                "non_empty_lines": len(restore_df),
                            },
                            stages=stages,
                            statistical_backend="Historial",
                            semantic_scope="Alertas persistidas",
                            persistence_error=None,
                            silhouette_score=0.0,
                            davies_bouldin_index=0.0,
                            run_id=sel_run_id,
                            log_source=sel_source,
                        )

                        st.session_state["last_result"] = restored_result
                        st.session_state["is_historical_view"] = True
                        st.session_state["last_params"] = {
                            "source": sel_source,
                            "contamination": 0.15,
                            "clustering_method": "auto",
                            "clustering_eps": 0.8,
                            "clustering_min_samples": 2,
                            "clustering_n_clusters": 5,
                            "nlp_backend": "auto",
                        }
                        st.rerun()


                    # Descargar reporte histórico
                    st.markdown("##### 📥 Exportar esta ejecución histórica")

                    hist_key = f"hist_reports_{sel_run_id}"
                    if hist_key not in st.session_state:
                        st.session_state[hist_key] = None

                    if st.session_state[hist_key] is None:
                        st.info("Haz clic en el botón de abajo para preparar los archivos de descarga para esta ejecución histórica.")
                        if st.button("⚙️ Preparar descargas para esta ejecución", key=f"btn_gen_hist_{sel_run_id}", use_container_width=True):
                            with st.spinner("Cargando incidentes del historial y generando reportes..."):
                                # Consultar incidentes completos para este run_id (evitando el límite de 200 de list_incidents)
                                from app.database.connection import get_connection
                                with get_connection() as conn:
                                    import pandas as pd
                                    import sqlalchemy as sa
                                    full_hist_incidents = pd.read_sql_query(
                                        sa.text("SELECT * FROM incidents WHERE run_id = :run_id ORDER BY line_id ASC"),
                                        conn,
                                        params={"run_id": sel_run_id},
                                    )

                                # Emular un objeto de resultado simplificado para el generador de reportes
                                class HistoricalResult:
                                    def __init__(
                                        self,
                                        run_id,
                                        log_source,
                                        silhouette_score=0.0,
                                        davies_bouldin_index=0.0,
                                    ):
                                        self.run_id = run_id
                                        self.log_source = log_source
                                        self.anomaly_count = int(selected_row["anomalies"])
                                        self.silhouette_score = silhouette_score
                                        self.davies_bouldin_index = davies_bouldin_index
                                        self.stages = [
                                            {
                                                "stage": "Perfil del archivo",
                                                "status": "Completado",
                                                "detail": "Restaurado del historial",
                                            },
                                            {
                                                "stage": "Ingestion + limpieza",
                                                "status": "Completado",
                                                "detail": f"{int(selected_row['total_events'])} alertas guardadas",
                                            },
                                            {
                                                "stage": "Persistencia",
                                                "status": "Completado",
                                                "detail": "SQLite Historial",
                                            },
                                        ]

                                hist_res = HistoricalResult(sel_run_id, sel_source)

                                h_html = generate_html_report(full_hist_incidents, hist_res)
                                h_json = generate_json_report(full_hist_incidents, hist_res)
                                h_csv = generate_csv_report(full_hist_incidents)

                                # Intentar generar reporte XLSX histórico desde base de datos
                                try:
                                    h_xlsx = generate_report("xlsx", run_id=sel_run_id)
                                    h_xlsx_available = True
                                except Exception:
                                    h_xlsx = b""
                                    h_xlsx_available = False

                                st.session_state[hist_key] = {
                                    "html": h_html,
                                    "json": h_json,
                                    "csv": h_csv,
                                    "xlsx": h_xlsx,
                                    "xlsx_available": h_xlsx_available
                                }
                                st.rerun()

                    if st.session_state[hist_key] is not None:
                        h_reports = st.session_state[hist_key]
                        h_dl1, h_dl2, h_dl3, h_dl4 = st.columns(4)
                        h_dl1.download_button(
                            label="📄 Reporte HTML Histórico",
                            data=h_reports["html"],
                            file_name=f"reporte_historico_{sel_run_id}.html",
                            mime="text/html",
                            key=f"h_html_{sel_run_id}",
                            use_container_width=True,
                        )
                        h_dl2.download_button(
                            label="💻 Datos JSON Históricos",
                            data=h_reports["json"],
                            file_name=f"reporte_historico_{sel_run_id}.json",
                            mime="application/json",
                            key=f"h_json_{sel_run_id}",
                            use_container_width=True,
                        )
                        h_dl3.download_button(
                            label="📊 Tabla CSV Histórica",
                            data=h_reports["csv"],
                            file_name=f"alertas_historicas_{sel_run_id}.csv",
                            mime="text/csv",
                            key=f"h_csv_{sel_run_id}",
                            use_container_width=True,
                        )
                        with h_dl4:
                            if h_reports["xlsx_available"] and len(h_reports["xlsx"]) > 200:
                                st.download_button(
                                    label="🟢 Excel XLSX Histórico",
                                    data=h_reports["xlsx"],
                                    file_name=f"reporte_historico_{sel_run_id}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"h_xlsx_{sel_run_id}",
                                    use_container_width=True,
                                )
                            else:
                                st.button(
                                    label="🟢 XLSX no disponible",
                                    disabled=True,
                                    key=f"h_xlsx_dis_{sel_run_id}",
                                    use_container_width=True,
                                    help="Para descargar en XLSX, instala openpyxl en el entorno local.",
                                )

                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.button("🔄 Volver a preparar descargas", key=f"btn_regen_hist_{sel_run_id}", use_container_width=True):
                            st.session_state[hist_key] = None
                            st.rerun()


                    # Mostrar incidentes en un dataframe interactivo
                    st.markdown("##### 🔍 Eventos guardados")
                    st.dataframe(
                        hist_incidents,
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "line_id": st.column_config.NumberColumn(
                                "Linea", width="small"
                            ),
                            "level": st.column_config.TextColumn(
                                "Severidad", width="small"
                            ),
                            "raw_log": st.column_config.TextColumn(
                                "Log original", width="large"
                            ),
                            "event_template": st.column_config.TextColumn(
                                "Plantilla Drain", width="medium"
                            ),
                            "anomaly_score": st.column_config.NumberColumn(
                                "Score ML", format="%.4f"
                            ),
                            "root_cause": st.column_config.TextColumn(
                                "Causa probable", width="medium"
                            ),
                            "recommendation": st.column_config.TextColumn(
                                "Recomendacion", width="large"
                            ),
                        },
                    )

                    # Opción para eliminar
                    st.divider()
                    st.markdown("##### ⚠️ Zona de Peligro")
                    del_confirm = st.checkbox(
                        "Confirmar que deseo eliminar esta ejecución de la base de datos de manera permanente",
                        key=f"del_conf_{sel_run_id}",
                    )
                    if st.button(
                        "🗑️ Eliminar ejecución de la Base de Datos",
                        type="primary",
                        disabled=not del_confirm,
                        key=f"del_btn_{sel_run_id}",
                    ):
                        delete_run(sel_run_id)
                        st.success(
                            f"Ejecución '{sel_run_id}' eliminada correctamente."
                        )
                        st.rerun()

                with view_tab2:
                    st.markdown(
                        "##### 🔎 Buscar incidentes en todo el historial SQLite"
                    )
                    q_global = st.text_input(
                        "Término de búsqueda (Ej: Connection, Exception, Error)",
                        value="",
                        key="q_global_hist",
                    )
                    if q_global:
                        search_results = search_all_incidents(q_global)
                        if search_results.empty:
                            st.info(
                                "No se encontraron incidentes que coincidan con la búsqueda."
                            )
                        else:
                            st.markdown(
                                f"Se encontraron **{len(search_results)}** incidentes históricos:"
                            )
                            st.dataframe(
                                search_results,
                                width="stretch",
                                hide_index=True,
                                column_config={
                                    "log_source": st.column_config.TextColumn(
                                        "Archivo origen", width="medium"
                                    ),
                                    "created_at": st.column_config.TextColumn(
                                        "Fecha", width="medium"
                                    ),
                                    "line_id": st.column_config.NumberColumn(
                                        "Linea", width="small"
                                    ),
                                    "level": st.column_config.TextColumn(
                                        "Severidad", width="small"
                                    ),
                                    "raw_log": st.column_config.TextColumn(
                                        "Log original", width="large"
                                    ),
                                    "root_cause": st.column_config.TextColumn(
                                        "Causa probable", width="medium"
                                    ),
                                    "recommendation": st.column_config.TextColumn(
                                        "Recomendacion", width="large"
                                    ),
                                },
                            )
                    else:
                        st.caption(
                            "Escribe un término arriba para realizar una consulta global en la base de datos local."
                        )
    except Exception as exc:
        st.warning(f"Error al interactuar con el historial Supabase: {exc}")
