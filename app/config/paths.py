from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[2]
APP_DIR = ROOT_DIR / "app"
DATASETS_DIR = ROOT_DIR / "datasets"
SAMPLES_DIR = DATASETS_DIR / "samples"
REPORTS_DIR = ROOT_DIR / "reports"
TRAINED_MODELS_DIR = ROOT_DIR / "trained_models"
DATABASE_PATH = ROOT_DIR / "incidents.sqlite3"


def ensure_directories() -> None:
    for path in (DATASETS_DIR, SAMPLES_DIR, REPORTS_DIR, TRAINED_MODELS_DIR):
        path.mkdir(parents=True, exist_ok=True)
