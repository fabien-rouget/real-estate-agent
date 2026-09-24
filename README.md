# 🏢 Real Estate AI Agent — Google ADK & ADEME DPE Reconciliation

[![CI Pipeline](https://github.com/fabien-rouget/real-estate-agent/actions/workflows/deploy.yml/badge.svg)](https://github.com/fabien-rouget/real-estate-agent/actions/workflows/deploy.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google-ADK%202.9-orange.svg)](https://google.github.io/adk-docs/)
[![Google Cloud](https://img.shields.io/badge/GCP-Vertex%20AI%20Agent%20Engine-4285F4.svg)](https://cloud.google.com/vertex-ai)

Autonomous AI Agent built with the official **Google Agent Development Kit (ADK)** and deployed on **Google Cloud Vertex AI Agent Engine**.

It identifies the exact physical address of real estate listings (e.g. from Leboncoin) by cross-referencing extracted technical characteristics (living surface area, DPE energy consumption / rating letter, official diagnostic date, construction period, building floor) with the French Environmental Agency (**ADEME**) open-data registry of 15.6M+ certified DPE records.

---

## 🎯 Key Features

- **Multi-Tool Autonomous Agent (ReAct)**:
  1. `fetch_leboncoin_listing`: Real-time retrieval of raw classified ads from Leboncoin.
  2. `search_ademe_dpe`: High-precision querying of the official French ADEME open-data registry (`data.ademe.fr`, dataset `meg-83tjwtg8dyz4vv7h1dqe`).
- **Strictly Typed Structured Output**: Validated against the `ImmoAnalysisResult` Pydantic v2 contract.
- **Self-Correction & Fallbacks**: Handles missing kWh numbers by leveraging official DPE letter boundaries (A to G), with exact diagnostic date matching.
- **Enterprise-Grade Cloud Deployment**: Managed serverless runtime on **Vertex AI Agent Engine** (`europe-west1`) with native OpenTelemetry distributed tracing and IAM-based authentication (0 hardcoded API keys).
- **100% Deterministic Testing**: 27 unit tests with 0 token spend.

---

## 📂 Project Structure

```text
.
├── .github/
│   └── workflows/
│       └── deploy.yml        # CI/CD: Automated testing & GCP deployment
├── app/
│   ├── .env                  # Enterprise GCP config (Vertex AI)
│   ├── agent.py              # Official ADK root_agent definition
│   ├── schemas/              # Strongly typed Pydantic models (ImmoAnalysisResult, ADEME DTOs)
│   ├── clients/              # External HTTP clients (ADEME, Leboncoin)
│   └── services/             # Business logic layer (DPE matching algorithms, ranking score)
├── tests/
│   └── unit/                 # 100% offline mocked unit tests
├── pyproject.toml            # Project configuration & pytest settings
├── requirements.txt          # Python dependencies
└── sample_listing.txt        # Sample real estate ad (Bordeaux apartment)
```

---

## 🚀 Quickstart

### 1. Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Cloud Authentication

```bash
gcloud auth login
gcloud config set project <YOUR_PROJECT_ID>
gcloud auth application-default login
gcloud auth application-default set-quota-project <YOUR_PROJECT_ID>
```

### 3. Local Testing

#### Terminal CLI:
```bash
adk run app "Peux-tu trouver l'adresse de cette annonce : https://www.leboncoin.fr/ad/ventes_immobilieres/3271779569"
```

#### Visual Web Playground:
```bash
adk web app
```
Open `http://127.0.0.1:8000` to interact with the agent, inspect tool calls, and view execution traces.

### 4. Unit Tests

```bash
pytest -v
```

---

## ☁️ Deployment to Google Cloud (Vertex AI Agent Engine)

```bash
adk deploy agent_engine app \
  --project=real-estate-agent-509518 \
  --region=europe-west1 \
  --display_name="real-estate-agent" \
  --otel_to_cloud
```

*The `--otel_to_cloud` flag enables automatic OpenTelemetry trace ingestion into Google Cloud Trace and Cloud Monitoring.*
