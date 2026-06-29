from app.correlation.recommendation_engine import infer_semantic_diagnostics, recommend_action
from app.correlation.root_cause import infer_root_cause

def test_infer_semantic_diagnostics_tfidf():
    # Probar que el backend TF-IDF funciona sin errores de dimensión
    messages = [
        "Database connection timeout",
        "Network connection refused",
        "Random unknown error"
    ]
    causes, recs = infer_semantic_diagnostics(messages, threshold=0.1, force_backend="tfidf")
    
    assert len(causes) == 3
    assert len(recs) == 3
    # El primero deberia matchear BD debido a las palabras clave
    assert "base de datos" in causes[0].lower()

def test_infer_root_cause_rules():
    assert "base de datos" in infer_root_cause("SQL query failed").lower()
    assert "red" in infer_root_cause("Network unreachable").lower()
    assert "disco" in infer_root_cause("Disk full").lower()
    assert "autenticacion" in infer_root_cause("Permission denied").lower()
    assert "recursos" in infer_root_cause("OOM error").lower()
    assert "Anomalia detectada" in infer_root_cause("Unknown error xyz")

def test_recommend_action():
    assert "motor" in recommend_action("Posible caida o saturacion de base de datos")
    assert "Revisar logs cercanos" in recommend_action("Anomalia detectada; requiere revision tecnica")
