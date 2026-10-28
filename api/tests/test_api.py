from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app


def test_home():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.data == b"OK !"


def test_predict():
    client = app.test_client()
    dataset = pd.read_json(
        Path(__file__).resolve().parents[1] / "sample-payload.json"
    )

    response = client.post(
        "/predict", json=dataset.to_dict(orient="records")
    )
    assert response.status_code == 200

    predictions = response.get_json()
    assert len(predictions) == 10
    assert set(predictions) <= {0, 1}
