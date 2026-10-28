from kedro.pipeline import Node, Pipeline  # noqa

from .nodes import push_to_model_registry, stage_model


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                push_to_model_registry,
                ["params:mlflow_model_registry", "mlflow_model_uri"],
                "mlflow_model_version",
            ),
            Node(
                stage_model,
                ["params:mlflow_model_registry", "mlflow_model_version"],
                None,
            ),
        ]
    )
