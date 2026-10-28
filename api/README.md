# purchase-predict API

Flask service that loads the `purchase_predict` model from an MLflow registry and
answers `POST /predict`. The alias it loads is the value of `ENV` (`staging` by
default), so the same image serves whatever version the deployment pipeline promoted.
The README at the root of the repository describes the whole project; this file only
lists the commands for this folder.

```
cp .env.example .env
uv sync
uv run pytest
uv run python app.py          # http://127.0.0.1:5003
```

```
curl -X POST http://127.0.0.1:5003/predict \
  -H "Content-Type: application/json" \
  --data @sample-payload.json
# [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
```

`mlruns/` is a small MLflow store with the registered model (version 1, alias
`staging`) so the API runs without the training pipeline. To serve a model you just
trained, point `MLFLOW_SERVER` at `../pipeline/mlruns` instead.

With Docker: `docker compose up --build`, then the API answers on
http://127.0.0.1:8080. The image bakes the store into `/app/mlruns`; on Cloud Build the
store is replaced by the one exported by the training build (see `deploy/`).
