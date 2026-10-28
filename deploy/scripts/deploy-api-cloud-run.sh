#!/usr/bin/env bash
# Rebuild the API from the model stored in the bucket and redeploy it on Cloud Run,
# without retraining. Usage: BUCKET=my-bucket deploy/scripts/deploy-api-cloud-run.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
BUCKET="${BUCKET:?set BUCKET to the GCS bucket that holds the exported mlruns}"
MLRUNS_GCS_PATH="${MLRUNS_GCS_PATH:-gs://${BUCKET}/preprod/latest/mlruns}"
REGION="${REGION:-europe-west1}"
REPOSITORY="${REPOSITORY:-purchased-docker}"
SERVICE="${SERVICE:-purchase-predict-api}"
ENV_NAME="${ENV_NAME:-staging}"
IMAGE_TAG="${IMAGE_TAG:-manual-$(date +%Y%m%d%H%M%S)}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "MLRUNS_GCS_PATH=${MLRUNS_GCS_PATH}"
echo "IMAGE=${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE}:${IMAGE_TAG}"

gcloud builds submit . \
  --config deploy/cloudbuild.api.yaml \
  --substitutions="_ENV=${ENV_NAME},_IMAGE_TAG=${IMAGE_TAG},_MLRUNS_GCS_PATH=${MLRUNS_GCS_PATH},_REGION=${REGION},_REPOSITORY=${REPOSITORY},_SERVICE=${SERVICE}"
