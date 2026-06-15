import streamlit as st
import pandas as pd

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except Exception:
    px = None
    go = None
    make_subplots = None


COLOR_MAP = {
    "DEBUG":    "#64748b",
    "INFO":     "#0ea5e9",
    "WARNING":  "#f59e0b",
    "WARN":     "#f59e0b",
    "ERROR":    "#ef4444",
    "CRITICAL": "#b91c1c",
    "FATAL":    "#7f1d1d",
}

SEVERITY_ORDER = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]


def _layout_base(h: int = 300) -> dict:
    """Retorna configuración de layout compartida para todos los gráficos."""
    return dict(
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color="#1e293b"),
        height=h,
        margin=dict(l=10, r=10, t=24, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )


def render_tradingview_timeline(logs: pd.DataFrame) -> None:
    """
    Línea de tiempo interactiva de anomalías y eventos críticos con
    anotaciones de picos de riesgo y colores semánticos.
    """
    st.subheader("Línea temporal de anomalías y eventos críticos")
    st.markdown(
        '<p class="section-note">Eventos críticos distribuidos a lo largo del archivo de log. '
        'Pasa el cursor sobre los marcadores para inspeccionar el diagnóstico semántico.</p>',
        unsafe_allow_html=True,
    )

    if not go:
        st.info("Visualización simplificada (Plotly no disponible).")
        return

    alert_logs = logs[
        logs["is_anomaly"] | logs["level"].isin(["WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"])
    ].copy()

    if alert_logs.empty:
        st.info("No se detectaron eventos críticos ni anomalías para mostrar en la línea temporal.")
        return

    alert_logs = alert_logs.sort_values("line_id").reset_index(drop=True)

    if len(alert_logs) > 300:
        alert_logs = (
            alert_logs.sort_values("anomaly_score", ascending=False)
            .head(300)
            .sort_values("line_id")
            .reset_index(drop=True)
        )

    def _y(row):
        lvl = row["level"]
        if lvl in ("CRITICAL", "FATAL"):
            return 4
        if lvl == "ERROR":
            return 3
        if lvl in ("WARNING", "WARN"):
            return 2
        return 1  # INFO / anomalía sin nivel alto

    alert_logs["y_pos"] = alert_logs.apply(_y, axis=1)

    fig = go.Figure()

    # Líneas de referencia por nivel
    for y_val, label, color in [
        (2, "Warnings",       "#fef3c7"),
        (3, "Errores",        "#fee2e2"),
        (4, "Críticos/Fatal", "#fecdd3"),
    ]:
        fig.add_hrect(
            y0=y_val - 0.4, y1=y_val + 0.4,
            fillcolor=color, opacity=0.25,
            line_width=0,
        )

    # Traza principal de eventos
    fig.add_trace(
        go.Scatter(
            x=alert_logs["line_id"],
            y=alert_logs["y_pos"],
            mode="markers",
            marker=dict(
                size=[14 if a else 10 for a in alert_logs["is_anomaly"]],
                color=[COLOR_MAP.get(lvl, "#2563eb") for lvl in alert_logs["level"]],
                symbol=["diamond" if a else "circle" for a in alert_logs["is_anomaly"]],
                line=dict(color="#ffffff", width=1.5),
                opacity=0.9,
            ),
            customdata=list(zip(
                alert_logs["line_id"],
                alert_logs["level"],
                alert_logs["anomaly_score"].round(4),
                alert_logs["root_cause"],
                alert_logs["recommendation"],
                alert_logs["clean_log"].str.slice(0, 100),
            )),
            hovertemplate=(
                "<b>Línea L%{customdata[0]}</b><br>"
                "<b>Nivel:</b> %{customdata[1]} — Score: %{customdata[2]}<br>"
                "<b>Causa:</b> %{customdata[3]}<br>"
                "<b>Acción:</b> %{customdata[4]}<br>"
                "<b>Mensaje:</b> %{customdata[5]}…<extra></extra>"
            ),
            name="Eventos",
        )
    )

    layout = _layout_base(290)
    layout.update(
        showlegend=False,
        xaxis=dict(
            gridcolor="#e2e8f0", title="Línea del Log",
            showline=True, linecolor="#cbd5e1",
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=[1, 2, 3, 4],
            ticktext=["Info/Anomalía", "Warning", "Error", "Crítico/Fatal"],
            gridcolor="#e2e8f0",
            range=[0.4, 4.6],
            fixedrange=True,
        ),
    )
    fig.update_layout(**layout)
    st.plotly_chart(fig, use_container_width=True)


