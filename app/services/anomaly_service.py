from app.models.anomaly_detector import detect_anomalies
from app.config.settings import (
    DEFAULT_CONTAMINATION,
    DEFAULT_DBSCAN_EPS,
    DEFAULT_DBSCAN_MIN_SAMPLES,
)


def enrich_with_anomalies(
    logs,
    tfidf,
    numeric,
    contamination: float = DEFAULT_CONTAMINATION,
    clustering_method: str = "auto",
    clustering_eps: float = DEFAULT_DBSCAN_EPS,
    clustering_min_samples: int = DEFAULT_DBSCAN_MIN_SAMPLES,
    clustering_n_clusters: int = 5,
):
    """
    Enriquece el DataFrame de logs con información sobre anomalías detectadas
    e identificadores de clústeres. Almacena las métricas obtenidas en df.attrs.
    """
    df = logs.copy()
    isolation, dbscan = detect_anomalies(
        tfidf,
        numeric,
        contamination=contamination,
        clustering_method=clustering_method,
        clustering_eps=clustering_eps,
        clustering_min_samples=clustering_min_samples,
        clustering_n_clusters=clustering_n_clusters,
    )
    df["is_anomaly"] = isolation["is_anomaly"]
    df["anomaly_score"] = isolation["anomaly_score"]
    df["dbscan_cluster"] = dbscan["cluster"].values

    # Guardar métricas evaluadas
    df.attrs["statistical_cluster_backend"] = dbscan.get("backend", "unknown")
    df.attrs["silhouette_score"] = dbscan.get("silhouette_score", 0.0)
    df.attrs["davies_bouldin_index"] = dbscan.get("davies_bouldin_index", 0.0)

    return df
