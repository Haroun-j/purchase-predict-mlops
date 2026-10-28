from kedro.io import DataCatalog
from kedro.runner import SequentialRunner

from purchase_predict.pipelines.processing.pipeline import create_pipeline


def test_pipeline(catalog_test: DataCatalog):
    runner = SequentialRunner()
    pipeline = create_pipeline()

    runner.run(pipeline, catalog_test)
    X_train = catalog_test.load("X_train")
    y_train = catalog_test.load("y_train")
    X_test = catalog_test.load("X_test")
    y_test = catalog_test.load("y_test")
    primary = catalog_test.load("primary")

    assert X_train.shape[0] == y_train.shape[0]
    assert X_test.shape[0] == y_test.shape[0]
    assert X_train.shape[0] + X_test.shape[0] == primary.shape[0]
