from app.services.nlp_service import enrich_with_semantics
from app.config.paths import SAMPLES_DIR
from app.services.log_service import load_and_parse


def test_semantic_cluster_column_is_added():
    logs = load_and_parse(SAMPLES_DIR / "sample.log")
    enriched = enrich_with_semantics(logs)

    assert "semantic_cluster" in enriched.columns
    assert len(enriched) == len(logs)


def test_tfidf_backend_consistency():
    from app.nlp.distilbert_model import SemanticEmbedder

    embedder = SemanticEmbedder()
    embedder.backend = "tfidf"

    all_texts = ["connection refused", "disk space full", "database timeout", "oom error"]
    subset1 = ["connection refused", "database timeout"]
    subset2 = ["disk space full"]

    res_all = embedder.encode(all_texts)
    res_sub1 = embedder.encode(subset1)
    res_sub2 = embedder.encode(subset2)

    assert res_all.shape[1] == res_sub1.shape[1]
    assert res_all.shape[1] == res_sub2.shape[1]
    assert res_all.shape[1] > 0

