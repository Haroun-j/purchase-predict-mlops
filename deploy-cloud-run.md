# Cloud Run deployment

This file summarizes the manual deployment commands for the API image.

Replace the placeholders before running the commands:

```bash
PROJECT_ID="<gcp-project-id>"
REGION="europe-west1"
REPOSITORY="purchased-docker"
SERVICE="purchase-predict-api"
SERVICE_ACCOUNT="purchase-predict-api-sa@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:latest"
MLFLOW_SERVER="file:///app/mlruns"
```

Build and push the image:

```bash
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
docker build -t "${IMAGE}" .
docker push "${IMAGE}"
```

Deploy to Cloud Run:

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
  --set-env-vars "ENV=staging,MLFLOW_SERVER=${MLFLOW_SERVER},MLFLOW_REGISTRY_NAME=purchase_predict,WEB_CONCURRENCY=1"
```

Important notes:

- The container listens on the `PORT` environment variable, which is required by Cloud Run.
- In local Docker Compose, MLflow is mounted as `file:///mlruns`.
- In this demo deployment, MLflow metadata and artifacts are embedded in the image under `/app/mlruns`.
- In a production deployment, `MLFLOW_SERVER` should point to a reachable MLflow tracking server, usually through a VPC connector.
