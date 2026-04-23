import os
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.tracking import MlflowClient

ENV = os.environ["ENV"]
MLFLOW_REGISTRY_NAME = os.environ["MLFLOW_REGISTRY_NAME"]


def _tracking_uri() -> str:
    uri = os.getenv("MLFLOW_SERVER")
    if uri is None:
        raise RuntimeError("MLFLOW_SERVER must be defined.")
    if "://" in uri:
        return uri
    return (Path(__file__).resolve().parents[1] / uri).resolve().as_uri()


def _run_id_from_source(source: str) -> str:
    match = re.match(r"runs:/([^/]+)/", source)
    if not match:
        raise RuntimeError("Unable to recover run id from model source.")
    return match.group(1)


def _local_tracking_root() -> Path | None:
    uri = mlflow.get_tracking_uri()
    parsed = urlparse(uri)
    if parsed.scheme == "file":
        return Path(unquote(parsed.path))
    if not parsed.scheme:
        return Path(uri)
    return None


def _find_local_artifact(run_id: str, artifact_path: str) -> Path | None:
    tracking_root = _local_tracking_root()
    if tracking_root is None or not tracking_root.exists():
        return None

    for candidate in tracking_root.glob(f"*/{run_id}/artifacts/{artifact_path}"):
        if candidate.exists():
            return candidate
    return None


mlflow.set_tracking_uri(_tracking_uri())


class Model:
    def __init__(self):
        self.model = None
        self.transform_pipeline = None
        self.load_model()

    def load_model(self):
        client = MlflowClient()
        alias = ENV
        model_version = client.get_model_version_by_alias(
            MLFLOW_REGISTRY_NAME,
            alias,
        )
        run_id = model_version.run_id or _run_id_from_source(model_version.source)

        try:
            pipeline_path = mlflow.artifacts.download_artifacts(
                artifact_uri=f"runs:/{run_id}/transform_pipeline.pkl"
            )
        except OSError:
            local_pipeline_path = _find_local_artifact(
                run_id,
                "transform_pipeline.pkl",
            )
            if local_pipeline_path is None:
                raise
            pipeline_path = str(local_pipeline_path)

        try:
            self.model = mlflow.sklearn.load_model(
                f"models:/{MLFLOW_REGISTRY_NAME}@{alias}"
            )
        except OSError:
            local_model_path = _find_local_artifact(run_id, "model")
            if local_model_path is None:
                raise
            self.model = mlflow.sklearn.load_model(str(local_model_path))

        self.transform_pipeline = joblib.load(pipeline_path)

    def predict(self, X: pd.DataFrame):
        if self.model is None:
            return None

        X = X.copy()
        if self.transform_pipeline:
            if isinstance(self.transform_pipeline, dict):
                encoders = self.transform_pipeline.items()
            else:
                encoders = self.transform_pipeline

            for name, encoder in encoders:
                X[name] = X[name].astype("string").fillna("unknown")
                known_values = set(encoder.classes_)
                if "unknown" in known_values:
                    X[name] = X[name].where(X[name].isin(known_values), "unknown")
                X[name] = encoder.transform(X[name])

        for col in ["user_id", "user_session", "purchased"]:
            if col in X:
                X = X.drop(col, axis=1)
        return self.model.predict(X)
