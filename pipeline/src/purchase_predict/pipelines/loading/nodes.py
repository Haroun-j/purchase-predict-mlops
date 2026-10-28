from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
from google.cloud import storage


def _read_csv_files(files: list[Path]) -> pd.DataFrame:
    if not files:
        raise FileNotFoundError("No CSV file found for loading pipeline.")

    dataframes = [pd.read_csv(file, index_col=None, sep=",") for file in files]
    return pd.concat(dataframes, axis=0, ignore_index=True)


def _load_local_csv(bucket_path: str) -> pd.DataFrame:
    path = Path(bucket_path)

    if path.is_file():
        return pd.read_csv(path, index_col=None, sep=",")

    files = sorted(path.glob("*.csv"))
    if not files:
        files = sorted(path.rglob("*.csv"))
    return _read_csv_files(files)


def load_csv_from_bucket(project: str, bucket_path: str) -> pd.DataFrame:
    """
    Loads multiple CSV files from bucket or from a local test path.
    """
    if Path(bucket_path).exists():
        return _load_local_csv(bucket_path)

    storage_client = storage.Client(project=project)
    bucket_name, _, prefix = bucket_path.partition("/")

    with TemporaryDirectory() as tmp_dir:
        files = []
        for index, blob in enumerate(storage_client.list_blobs(bucket_name, prefix=prefix)):
            if blob.name.endswith(".csv"):
                filename = Path(tmp_dir) / f"part-{index}.csv"
                blob.download_to_filename(filename)
                files.append(filename)

        return _read_csv_files(files)
