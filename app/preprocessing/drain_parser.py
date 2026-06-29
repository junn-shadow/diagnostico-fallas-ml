import re
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Expresiones regulares para normalización inicial de tokens
DATE_RE = re.compile(r"\b\d{4}[-/]\d{2}[-/]\d{2}\b")
TIME_RE = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b")
NUMBER_RE = re.compile(r"\b\d+\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
LEVEL_RE = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)


class LogGroup:
    """Representa un grupo de logs que comparten la misma plantilla (template)."""

    def __init__(self, template_tokens: list[str], group_id: int):
        self.template_tokens = template_tokens
        self.group_id = group_id


class DrainNode:
    """Nodo en el árbol de búsqueda de Drain."""

    def __init__(self):
        self.child_nodes = {}
        self.log_groups = []


class DrainParser:
    """Implementación limpia y dinámica del algoritmo clásico Drain para minería de plantillas de logs."""

    def __init__(self, depth: int = 4, sim_threshold: float = 0.5):
        self.depth = depth
        self.sim_threshold = sim_threshold
        self.root = DrainNode()
        self.next_group_id = 1

    def _has_numbers(self, s: str) -> bool:
        """Determina si un token contiene dígitos, sugiriendo una variable."""
        return any(c.isdigit() for c in s)

    def _preprocess_tokens(self, message: str) -> list[str]:
        """Preprocesa el texto aplicando expresiones regulares antes del análisis en árbol."""
        text = DATE_RE.sub("<DATE>", message)
        text = TIME_RE.sub("<TIME>", text)
        text = IP_RE.sub("<IP>", text)
        text = HEX_RE.sub("<HEX>", text)
        text = NUMBER_RE.sub("<NUM>", text)
        return text.split()

    def add_log_message(self, message: str) -> tuple[int, str]:
        """Inserta un log en el árbol y retorna su identificador y plantilla."""
        if not message or not str(message).strip():
            return 0, "[EMPTY_LOG]"
        
        # Truncate extremely long messages
        if len(message) > 10000:
            message = message[:10000] + " ...[TRUNCATED]"

        tokens = self._preprocess_tokens(message)
        log_len = len(tokens)

        # Nivel 1: Longitud de la lista de tokens
        if log_len not in self.root.child_nodes:
            self.root.child_nodes[log_len] = DrainNode()
        parent_node = self.root.child_nodes[log_len]

        # Niveles 2 a d: Tokens en posiciones fijas (para dividir el espacio de búsqueda)
        max_depth = min(self.depth - 1, log_len)
        for i in range(max_depth):
            token = tokens[i]
            # Si el token tiene números, se asume que es una variable/comodín en la ruta de búsqueda
            token_key = "<*>" if self._has_numbers(token) else token

            if token_key not in parent_node.child_nodes:
                parent_node.child_nodes[token_key] = DrainNode()
            parent_node = parent_node.child_nodes[token_key]

        # En el nodo hoja: encontrar la plantilla más similar
        best_match = None
        best_sim = -1.0

        for group in parent_node.log_groups:
            if len(group.template_tokens) != log_len:
                continue

            sim = 0
            for t_log, t_grp in zip(tokens, group.template_tokens):
                if t_log == t_grp:
                    sim += 1

            sim_ratio = sim / log_len if log_len > 0 else 1.0
            if sim_ratio > best_sim:
                best_sim = sim_ratio
                best_match = group

        # Actualizar grupo coincidente o crear uno nuevo
        if best_sim >= self.sim_threshold and best_match is not None:
            # Fusión de plantilla: los tokens diferentes se marcan con comodín <*>
            new_template = []
            for t_log, t_grp in zip(tokens, best_match.template_tokens):
                if t_log == t_grp:
                    new_template.append(t_grp)
                else:
                    new_template.append("<*>")
            best_match.template_tokens = new_template
            matched_group = best_match
        else:
            # Crear nuevo grupo
            matched_group = LogGroup(tokens, self.next_group_id)
            self.next_group_id += 1
            parent_node.log_groups.append(matched_group)

        template_str = " ".join(matched_group.template_tokens)
        return matched_group.group_id, template_str


def parse_level(message: str) -> str:
    """Busca y extrae el nivel de severidad del log."""
    match = LEVEL_RE.search(message)
    return match.group(1).upper() if match else "INFO"


def parse_logs(logs: pd.DataFrame) -> pd.DataFrame:
    """Punto de entrada compatible con el pipeline de DiagnosticOps ML."""
    df = logs.copy()
    source_col = "clean_log" if "clean_log" in df.columns else "raw_log"

    parser = DrainParser()
    event_ids = []
    event_templates = []

    for msg in df[source_col].astype(str):
        event_id, template = parser.add_log_message(msg)
        event_ids.append(event_id)
        event_templates.append(template)

    logger.info("DrainParser creó %d plantillas únicas a partir de %d mensajes.", parser.next_group_id - 1, len(df))

    df["event_template"] = event_templates
    df["level"] = df[source_col].astype(str).map(parse_level)
    df["event_id"] = event_ids
    return df
