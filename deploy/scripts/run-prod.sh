#!/usr/bin/env bash
# Production: train, export to prod/, rebuild the API and roll it out on GKE.
# The cluster must exist (deploy/scripts/create-gke-cluster.sh).
# Usage: BUCKET=my-bucket deploy/scripts/run-prod.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
BUCKET="${BUCKET:?set BUCKET to the GCS bucket that holds data/03_primary}"
ENV_NAME="${ENV_NAME:-staging}"
AUTOML_MAX_EVALS="${AUTOML_MAX_EVALS:-1}"
GKE_CLUSTER="${GKE_CLUSTER:-purchase-predict-api}"
GKE_ZONE="${GKE_ZONE:-europe-west1-b}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "BUCKET=${BUCKET}"
echo "GKE_CLUSTER=${GKE_CLUSTER} (${GKE_ZONE})"
echo "CONFIG=deploy/cloudbuild.prod.yaml"

gcloud builds submit . \
  --config deploy/cloudbuild.prod.yaml \
  --substitutions="_BUCKET=${BUCKET},_ENV=${ENV_NAME},_AUTOML_MAX_EVALS=${AUTOML_MAX_EVALS},_GKE_CLUSTER=${GKE_CLUSTER},_GKE_ZONE=${GKE_ZONE}"
