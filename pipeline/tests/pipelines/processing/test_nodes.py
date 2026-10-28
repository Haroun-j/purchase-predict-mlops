import numpy as np
import pandas as pd

from purchase_predict.pipelines.processing.nodes import split_dataset

BALANCE_THRESHOLD = 0.1
MIN_SAMPLES = 5_000


def test_encode_features(dataset_encoded: pd.DataFrame):
    assert "user_id" not in dataset_encoded.columns
    assert "user_session" not in dataset_encoded.columns
    assert dataset_encoded["purchased"].isin([0, 1]).all()

    for column in dataset_encoded.columns:
        assert pd.api.types.is_numeric_dtype(dataset_encoded.dtypes[column])

    assert dataset_encoded.shape[0] > MIN_SAMPLES
    assert (dataset_encoded["purchased"].value_counts(normalize=True) > BALANCE_THRESHOLD).all()


def test_split_dataset(dataset_encoded: pd.DataFrame, test_ratio: float):
    split = split_dataset(dataset_encoded, test_ratio)
    X_train = split["X_train"]
    y_train = split["y_train"]
    X_test = split["X_test"]
    y_test = split["y_test"]

    assert X_train.shape[0] == y_train.shape[0]
    assert X_test.shape[0] == y_test.shape[0]
    assert X_train.shape[0] + X_test.shape[0] == dataset_encoded.shape[0]
    assert np.ceil(dataset_encoded.shape[0] * test_ratio) == X_test.shape[0]
    assert "purchased" not in X_train.columns
    assert "purchased" in y_train.columns
