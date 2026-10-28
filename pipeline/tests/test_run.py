from pathlib import Path

from kedro.framework.startup import bootstrap_project

from purchase_predict.pipeline_registry import register_pipelines

PROCESSING_NODE_COUNT = 2
TRAINING_NODE_COUNT = 1
LOADING_NODE_COUNT = 1
DEPLOYMENT_NODE_COUNT = 2


class TestKedroRun:
    def test_register_pipelines(self):
        bootstrap_project(Path.cwd())

        pipelines = register_pipelines()

        assert "processing" in pipelines
        assert "training" in pipelines
        assert "loading" in pipelines
        assert "deployment" in pipelines
        assert "__default__" in pipelines
        assert len(pipelines["processing"].nodes) == PROCESSING_NODE_COUNT
        assert len(pipelines["training"].nodes) == TRAINING_NODE_COUNT
        assert len(pipelines["loading"].nodes) == LOADING_NODE_COUNT
        assert len(pipelines["deployment"].nodes) == DEPLOYMENT_NODE_COUNT
