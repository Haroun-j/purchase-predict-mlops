import os
import warnings
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypedDict

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from hyperopt import fmin, hp, space_eval, tpe
from lightgbm.sklearn import LGBMClassifier
from mlflow.models import infer_signature
from sklearn.base import BaseEstimator, clone
from sklearn.metrics import PrecisionRecallDisplay, f1_score, precision_recall_curve
from sklearn.model_selection import RepeatedKFold

warnings.filterwarnings("ignore")


class ModelSpec(TypedDict, total=True):
    name: str
    model_class: Callable[..., BaseEstimator]
    params: dict[str, Any]
    override_schemas: dict[str, type]


MODELS: list[ModelSpec] = [
    {
        "name": "LightGBM",
        "model_class": LGBMClassifier,
        "params": {
            "objective": "binary",
            "verbose": -1,
            "learning_rate": hp.uniform("learning_rate", 0.001, 1),
            "num_iterations": hp.quniform("num_iterations", 100, 1000, 20),
            "max_depth": hp.quniform("max_depth", 4, 12, 6),
            "num_leaves": hp.quniform("num_leaves", 8, 128, 10),
            "colsample_bytree": hp.uniform("colsample_bytree", 0.3, 1),
            "subsample": hp.uniform("subsample", 0.5, 1),
            "min_child_samples": hp.quniform("min_child_samples", 1, 20, 1),
            "reg_alpha": hp.choice("reg_alpha", [0, 1e-1, 1, 2, 5, 10]),
            "reg_lambda": hp.choice("reg_lambda", [0, 1e-1, 1, 2, 5, 10]),
        },
        "override_schemas": {
            "num_leaves": int,
            "min_child_samples": int,
            "max_depth": int,
            "num_iterations": int,
        },
    }
]

REPORTING_DIR = Path("data/08_reporting")
TRANSFORM_PIPELINE_PATH = Path("data/04_feature/transform_pipeline.pkl")


def get_model_config(instance: BaseEstimator) -> ModelSpec:
    """Returns the configuration dictionary for the given model instance."""
    for model_spec in MODELS:
        model_cls = model_spec["model_class"]
        if isinstance(model_cls, type) and isinstance(instance, model_cls):
            return model_spec
    raise ValueError(f"Unsupported model: {type(instance)}")


def train_model(
    instance: BaseEstimator,
    training_set: tuple[pd.DataFrame, pd.DataFrame | pd.Series],
    params: dict[str, Any] | None = None,
) -> Any:
    """
    Trains a new instance of model with supplied training set and hyper-parameters.
    """
    model_conf = get_model_config(instance)
    params = params.copy() if params else {}

    override_schemas = model_conf.get("override_schemas", {})
    for param in set(override_schemas).intersection(params):
        params[param] = override_schemas[param](params[param])

    X, y = training_set
    model = clone(instance)
    model.set_params(**params)
    model.fit(X, np.ravel(y))
    return model


def optimize_hyp(
    instance: BaseEstimator,
    dataset: tuple[pd.DataFrame, pd.DataFrame | pd.Series],
    search_space: dict[str, Any],
    metric: Callable[[Any, Any], float],
    max_evals: int = 40,
) -> dict[str, Any]:
    """
    Trains model's instances on hyper-parameters search space and returns most accurate
    hyper-parameters based on eval set.
    """
    X, y = dataset
    y_series = pd.Series(np.ravel(y), index=X.index)

    def objective(params: dict[str, Any]) -> float:
        rep_kfold = RepeatedKFold(n_splits=4, n_repeats=1, random_state=40)
        scores_test = []

        for train_index, test_index in rep_kfold.split(X):
            X_fold_train = X.iloc[train_index, :]
            y_fold_train = y_series.iloc[train_index]
            X_fold_test = X.iloc[test_index, :]
            y_fold_test = y_series.iloc[test_index]

            model = train_model(
                instance=instance,
                training_set=(X_fold_train, y_fold_train),
                params=params,
            )
            scores_test.append(metric(y_fold_test, model.predict(X_fold_test)))

        return float(np.mean(scores_test))

    best = fmin(
        fn=objective,
        space=search_space,
        algo=tpe.suggest,
        max_evals=max_evals,
        rstate=np.random.default_rng(40),
    )
    return space_eval(search_space, best)


