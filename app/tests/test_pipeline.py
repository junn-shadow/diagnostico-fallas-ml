from app.config.paths import SAMPLES_DIR
from app.services.pipeline_service import PipelineService


def test_pipeline_runs_without_persistence():
    result = PipelineService().run(SAMPLES_DIR / "sample.log", persist=False)

    assert len(result.logs) > 0
    assert "is_anomaly" in result.logs.columns
    assert "root_cause" in result.logs.columns
    assert result.saved_incidents == 0
    assert result.log_source == "sample.log"
    assert result.run_id.startswith("run_")
    assert len(result.stages) > 0
    assert "duration_s" in result.stages[0]
