import re
from datetime import datetime
from pathlib import Path

import pandas as pd

# Patron heuristico para extraer timestamp y nivel de una linea de log.
# Soporta formatos comunes como:
#   2026-01-15 12:34:56 ERROR  mensaje
#   2026-01-15T12:34:56 [WARNING] mensaje
#   [2026-01-15 12:34:56] INFO: mensaje
_LOG_LINE_RE = re.compile(
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"
    r"[,\s\[\]]*"
    r"(?P<lvl>DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)?"
    r"\s*[:\-\]]?\s*"
    r"(?P<msg>.*)",
    re.IGNORECASE,
)

_LEVEL_ALIASES = {"WARN": "WARNING"}


def _parse_line(line: str) -> tuple:
    """Extrae (timestamp, level, message) de una linea de log.

    Si la linea no coincide con el patron, devuelve la fecha actual,
    nivel INFO y el texto completo como mensaje.
    """
    m = _LOG_LINE_RE.match(line.strip())
    if m:
        ts = m.group("ts") or datetime.now().isoformat(sep=" ", timespec="seconds")
        raw_lvl = (m.group("lvl") or "INFO").upper()
        lvl = _LEVEL_ALIASES.get(raw_lvl, raw_lvl)
        msg = m.group("msg").strip() or line.strip()
    else:
        ts = datetime.now().isoformat(sep=" ", timespec="seconds")
        lvl = "INFO"
        msg = line.strip()
    return ts, lvl, msg


def profile_log_file(path, persist: bool = True) -> dict:
    """Analiza un archivo de log y devuelve metadatos de perfil.

    Args:
        path: Ruta al archivo de log.
        persist: Si True, registra en SQLite un resumen del perfilado.

    Returns:
        Diccionario con file_name, size_bytes, size_mb, total_lines,
        non_empty_lines y sample_lines.
    """
    log_path = Path(path)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    total_lines = 0
    non_empty_lines = 0
    sample_lines = []
    with log_path.open("r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            total_lines += 1
            if line.strip():
                non_empty_lines += 1
                if len(sample_lines) < 5:
                    sample_lines.append(line.strip())

    size_bytes = log_path.stat().st_size
    profile = {
        "file_name": log_path.name,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "total_lines": total_lines,
        "non_empty_lines": non_empty_lines,
        "sample_lines": sample_lines,
    }

    if persist:
        try:
            from app.database.repositories import LogRepository

            summary_msg = (
                f"Perfilado de '{log_path.name}': "
                f"{total_lines} lineas totales, {non_empty_lines} no vacias, "
                f"{round(size_bytes / 1024, 1)} KB"
            )
            LogRepository.add_log(
                message=summary_msg,
                timestamp=datetime.now().isoformat(sep=" ", timespec="seconds"),
                level="INFO",
                source="profile",
            )
        except Exception:
            pass  # No bloquear el flujo si la DB no esta disponible

    return profile


def load_log_file(path, persist: bool = True) -> pd.DataFrame:
    """Carga un archivo de log en un DataFrame preservando numeros de linea.

    Adicionalmente, si persist=True, almacena cada linea valida en la
    tabla raw_logs de SQLite como parte de la base de conocimientos.
    La insercion se realiza en bloque (bulk) para maximo rendimiento.

    Args:
        path: Ruta al archivo de log.
        persist: Si True, guarda las lineas en SQLite.
                 Poner False en tests unitarios para evitar I/O.

    Returns:
        DataFrame con columnas line_id y raw_log.
    """
    log_path = Path(path)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    rows = []
    bulk_records = []

    with log_path.open("r", encoding="utf-8", errors="ignore") as file:
        for index, line in enumerate(file, start=1):
            message = line.strip()
            if not message:
                continue

            ts, lvl, msg = _parse_line(message)
            rows.append({"line_id": index, "raw_log": message})

            if persist:
                bulk_records.append(
                    {
                        "line_id": index,
                        "timestamp": ts,
                        "level": lvl,
                        "message": msg,
                        "source": str(log_path),
                    }
                )

    if persist and bulk_records:
        try:
            from app.database.repositories import LogRepository

            LogRepository.add_logs_bulk(bulk_records)
        except Exception:
            pass  # No bloquear el pipeline si la DB no esta disponible

    return pd.DataFrame(rows, columns=["line_id", "raw_log"])
