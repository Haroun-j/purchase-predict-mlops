#!/usr/bin/env bash
# Pre-production: train, export to preprod/, rebuild the API and redeploy Cloud Run.
# Usage: BUCKET=my-bucket deploy/scripts/run-preprod.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
BUCKET="${BUCKET:?set BUCKET to the GCS bucket that holds data/03_primary}"
ENV_NAME="${ENV_NAME:-staging}"
AUTOML_MAX_EVALS="${AUTOML_MAX_EVALS:-1}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "BUCKET=${BUCKET}"
echo "CONFIG=deploy/cloudbuild.preprod.yaml"

gcloud builds submit . \
  --config deploy/cloudbuild.preprod.yaml \
  --substitutions="_BUCKET=${BUCKET},_ENV=${ENV_NAME},_AUTOML_MAX_EVALS=${AUTOML_MAX_EVALS}"
