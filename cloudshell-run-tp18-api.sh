#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project)"
REGION="europe-west1"
REPOSITORY="purchased-docker"
SERVICE="purchase-predict-api"
IMAGE_TAG="preprod-manual"
MLRUNS_GCS_PATH="gs://purchase-predict-haroun-2026/preprod/latest/mlruns"

echo "PROJECT_ID=${PROJECT_ID}"
echo "REGION=${REGION}"
echo "REPOSITORY=${REPOSITORY}"
echo "SERVICE=${SERVICE}"
echo "IMAGE_TAG=${IMAGE_TAG}"
echo "MLRUNS_GCS_PATH=${MLRUNS_GCS_PATH}"

gcloud builds submit . \
  --config cloudbuild.yaml \
  --substitutions=_ENV=staging,_IMAGE_TAG="${IMAGE_TAG}",_MLRUNS_GCS_PATH="${MLRUNS_GCS_PATH}",_REGION="${REGION}",_REPOSITORY="${REPOSITORY}",_SERVICE="${SERVICE}"
