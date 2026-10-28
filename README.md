# purchase-predict

End-to-end MLOps project built during the MLOps module at CY Tech (ING3, 2025-2026).
The question: given what a visitor did in an e-commerce session, will they buy the
product they put in their cart? The point was less the model than everything around
it: a Kedro pipeline with tests, MLflow tracking and a model registry, a Flask API in
Docker, and Cloud Build pipelines that retrain the model and redeploy the API on Cloud
Run (pre-production) and on a GKE cluster (production).

## What is in the repository

```
pipeline/   Kedro project: loading -> processing -> training -> deployment, tests,
            scripts/build_primary_dataset.py (raw events -> session/product table)
api/        Flask API (POST /predict), Dockerfile, docker-compose.yml, tests and a
            small MLflow store with the registered model so it runs out of the box
deploy/     Cloud Build configs, Kubernetes manifests and the gcloud scripts
docs/       Kedro graph, model figures and screenshots of the real cloud builds
```

![Kedro pipeline](docs/pipeline/kedro-pipeline.png)

## Data and model

The raw file is one day (1 October 2019) of a public e-commerce event log: 1,244,245
rows of `view`, `cart` and `purchase` events with 9 columns (time, product, category,
brand, price, user, session). 97% of the events are views, 190,188 users opened
268,737 sessions and 6% of the sessions contain a purchase.

`scripts/build_primary_dataset.py` turns that log into one row per (session, product)
pair that reached the cart or the purchase stage: 22,971 rows, a `purchased` target and
13 features (product id, brand, price, category and sub-category, views in the session,
views of the product, hour, minute, weekday, session duration, number of previous
sessions, previous views of the product). 78% of those rows are purchases.

I chose LightGBM because it trains in seconds on this table and handles the label
encoded categories without much preparation. `brand`, `category` and `sub_category` are
label-encoded and the encoders are saved next to the model, so the API applies exactly
the same transformation. Hyperopt (TPE) searches the learning rate, number of
iterations, depth, leaves, subsampling and regularisation on F1 with a 4-fold
cross-validation; the Kedro `training` node then refits the best candidate and logs
parameters, F1, the precision-recall curve, the encoders and the model to MLflow. The
`deployment` node registers the model as `purchase_predict` and gives the version the
alias `staging`.

Results on the held-out split (25% of the rows in the notebook study, 30% in the
pipeline), threshold 0.5:

| Model | F1 | Precision | Recall | ROC AUC |
|---|---|---|---|---|
| Notebook model, Hyperopt (5,743 test rows) | 0.876 | 0.804 | 0.962 | 0.765 |
| Best run tracked by the pipeline (6,892 test rows) | 0.873 | 0.813 | 0.943 | 0.763 |
| Registered version 1, `@staging` (1 Hyperopt evaluation, the one the API serves) | 0.850 | 0.820 | 0.883 | 0.725 |

Two honest remarks about these numbers. With 78% positives, predicting "purchase" for
every row already gives F1 0.873, so F1 says almost nothing here; the ROC AUC of about
0.76 and the precision-recall curve are the numbers to look at. And Hyperopt did not
beat the first hand-set LightGBM (F1 0.876 in the notebook as well) by more than a few
tenths of a point. SHAP puts `product_id`, the number of views in the session, the
session duration, `brand` and `price` on top.

![Precision-recall curve](docs/figures/precision-recall-curve.png)
![SHAP summary](docs/figures/shap-summary.png)

## Running it locally

Everything below was run on Windows with Python 3.12 and [uv](https://docs.astral.sh/uv/).

Pipeline (works offline, the primary table is in the repository):

```
cd pipeline
uv sync
uv run pytest                                   # 6 passed, 2 skipped until a model exists
uv run kedro run --params automl_max_evals=1    # add more evaluations when you have time
```

`kedro run` writes the splits and `model.pkl` under `data/`, logs the run to
`pipeline/mlruns` and registers the model with the alias from `ENV` (`staging` by
default). To load the table from GCS instead of the local file, add
`conf/local/parameters_loading.yml` with your project id and bucket (see
`pipeline/README.md`).

API:

```
cd api
cp .env.example .env
uv sync
uv run pytest                                   # 2 passed
uv run python app.py
curl -X POST http://127.0.0.1:5003/predict -H "Content-Type: application/json" --data @sample-payload.json
# [1, 1, 1, 1, 1, 1, 1, 1, 1, 0]
```

The API loads `models:/purchase_predict@staging` from `MLFLOW_SERVER`. `api/mlruns` is a
copy of the store with the registered model; point `MLFLOW_SERVER` at
`../pipeline/mlruns` to serve the model you just trained. `docker compose up --build`
builds the same image Cloud Build builds and serves it on port 8080.

## Cloud deployment

The cloud part needs a GCP project, a bucket with the primary table and the scripts in
`deploy/scripts` (`deploy/README.md` lists the order and the IAM roles). Nothing here
runs without those, so this section describes what ran in April 2026.

- `cloudbuild.pipeline.yaml`: unit tests, `kedro run`, post-training tests, export of
  `data/` and `mlruns/` to `gs://<bucket>/cloud-build-artifacts/<build id>/`.
- `cloudbuild.preprod.yaml`: the same, then a child build (`cloudbuild.api.yaml`) that
  downloads the new store, tests the API, builds the image, pushes it to Artifact
  Registry and redeploys the Cloud Run service.
- `cloudbuild.prod.yaml`: the same, with `cloudbuild.gke.yaml` as the child build: the
  image tag is injected into `deploy/k8s/deployment.yaml` (2 replicas, rolling update
  without surge because the cluster is tiny), applied with `kubectl`, and the build waits
  for the rollout. A NodePort service and a GCE ingress expose the pods.

The parent builds used to clone a separate API repository with a GitHub token from
Secret Manager; since the API now lives in this repository, the child build is simply
submitted from the same workspace. Screenshots of the builds, the registry and the
cluster are in `docs/screenshots`.

![Cloud Build steps of the training pipeline](docs/screenshots/cloud-build-training-steps.png)

## Limitations and what I would do next

- The table only keeps session/product pairs that reached the cart, so the model
  predicts "will this cart item be bought", not "will this visitor buy". Features like
  the session duration and the number of views are computed on the whole session,
  including what happens after the purchase. A fair version would cut each session at
  the cart event and use a time-based split instead of a random one.
- Hyperopt's cross-validation runs on train and test concatenated, so the test set
  leaks into the choice of hyper-parameters. The threshold was never tuned either.
- The deployment node gives the alias to whatever run just finished, without comparing
  it with the current model, and the production pipeline runs with one Hyperopt
  evaluation and `ENV=staging`. Each Cloud Build also starts from an empty MLflow store,
  so the registry never holds more than one version. That is how a one-evaluation model
  (F1 0.850) ended up in production while a better run (F1 0.873) sat in a local store.
  Promotion should be gated on the metrics, with a separate `production` alias and a
  store that outlives the build.
- MLflow is a file store copied around through GCS and baked into the image. Next steps:
  a tracking server with a GCS artifact store, and Cloud Build triggers on push instead
  of manual `gcloud builds submit`.

## Context

MLOps module, CY Tech ING3, 2025-2026. Team: Amine Filali, Hadj Rabearimananana,
Haroun Joudi and Mouad Ouad. The exploratory notebooks and the oral presentation were
team work; I wrote most of the implementation in this repository (Kedro pipeline,
MLflow integration, API, Docker image, Cloud Build pipelines and the GKE deployment).
The course notebooks are not included; the pipeline holds the same processing and
training code.
