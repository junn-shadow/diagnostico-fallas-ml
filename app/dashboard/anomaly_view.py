import streamlit as st
import pandas as pd

try:
    import plotly.express as px
    import plotly.graph_objects as go
except Exception:
    px = None
    go = None


COLOR_MAP = {
    "DEBUG": "#64748b",
    "INFO": "#0ea5e9",
    "WARNING": "#f59e0b",
    "WARN": "#f59e0b",
    "ERROR": "#ef4444",
    "CRITICAL": "#b91c1c",
    "FATAL": "#7f1d1d",
}


def render_anomalies(logs: pd.DataFrame) -> None:
    total_alerts = len(
        logs[logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])]
    )

    # Encabezado con contador de alertas activas
    col_h, col_badge = st.columns([3, 1])
    with col_h:
        st.subheader("Bandeja de Alertas Activas")
        st.markdown(
            '<p class="section-note">Eventos priorizados por severidad y score ML. '
            "Empieza por las filas marcadas con ◆ o nivel CRITICAL.</p>",
            unsafe_allow_html=True,
        )
    with col_badge:
        badge_color = (
            "#ef4444"
            if total_alerts > 5
            else "#f59e0b" if total_alerts > 0 else "#10b981"
        )
        badge_text = (
            "CRÍTICO"
            if total_alerts > 5
            else "ATENCIÓN" if total_alerts > 0 else "ESTABLE"
        )
        st.markdown(
            f"""
            <div style="
                text-align:center;
                background:{badge_color};
                color:#ffffff;
                border-radius:8px;
                padding:0.6rem 0.8rem;
                margin-top:1rem;
                font-weight:700;
                font-size:0.85rem;
                letter-spacing:0.05em;
            ">
                {total_alerts} alertas<br>
                <span style="font-size:0.7rem;opacity:0.9;">{badge_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Mini gráfico de barras de severidad antes de la tabla
    if go and not logs.empty:
        sev_counts = logs[
            logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
        ]["level"].value_counts()

        if not sev_counts.empty:
            mini_fig = go.Figure(
                go.Bar(
                    x=sev_counts.index.tolist(),
                    y=sev_counts.values.tolist(),
                    marker_color=[
                        COLOR_MAP.get(l, "#64748b") for l in sev_counts.index
                    ],
                    text=sev_counts.values.tolist(),
                    textposition="outside",
                    textfont=dict(size=10),
                )
            )
            mini_fig.update_layout(
                height=130,
                margin=dict(l=5, r=5, t=8, b=5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(
                    family="Plus Jakarta Sans, sans-serif", size=10, color="#475569"
                ),
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9", title=""),
                showlegend=False,
            )
            st.plotly_chart(mini_fig, use_container_width=True)

    # Tabla de alertas
    columns = [
        "line_id",
        "level",
        "is_anomaly",
        "anomaly_score",
        "event_template",
        "root_cause",
        "recommendation",
    ]
    alerts = logs[
        logs["is_anomaly"] | logs["level"].isin(["ERROR", "CRITICAL", "FATAL"])
    ]

    if alerts.empty:
        st.success("No hay alertas activas con los filtros actuales.")
        return

    min_score = (
        float(logs["anomaly_score"].min())
        if not logs["anomaly_score"].isna().all()
        else 0.0
    )
    max_score = (
        float(logs["anomaly_score"].max())
        if not logs["anomaly_score"].isna().all()
        else 1.0
    )
    if min_score >= max_score:
        max_score = min_score + 1.0

    st.dataframe(
        alerts[columns].sort_values(
            ["is_anomaly", "anomaly_score"], ascending=[False, False]
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "line_id": st.column_config.NumberColumn("Línea", width="small"),
            "level": st.column_config.TextColumn("Severidad", width="small"),
            "is_anomaly": st.column_config.CheckboxColumn("◆ ML", width="small"),
            "anomaly_score": st.column_config.ProgressColumn(
                "Riesgo ML",
                min_value=min_score,
                max_value=max_score,
            ),
            "event_template": st.column_config.TextColumn(
                "Plantilla Drain", width="medium"
            ),
            "root_cause": st.column_config.TextColumn("Causa probable", width="medium"),
            "recommendation": st.column_config.TextColumn(
                "Acción sugerida", width="large"
            ),
        },
    )