def get_tracking_uri() -> str:
    """Return the configured MLflow tracking URI, or a local file store."""
    return os.getenv("MLFLOW_SERVER", Path("mlruns").resolve().as_uri())


def get_experiment_id(experiment_id: int = -1, experiment_name: str = "purchase_predict") -> str:
    """Return an MLflow experiment id, creating the default experiment when needed."""
    if experiment_id >= 0:
        experiment = mlflow.get_experiment(str(experiment_id))
        if experiment is not None:
            return experiment.experiment_id

    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is not None:
        return experiment.experiment_id

    return mlflow.create_experiment(experiment_name)


def save_pr_curve(X: pd.DataFrame, y: pd.DataFrame, model: Any) -> Path:
    """Save a Precision-Recall curve artifact for MLflow."""
    REPORTING_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTING_DIR / "pr_curve.png"
    plt.figure(figsize=(16, 11))
    precision, recall, _ = precision_recall_curve(
        np.ravel(y),
        model.predict_proba(X)[:, 1],
        pos_label=1,
    )
    PrecisionRecallDisplay(precision=precision, recall=recall).plot(ax=plt.gca())
    plt.title("PR Curve", fontsize=16)
    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1, 0))
    plt.gca().yaxis.set_major_formatter(mtick.PercentFormatter(1, 0))
    plt.savefig(output_path)
    plt.close()
    return output_path


def log_model_to_mlflow(
    best_model: dict[str, Any],
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
) -> str:
    """Log the selected model, metrics, parameters and artifacts to MLflow."""
    model = best_model["model"]
    mlflow.log_metric("f1", best_model["score"])
    mlflow.log_params(best_model["params"])
    save_pr_curve(X_test, y_test, model)
    mlflow.log_artifacts(str(REPORTING_DIR), artifact_path="plots")

    if TRANSFORM_PIPELINE_PATH.exists():
        mlflow.log_artifact(str(TRANSFORM_PIPELINE_PATH))

    signature = infer_signature(X_train, model.predict(X_train))
    input_example = X_test.iloc[0:1].copy()
    model_info = mlflow.sklearn.log_model(
        model,
        artifact_path="model",
        signature=signature,
        input_example=input_example,
    )
    return model_info.model_uri


def auto_ml(  # noqa: PLR0913
    X_train: pd.DataFrame,
    y_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_test: pd.DataFrame,
    max_evals: int = 40,
    log_to_mlflow: bool = False,
    experiment_id: int = -1,
) -> dict[str, dict[str, Any] | str]:
    """
    Runs training of multiple model instances and select the most accurated based on objective function.
    """
    X = pd.concat((X_train, X_test))
    y = pd.concat((y_train, y_test))

    opt_models = []
    for model_spec in MODELS:
        instance = model_spec["model_class"]()
        optimum_params = optimize_hyp(
            instance,
            dataset=(X, y),
            search_space=model_spec["params"],
            metric=lambda x, y_pred: -f1_score(x, y_pred),
            max_evals=max_evals,
        )
        model: Any = train_model(
            instance,
            training_set=(X_train, y_train),
            params=optimum_params,
        )
        opt_models.append(
            {
                "model": model,
                "name": model_spec["name"],
                "params": optimum_params,
                "score": f1_score(np.ravel(y_test), model.predict(X_test)),
            }
        )

    best_model = max(opt_models, key=lambda x: x["score"])
    run_id = ""
    model_uri = ""
    if log_to_mlflow:
        mlflow.set_tracking_uri(get_tracking_uri())
        mlflow_experiment_id = get_experiment_id(experiment_id)
        with mlflow.start_run(experiment_id=mlflow_experiment_id) as run:
            run_id = run.info.run_id
            model_uri = log_model_to_mlflow(best_model, X_train, X_test, y_test)

    return {
        "model": best_model,
        "mlflow_run_id": run_id,
        "mlflow_model_uri": model_uri,
    }
