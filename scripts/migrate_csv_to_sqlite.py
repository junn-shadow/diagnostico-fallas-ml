"""
migrate_csv_to_sqlite.py – Migra archivos de log CSV/TXT existentes a SQLite.

Uso desde la raiz del proyecto::

    python scripts/migrate_csv_to_sqlite.py [--dir DATASETS_DIR] [--dry-run]

El script recorre recursivamente el directorio indicado (por defecto
``datasets/``), procesa cada archivo ``.log`` y ``.csv`` encontrado
e inserta las lineas en la tabla ``raw_logs`` mediante
``LogRepository.add_logs_bulk``.

Si el archivo ya fue ingerido previamente (misma ruta absoluta),
se limpia primero su fuente en SQLite para evitar duplicados.
"""
import argparse
import csv
import sys
from pathlib import Path

# Asegurar que el paquete app sea importable desde la raiz del proyecto
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from app.ingestion.load_logs import _parse_line  # extractor de ts/lvl/msg
from app.database.repositories import LogRepository


def _migrate_log_file(path: Path, dry_run: bool = False) -> int:
    """Parsea un archivo .log plano y lo inserta en raw_logs."""
    records = []
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for idx, line in enumerate(f, start=1):
            message = line.strip()
            if not message:
                continue
            ts, lvl, msg = _parse_line(message)
            records.append(
                {
                    "line_id": idx,
                    "timestamp": ts,
                    "level": lvl,
                    "message": msg,
                    "source": str(path),
                }
            )

    if not records:
        return 0

    if not dry_run:
        # Borrar ingestiones previas para evitar duplicados
        LogRepository.clear_source(str(path))
        return LogRepository.add_logs_bulk(records)

    return len(records)  # dry-run: reportar cuantas se insertarian


def _migrate_csv_file(path: Path, dry_run: bool = False) -> int:
    """Parsea un CSV con columnas timestamp, level, message y lo inserta."""
    records = []
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            return 0

        for idx, row in enumerate(reader, start=1):
            msg = row.get("message") or row.get("raw_log") or ""
            if not msg.strip():
                continue
            records.append(
                {
                    "line_id": idx,
                    "timestamp": row.get("timestamp", ""),
                    "level": (row.get("level") or "INFO").upper(),
                    "message": msg.strip(),
                    "source": str(path),
                }
            )

    if not records:
        return 0

    if not dry_run:
        LogRepository.clear_source(str(path))
        return LogRepository.add_logs_bulk(records)

    return len(records)


def migrate(data_dir: Path, dry_run: bool = False) -> None:
    """Punto de entrada principal de la migracion."""
    if not data_dir.exists():
        print(f"[ERROR] Directorio no encontrado: {data_dir}")
        sys.exit(1)

    log_files = list(data_dir.rglob("*.log"))
    csv_files = list(data_dir.rglob("*.csv"))
    all_files = log_files + csv_files

    if not all_files:
        print(f"[INFO] No se encontraron archivos .log o .csv en {data_dir}")
        return

    total_inserted = 0
    mode = "[DRY-RUN]" if dry_run else "[INSERTING]"

    for f in all_files:
        try:
            if f.suffix == ".log":
                n = _migrate_log_file(f, dry_run=dry_run)
            else:
                n = _migrate_csv_file(f, dry_run=dry_run)

            print(f"  {mode} {f.relative_to(data_dir.parent):50s}  -> {n:>6} registros")
            total_inserted += n
        except Exception as exc:
            print(f"  [ERROR] {f}: {exc}")

    action = "se insertarian" if dry_run else "insertados"
    print(f"\n[DONE] Total registros {action}: {total_inserted}")
    if dry_run:
        print("       (ejecutar sin --dry-run para aplicar los cambios)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Migra archivos de log CSV/TXT a la base de conocimientos SQLite."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=_ROOT / "datasets",
        help="Directorio raiz de los datasets (default: datasets/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra cuantos registros se insertarian sin modificar la BD.",
    )
    args = parser.parse_args()
    migrate(args.dir, dry_run=args.dry_run)
