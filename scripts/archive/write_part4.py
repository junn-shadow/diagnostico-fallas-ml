with open("app/dashboard/streamlit_app.py", "a", encoding="utf-8") as f:
    f.write("""
with tab_history:
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
                    h_col2.metric("Fecha de Ejecución", sel_created)
                    h_col3.metric("Anomalías Guardadas", summary_db["anomalies"])
                    h_col4.metric(
                        "Errores/Críticos Guardados", summary_db["errors"]
                    )

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
                                restore_df = pd.read_sql_query(
                                    "SELECT * FROM incidents WHERE run_id = ? ORDER BY line_id ASC",
                                    conn,
                                    params=(sel_run_id,),
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
                                    full_hist_incidents = pd.read_sql_query(
                                        "SELECT * FROM incidents WHERE run_id = ? ORDER BY line_id ASC",
                                        conn,
                                        params=(sel_run_id,),
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
        st.warning(f"Error al interactuar con el historial SQLite: {exc}")

else:
    with tab_overview:
        st.markdown(
            \"\"\"
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
            \"\"\",
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

""")
