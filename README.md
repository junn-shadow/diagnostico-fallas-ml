<<<<<<< HEAD
# Diagnostico automatico de fallas con ML y NLP

Prototipo en Python para analizar logs de servidores web, estructurarlos con un parser tipo Drain, detectar anomalias con Machine Learning no supervisado y sugerir posibles causas raiz mediante NLP y reglas de correlacion.

## Modulos principales

- `app/ingestion`: carga archivos `.log` o `.txt`.
- `app/preprocessing`: limpieza, parsing tipo Drain y feature engineering.
- `app/models`: deteccion no supervisada con Isolation Forest y DBSCAN.
- `app/nlp`: embeddings semanticos con DistilBERT si esta disponible localmente; fallback TF-IDF para demos offline.
- `app/correlation`: inferencia de causa raiz y recomendaciones.
- `app/database`: persistencia de incidentes en SQLite.
- `app/dashboard`: dashboard Streamlit.
- `app/services`: orquestacion del pipeline.

El dashboard incluye una linea temporal avanzada tipo TradingView mediante Lightweight Charts para visualizar el score de anomalia, severidad y marcadores de incidentes. Lightweight Charts es una tecnologia de TradingView; se mantiene la atribucion visual dentro del componente.

## Instalacion

```bash
pip install -r requirements.txt
```

## Ejecucion por consola

```bash
python run.py --log datasets/samples/sample.log
```

## Dashboard

```bash
streamlit run app/dashboard/streamlit_app.py
```

## Flujo

Logs -> carga -> limpieza -> parser tipo Drain -> features -> Isolation Forest / DBSCAN -> NLP semantico -> correlacion -> alertas -> dashboard.

El prototipo esta preparado para datasets como HDFS, BGL y OpenStack siempre que se entreguen como archivos de texto plano.
=======
# Diagnóstico de Fallas en Machine Learning

Esta aplicación facilita la identificación y corrección de errores en modelos de ML mediante:
- **Limpieza y pre‑procesamiento** de datos (`app/preprocessing/cleaner.py`).
- **Gestión de datos** con repositorios estructurados (`app/database/repositories.py`).
- **Pipeline modular** que orquesta entrenamiento y predicción (`app/services/pipeline_service.py`).
- **Panel de control web** con tema personalizado (`app/dashboard/custom_theme.css`).

Ideal para equipos que buscan mejorar la fiabilidad y el rendimiento de sus modelos de aprendizaje automático.
>>>>>>> d81220f4205b826ceec49151d687edc326f06170