def render_charts(logs: pd.DataFrame) -> None:
    """Gráficos estadísticos principales: severidad, clusters y tendencia de riesgo."""

    # ── 1. Distribución de severidad (barras horizontales) + Donut de NLP ──────
    severity = (
        logs["level"]
        .value_counts()
        .rename_axis("level")
        .reset_index(name="count")
    )
    clusters_counts = logs["semantic_cluster"].value_counts().sort_index()
    clusters = pd.DataFrame({
        "cluster": [
            f"Cluster {int(c)}" if c >= 0 else "Sin asignar"
            for c in clusters_counts.index
        ],
        "count": clusters_counts.values,
    })

    col_a, col_b = st.columns([1.1, 0.9])

    with col_a:
        st.subheader("Distribución de severidad")
        if px:
            # Ordenar por severidad natural
            severity["order"] = severity["level"].apply(
                lambda l: SEVERITY_ORDER.index(l) if l in SEVERITY_ORDER else 99
            )
            severity = severity.sort_values("order")

            fig = px.bar(
                severity,
                x="count",
                y="level",
                orientation="h",
                color="level",
                color_discrete_map=COLOR_MAP,
                text="count",
            )
            fig.update_traces(textposition="outside", textfont_size=11)
            layout = _layout_base(260)
            layout.update(
                showlegend=False,
                xaxis=dict(gridcolor="#e2e8f0", title="Cantidad", showgrid=True),
                yaxis=dict(gridcolor="#e2e8f0", title="", autorange="reversed"),
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(logs["level"].value_counts())

    with col_b:
        st.subheader("Familias semánticas (NLP)")
        if go:
            fig = go.Figure(
                go.Pie(
                    labels=clusters["cluster"],
                    values=clusters["count"],
                    hole=0.62,
                    textinfo="label+percent",
                    textfont_size=11,
                    marker=dict(
                        colors=px.colors.qualitative.Safe if px else None,
                        line=dict(color="#ffffff", width=2),
                    ),
                    hovertemplate="<b>%{label}</b><br>%{value} eventos (%{percent})<extra></extra>",
                )
            )
            # Anotación central con el total
            total_unique = logs["semantic_cluster"].nunique()
            fig.add_annotation(
                text=f"<b>{total_unique}</b><br><span style='font-size:9px'>familias</span>",
                showarrow=False,
                font=dict(size=16, color="#0f172a"),
                x=0.5, y=0.5,
            )
            layout = _layout_base(260)
            layout.update(
                legend=dict(
                    orientation="v",
                    yanchor="middle", y=0.5,
                    xanchor="left", x=1.02,
                    font=dict(size=10),
                )
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(logs["semantic_cluster"].value_counts().sort_index())

    # ── 2. Heatmap de actividad por cluster y severidad ──────────────────────
    st.subheader("Heatmap de actividad: Clusters × Severidad")
    st.markdown(
        '<p class="section-note">Cruza los clusters NLP con el nivel de severidad para identificar '
        'qué familia de eventos concentra la mayor actividad crítica.</p>',
        unsafe_allow_html=True,
    )
    if go:
        top_clusters = (
            logs["semantic_cluster"].value_counts().head(12).index.tolist()
        )
        heat_data = (
            logs[logs["semantic_cluster"].isin(top_clusters)]
            .groupby(["semantic_cluster", "level"])
            .size()
            .unstack(fill_value=0)
        )
        # Ordenar columnas por severidad natural
        ordered_levels = [l for l in SEVERITY_ORDER if l in heat_data.columns]
        heat_data = heat_data[ordered_levels]

        heat_fig = go.Figure(
            go.Heatmap(
                z=heat_data.values,
                x=ordered_levels,
                y=[f"Cluster {int(c)}" if c >= 0 else "Sin asignar" for c in heat_data.index],
                colorscale=[
                    [0.0, "#f0f9ff"],
                    [0.3, "#bae6fd"],
                    [0.6, "#f97316"],
                    [1.0, "#b91c1c"],
                ],
                showscale=True,
                colorbar=dict(title="Eventos", thickness=12, len=0.8),
                hovertemplate="<b>%{y} / %{x}</b><br>%{z} eventos<extra></extra>",
            )
        )
        layout = _layout_base(300)
        layout.update(
            xaxis=dict(title="Severidad"),
            yaxis=dict(title="Cluster NLP", autorange="reversed"),
        )
        heat_fig.update_layout(**layout)
        st.plotly_chart(heat_fig, use_container_width=True)

    # ── 3. Curva de tendencia de riesgo suavizada ────────────────────────────
    st.subheader("Tendencia de riesgo operativo")
    st.markdown(
        '<p class="section-note">Media móvil adaptativa sobre el score de anomalía. '
        'Los picos rojos indican concentraciones de eventos críticos confirmados.</p>',
        unsafe_allow_html=True,
    )

    if go:
        ordered = logs.sort_values("line_id").reset_index(drop=True).copy()
        window_size = max(5, len(ordered) // 40)
        ordered["smoothed_risk"] = (
            ordered["anomaly_score"]
            .rolling(window=window_size, min_periods=1, center=True)
            .mean()
        )
        min_r = ordered["smoothed_risk"].min()
        max_r = ordered["smoothed_risk"].max()
        spread = max(max_r - min_r, 1e-6)
        ordered["normalized_risk"] = (ordered["smoothed_risk"] - min_r) / spread

        fig = go.Figure()

        # Área de riesgo bajo (verde)
        fig.add_trace(
            go.Scatter(
                x=ordered["line_id"],
                y=ordered["normalized_risk"].clip(upper=0.4),
                mode="lines",
                line=dict(color="rgba(16,185,129,0)", width=0),
                fill="tozeroy",
                fillcolor="rgba(16,185,129,0.07)",
                showlegend=False,
                hoverinfo="skip",
            )
        )
        # Área de riesgo alto (rojo)
        fig.add_trace(
            go.Scatter(
                x=ordered["line_id"],
                y=ordered["normalized_risk"].clip(lower=0.7),
                mode="lines",
                line=dict(color="rgba(239,68,68,0)", width=0),
                fill="tozeroy",
                fillcolor="rgba(239,68,68,0.09)",
                showlegend=False,
                hoverinfo="skip",
            )
        )
        # Curva principal
        fig.add_trace(
            go.Scatter(
                x=ordered["line_id"],
                y=ordered["normalized_risk"],
                mode="lines",
                name="Tendencia",
                line=dict(color="#0284c7", width=2.5, shape="spline"),
                fill="tozeroy",
                fillcolor="rgba(14,165,233,0.07)",
                hovertemplate="Línea %{x} — Riesgo: %{y:.3f}<extra></extra>",
            )
        )

        # Picos críticos confirmados
        crits = ordered[
            ordered["is_anomaly"] & ordered["level"].isin(["ERROR", "CRITICAL", "FATAL"])
        ]
        if not crits.empty:
            sample = crits.nlargest(60, "anomaly_score")
            fig.add_trace(
                go.Scatter(
                    x=sample["line_id"],
                    y=ordered.loc[sample.index, "normalized_risk"],
                    mode="markers",
                    name="Pico crítico",
                    marker=dict(
                        color="#ef4444", size=9, symbol="diamond",
                        line=dict(color="#ffffff", width=1),
                    ),
                    hovertemplate="Pico crítico — Línea %{x}<extra></extra>",
                )
            )

        # Bandas de umbral
        for y_val, label, color in [(0.4, "Bajo", "#10b981"), (0.7, "Alto", "#ef4444")]:
            fig.add_hline(
                y=y_val, line_dash="dot", line_color=color, opacity=0.5,
                annotation_text=f"  Umbral {label}",
                annotation_position="right",
                annotation_font_size=9,
            )

        layout = _layout_base(320)
        layout.update(
            hovermode="x unified",
            xaxis=dict(
                gridcolor="#e2e8f0", title="Línea del Log",
                showline=True, linecolor="#cbd5e1",
            ),
            yaxis=dict(
                gridcolor="#e2e8f0", title="Nivel de Riesgo (normalizado)",
                showline=True, linecolor="#cbd5e1",
                range=[-0.05, 1.1],
                tickformat=".0%",
            ),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1,
            ),
        )
        fig.update_layout(**layout)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.line_chart(logs.sort_values("line_id")["anomaly_score"])


def render_pattern_analysis(logs: pd.DataFrame) -> None:
    """
    Pestaña avanzada de análisis de patrones:
    - Top plantillas Drain con frecuencia y tasa de anomalía
    - Distribución temporal de errores por ventana
    - Tabla interactiva de plantillas con métricas ML
    """
    st.subheader("🔬 Análisis de Patrones de Eventos")
    st.markdown(
        '<p class="section-note">Desglosa los patrones de logs más frecuentes y su relación '
        'con anomalías detectadas por el modelo de ML.</p>',
        unsafe_allow_html=True,
    )

    if "event_template" not in logs.columns:
        st.info("No hay plantillas Drain disponibles.")
        return

    # Tabla de patrones con métricas
    pattern_stats = (
        logs.groupby("event_template")
        .agg(
            cantidad=("line_id", "count"),
            anomalias=("is_anomaly", "sum"),
            score_max=("anomaly_score", "max"),
            score_medio=("anomaly_score", "mean"),
            severidad_dominante=("level", lambda s: s.value_counts().index[0]),
        )
        .reset_index()
        .sort_values("anomalias", ascending=False)
    )
    pattern_stats["tasa_anomalia_%"] = (
        (pattern_stats["anomalias"] / pattern_stats["cantidad"]) * 100
    ).round(1)
    pattern_stats["score_max"] = pattern_stats["score_max"].round(4)
    pattern_stats["score_medio"] = pattern_stats["score_medio"].round(4)

    top_n = st.slider("Mostrar top N patrones", 5, 50, 15, key="pattern_topn")
    top_patterns = pattern_stats.head(top_n)

    # Gráfico de burbujas: frecuencia vs tasa de anomalía
    if px and go:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Top patrones por anomalías**")
            fig_bar = px.bar(
                top_patterns.head(10),
                x="anomalias",
                y="event_template",
                orientation="h",
                color="tasa_anomalia_%",
                color_continuous_scale=["#0ea5e9", "#f97316", "#ef4444"],
                text="anomalias",
                labels={"anomalias": "Anomalías", "event_template": "Plantilla"},
            )
            fig_bar.update_traces(textposition="outside", textfont_size=10)
            layout = _layout_base(320)
            layout.update(
                coloraxis_colorbar=dict(title="Tasa %", thickness=10),
                yaxis=dict(autorange="reversed", tickfont=dict(size=9)),
                xaxis=dict(title="Total anomalías"),
            )
            fig_bar.update_layout(**layout)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col2:
            st.markdown("**Frecuencia total vs Score ML máximo**")
            fig_scatter = px.scatter(
                top_patterns,
                x="cantidad",
                y="score_max",
                size="anomalias",
                color="severidad_dominante",
                color_discrete_map=COLOR_MAP,
                hover_data=["event_template", "tasa_anomalia_%"],
                labels={
                    "cantidad": "Frecuencia Total",
                    "score_max": "Score ML Máximo",
                    "severidad_dominante": "Severidad",
                },
            )
            layout = _layout_base(320)
            layout.update(
                xaxis=dict(gridcolor="#e2e8f0", title="Frecuencia Total"),
                yaxis=dict(gridcolor="#e2e8f0", title="Score ML Máximo"),
                legend=dict(font=dict(size=10)),
            )
            fig_scatter.update_layout(**layout)
            st.plotly_chart(fig_scatter, use_container_width=True)

    # Tabla interactiva de patrones
    st.markdown("**Tabla de patrones con métricas completas**")
    st.dataframe(
        top_patterns,
        use_container_width=True,
        hide_index=True,
        column_config={
            "event_template": st.column_config.TextColumn("Plantilla Drain", width="large"),
            "cantidad": st.column_config.NumberColumn("Frecuencia", width="small"),
            "anomalias": st.column_config.NumberColumn("Anomalías", width="small"),
            "tasa_anomalia_%": st.column_config.ProgressColumn(
                "Tasa Anomalía %", min_value=0, max_value=100, format="%.1f%%"
            ),
            "score_max": st.column_config.NumberColumn("Score Máx.", format="%.4f"),
            "score_medio": st.column_config.NumberColumn("Score Medio", format="%.4f"),
            "severidad_dominante": st.column_config.TextColumn("Severidad", width="small"),
        },
    )
