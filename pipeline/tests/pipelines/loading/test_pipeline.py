import pandas as pd
from kedro.io import DataCatalog
from kedro.runner import SequentialRunner

from purchase_predict.pipelines.loading.pipeline import create_pipeline


def test_pipeline(catalog_test: DataCatalog, primary_dataframe: pd.DataFrame):
    runner = SequentialRunner()
    pipeline = create_pipeline()

    runner.run(pipeline, catalog_test)
    df = catalog_test.load("primary")

    assert isinstance(df, pd.DataFrame)
    assert df.shape == primary_dataframe.shape
    assert list(df.columns) == list(primary_dataframe.columns)
    assert "purchased" in df.columns
