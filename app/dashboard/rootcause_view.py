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


@st.cache_data(show_spinner=False)
def _aggregate_root_causes(logs: pd.DataFrame) -> pd.DataFrame:
    return (
        logs.groupby("root_cause")
        .agg(
            cantidad=("line_id", "count"),
            anomalias=("is_anomaly", "sum"),
            score_max=("anomaly_score", "max"),
        )
        .reset_index()
        .sort_values("cantidad", ascending=False)
    )

def render_root_causes(logs: pd.DataFrame) -> None:
    st.subheader("Mapa de Causas Raíz")
    st.markdown(
        '<p class="section-note">Hipótesis generadas automáticamente por reglas de correlación '
        "semántica. Las causas con mayor repetición son los focos principales de inestabilidad.</p>",
        unsafe_allow_html=True,
    )

    summary = _aggregate_root_causes(logs)

    if summary.empty:
        st.info("No hay datos de causas raíz disponibles.")
        return

    if px and go:
        col1, col2 = st.columns([1.4, 0.6])

        with col1:
            # Barras horizontales con doble encoding: largo = cantidad, color = score máx
            fig = px.bar(
                summary.head(12),
                y="root_cause",
                x="cantidad",
                orientation="h",
                color="score_max",
                color_continuous_scale=["#bae6fd", "#f97316", "#b91c1c"],
                text="cantidad",
                labels={
                    "root_cause": "Causa Raíz",
                    "cantidad": "Eventos",
                    "score_max": "Score ML Máx",
                },
            )
            fig.update_traces(textposition="outside", textfont_size=10)
            fig.update_layout(
                font=dict(
                    family="Plus Jakarta Sans, sans-serif", size=11, color="#1e293b"
                ),
                height=340,
                margin=dict(l=10, r=10, t=18, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
                xaxis=dict(title="Total eventos", gridcolor="#e2e8f0"),
                coloraxis_colorbar=dict(title="Score ML", thickness=10),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Donut de las top 6 causas
            top6 = summary.head(6)
            fig_donut = go.Figure(
                go.Pie(
                    labels=top6["root_cause"],
                    values=top6["cantidad"],
                    hole=0.58,
                    textinfo="percent",
                    textfont_size=11,
                    marker=dict(
                        colors=[
                            "#0ea5e9",
                            "#f59e0b",
                            "#ef4444",
                            "#10b981",
                            "#8b5cf6",
                            "#64748b",
                        ],
                        line=dict(color="#ffffff", width=2),
                    ),
                    hovertemplate="<b>%{label}</b><br>%{value} eventos (%{percent})<extra></extra>",
                )
            )
            total_causes = len(summary)
            fig_donut.add_annotation(
                text=f"<b>{total_causes}</b><br><span style='font-size:9px'>causas</span>",
                showarrow=False,
                font=dict(size=15, color="#0f172a"),
                x=0.5,
                y=0.5,
            )
            fig_donut.update_layout(
                font=dict(
                    family="Plus Jakarta Sans, sans-serif", size=11, color="#1e293b"
                ),
                height=340,
                margin=dict(l=10, r=10, t=18, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    # Tabla completa de causas raíz
    st.markdown("**Tabla detallada de causas raíz**")
    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "root_cause": st.column_config.TextColumn("Causa Raíz", width="large"),
            "cantidad": st.column_config.NumberColumn("Total Eventos", width="small"),
            "anomalias": st.column_config.NumberColumn("Anomalías ML", width="small"),
            "score_max": st.column_config.NumberColumn(
                "Score Máx.", format="%.4f", width="small"
            ),
        },
    )
