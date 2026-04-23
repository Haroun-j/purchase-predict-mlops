API Flask du modele `purchase_predict`.

L'application charge le modele `purchase_predict@staging` depuis le registre MLflow local du projet Kedro, puis expose une route `POST /predict`.

```powershell
$env:Path = "C:\Users\CYTech Student\.local\bin;$env:Path"
uv run python app.py
```

Tests locaux :

```powershell
$env:Path = "C:\Users\CYTech Student\.local\bin;$env:Path"
$env:ENV = "staging"
$env:MLFLOW_SERVER = "../notebooks/purchase-predict/mlruns"
$env:MLFLOW_REGISTRY_NAME = "purchase_predict"
uv run pytest
```

Version Docker locale :

```powershell
docker compose up --build
```

L'API conteneurisee est disponible sur `http://127.0.0.1:8080`.

Pipeline pre-production Cloud Build :

```bash
chmod +x cloudshell-run-tp18-api.sh
./cloudshell-run-tp18-api.sh
```

Le fichier `cloudbuild.yaml` :

- recupere `mlruns` depuis `gs://purchase-predict-haroun-2026/preprod/latest/mlruns`
- teste l'API
- construit et pousse l'image vers Artifact Registry
- redeploie `purchase-predict-api` sur Cloud Run

Preparation Kubernetes pour TP19 :

```bash
chmod +x cloudshell-create-tp19-gke-cluster.sh
./cloudshell-create-tp19-gke-cluster.sh

chmod +x cloudshell-run-tp19-gke.sh
./cloudshell-run-tp19-gke.sh
```

Les fichiers associes :

- `k8s/` contient `ns.yaml`, `deployment.yaml`, `service.yaml` et `ingress.yaml`
- `cloudbuild.gke.yaml` construit l'image, la pousse dans Artifact Registry et applique les manifests sur GKE
