"""
test_sqlite_repo.py – Tests unitarios del LogRepository (base de conocimientos).

Todos los tests usan la fixture in_memory_db de conftest.py para operar
sobre una base SQLite en-memoria sin tocar el archivo incidents.sqlite3.
"""
import pytest

from app.database.repositories import LogRepository


# ─── helpers ────────────────────────────────────────────────────────────────

def _make_record(n: int, level: str = "INFO", source: str = "test.log") -> dict:
    return {
        "line_id": n,
        "timestamp": f"2026-01-0{n} 12:00:00",
        "level": level,
        "message": f"Mensaje de prueba numero {n}",
        "source": source,
    }


# ─── tests individuales ──────────────────────────────────────────────────────

def test_add_log_inserts_row(in_memory_db):
    """add_log debe insertar exactamente una fila."""
    LogRepository.add_log(
        message="Conexion rechazada",
        line_id=1,
        timestamp="2026-01-01 10:00:00",
        level="ERROR",
        source="server.log",
    )
    assert LogRepository.count() == 1


def test_count_returns_zero_when_empty(in_memory_db):
    """count() debe devolver 0 cuando no hay filas."""
    assert LogRepository.count() == 0


def test_add_logs_bulk_inserts_multiple(in_memory_db):
    """add_logs_bulk debe insertar N filas de manera eficiente."""
    records = [_make_record(i) for i in range(1, 6)]
    inserted = LogRepository.add_logs_bulk(records)
    assert inserted == 5
    assert LogRepository.count() == 5


def test_add_logs_bulk_empty_list_returns_zero(in_memory_db):
    """add_logs_bulk con lista vacia debe devolver 0 y no fallar."""
    assert LogRepository.add_logs_bulk([]) == 0


def test_get_by_id_returns_correct_row(in_memory_db):
    """get_by_id debe devolver el registro con el id indicado."""
    LogRepository.add_log(message="Test get_by_id", level="DEBUG", source="unit")
    row = LogRepository.get_by_id(1)
    assert row is not None
    assert row["message"] == "Test get_by_id"
    assert row["level"] == "DEBUG"


def test_get_by_id_returns_none_for_missing(in_memory_db):
    """get_by_id debe devolver None si el id no existe."""
    assert LogRepository.get_by_id(999) is None


def test_list_all_returns_dataframe(in_memory_db):
    """list_all debe devolver un DataFrame con las columnas esperadas."""
    LogRepository.add_logs_bulk([_make_record(1), _make_record(2)])
    df = LogRepository.list_all()
    assert len(df) == 2
    assert "message" in df.columns
    assert "level" in df.columns
    assert "source" in df.columns


def test_list_all_filters_by_source(in_memory_db):
    """list_all con source= debe filtrar correctamente."""
    LogRepository.add_log(message="A", source="alpha.log")
    LogRepository.add_log(message="B", source="beta.log")
    df = LogRepository.list_all(source="alpha.log")
    assert len(df) == 1
    assert df.iloc[0]["source"] == "alpha.log"


def test_search_by_level_filters_correctly(in_memory_db):
    """search_by_level debe devolver solo los logs del nivel solicitado."""
    LogRepository.add_logs_bulk([
        _make_record(1, level="ERROR"),
        _make_record(2, level="INFO"),
        _make_record(3, level="ERROR"),
    ])
    df = LogRepository.search_by_level("ERROR")
    assert len(df) == 2
    assert all(df["level"] == "ERROR")


def test_search_by_keyword_finds_matches(in_memory_db):
    """search_by_keyword debe encontrar mensajes que contengan la clave."""
    LogRepository.add_log(message="Connection refused from 10.0.0.1", level="ERROR")
    LogRepository.add_log(message="Disk full warning on /var/log", level="WARNING")
    LogRepository.add_log(message="Service started successfully", level="INFO")

    df = LogRepository.search_by_keyword("Connection")
    assert len(df) == 1
    assert "Connection" in df.iloc[0]["message"]


def test_search_by_keyword_case_insensitive(in_memory_db):
    """LIKE en SQLite no distingue mayusculas/minusculas para ASCII."""
    LogRepository.add_log(message="connection timeout", level="ERROR")
    df = LogRepository.search_by_keyword("CONNECTION")
    assert len(df) == 1


def test_count_by_source(in_memory_db):
    """count con source= debe contar solo las filas de esa fuente."""
    LogRepository.add_log(message="A", source="app.log")
    LogRepository.add_log(message="B", source="app.log")
    LogRepository.add_log(message="C", source="other.log")
    assert LogRepository.count(source="app.log") == 2
    assert LogRepository.count(source="other.log") == 1
    assert LogRepository.count() == 3


def test_clear_source_removes_only_that_source(in_memory_db):
    """clear_source debe eliminar solo los logs de la fuente indicada."""
    LogRepository.add_log(message="A", source="app.log")
    LogRepository.add_log(message="B", source="app.log")
    LogRepository.add_log(message="C", source="other.log")

    deleted = LogRepository.clear_source("app.log")
    assert deleted == 2
    assert LogRepository.count(source="app.log") == 0
    assert LogRepository.count(source="other.log") == 1
    assert LogRepository.count() == 1
