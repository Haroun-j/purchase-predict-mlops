import os
from pathlib import Path

import pandas as pd
import pytest
from kedro.io import DataCatalog, MemoryDataset

from purchase_predict.pipelines.loading.nodes import load_csv_from_bucket
from purchase_predict.pipelines.processing.nodes import encode_features


@pytest.fixture(scope="module")
def dataset_not_encoded() -> pd.DataFrame:
    data_path = Path("data/03_primary/primary.csv")
    if data_path.exists():
        return pd.read_csv(data_path)

    project_id = os.getenv("GCP_PROJECT_ID")
    primary_folder = os.getenv("GCS_PRIMARY_FOLDER")
    if not project_id or not primary_folder:
        pytest.skip("data/03_primary/primary.csv is missing and GCP_PROJECT_ID / GCS_PRIMARY_FOLDER are not set")
    return load_csv_from_bucket(project_id, primary_folder)


@pytest.fixture(scope="module")
def test_ratio() -> float:
    return 0.3


@pytest.fixture(scope="module")
def dataset_encoded(dataset_not_encoded: pd.DataFrame) -> pd.DataFrame:
    encoded = encode_features(dataset_not_encoded)
    features = encoded["features"]
    assert isinstance(features, pd.DataFrame)
    return features


@pytest.fixture(scope="module")
def catalog_test(dataset_not_encoded: pd.DataFrame, test_ratio: float) -> DataCatalog:
    return DataCatalog(
        {
            "primary": MemoryDataset(dataset_not_encoded),
            "params:test_ratio": MemoryDataset(test_ratio),
            "dataset": MemoryDataset(),
            "transform_pipeline": MemoryDataset(),
            "X_train": MemoryDataset(),
            "y_train": MemoryDataset(),
            "X_test": MemoryDataset(),
            "y_test": MemoryDataset(),
        }
    )
