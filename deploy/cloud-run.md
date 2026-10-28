# Deploying the API on Cloud Run by hand

The scripts in `scripts/` do this for you; these are the underlying commands, useful
when something goes wrong.

```bash
PROJECT_ID="<gcp-project-id>"
REGION="europe-west1"
REPOSITORY="purchased-docker"
SERVICE="purchase-predict-api"
SERVICE_ACCOUNT="purchase-predict-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:latest"
```

Build and push the image from the `api/` folder:

```bash
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
docker build -t "${IMAGE}" api
docker push "${IMAGE}"
```

Deploy:

```bash
gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 80 \
  --service-account "${SERVICE_ACCOUNT}" \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --set-env-vars "ENV=staging,MLFLOW_SERVER=file:///app/mlruns,MLFLOW_REGISTRY_NAME=purchase_predict,WEB_CONCURRENCY=1"
```

Notes:

- The container listens on `PORT`, which Cloud Run sets.
- The MLflow store is embedded in the image under `/app/mlruns`. That keeps the
  service self-contained, at the price of rebuilding the image for every new model.
  With a real MLflow tracking server, `MLFLOW_SERVER` would point to it (through a
  VPC connector) and the image would only contain the code.
