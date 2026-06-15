import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.config.settings import DEFAULT_CONTAMINATION, DEFAULT_RANDOM_STATE


def detect_with_isolation_forest(tfidf, numeric: pd.DataFrame, contamination: float = DEFAULT_CONTAMINATION):
    scaler = StandardScaler()
    numeric_scaled = scaler.fit_transform(numeric)
    features = hstack([tfidf, numeric_scaled])
    model = IsolationForest(
        contamination=contamination,
        random_state=DEFAULT_RANDOM_STATE,
        n_estimators=150,
    )
    labels = model.fit_predict(features)
    scores = model.decision_function(features)
    return {
        "model": model,
        "scaler": scaler,
        "is_anomaly": labels == -1,
        "anomaly_score": np.round(-scores, 4),
    }
