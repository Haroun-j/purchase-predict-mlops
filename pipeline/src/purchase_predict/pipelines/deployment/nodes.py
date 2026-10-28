import os
from pathlib import Path

import mlflow
from mlflow.exceptions import MlflowException
from mlflow.tracking import MlflowClient


def get_tracking_uri() -> str:
    """Return the configured MLflow tracking URI, or a local file store."""
    return os.getenv("MLFLOW_SERVER", Path("mlruns").resolve().as_uri())


def push_to_model_registry(registry_name: str, model_uri: str) -> str:
    """
    Pushes a tracked model version to the specified registry.
    """
    if not model_uri:
        raise ValueError("model_uri is required to push a model to the registry.")

    mlflow.set_tracking_uri(get_tracking_uri())
    client = MlflowClient()
    try:
        client.get_registered_model(registry_name)
    except MlflowException:
        client.create_registered_model(registry_name)

    result = client.create_model_version(name=registry_name, source=model_uri)
    return result.version


def stage_model(registry_name: str, version: str) -> None:
    """
    Assigns an environment alias to a model version in the registry.
    """
    env = os.getenv("ENV", "staging")
    mlflow.set_tracking_uri(get_tracking_uri())
    client = MlflowClient()
    client.set_registered_model_alias(
        name=registry_name,
        alias=env,
        version=version,
    )
