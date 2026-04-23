#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project)"
REGION="${REGION:-europe-west1}"
REPOSITORY="${REPOSITORY:-purchased-docker}"
SERVICE="${SERVICE:-purchase-predict-api}"
SERVICE_ACCOUNT_NAME="${SERVICE_ACCOUNT_NAME:-purchase-predict-api-sa}"
SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:latest"

echo "PROJECT_ID=${PROJECT_ID}"
echo "REGION=${REGION}"
echo "REPOSITORY=${REPOSITORY}"
echo "SERVICE=${SERVICE}"
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
    --description="Docker images for purchase predict API"
fi

if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" >/dev/null 2>&1; then
  gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
    --display-name="Purchase Predict API Cloud Run"
fi

gcloud builds submit . --tag "${IMAGE}"

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
  --data-binary @sample-payload.json
echo
