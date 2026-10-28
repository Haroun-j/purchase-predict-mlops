# Deployment

Everything here runs on Google Cloud Build and is submitted from the repository root,
so the configs can reach both `pipeline/` and `api/`.

| File | What it does |
|---|---|
| `cloudbuild.pipeline.yaml` | tests, `kedro run`, post-training tests, export of `data/` and `mlruns/` to GCS |
| `cloudbuild.api.yaml` | fetch the exported `mlruns` from GCS, test the API, build and push the image, deploy on Cloud Run |
| `cloudbuild.gke.yaml` | same, then render `k8s/` with the new image tag and `kubectl apply` on the GKE cluster |
| `cloudbuild.preprod.yaml` | training build followed by `cloudbuild.api.yaml` as a child build (pre-production) |
| `cloudbuild.prod.yaml` | training build followed by `cloudbuild.gke.yaml` as a child build (production) |
| `k8s/` | namespace, Deployment (2 replicas, rolling update without surge), NodePort Service, GCE Ingress |
| `scripts/` | thin wrappers around `gcloud builds submit` with the substitutions filled in |
| `cloud-run.md` | the manual Cloud Run commands |

Order of operations on a fresh project:

```bash
export BUCKET=my-bucket                      # holds data/03_primary/*.csv and data-test.csv/
deploy/scripts/bootstrap-cloud-run.sh        # Artifact Registry repo, service account, first Cloud Run deploy
deploy/scripts/run-training-build.sh         # first training build, artifacts under cloud-build-artifacts/<build id>/
deploy/scripts/run-preprod.sh                # train + redeploy Cloud Run
deploy/scripts/create-gke-cluster.sh         # once
deploy/scripts/run-prod.sh                   # train + roll out on GKE
```

Variables every script accepts: `PROJECT_ID` (defaults to the active gcloud project),
`BUCKET` (required), `REGION`, `REPOSITORY`, `SERVICE`, `ENV_NAME`, `AUTOML_MAX_EVALS`,
`GKE_CLUSTER`, `GKE_ZONE`. The Cloud Build service account needs
`roles/storage.objectAdmin` on the bucket, `roles/run.admin` and
`roles/iam.serviceAccountUser` for Cloud Run, `roles/container.developer` for GKE and
`roles/cloudbuild.builds.editor` to start the child builds.
