import pandas as pd
from app.preprocessing.drain_parser import DrainParser, parse_logs


def test_drain_parser_empty_message():
    parser = DrainParser()
    event_id, template = parser.add_log_message("")
    assert event_id == 0
    assert template == "[EMPTY_LOG]"

    event_id, template = parser.add_log_message("   ")
    assert event_id == 0
    assert template == "[EMPTY_LOG]"


def test_drain_parser_extremely_long_message():
    parser = DrainParser()
    long_msg = "A" * 15000
    event_id, template = parser.add_log_message(long_msg)
    
    assert event_id > 0
    assert "A" * 10000 in template
    assert "[TRUNCATED]" in template


def test_drain_parser_template_matching():
    parser = DrainParser()
    id1, temp1 = parser.add_log_message("Connection refused from 10.0.0.1")
    id2, temp2 = parser.add_log_message("Connection refused from 192.168.1.5")
    
    # Ambos deben agruparse en la misma plantilla gracias a la normalización de IP
    assert id1 == id2
    assert "<IP>" in temp1


def test_parse_logs_dataframe():
    df = pd.DataFrame([
        {"raw_log": "Connection refused from 10.0.0.1 on port 22"},
        {"raw_log": ""},
        {"raw_log": "Connection refused from 192.168.1.5 on port 80"}
    ])
    
    # Simulamos limpieza
    df["clean_log"] = df["raw_log"]
    
    parsed = parse_logs(df)
    assert len(parsed) == 3
    assert "event_template" in parsed.columns
    
    # El segundo mensaje debe ser vacío
    assert parsed.loc[1, "event_template"] == "[EMPTY_LOG]"
    
    # El primero y tercero deben agruparse
    assert parsed.loc[0, "event_id"] == parsed.loc[2, "event_id"]
    assert "<IP>" in parsed.loc[0, "event_template"]
    assert "<NUM>" in parsed.loc[0, "event_template"]
