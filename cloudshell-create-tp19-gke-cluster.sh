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
    --disk-size "10" \
    --release-channel "regular"
fi

gcloud container clusters get-credentials "${GKE_CLUSTER}" --zone "${GKE_ZONE}"

kubectl get ns
