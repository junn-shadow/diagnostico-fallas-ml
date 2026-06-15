import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.nlp.distilbert_model import SemanticEmbedder
from app.nlp.remote_distilbert import RemoteSemanticEmbedder
from app.config.settings import HF_API_TOKEN
from app.correlation.root_cause import infer_root_cause

# Base de conocimiento semántica para diagnóstico de fallas comunes
SEMANTIC_KNOWLEDGE_BASE = [
    {
        "pattern": "Database connection timeout pool exhausted sql query failure socket error database unreachable connection aborted",
        "root_cause": "Posible caida o saturacion de base de datos",
        "recommendation": "Verificar disponibilidad del motor, pool de conexiones y latencia hacia la BD."
    },
    {
        "pattern": "Network connection refused port unreachable host disconnected DNS lookup failed connection timeout packet loss link down",
        "root_cause": "Posible problema de red o servicio no disponible",
        "recommendation": "Validar conectividad, DNS, firewall y estado del servicio remoto."
    },
    {
        "pattern": "Disk space full write failed filesystem read-only partition capacity limit out of disk memory write disk error write failed",
        "root_cause": "Posible falla de disco o falta de espacio",
        "recommendation": "Revisar SMART/IO, espacio libre y errores del sistema de archivos."
    },
    {
        "pattern": "Out of memory error HeapSpace high CPU usage process killed server overload system out of memory high ram load",
        "root_cause": "Posible saturacion de recursos del servidor",
        "recommendation": "Inspeccionar procesos, consumo CPU/RAM y limites del contenedor o servidor."
    },
    {
        "pattern": "Access denied unauthorized credentials expired token invalid login forbidden permission error unauthorized access credentials failure",
        "root_cause": "Posible problema de autenticacion o permisos",
        "recommendation": "Revisar credenciales, permisos, tokens vencidos y cambios recientes de acceso."
    }
]

# Recomendaciones tradicionales basadas en reglas para mapeo rápido
RECOMMENDATIONS = {
    "base de datos": "Verificar disponibilidad del motor, pool de conexiones y latencia hacia la BD.",
    "red": "Validar conectividad, DNS, firewall y estado del servicio remoto.",
    "disco": "Revisar SMART/IO, espacio libre y errores del sistema de archivos.",
    "recursos": "Inspeccionar procesos, consumo CPU/RAM y limites del contenedor o servidor.",
    "autenticacion": "Revisar credenciales, permisos, tokens vencidos y cambios recientes de acceso.",
}


def recommend_action(root_cause: str) -> str:
    """Busca una recomendación adecuada según la causa raíz diagnosticada."""
    text = root_cause.lower()
    for key, recommendation in RECOMMENDATIONS.items():
        if key in text:
            return recommendation
    return "Revisar logs cercanos en el tiempo, plantilla del evento y cambios recientes del despliegue."


def _get_embedder(force_backend: str = None):
    """Return the appropriate embedder based on force_backend."""
    if force_backend == "remote":
        return RemoteSemanticEmbedder()
    return SemanticEmbedder(force_backend=force_backend)


def infer_semantic_diagnostics(messages: list[str], threshold: float = 0.50, force_backend: str = None) -> tuple[list[str], list[str]]:
    """
    Infiere causa raíz y recomendaciones operativas utilizando similitud semántica (coseno)
    sobre embeddings de DistilBERT (local o remoto) o TF-IDF comparando con la base de conocimientos.
    """
    root_causes = []
    recommendations = []

    if not messages:
        return [], []

    try:
        embedder = _get_embedder(force_backend)
        knowledge_patterns = [item["pattern"] for item in SEMANTIC_KNOWLEDGE_BASE]
        unique_msgs = list(set(messages))

        # Ajuste y codificación según backend
        if embedder.backend == "tfidf":
            all_texts = unique_msgs + knowledge_patterns
            embedder.encode(all_texts)
            msg_vectors = embedder.encode(unique_msgs)
            pattern_vectors = embedder.encode(knowledge_patterns)
        else:
            msg_vectors = embedder.encode(unique_msgs)
            pattern_vectors = embedder.encode(knowledge_patterns)

        # Si las dimensiones coinciden, realizamos la similitud semántica
        if msg_vectors.shape[1] == pattern_vectors.shape[1]:
            sim_matrix = cosine_similarity(msg_vectors, pattern_vectors)
            msg_mapping = {}
            for idx, msg in enumerate(unique_msgs):
                scores = sim_matrix[idx]
                best_idx = int(np.argmax(scores))
                best_score = float(scores[best_idx])

                if best_score >= threshold:
                    matched = SEMANTIC_KNOWLEDGE_BASE[best_idx]
                    msg_mapping[msg] = (matched["root_cause"], matched["recommendation"])
                else:
                    cause = infer_root_cause(msg)
                    rec = recommend_action(cause)
                    msg_mapping[msg] = (cause, rec)
        else:
            raise ValueError("Mismatch in embedding dimensions")

        # Reconstruir en orden original
        for msg in messages:
            cause, rec = msg_mapping[msg]
            root_causes.append(cause)
            recommendations.append(rec)

    except Exception:
        # Fallback seguro basado en reglas estáticas
        for msg in messages:
            cause = infer_root_cause(msg)
            rec = recommend_action(cause)
            root_causes.append(cause)
            recommendations.append(rec)

    return root_causes, recommendations
