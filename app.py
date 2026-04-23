import os
from io import StringIO

import pandas as pd
from flask import Flask, jsonify, request

from src.model import Model

app = Flask(__name__)
model = Model()


@app.route("/", methods=["GET"])
def home():
    return "OK !", 200


@app.route("/predict", methods=["POST"])
def predict():
    body = request.get_json()
    if body is None:
        return jsonify({"error": "Missing JSON body."}), 400

    if isinstance(body, str):
        df = pd.read_json(StringIO(body))
    else:
        df = pd.DataFrame(body)

    results = [int(x) for x in model.predict(df).flatten()]
    return jsonify(results), 200


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", os.getenv("API_PORT", "5003"))))
