with open("app/dashboard/streamlit_app.py", "a", encoding="utf-8") as f:
    f.write("""
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
        st.markdown(
            '<p class="section-note">Lectura rapida del comportamiento operativo detectado.</p>',
            unsafe_allow_html=True,
        )
        profile = result.profile
        st.markdown(
            f\"\"\"
            <div class="dataset-card">
                <div><span>Archivo</span><strong>{profile["file_name"]}</strong></div>
                <div><span>Tamano</span><strong>{profile["size_mb"]} MB</strong></div>
                <div><span>Lineas utiles</span><strong>{profile["non_empty_lines"]:,}</strong></div>
                <div><span>Modo</span><strong>{"Large Log" if profile["non_empty_lines"] > LARGE_LOG_THRESHOLD_ROWS else "Interactivo"}</strong></div>
            </div>
            \"\"\",
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
            f\"\"\"
            <div class="model-status">
                <span class="eyebrow">Hugging Face Transformers</span>
                <p><strong>{model_status.model_name}</strong>
                <span class="model-badge {badge_class}">{badge_text}</span></p>
                <p>{model_status.detail}</p>
            </div>
            \"\"\",
            unsafe_allow_html=True,
        )
        st.markdown(
            f\"\"\"
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
            \"\"\",
            unsafe_allow_html=True,
        )
        st.subheader("Estado del pipeline")
        pipeline_cols = st.columns(4)
        for index, stage in enumerate(result.stages):
            status_class = stage["status"].lower()
            with pipeline_cols[index % 4]:
                st.markdown(
                    f\"\"\"
                    <div class="pipeline-step">
                        <strong>{stage["stage"]}</strong>
                        <span class="{status_class}">{stage["status"]}</span>
                        <p>{stage["detail"]}</p>
                    </div>
                    \"\"\",
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
            f\"\"\"
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
            \"\"\",
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
        render_anomalies(visible_logs)

    with tab_root:
        render_root_causes(logs)

    with tab_patterns:
        render_pattern_analysis(logs)

    with tab_data:
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
""")
