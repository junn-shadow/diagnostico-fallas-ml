with open("app/dashboard/streamlit_app.py", "a", encoding="utf-8") as f:
    f.write("""
with st.sidebar:
    st.markdown(
        \"\"\"
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">🔬</div>
            <span class="sidebar-brand-text">DiagnosticOps</span>
        </div>
        <div class="sidebar-version">v2.0 · ML Pipeline</div>
        \"\"\",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Fuente de logs", type=["log", "txt"])
    use_sample = st.toggle("Usar dataset de muestra", value=uploaded is None)
    persist = st.toggle("Persistir incidentes", value=True)
    auto_run = st.toggle("Analizar al cargar", value=False)

    st.divider()
    st.markdown(
        '<div class="sidebar-section-label">Hiperparámetros ML</div>',
        unsafe_allow_html=True,
    )
    contamination = st.slider(
        "Contaminación (Isolation Forest)",
        min_value=0.01,
        max_value=0.50,
        value=0.15,
        step=0.01,
        help="Proporción esperada de anomalías en el dataset.",
    )
    clustering_method = st.selectbox(
        "Método de Agrupamiento",
        options=["auto", "dbscan", "kmeans"],
        index=0,
        help="Algoritmo de clustering para categorizar las anomalías.",
    )
    with st.expander("Parámetros del Clustering"):
        clustering_eps = st.slider(
            "DBSCAN Epsilon",
            min_value=0.05,
            max_value=2.00,
            value=0.80,
            step=0.05,
            help="Distancia máxima coseno para considerar puntos del mismo cluster.",
        )
        clustering_min_samples = st.slider(
            "DBSCAN Min Samples",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
            help="Muestras mínimas para formar un cluster en DBSCAN.",
        )
        clustering_n_clusters = st.slider(
            "Clusters K (K-Means)",
            min_value=2,
            max_value=20,
            value=5,
            step=1,
            help="Número de centroides a ajustar en el algoritmo K-Means.",
        )

    st.divider()
    st.markdown(
        '<div class="sidebar-section-label">Motor NLP</div>', unsafe_allow_html=True
    )

    nlp_backend = st.selectbox(
        "Backend NLP",
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


def run_pipeline(
    log_path: Path,
    persist: bool,
    contamination: float,
    clustering_method: str,
    clustering_eps: float,
    clustering_min_samples: int,
    clustering_n_clusters: int,
    nlp_backend: str,
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

    st.session_state["last_result"] = run_pipeline(
        log_path,
        persist,
        contamination=contamination,
        clustering_method=clustering_method,
        clustering_eps=clustering_eps,
        clustering_min_samples=clustering_min_samples,
        clustering_n_clusters=clustering_n_clusters,
        nlp_backend=nlp_backend,
    )
    st.session_state["last_params"] = current_params
    st.session_state["is_historical_view"] = False

""")
