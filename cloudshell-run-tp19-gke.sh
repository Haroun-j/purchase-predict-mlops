#!/usr/bin/env bash

set -euo pipefail

PROJECT_ID="${PROJECT_ID:-purchase-predict-mlops}"
PROJECT_NUMBER="${PROJECT_NUMBER:-$(gcloud projects describe "${PROJECT_ID}" --format='value(projectNumber)')}"
GKE_CLUSTER="${GKE_CLUSTER:-purchase-predict-api}"
GKE_ZONE="${GKE_ZONE:-europe-west1-b}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"

echo "PROJECT_ID=${PROJECT_ID}"
echo "PROJECT_NUMBER=${PROJECT_NUMBER}"
echo "GKE_CLUSTER=${GKE_CLUSTER}"
echo "GKE_ZONE=${GKE_ZONE}"
echo "IMAGE_TAG=${IMAGE_TAG}"

gcloud config set project "${PROJECT_ID}"

gcloud services enable \
  container.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/container.developer" >/dev/null

gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --role="roles/artifactregistry.reader" >/dev/null

gcloud container clusters describe "${GKE_CLUSTER}" --zone "${GKE_ZONE}" >/dev/null

gcloud builds submit . \
  --config cloudbuild.gke.yaml \
  --substitutions=SHORT_SHA="${IMAGE_TAG}",_GKE_CLUSTER="${GKE_CLUSTER}",_GKE_ZONE="${GKE_ZONE}"
