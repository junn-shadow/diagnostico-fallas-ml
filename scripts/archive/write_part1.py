with open("app/dashboard/streamlit_app.py", "w", encoding="utf-8") as f:
    f.write("""import sys
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
    \"\"\"Wrapper — runs check_distilbert_status dynamically to reflect actual env variables.\"\"\"
    return check_distilbert_status()


st.set_page_config(
    page_title="DiagnosticOps ML — Diagnóstico Inteligente de Fallas",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Cargar tema CSS premium personalizado
theme_path = Path(__file__).parent / "custom_theme.css"
if theme_path.exists():
    with open(theme_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

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
    hero_badge_html = f\"\"\"
<div style="text-align:right;min-width:130px;">
<div style="background:{_badge_color};color:#fff;border-radius:8px;padding:0.4rem 0.8rem;font-weight:700;font-size:0.8rem;letter-spacing:0.05em;margin-bottom:0.3rem;">
{_badge_label}
</div>
<div style="font-size:0.75rem;color:#64748b;">{_hero_anomalies} anomalías · {_hero_errors} errores</div>
</div>
\"\"\"
else:
    hero_badge_html = ""

st.markdown(
    f\"\"\"
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
\"\"\",
    unsafe_allow_html=True,
)


# Mostrar banner destacado si se carga una consulta histórica
if st.session_state.get("is_historical_view", False) and "last_result" in st.session_state:
    res = st.session_state["last_result"]
    st.markdown(
        f\"\"\"
        <div style="background-color: rgba(37, 99, 235, 0.08); border-left: 5px solid #2563eb; padding: 1.25rem; border-radius: 8px; margin-top: 1rem; margin-bottom: 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="color: #1e3a8a; font-family: 'Plus Jakarta Sans', sans-serif;">
                <span style="font-weight: 700; font-size: 1.05rem; display: block; margin-bottom: 0.25rem; color: #1e40af;">📂 Modo de Visualización Histórica Activo</span>
                Estás visualizando los resultados del diagnóstico guardado para el archivo <strong>{res.log_source}</strong> (ID: <code>{res.run_id}</code>). 
                Toda la información del dashboard, métricas y reportes proviene del historial persistido en SQLite.
            </div>
        </div>
        \"\"\",
        unsafe_allow_html=True,
    )
    col_exit_lbl, col_exit_btn = st.columns([3, 1])
    with col_exit_btn:
        if st.button("❌ Salir de Vista Histórica", key="exit_hist_view_btn", type="secondary", use_container_width=True):
            st.session_state.pop("last_result", None)
            st.session_state.pop("last_params", None)
            st.session_state["is_historical_view"] = False
            st.rerun()

""")
