import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, MiniBatchKMeans, KMeans
from sklearn.metrics.pairwise import cosine_distances
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics import silhouette_score, davies_bouldin_score

from app.config.settings import (
    DEFAULT_DBSCAN_EPS,
    DEFAULT_DBSCAN_MIN_SAMPLES,
    DEFAULT_LARGE_LOG_CLUSTERS,
    DEFAULT_RANDOM_STATE,
    MAX_PAIRWISE_CLUSTER_ROWS,
)


def cluster_with_dbscan(
    tfidf,
    eps: float = DEFAULT_DBSCAN_EPS,
    min_samples: int = DEFAULT_DBSCAN_MIN_SAMPLES,
    method: str = "auto",
    n_clusters: int = 5,
):
    """
    Agrupa logs por similitud utilizando DBSCAN o KMeans.
    Calcula y adjunta métricas de Silhouette y Davies-Bouldin para la evaluación del modelo.
    """
    rows = tfidf.shape[0]
    if rows <= 1:
        return {
            "model": None,
            "cluster": pd.Series([0] * rows),
            "backend": "single",
            "silhouette_score": 0.0,
            "davies_bouldin_index": 0.0,
        }

    # Determinar el método real a ejecutar
    run_method = method
    if method == "auto":
        run_method = "minibatch_kmeans" if rows > MAX_PAIRWISE_CLUSTER_ROWS else "dbscan"

    model = None
    labels = None
    backend = run_method

    if run_method in ("minibatch_kmeans", "kmeans"):
        # Reducción dimensional para KMeans en matrices sparsas de gran volumen
        components = max(2, min(50, tfidf.shape[1] - 1, rows - 1))
        reduced = TruncatedSVD(n_components=components, random_state=DEFAULT_RANDOM_STATE).fit_transform(tfidf)
        k = max(2, min(n_clusters, rows - 1))
        
        if run_method == "minibatch_kmeans":
            model = MiniBatchKMeans(
                n_clusters=k,
                random_state=DEFAULT_RANDOM_STATE,
                batch_size=2048,
                n_init="auto",
            )
            backend = "minibatch_kmeans"
        else:
            model = KMeans(
                n_clusters=k,
                random_state=DEFAULT_RANDOM_STATE,
                n_init="auto",
            )
            backend = "kmeans"

        labels = model.fit_predict(reduced)
    else:  # dbscan
        # DBSCAN basado en distancia coseno
        distances = cosine_distances(tfidf)
        model = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed")
        labels = model.fit_predict(distances)
        backend = "dbscan"

    # Cálculo seguro de métricas de calidad de clustering
    sil = 0.0
    db_idx = 0.0
    unique_labels = set(labels)

    if len(unique_labels) > 1 and len(unique_labels) < rows:
        try:
            # Optimizamos el cálculo usando muestreo aleatorio en conjuntos grandes
            sample_size = 1000 if rows > 1000 else None
            sil = float(
                silhouette_score(
                    tfidf,
                    labels,
                    metric="cosine",
                    sample_size=sample_size,
                    random_state=DEFAULT_RANDOM_STATE,
                )
            )
        except Exception:
            sil = 0.0

        try:
            dense_features = tfidf.toarray() if hasattr(tfidf, "toarray") else tfidf
            db_idx = float(davies_bouldin_score(dense_features, labels))
        except Exception:
            db_idx = 0.0

    return {
        "model": model,
        "cluster": pd.Series(labels),
        "backend": backend,
        "silhouette_score": round(sil, 4),
        "davies_bouldin_index": round(db_idx, 4),
    }
