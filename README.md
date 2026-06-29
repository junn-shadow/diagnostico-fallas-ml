# Diagnostico Automatico de Fallas con Machine Learning y NLP

Sistema desarrollado en Python para analizar logs de servidores, detectar anomalias mediante tecnicas de Machine Learning no supervisado y sugerir posibles causas raiz utilizando NLP.

## Caracteristicas

- Deteccion de anomalias con Isolation Forest y DBSCAN.
- Parsing de logs mediante enfoque tipo Drain.
- Embeddings semanticos con DistilBERT (remoto via HF API o local).
- Correlacion de eventos y recomendaciones automaticas.
- Dashboard interactivo con Streamlit.
- **Base de conocimientos SQLite** con persistencia de logs crudos e incidentes.

## Estructura del proyecto

```
app/
  ingestion/      # Carga de logs (load_logs.py)
  preprocessing/  # Limpieza y extraccion de caracteristicas
  models/         # Modelos de deteccion (IsolationForest, DBSCAN)
  nlp/            # Procesamiento semantico (DistilBERT, TF-IDF fallback)
  correlation/    # Analisis de causa raiz y recomendaciones
  dashboard/      # Interfaz Streamlit
  database/       # Persistencia SQLite
    connection.py     # Conexion WAL al archivo incidents.sqlite3
    sqlite_db.py      # Esquema (incidents + raw_logs) e inicializacion
    repositories.py   # IncidentRepository + LogRepository (CRUD)
  services/       # Orquestacion del pipeline
  config/         # settings.py y paths.py
datasets/
  samples/        # Logs de ejemplo
scripts/
  migrate_csv_to_sqlite.py  # Migracion de logs CSV/TXT a SQLite
```

## Instalacion

```bash
pip install -r requirements.txt
```

Crea un archivo `.env` en la raiz con tus credenciales (ver `.env.example`):

```env
HF_API_TOKEN=hf_...           # Token de Hugging Face (opcional)
SQLITE_DB_PATH=incidents.sqlite3  # Ruta del archivo SQLite (opcional)
```

## Ejecucion

### Consola

```bash
python run.py --log datasets/samples/sample.log
```

### Dashboard

```bash
streamlit run app/dashboard/streamlit_app.py
```

## Flujo del sistema

```
Logs → Ingestion (load_logs) → Preprocesamiento → Parser Drain
     → Extraccion de caracteristicas → Deteccion de anomalias
     → NLP (embeddings) → Correlacion → Alertas → Dashboard
          ↓                                   ↓
     raw_logs (SQLite)               incidents (SQLite)
```

## Persistencia con SQLite

El sistema utiliza una base de datos SQLite (`incidents.sqlite3`) con dos tablas:

| Tabla | Descripcion |
|-------|-------------|
| `incidents` | Anomalias y errores detectados por el pipeline de ML |
| `raw_logs` | **Base de conocimientos**: todas las lineas de log ingeridas |

### Acceso via LogRepository

```python
from app.database.repositories import LogRepository

# Buscar logs por palabra clave
df = LogRepository.search_by_keyword("Connection refused")

# Filtrar por nivel de severidad
errores = LogRepository.search_by_level("ERROR")

# Contar logs de un archivo especifico
n = LogRepository.count(source="server.log")

# Ver todos los logs recientes
todos = LogRepository.list_all(limit=50)
```

### Migracion de datos existentes

```bash
# Ver cuantos registros se migrarian (sin modificar la BD)
python scripts/migrate_csv_to_sqlite.py --dry-run

# Ejecutar la migracion real
python scripts/migrate_csv_to_sqlite.py

# Migrar desde un directorio especifico
python scripts/migrate_csv_to_sqlite.py --dir /ruta/a/mis/logs
```

### Consulta directa de la BD

```bash
sqlite3 incidents.sqlite3 "SELECT COUNT(*) FROM raw_logs;"
sqlite3 incidents.sqlite3 "SELECT level, COUNT(*) FROM raw_logs GROUP BY level;"
```

## Tests

```bash
# Suite completa (excluye test_nlp por requerir modelo grande)
pytest app/tests/test_sqlite_repo.py app/tests/test_parser.py app/tests/test_models.py app/tests/test_pipeline.py -v

# Solo tests del repositorio SQLite
pytest app/tests/test_sqlite_repo.py -v
```

Los tests del repositorio usan una base SQLite **en-memoria** (via fixture `in_memory_db`) y no requieren el archivo `incidents.sqlite3`.

## Tecnologias utilizadas

- Python 3.10+
- Streamlit
- Scikit-learn (IsolationForest, DBSCAN, TF-IDF)
- DistilBERT / Hugging Face Transformers
- SQLite (std-lib `sqlite3`)
- Docker
