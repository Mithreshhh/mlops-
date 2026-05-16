# MLOps Student — Commands Reference

## Project URLs (after everything is running)

| Service            | URL                        | Purpose                          |
|--------------------|----------------------------|----------------------------------|
| Frontend           | http://localhost:3000       | React prediction UI              |
| FastAPI            | http://localhost:8000       | REST API (`/predict`, `/health`) |
| FastAPI Docs       | http://localhost:8000/docs  | Swagger / OpenAPI docs           |
| FastAPI Metrics    | http://localhost:8000/metrics | Prometheus metrics endpoint    |
| MLflow             | http://localhost:5000       | Experiment tracking UI           |
| Marquez API        | http://localhost:5001       | Lineage API                      |
| Marquez Web        | http://localhost:3002       | Lineage UI                       |
| Prometheus         | http://localhost:9090       | Metrics dashboard                |
| Grafana            | http://localhost:3001       | Monitoring dashboards            |

Grafana default login: `admin` / `admin`

---

## 1. Initial Setup (one-time)

### 1a. Create Python 3.12 virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 1b. Install frontend dependencies

```powershell
cd frontend
npm install
cd ..
```

### 1c. Install promptfoo (optional, needs Node.js)

```powershell
npm install -g promptfoo
```

---

## 2. Train the Model (run locally BEFORE Docker)

You must train at least once so `mlruns/` and `mlartifacts/` contain a registered model.
Docker containers mount these folders.

### 2a. Start MLflow server locally

```powershell
.\venv\Scripts\Activate.ps1
mlflow server --host 127.0.0.1 --port 5000
```

### 2b. In a SECOND terminal — run training

```powershell
.\venv\Scripts\Activate.ps1
python src/train.py
```

You should see output like:

```
Validation OK: 316 train, 79 test rows
Run ID  : <some-id>
Accuracy: 0.8861
F1 Score: 0.9109
Created version 'X' of model 'StudentPerformanceModel'.
```

### 2c. Stop the local MLflow server

Press `Ctrl+C` in the first terminal. Docker will run its own MLflow.

---

## 3. Run Data Validation (optional, local)

```powershell
.\venv\Scripts\Activate.ps1
python src/validate.py
```

Output: `Validation PASSED 6/6 expectations`
Report saved to: `monitoring/validation_report.html`

---

## 4. Run Drift Report (optional, local)

```powershell
.\venv\Scripts\Activate.ps1
python monitoring/drift_report.py
```

Report saved to: `monitoring/drift_report.html`

---

## 5. Feast Feature Store (optional, local)

### 5a. Prepare data for Feast

```powershell
.\venv\Scripts\Activate.ps1
python src/feast_repo/prep_data.py
```

### 5b. Apply Feast definitions

```powershell
cd src/feast_repo
feast apply
cd ../..
```

---

## 6. Docker — Build & Start Everything

### 6a. Build and start all containers

```powershell
docker compose up --build -d
```

This starts 8 services: api, frontend, mlflow, marquez-db, marquez, marquez-web, prometheus, grafana.

First build takes a few minutes (downloading images, installing dependencies).

### 6b. Verify all containers are running

```powershell
docker compose ps
```

All services should show `Up` or `Running`.

---

## 7. Docker — Useful Commands

### View logs for a specific service

```powershell
docker compose logs api --tail 20
docker compose logs mlflow --tail 20
docker compose logs marquez --tail 20
docker compose logs marquez-web --tail 5
docker compose logs frontend --tail 10
docker compose logs grafana --tail 10
```

### Follow logs in real time (Ctrl+C to stop)

```powershell
docker compose logs -f api
```

### Restart a single service (after config changes)

```powershell
docker compose up -d marquez-web
docker compose up -d api
```

### Rebuild a single service (after code changes)

```powershell
docker compose up --build -d api
docker compose up --build -d frontend
```

### Stop everything

```powershell
docker compose down
```

### Stop everything AND delete volumes (full reset)

```powershell
docker compose down -v
```

### Check which ports are in use

```powershell
docker compose ps --format "table {{.Name}}\t{{.Ports}}\t{{.Status}}"
```

---

## 8. Lineage Events (Marquez)

Lineage events are emitted automatically when you run `python src/train.py`.
The script sends OpenLineage events to `http://localhost:5001` for three steps:

- `data_ingestion`
- `data_validation`
- `model_training`

To re-send lineage events (Docker must be running):

```powershell
.\venv\Scripts\Activate.ps1
python src/train.py
```

Then open http://localhost:3002 to see the jobs in Marquez.

---

## 9. Promptfoo (Prompt Testing)

```powershell
promptfoo eval
```

Config file: `promptfooconfig.yaml`

---

## 10. DVC (Data Version Control)

### Track a data file

```powershell
dvc add data/student-mat.csv
```

### Pull data (if cloned fresh)

```powershell
dvc pull
```

---

## 11. Common Troubleshooting

| Problem | Solution |
|---------|----------|
| `localhost:8000` not loading | Run `docker compose logs api --tail 20` — if it says "Could not load model", you need to train locally first (Step 2) |
| `localhost:5000` not loading | Wait 30-60 seconds — MLflow container installs mlflow on every start |
| `localhost:3002` blank | Run `docker compose logs marquez-web --tail 5` — needs WEB_PORT env var (already set in docker-compose.yml) |
| Marquez shows no jobs | Run `python src/train.py` locally while Docker is up (Step 8) |
| Frontend can't reach API | Make sure api container is up: `docker compose logs api --tail 5` |
| Port already in use | Stop local servers (MLflow, uvicorn) before running Docker, or `docker compose down` first |
| `mlruns/` empty error | Train the model locally first (Step 2) before `docker compose up` |
| Model version not found | Re-train with `python src/train.py` — it creates a new version in the registry |

---

## Quick Start (TL;DR)

```powershell
# 1. Activate venv & train model
.\venv\Scripts\Activate.ps1
mlflow server --host 127.0.0.1 --port 5000          # Terminal 1

.\venv\Scripts\Activate.ps1                           # Terminal 2
python src/train.py                                   # Terminal 2

# 2. Stop local MLflow (Ctrl+C in Terminal 1)

# 3. Start Docker stack
docker compose up --build -d

# 4. Open in browser
# Frontend:    http://localhost:3000
# API docs:    http://localhost:8000/docs
# MLflow:      http://localhost:5000
# Marquez:     http://localhost:3002
# Prometheus:  http://localhost:9090
# Grafana:     http://localhost:3001

# 5. Send lineage events to Marquez
python src/train.py
```
