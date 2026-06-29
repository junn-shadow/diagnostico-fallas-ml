from app.services.pipeline_service import PipelineService


def main(log_path: str | None = None):
    result = PipelineService().run(log_path)
    print("Diagnostico automatico completado")
    print(f"Registros analizados: {len(result.logs)}")
    print(f"Anomalias detectadas: {result.anomaly_count}")
    print(f"Backend semantico: {result.semantic_backend}")
    print(f"Incidentes guardados: {result.saved_incidents}")
    if result.persistence_error:
        print(f"Persistencia SQLite no disponible: {result.persistence_error}")
    print(
        result.logs[
            ["line_id", "level", "is_anomaly", "root_cause", "recommendation"]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
