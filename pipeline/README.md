# Training pipeline

Kedro project that turns the session/product table into a LightGBM model, logs the
run to MLflow and gives the registered version an alias. The README at the root of
the repository explains the whole project; this file only lists the commands.

```
uv sync
uv run kedro run                                   # loading -> processing -> training -> deployment
uv run kedro run --pipeline training --params automl_max_evals=1
uv run pytest
uv run ruff check src tests
uv run kedro viz run
```

`conf/base` points the loading pipeline at `data/03_primary/primary.csv`, which is in
the repository, so `kedro run` works offline. To read the table from GCS instead,
create `conf/local/parameters_loading.yml` (the folder is ignored by git):

```
gcp_project_id: my-gcp-project
gcs_primary_folder: my-bucket/data/03_primary
```

and authenticate with `gcloud auth application-default login` or
`GOOGLE_APPLICATION_CREDENTIALS`.

The primary table is rebuilt from the raw event log with
`uv run python scripts/build_primary_dataset.py data/01_raw/events.csv`.
MLflow writes to `./mlruns` unless `MLFLOW_SERVER` says otherwise; the alias given
to the registered model is the value of `ENV` (default `staging`).
