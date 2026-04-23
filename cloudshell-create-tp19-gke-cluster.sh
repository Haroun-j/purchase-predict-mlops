#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-purchase-predict-mlops}"
GKE_CLUSTER="${GKE_CLUSTER:-purchase-predict-api}"
GKE_ZONE="${GKE_ZONE:-europe-west1-b}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "GKE_CLUSTER=${GKE_CLUSTER}"
echo "GKE_ZONE=${GKE_ZONE}"

gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  container.googleapis.com \
  compute.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

if ! gcloud container clusters describe "${GKE_CLUSTER}" --zone "${GKE_ZONE}" >/dev/null 2>&1; then
  gcloud container clusters create "${GKE_CLUSTER}" \
    --zone "${GKE_ZONE}" \
    --machine-type "e2-medium" \
    --num-nodes "1" \
    --enable-autoscaling \
    --min-nodes "1" \
    --max-nodes "5" \
    --disk-size "20" \
    --release-channel "regular"
fi

CLUSTER_STATUS="$(gcloud container clusters describe "${GKE_CLUSTER}" --zone "${GKE_ZONE}" --format='value(status)' 2>/dev/null || true)"
echo "CLUSTER_STATUS=${CLUSTER_STATUS}"

if [ "${CLUSTER_STATUS}" != "RUNNING" ]; then
  echo "Cluster exists but is not RUNNING. Delete it and recreate it with a larger disk."
  echo "Suggested command:"
  echo "gcloud container clusters delete ${GKE_CLUSTER} --zone ${GKE_ZONE} --quiet"
  exit 1
fi

gcloud container clusters get-credentials "${GKE_CLUSTER}" --zone "${GKE_ZONE}"

kubectl get ns
