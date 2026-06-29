import sys
import os

sys.path.append("e:/diagnostico-fallas-ml")
from app.services.pipeline_service import PipelineService
from app.config.paths import SAMPLES_DIR

if __name__ == "__main__":
    sample_path = SAMPLES_DIR / "sample.log"
    result = PipelineService().run(sample_path)
    print("Profile:", result.profile)
    print("Stages:")
    for stage in result.stages:
        print(stage)
    print("Semantic backend:", result.semantic_backend)
    print("Statistical backend:", result.statistical_backend)
