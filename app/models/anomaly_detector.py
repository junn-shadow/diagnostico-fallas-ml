from app.models.dbscan_model import cluster_with_dbscan
from app.models.isolation_forest import detect_with_isolation_forest
from app.config.settings import DEFAULT_CONTAMINATION, DEFAULT_DBSCAN_EPS, DEFAULT_DBSCAN_MIN_SAMPLES


def detect_anomalies(
    tfidf,
    numeric,
    contamination: float = DEFAULT_CONTAMINATION,
    clustering_method: str = "auto",
    clustering_eps: float = DEFAULT_DBSCAN_EPS,
    clustering_min_samples: int = DEFAULT_DBSCAN_MIN_SAMPLES,
    clustering_n_clusters: int = 5,
):
    """
    Orquesta la ejecución del detector de anomalías (Isolation Forest) y 
    del agrupamiento (DBSCAN/KMeans) utilizando los parámetros configurados.
    """
    isolation = detect_with_isolation_forest(tfidf, numeric, contamination=contamination)
    dbscan = cluster_with_dbscan(
        tfidf,
        eps=clustering_eps,
        min_samples=clustering_min_samples,
        method=clustering_method,
        n_clusters=clustering_n_clusters,
    )
    return isolation, dbscan
