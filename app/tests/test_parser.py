import pandas as pd

from app.preprocessing.cleaner import clean_logs
from app.preprocessing.drain_parser import parse_logs


def test_parser_extracts_level_and_template():
    logs = pd.DataFrame(
        [{"line_id": 1, "raw_log": "2026-05-25 ERROR Connection failed from 10.0.0.1"}]
    )

    parsed = parse_logs(clean_logs(logs))

    assert parsed.loc[0, "level"] == "ERROR"
    assert "<DATE>" in parsed.loc[0, "event_template"]
    assert "<IP>" in parsed.loc[0, "event_template"]
