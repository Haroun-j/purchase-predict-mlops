#!/usr/bin/env bash
# Rebuild the API from the model stored in the bucket and roll it out on GKE, without
# retraining. Usage: BUCKET=my-bucket deploy/scripts/deploy-api-gke.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
PROJECT_NUMBER="${PROJECT_NUMBER:-$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')}"
BUCKET="${BUCKET:?set BUCKET to the GCS bucket that holds the exported mlruns}"
MLRUNS_GCS_PATH="${MLRUNS_GCS_PATH:-gs://${BUCKET}/prod/latest/mlruns}"
GKE_CLUSTER="${GKE_CLUSTER:-purchase-predict-api}"
GKE_ZONE="${GKE_ZONE:-europe-west1-b}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "GKE_CLUSTER=${GKE_CLUSTER} (${GKE_ZONE})"
echo "MLRUNS_GCS_PATH=${MLRUNS_GCS_PATH}"
echo "IMAGE_TAG=${IMAGE_TAG}"

gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

# Cloud Build applies the manifests; the nodes pull the image from Artifact Registry.
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/container.developer" >/dev/null

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader" >/dev/null

CLUSTER_STATUS="$(gcloud container clusters describe "${GKE_CLUSTER}" --zone "${GKE_ZONE}" --format='value(status)')"
echo "CLUSTER_STATUS=${CLUSTER_STATUS}"

if [ "${CLUSTER_STATUS}" != "RUNNING" ]; then
  echo "The GKE cluster must be RUNNING before launching Cloud Build (current status: ${CLUSTER_STATUS})."
  exit 1
fi

gcloud builds submit . \
  --config deploy/cloudbuild.gke.yaml \
  --substitutions="SHORT_SHA=${IMAGE_TAG},_GKE_CLUSTER=${GKE_CLUSTER},_GKE_ZONE=${GKE_ZONE},_MLRUNS_GCS_PATH=${MLRUNS_GCS_PATH}"
