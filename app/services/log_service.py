from app.ingestion.load_logs import load_log_file
from app.preprocessing.cleaner import clean_logs
from app.preprocessing.drain_parser import parse_logs


def load_and_parse(path):
    logs = load_log_file(path)
    logs = clean_logs(logs)
    return parse_logs(logs)
