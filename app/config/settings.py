DEFAULT_CONTAMINATION = 0.15
DEFAULT_DBSCAN_EPS = 0.8
DEFAULT_DBSCAN_MIN_SAMPLES = 2
DEFAULT_RANDOM_STATE = 42
DISTILBERT_MODEL_NAME = "distilbert-base-uncased"
MAX_PAIRWISE_CLUSTER_ROWS = 3000
DEFAULT_LARGE_LOG_CLUSTERS = 8
LARGE_LOG_THRESHOLD_ROWS = 10000
MAX_SEMANTIC_TEMPLATES = 5000
MAX_UPLOAD_SIZE_MB = 1024
import os
from pathlib import Path

# Cargar .env de forma manual para evitar dependencias externas como python-dotenv
_env_path = Path(__file__).resolve().parents[2] / ".env"
if _env_path.exists():
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _key, _val = _line.split("=", 1)
                    # Limpiar comillas si las hay
                    _val_clean = _val.strip().strip("'\"")
                    os.environ[_key.strip()] = _val_clean
    except Exception:
        pass

HF_API_TOKEN = os.getenv("HF_API_TOKEN", "")

# Ruta del archivo SQLite. Se puede sobrescribir con la variable SQLITE_DB_PATH en .env
# Por defecto usa la ruta definida en paths.py (incidents.sqlite3).
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "")

SEVERITY_WEIGHTS = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "WARN": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}
