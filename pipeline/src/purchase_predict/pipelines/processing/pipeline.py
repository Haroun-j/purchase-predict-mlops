from kedro.pipeline import Node, Pipeline  # noqa

from .nodes import encode_features, split_dataset


def create_pipeline(**kwargs) -> Pipeline:
    return Pipeline(
        [
            Node(
                encode_features,
                "primary",
                dict(features="dataset", transform_pipeline="transform_pipeline"),
            ),
            Node(
                split_dataset,
                ["dataset", "params:test_ratio"],
                dict(
                    X_train="X_train",
                    y_train="y_train",
                    X_test="X_test",
                    y_test="y_test",
                ),
            ),
        ]
    )
