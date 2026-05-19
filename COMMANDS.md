# MLOps Student — Run Guide (All Ways)

This project can run in 5 different ways, from simplest to most production-like:

| # | Mode | What runs where | When to use |
|---|------|----------------|-------------|
| 1 | **Bare metal (venv)** | Python scripts directly on your machine | Development, debugging, training |
| 2 | **Docker (single service)** | One container at a time | Testing a single piece in isolation |
| 3 | **Docker Compose** | All 8 services in containers on your machine | Local full-stack demo |
| 4 | **Kubernetes (Minikube)** | API + Frontend pods on Minikube | Practice production K8s deployment |
| 5 | **ArgoCD (GitOps)** | K8s pulls from GitHub automatically | True production-style continuous deployment |

---

## URLs Reference

| Service | Docker URL | Kubernetes URL |
|---------|-----------|----------------|
| Frontend | http://localhost:3000 | http://localhost:30081 |
| FastAPI | http://localhost:8000 | http://localhost:30080 |
| FastAPI Docs | http://localhost:8000/docs | http://localhost:30080/docs |
| MLflow | http://localhost:5000 | (still in Docker) |
| Marquez Web | http://localhost:3002 | (still in Docker) |
| Marquez API | http://localhost:5001 | (still in Docker) |
| Prometheus | http://localhost:9090 | (still in Docker) |
| Grafana | http://localhost:3001 | (still in Docker) |
| ArgoCD UI | — | https://localhost:8080 |

Grafana login: `admin` / `admin`

---

# Mode 1 — Bare Metal (Inside venv)

Run everything directly on your Windows machine using a Python virtual environment. No containers, no Kubernetes. Easiest for development.

## 1.1 One-time setup

```powershell
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

You'll know the venv is active when your prompt shows `(venv)`.

## 1.2 Train the model (needs 2 terminals)

**Terminal 1 — MLflow server:**

```powershell
.\venv\Scripts\Activate.ps1
mlflow server --host 127.0.0.1 --port 5000
```

Leave this running. Open http://localhost:5000 to see the MLflow UI.

**Terminal 2 — Run training:**

```powershell
.\venv\Scripts\Activate.ps1
python src/train.py
```

This registers `StudentPerformanceModel` in MLflow's registry. The `mlruns/` and `mlartifacts/` folders are populated.

## 1.3 Run the API locally

```powershell
.\venv\Scripts\Activate.ps1
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

`--reload` auto-restarts when you edit code. Open http://localhost:8000/docs.

## 1.4 Run the frontend locally

```powershell
cd frontend
npm run dev
```

Opens at http://localhost:5173 (Vite's default dev port). Edits hot-reload instantly.

## 1.5 Run other scripts (anytime, in venv)

```powershell
python src/validate.py                    # Generates validation_report.html
python monitoring/drift_report.py         # Generates drift_report.html
python src/feast_repo/prep_data.py        # Prepares Feast data
cd src/feast_repo; feast apply; cd ../..  # Registers Feast features
promptfoo eval                            # Tests prompts (Node.js, not venv)
```

## When to use Mode 1

- Active development — fastest iteration
- Debugging Python errors (full stack traces)
- Running one-off scripts (validate, drift, train)
- You DON'T need Docker/K8s running

---

# Mode 2 — Docker (Single Service)

Run just ONE container in isolation, useful for testing a single piece.

```powershell
docker compose up -d api          # Just the API + dependencies (MLflow)
docker compose up -d mlflow       # Just MLflow
docker compose up -d frontend     # Just the frontend + its dependency (api)
docker compose up -d prometheus grafana   # Just monitoring stack
```

Docker Compose automatically starts any service this one `depends_on`.

```powershell
docker compose stop api           # Stop only the API
docker compose restart api        # Restart only the API
docker compose logs -f api        # Tail API logs
```

## When to use Mode 2

- You want to test ONE service against the others
- Debugging container-specific issues
- Saving resources (not running all 8 containers)

---

# Mode 3 — Docker Compose (Full Stack)

Run all 8 services together. This is the "demo mode" — everything in containers, one command.

