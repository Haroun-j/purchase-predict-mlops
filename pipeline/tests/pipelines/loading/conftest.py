import os
from pathlib import Path

import pandas as pd
import pytest
from kedro.io import DataCatalog, MemoryDataset

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def primary_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "product_id": 1004856,
                "brand": "samsung",
                "price": 130.76,
                "user_id": 543272936,
                "user_session": "session-1",
                "purchased": 1,
                "num_views_session": 3,
                "num_views_product": 3,
                "category": "electronics",
                "sub_category": "smartphone",
                "hour": 0,
                "minute": 2,
                "weekday": 1,
                "duration": 76,
                "num_prev_sessions": 0,
                "num_prev_product_views": 0,
            },
            {
                "product_id": 1002532,
                "brand": "apple",
                "price": 642.69,
                "user_id": 551377651,
                "user_session": "session-2",
                "purchased": 0,
                "num_views_session": 9,
                "num_views_product": 2,
                "category": "electronics",
                "sub_category": "smartphone",
                "hour": 0,
                "minute": 4,
                "weekday": 1,
                "duration": 547,
                "num_prev_sessions": 0,
                "num_prev_product_views": 0,
            },
        ]
    )


@pytest.fixture(scope="module")
def project_id() -> str:
    return os.getenv("GCP_PROJECT_ID", "local")


@pytest.fixture(scope="module")
def primary_folder() -> str:
    # By default the loader reads the two-row CSV in tests/pipelines/loading/fixtures.
    # Set GCS_TEST_FOLDER to "<bucket>/data-test.csv" (a folder with the same rows) to
    # run the tests against GCS, which is what the Cloud Build pipeline does.
    return os.getenv("GCS_TEST_FOLDER", str(FIXTURES_DIR))


@pytest.fixture(scope="module")
def catalog_test(project_id: str, primary_folder: str) -> DataCatalog:
    return DataCatalog(
        {
            "params:gcp_project_id": MemoryDataset(project_id),
            "params:gcs_primary_folder": MemoryDataset(primary_folder),
            "primary": MemoryDataset(),
        }
    )
