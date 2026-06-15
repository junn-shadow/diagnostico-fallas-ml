from pathlib import Path

import pandas as pd


def profile_log_file(path: str | Path) -> dict:
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
    return {
        "file_name": log_path.name,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2),
        "total_lines": total_lines,
        "non_empty_lines": non_empty_lines,
        "sample_lines": sample_lines,
    }


def load_log_file(path: str | Path) -> pd.DataFrame:
    """Load a plain-text log file into a dataframe preserving line numbers."""
    log_path = Path(path)
    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    rows = []
    with log_path.open("r", encoding="utf-8", errors="ignore") as file:
        for index, line in enumerate(file, start=1):
            message = line.strip()
            if message:
                rows.append({"line_id": index, "raw_log": message})

    return pd.DataFrame(rows, columns=["line_id", "raw_log"])
