from app.config.paths import SAMPLES_DIR
from app.services.pipeline_service import PipelineService


def test_pipeline_runs_without_persistence():
    result = PipelineService().run(SAMPLES_DIR / "sample.log", persist=False)

    assert len(result.logs) > 0
    assert "is_anomaly" in result.logs.columns
    assert "root_cause" in result.logs.columns
    assert result.saved_incidents == 0
