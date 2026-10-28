#!/usr/bin/env bash
# First deployment of the API on Cloud Run: creates the Artifact Registry repository
# and the runtime service account, builds the image from api/ (with the model store
# shipped in the repository) and deploys it. Later deployments go through
# deploy/cloudbuild.api.yaml. Usage: deploy/scripts/bootstrap-cloud-run.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
REGION="${REGION:-europe-west1}"
REPOSITORY="${REPOSITORY:-purchased-docker}"
SERVICE="${SERVICE:-purchase-predict-api}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-purchase-predict-api-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:latest"

echo "PROJECT_ID=${PROJECT_ID}"
echo "IMAGE=${IMAGE}"

gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  iam.googleapis.com \
  run.googleapis.com

if ! gcloud artifacts repositories describe "${REPOSITORY}" --location="${REGION}" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${REPOSITORY}" \
    --repository-format=docker \
    --location="${REGION}" \
    --description="Docker images of the purchase-predict API"
fi

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="purchase-predict API runtime"
fi

gcloud builds submit api --tag "${IMAGE}"

gcloud run deploy "${SERVICE}" \
  --image "${IMAGE}" \
  --region "${REGION}" \
  --platform managed \
  --allow-unauthenticated \
  --port 80 \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --service-account "${SERVICE_ACCOUNT}" \
  --set-env-vars "ENV=staging,MLFLOW_SERVER=file:///app/mlruns,MLFLOW_REGISTRY_NAME=purchase_predict,WEB_CONCURRENCY=1"

CLOUD_RUN_URL="$(gcloud run services describe "${SERVICE}" --region "${REGION}" --format='value(status.url)')"
echo "CLOUD_RUN_URL=${CLOUD_RUN_URL}"

echo "GET /"
curl -sS "${CLOUD_RUN_URL}/"
echo

echo "POST /predict"
curl -sS -X POST "${CLOUD_RUN_URL}/predict" \
  -H "Content-Type: application/json" \
  --data-binary @api/sample-payload.json
echo
