import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_distances

from app.config.settings import DEFAULT_LARGE_LOG_CLUSTERS, DEFAULT_RANDOM_STATE, MAX_PAIRWISE_CLUSTER_ROWS


def semantic_clusters(embeddings, eps: float = 0.35, min_samples: int = 1) -> pd.Series:
    rows = embeddings.shape[0] if hasattr(embeddings, "shape") else len(embeddings)
    if rows == 0:
        return pd.Series(dtype=int)
    if rows == 1:
        return pd.Series([0])

    if rows > MAX_PAIRWISE_CLUSTER_ROWS:
        if hasattr(embeddings, "toarray"):
            components = max(2, min(50, embeddings.shape[1] - 1, rows - 1))
            reduced = TruncatedSVD(n_components=components, random_state=DEFAULT_RANDOM_STATE).fit_transform(embeddings)
        else:
            reduced = embeddings
        clusters = max(2, min(DEFAULT_LARGE_LOG_CLUSTERS, rows // 1000 + 2))
        labels = MiniBatchKMeans(
            n_clusters=clusters,
            random_state=DEFAULT_RANDOM_STATE,
            batch_size=2048,
            n_init="auto",
        ).fit_predict(reduced)
        return pd.Series(labels)

    distances = cosine_distances(embeddings)
    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="precomputed").fit_predict(distances)
    return pd.Series(labels)
