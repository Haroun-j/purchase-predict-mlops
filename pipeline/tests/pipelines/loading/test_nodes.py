import pandas as pd

from purchase_predict.pipelines.loading.nodes import load_csv_from_bucket


def test_load_csv_from_bucket(project_id: str, primary_folder: str, primary_dataframe: pd.DataFrame):
    df = load_csv_from_bucket(project_id, primary_folder)

    assert isinstance(df, pd.DataFrame)
    assert df.shape == primary_dataframe.shape
    assert list(df.columns) == list(primary_dataframe.columns)
    assert "purchased" in df.columns
