import streamlit as st

COLOR_MAP = {
    "DEBUG":    "#64748b",
    "INFO":     "#0ea5e9",
    "WARNING":  "#f59e0b",
    "WARN":     "#f59e0b",
    "ERROR":    "#ef4444",
    "CRITICAL": "#b91c1c",
    "FATAL":    "#7f1d1d",
}


def render_metrics(logs) -> None:
    total = len(logs)
    anomalies = int(logs["is_anomaly"].sum())
    errors = int(logs["level"].isin(["ERROR", "CRITICAL", "FATAL"]).sum())
    clusters = logs["semantic_cluster"].nunique()
    critical = int(logs["level"].isin(["CRITICAL", "FATAL"]).sum())
    anomaly_rate = (anomalies / total * 100) if total else 0
    risk_score = min(100, round((critical * 18) + (errors * 9) + (anomalies * 12) + anomaly_rate))

    # Color semántico del riesgo
    if risk_score >= 70:
        risk_color = "#ef4444"
        risk_label = "Alto"
    elif risk_score >= 35:
        risk_color = "#f59e0b"
        risk_label = "Medio"
    else:
        risk_color = "#10b981"
        risk_label = "Bajo"

    cols = st.columns(5)
    cols[0].metric("📄 Logs analizados",  f"{total:,}")
    cols[1].metric("🔬 Anomalías ML",     anomalies, f"{anomaly_rate:.1f}% del total")
    cols[2].metric("⛔ Eventos de error", errors)
    cols[3].metric("🧩 Familias NLP",     clusters)
    cols[4].metric(
        "🔴 Riesgo operativo",
        f"{risk_score}/100",
        delta=risk_label,
        delta_color="inverse" if risk_score >= 35 else "normal",
        help="Índice compuesto de riesgo basado en anomalías, errores y eventos críticos."
    )


def render_status_strip(logs, backend: str) -> None:
    anomalies = int(logs["is_anomaly"].sum())
    critical = int(logs["level"].isin(["CRITICAL", "FATAL"]).sum())

    if critical:
        status_color = "#ef4444"
        status_icon = "🔴"
        status_text = "Crítico"
    elif anomalies:
        status_color = "#f59e0b"
        status_icon = "🟡"
        status_text = "Atención"
    else:
        status_color = "#10b981"
        status_icon = "🟢"
        status_text = "Estable"

    priority = "Alta" if (critical or anomalies > 2) else "Media" if anomalies else "Baja"

    st.markdown(
        f"""
        <div class="status-strip">
            <div>
                <span class="eyebrow">Estado del sistema</span>
                <strong style="color:{status_color}">{status_icon} {status_text}</strong>
            </div>
            <div>
                <span class="eyebrow">Motor semántico</span>
                <strong>{backend.upper()}</strong>
            </div>
            <div>
                <span class="eyebrow">Prioridad de respuesta</span>
                <strong>{priority}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
