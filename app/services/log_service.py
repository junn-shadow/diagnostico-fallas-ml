import logging
from app.ingestion.load_logs import load_log_file
from app.preprocessing.cleaner import clean_logs
from app.preprocessing.drain_parser import parse_logs

logger = logging.getLogger(__name__)

def load_and_parse(path):
    logger.info("Cargando logs desde: %s", path)
    logs = load_log_file(path)
    if logs.empty:
        logger.warning("El archivo de log está vacío o sin líneas válidas: %s", path)
        return logs
        
    logger.info("Limpiando %d eventos de log...", len(logs))
    logs = clean_logs(logs)
    
    logger.info("Parseando eventos de log con Drain...")
    logs = parse_logs(logs)
    
    logger.info("Carga y parseo completados.")
    return logs