## 3.1 Prerequisite

Train the model at least once (Mode 1, Step 1.2). The `mlruns/` and `mlartifacts/` folders get mounted into the MLflow + API containers.

## 3.2 Start everything

```powershell
docker compose up --build -d      # First time (builds images)
docker compose up -d              # Subsequent times (fast)
```

`-d` runs containers in the background (detached). Drop it to see logs streaming.

## 3.3 Verify

```powershell
docker compose ps
```

You should see 8 services in `Up` or `Running` state:
- `api`, `frontend`, `mlflow`, `marquez-db`, `marquez`, `marquez-web`, `prometheus`, `grafana`

## 3.4 Daily operations

```powershell
docker compose logs api --tail 20         # Recent API logs
docker compose logs -f api                # Stream API logs live
docker compose restart api                # Restart a service
docker compose up --build -d api          # Rebuild + restart (after code change)
docker compose down                       # Stop everything
docker compose down -v                    # Stop + delete volumes (full reset)
```

## 3.5 Generate traffic for monitoring

While Docker Compose is up, run training to populate Marquez:

```powershell
.\venv\Scripts\Activate.ps1
python src/train.py
```

Send test requests to populate Grafana metrics:

```powershell
for ($i = 1; $i -le 50; $i++) {
  Invoke-RestMethod -Uri "http://localhost:8000/predict" -Method POST `
    -ContentType "application/json" `
    -Body '{"school":"GP","sex":"F","age":18,"address":"U","famsize":"GT3","Pstatus":"A","Medu":4,"Fedu":4,"Mjob":"at_home","Fjob":"teacher","reason":"course","guardian":"mother","traveltime":2,"studytime":2,"failures":0,"schoolsup":"yes","famsup":"no","paid":"no","activities":"no","nursery":"yes","higher":"yes","internet":"no","romantic":"no","famrel":4,"freetime":3,"goout":4,"Dalc":1,"Walc":1,"health":3,"absences":6,"G1":5,"G2":6}' `
    -TimeoutSec 5 | Out-Null
}
```

## When to use Mode 3

- Full demo / interview
- Testing the entire system end-to-end locally
- Validating the same setup that will go to production

---

# Mode 4 — Kubernetes (Minikube)

Run the API + Frontend on Minikube (local Kubernetes). MLflow, Prometheus, Grafana, Marquez stay in Docker Compose — K8s pods reach them via the host IP.

## 4.1 Prerequisites

- Minikube installed and running: `minikube start`
- Docker images pushed to DockerHub (`mithreshh/student-api:latest`, `mithreshh/student-frontend:latest`)
- The GitHub Actions CI pipeline pushes these automatically on every push to `main`
- MLflow running in Docker Compose: `docker compose up -d mlflow`

## 4.2 Confirm host IP

`k8s/api-deployment.yaml` uses `http://192.168.49.1:5000` for MLflow. Verify with:

```powershell
minikube ssh "ip route" | Select-String "default"
```

The IP after `via` should match `192.168.49.1`. If different, update the YAML.

## 4.3 Deploy

```powershell
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

## 4.4 Verify

```powershell
kubectl get pods                  # Should show student-api (2 replicas) + student-frontend
kubectl get services              # NodePort services on 30080 and 30081
kubectl logs deploy/student-api   # Check API logs
```

Wait ~60 seconds for the API pods to pass their health checks.

## 4.5 Access

- API: http://localhost:30080
- Frontend: http://localhost:30081
- API Docs: http://localhost:30080/docs

If those don't load on Windows + Docker Driver, run:

```powershell
minikube service student-api-service --url
minikube service student-frontend-service --url
```

Minikube prints temporary URLs you can use instead.

## 4.6 Common operations

```powershell
kubectl rollout restart deploy student-api    # Restart pods (e.g., after image push)
kubectl scale deploy student-api --replicas=4 # Scale up to 4 pods
kubectl delete -f k8s/                        # Remove everything
kubectl describe pod <pod-name>               # Detailed troubleshooting
```

## When to use Mode 4

- Practice K8s commands
- Demonstrate auto-scaling, self-healing, rolling updates
- Closer to production behavior than Docker Compose

---

# Mode 5 — ArgoCD (GitOps)

ArgoCD watches your Git repository and automatically deploys whatever's in `k8s/` to Kubernetes. Push to `main` → ArgoCD syncs in ~3 minutes. This is "GitOps".

Your existing setup is at `argocd/application.yaml`:
- Source: `https://github.com/Mithreshhh/mlops-.git`, branch `main`, path `k8s/`
- Destination: `default` namespace on the in-cluster K8s
- Auto-sync, auto-prune (delete K8s resources removed from Git), self-heal (revert manual K8s changes)

