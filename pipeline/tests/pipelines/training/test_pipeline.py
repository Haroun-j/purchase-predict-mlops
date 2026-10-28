import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

PRICE_INVARIANCE_THRESHOLD = 0.10


@pytest.fixture(scope="module")
def model_bundle() -> dict[str, Any]:
    model_path = Path("data/06_models/model.pkl")
    if not model_path.exists():
        pytest.skip("no trained model in data/06_models, run `kedro run` first")
    with model_path.open("rb") as model_file:
        return pickle.load(model_file)


@pytest.fixture(scope="module")
def X_test() -> pd.DataFrame:
    data_path = Path("data/05_model_input/X_test.csv")
    if not data_path.exists():
        pytest.skip("no test split in data/05_model_input, run `kedro run` first")
    return pd.read_csv(data_path)


def test_model_predicts_valid_probabilities(model_bundle: dict[str, Any], X_test: pd.DataFrame):
    model = model_bundle["model"]
    probabilities = model.predict_proba(X_test.head(20))

    assert probabilities.shape == (20, 2)
    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)
    assert np.allclose(probabilities.sum(axis=1), 1)


def test_price_invariance_is_bounded(model_bundle: dict[str, Any], X_test: pd.DataFrame):
    model = model_bundle["model"]
    sample = X_test[X_test["price"] > 1].iloc[[0]].copy()

    sample_plus = sample.copy()
    sample_minus = sample.copy()
    sample_plus["price"] = sample_plus["price"] + 1
    sample_minus["price"] = sample_minus["price"] - 1

    delta = abs(model.predict_proba(sample_plus)[0, 1] - model.predict_proba(sample_minus)[0, 1])

    assert delta < PRICE_INVARIANCE_THRESHOLD
