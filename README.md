# content-moderation-mlops

Production-grade content moderation API with a lightweight MLOps pipeline. Built with FastAPI, scikit-learn, MLflow, and Docker.

## What it does

Classifies text as **spam** or **ham** using a TF-IDF + Logistic Regression model, served via a REST API with experiment tracking and monitoring.

## Architecture

```mermaid
flowchart LR
  U[User] --> B[Browser/Client]
  B -->|GET / (UI)| API[FastAPI API]
  B -->|POST /predict<br/>POST /predict/batch| API
  API --> P[Predictor]
  P --> M[(model/model.pkl)]
  T[Training pipeline<br/>python main.py] --> M
  API --> MF[MLflow tracking]
```

## Project structure

```
content-moderation-mlops/
|-- app/                        # FastAPI application
|   |-- main.py                 # UI + /health, /ready, /predict
|   |-- predictor.py            # Loads model bundle and serves predictions
|   |-- schemas.py              # Pydantic request/response validation
|   `-- logger.py               # Shared logger
|-- pipeline/                   # ML pipeline
|   |-- extract.py              # Reads SMS zip, returns DataFrame
|   |-- preprocessing.py        # Text cleaning
|   |-- train.py                # Train TF-IDF + LogisticRegression pipeline
|   |-- test_evaluate.py        # Metrics + MLflow logging
|   |-- save_model.py           # Save model bundle
|   `-- utils.py                # Dataset preview + save cleaned CSV
|-- config/
|   `-- settings.py             # Paths, hyperparameters, constants
|-- tests/
|   `-- test_api.py             # API tests (pytest)
|-- Dockerfile
|-- docker-compose.yml
|-- docker-compose.prod.yml
|-- pyproject.toml
`-- main.py                     # Runs the full pipeline
```

## Stack

- FastAPI (API)
- scikit-learn (TF-IDF + Logistic Regression)
- MLflow (experiment tracking)
- Docker / Docker Compose
- slowapi (rate limiting)
- pytest (tests)

## Quickstart (Docker)

### 1) Put the dataset in `data/`

- Download the “SMS Spam Collection” dataset and place it at:
  - `data/sms+spam+collection.zip`

### 2) Train the model (writes `model/model.pkl`)

Option A (recommended): run training inside Docker
```bash
docker compose run --rm api python main.py
```

Option B: run training locally
```bash
python -m pip install -e .
python main.py
```

### 3) Run the API + UI

Development (includes an MLflow container):
```bash
docker compose up --build
```

Production-like (no MLflow container, hardened runtime settings):
```bash
docker compose -f docker-compose.prod.yml up --build
```

Open the UI:
- `http://localhost:8000/`

Open the API docs UI:
- `http://localhost:8000/docs`

## Production notes (model artifact)

This project uses **option 1**: the model file (`model/model.pkl`) is expected to be present in the image/container.

To update the model in production:

1. Run the training pipeline to produce a new `model/model.pkl`
2. Rebuild and redeploy the Docker image

Optional: set `MODEL_SHA256` to verify the model file before loading (the pipeline writes
`model/model.pkl.sha256` when it trains).

## Recommended environment variables

### Require model checksum (recommended)

This prevents accidentally running a different/corrupted model file.

- `REQUIRE_MODEL_SHA256=1`
- Ensure `model/model.pkl.sha256` exists next to `model/model.pkl` (training creates it)

### Correct rate-limiting IPs behind a reverse proxy

If you run behind Nginx / a load balancer, enable trusted proxy headers so rate limiting uses the real client IP:

- `TRUST_PROXY_HEADERS=1`
- `TRUSTED_PROXY_IPS=<comma-separated proxy IPs>`

## API endpoints

- `GET /` (UI): minimal web UI for trying predictions
- `GET /health` (liveness): always `200` when the API process is up
- `GET /ready` (readiness): `200` only when the model is loaded
- `POST /predict`: returns `503` if the model is not loaded
- `POST /predict/batch`: classify multiple texts in one request

### Example: batch prediction

```bash
curl -X POST http://localhost:8000/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"texts":["free prize call now","hey see you later"]}'
```
