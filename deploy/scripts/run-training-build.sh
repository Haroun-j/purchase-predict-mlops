#!/usr/bin/env bash
# Train the model on Cloud Build and export data/ and mlruns/ to the bucket.
# Usage (Cloud Shell or any machine with gcloud): BUCKET=my-bucket deploy/scripts/run-training-build.sh
set -euo pipefail
cd "$(dirname "$0")/../.."

PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project)}"
PROJECT_NUMBER="$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')"
BUCKET="${BUCKET:?set BUCKET to the GCS bucket that holds data/03_primary}"
ENV_NAME="${ENV_NAME:-staging}"
AUTOML_MAX_EVALS="${AUTOML_MAX_EVALS:-4}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "BUCKET=${BUCKET}"

gcloud services enable cloudbuild.googleapis.com storage.googleapis.com

# Cloud Build reads the data from the bucket and writes the artifacts back to it.
for service_account in \
  "${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
do
  if gcloud iam service-accounts describe "${service_account}" >/dev/null 2>&1; then
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
      --member="serviceAccount:${service_account}" \
      --role="roles/storage.objectAdmin" \
      --quiet >/dev/null
    echo "granted roles/storage.objectAdmin to ${service_account}"
  fi
done

gcloud builds submit . \
  --config deploy/cloudbuild.pipeline.yaml \
  --substitutions="_BUCKET=${BUCKET},_ENV=${ENV_NAME},_AUTOML_MAX_EVALS=${AUTOML_MAX_EVALS}"