## 5.1 One-time: Install ArgoCD into Minikube

```powershell
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Wait for all ArgoCD pods to be ready:

```powershell
kubectl get pods -n argocd
```

## 5.2 Apply your Application manifest

```powershell
kubectl apply -f argocd/application.yaml
```

This tells ArgoCD: "Watch this repo, sync these manifests."

## 5.3 Access the ArgoCD UI

```powershell
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Open https://localhost:8080 (accept the self-signed cert warning).

**Get the initial admin password:**

```powershell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

Login: `admin` / `<password from above>`

You should see your `mlops-student` Application card showing `Synced` and `Healthy`.

## 5.4 The GitOps workflow

From this point, you don't run `kubectl apply` anymore. Just:

```powershell
# 1. Edit k8s/api-deployment.yaml (e.g., change replicas: 2 to replicas: 4)
git add k8s/
git commit -m "Scale API to 4 replicas"
git push
```

Within ~3 minutes, ArgoCD detects the change and applies it automatically. You can also force a sync via the UI or:

```powershell
kubectl patch application mlops-student -n argocd --type merge -p '{\"operation\":{\"sync\":{}}}'
```

## 5.5 Useful ArgoCD commands

```powershell
kubectl get applications -n argocd                       # List apps
kubectl describe application mlops-student -n argocd     # See sync status, last error
kubectl delete application mlops-student -n argocd       # Remove (also removes K8s resources due to prune)
```

## When to use Mode 5

- Demonstrating production-grade CD
- Showing GitOps in interviews
- Real teams: ArgoCD is industry standard for K8s deployments

---

# Recommended Workflow (Day-to-Day)

```
┌─────────────────────────────────────────────────────────────────────┐
│  Develop & train in venv  →  Test in Docker Compose  →  Push to git │
│         (Mode 1)                     (Mode 3)              ↓        │
│                                                                     │
│  CI builds image and pushes to DockerHub (GitHub Actions)           │
│                                                                     │
│                          ArgoCD pulls and deploys to K8s (Mode 5)   │
└─────────────────────────────────────────────────────────────────────┘
```

## Daily quick start

```powershell
# Open project, activate venv
.\venv\Scripts\Activate.ps1

# Start full stack
docker compose up -d

# Make code changes, then:
docker compose up --build -d api   # Rebuild changed service

# Stop when done
docker compose down
```

---

# Troubleshooting

| Symptom | Fix |
|---------|-----|
| `localhost:8000` not loading after `docker compose up` | Check `docker compose logs api`. If "Could not load model", train locally first (Mode 1, Step 1.2). |
| `localhost:5000` takes 60+ seconds | MLflow container installs mlflow on each start. Normal. |
| `localhost:3002` blank | Run `docker compose logs marquez-web`. The `WEB_PORT: "3000"` env var is set — restart it: `docker compose up -d marquez-web`. |
| Marquez shows no jobs | Run `python src/train.py` while Docker is up. |
| K8s pod restarting | `kubectl logs <pod>`. Usually MLflow unreachable — check host IP in `k8s/api-deployment.yaml`. |
| ArgoCD shows `OutOfSync` | Click `Sync` in the UI, or wait 3 minutes for auto-sync. |
| ArgoCD shows `Degraded` | `kubectl describe pod <failing-pod>` and check the events. |
| `Port already in use` | Stop local servers first, or `docker compose down`. |
