import logging
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.nlp.distilbert_model import SemanticEmbedder
from app.nlp.remote_distilbert import RemoteSemanticEmbedder
from app.config.settings import HF_API_TOKEN
from app.correlation.root_cause import infer_root_cause

logger = logging.getLogger(__name__)

# Base de conocimiento semántica para diagnóstico de fallas comunes
SEMANTIC_KNOWLEDGE_BASE = [
    {
        "pattern": "Database connection timeout pool exhausted sql query failure socket error database unreachable deadlock",
        "root_cause": "Caída, saturación o interbloqueo en Base de Datos",
        "recommendation": "Verificar disponibilidad del motor SQL, estado del pool de conexiones y métricas de latencia.",
    },
    {
        "pattern": "Network connection refused port unreachable host disconnected tcp udp ospf bgp ftp timeout link down interface",
        "root_cause": "Falla de red, protocolo inestable o pérdida de conexión",
        "recommendation": "Validar conectividad física/lógica, estado del protocolo (OSPF/BGP), firewall y puertos.",
    },
    {
        "pattern": "Disk space full write failed filesystem read-only partition capacity limit out of disk io error",
        "root_cause": "Falla de disco, saturación de I/O o falta de espacio",
        "recommendation": "Revisar logs SMART, espacio libre, inodes y posibles errores en el sistema de archivos.",
    },
    {
        "pattern": "Out of memory error HeapSpace high CPU usage process killed server overload segfault system out of memory",
        "root_cause": "Saturación de CPU/RAM o proceso finalizado por OOM",
        "recommendation": "Inspeccionar picos de consumo (CPU/RAM), límites del SO (OOM Killer) y procesos zombis.",
    },
    {
        "pattern": "Access denied unauthorized credentials expired token invalid login forbidden permission error password failure",
        "root_cause": "Fallo de autenticación o permisos insuficientes",
        "recommendation": "Revisar rotación de credenciales, tokens vencidos, políticas IAM y bloqueos de IP.",
    },
    {
        "pattern": "Syntax error invalid configuration missing key parse failure yaml format error",
        "root_cause": "Error en configuración o formato inválido",
        "recommendation": "Auditar los cambios recientes en archivos de configuración y validar sintaxis.",
    },
    {
        "pattern": "Service crashed daemon stopped fatal exit core dumped restart failed",
        "root_cause": "Caída crítica de servicio o demonio (Crash)",
        "recommendation": "Revisar los core dumps, logs del sistema (journalctl) e intentar reiniciar el servicio.",
    }
]

# Recomendaciones tradicionales basadas en reglas para mapeo rápido
RECOMMENDATIONS = {
    "base de datos": "Verificar disponibilidad del motor SQL, estado del pool de conexiones y métricas de latencia.",
    "red": "Validar conectividad física/lógica, estado del protocolo (OSPF/BGP), firewall y puertos.",
    "disco": "Revisar logs SMART, espacio libre, inodes y posibles errores en el sistema de archivos.",
    "recursos": "Inspeccionar picos de consumo (CPU/RAM), límites del SO (OOM Killer) y procesos zombis.",
    "cpu": "Inspeccionar picos de consumo (CPU/RAM), límites del SO (OOM Killer) y procesos zombis.",
    "autenticacion": "Revisar rotación de credenciales, tokens vencidos, políticas IAM y bloqueos de IP.",
    "configuración": "Auditar los cambios recientes en archivos de configuración y validar sintaxis.",
    "servicio": "Revisar los core dumps, logs del sistema (journalctl) e intentar reiniciar el servicio.",
}


def recommend_action(root_cause: str) -> str:
    """Busca una recomendación adecuada según la causa raíz diagnosticada."""
    text = root_cause.lower()
    for key, recommendation in RECOMMENDATIONS.items():
        if key in text:
            return RECOMMENDATIONS[key]

    return "Realizar un análisis de trazas para identificar el origen de este comportamiento anómalo."


def _get_embedder(force_backend: str = None):
    """Return the appropriate embedder based on force_backend."""
    if force_backend == "remote":
        return RemoteSemanticEmbedder()
    return SemanticEmbedder(force_backend=force_backend)


def infer_semantic_diagnostics(
    messages: list[str], threshold: float = 0.50, force_backend: str = None
) -> tuple[list[str], list[str]]:
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

        # Ajuste y codificación conjunta para garantizar mismas dimensiones
        all_texts = unique_msgs + knowledge_patterns
        all_vectors = embedder.encode(all_texts)
        
        msg_vectors = all_vectors[:len(unique_msgs)]
        pattern_vectors = all_vectors[len(unique_msgs):]

        # Si las dimensiones coinciden, realizamos la similitud semántica
        if msg_vectors.shape[1] == pattern_vectors.shape[1]:
            sim_matrix = cosine_similarity(msg_vectors, pattern_vectors)
            msg_mapping = {}
            for idx, msg in enumerate(unique_msgs):
                scores = sim_matrix[idx]
                best_idx = int(np.argmax(scores))
                best_score = float(scores[best_idx])
                
                logger.debug("Mensaje: '%s' | Mejor match (score=%.2f): '%s'", msg[:50], best_score, knowledge_patterns[best_idx][:50])

                if best_score >= threshold:
                    matched = SEMANTIC_KNOWLEDGE_BASE[best_idx]
                    msg_mapping[msg] = (
                        matched["root_cause"],
                        matched["recommendation"],
                    )
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
