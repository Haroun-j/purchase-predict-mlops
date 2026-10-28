import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


def encode_features(
    dataset: pd.DataFrame,
) -> dict[str, pd.DataFrame | dict[str, LabelEncoder]]:
    """
    Encode features of data file.
    """
    features = dataset.drop(["user_id", "user_session"], axis=1).copy()

    transform_pipeline: dict[str, LabelEncoder] = {}
    for label in ["category", "sub_category", "brand"]:
        features[label] = features[label].astype("string").fillna("unknown")
        encoder = LabelEncoder()
        features[label] = encoder.fit_transform(features[label])
        transform_pipeline[label] = encoder

    features["weekday"] = features["weekday"].astype(int)
    return dict(features=features, transform_pipeline=transform_pipeline)


def split_dataset(dataset: pd.DataFrame, test_ratio: float) -> dict[str, pd.DataFrame]:
    """
    Splits dataset into a training set and a test set.
    """
    X = dataset.drop("purchased", axis=1)
    y = dataset[["purchased"]]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_ratio,
        random_state=40,
    )

    return dict(X_train=X_train, y_train=y_train, X_test=X_test, y_test=y_test)
