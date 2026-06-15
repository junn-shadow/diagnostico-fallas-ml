from app.config.paths import SAMPLES_DIR
from app.preprocessing.feature_engineering import build_features
from app.services.log_service import load_and_parse
from app.services.anomaly_service import enrich_with_anomalies


def test_anomaly_columns_are_added():
    logs = load_and_parse(SAMPLES_DIR / "sample.log")
    tfidf, numeric, _ = build_features(logs)
    enriched = enrich_with_anomalies(logs, tfidf, numeric)

    assert "anomaly_score" in enriched.columns
    assert "dbscan_cluster" in enriched.columns
