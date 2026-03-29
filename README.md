# IT Support RAG Chatbot

GenAI-powered IT helpdesk using a **local** LLM (Ollama) and ChromaDB — documents stay on your machine unless you configure otherwise.

---

## Architecture

```
POST /ask (JSON)
    → FastAPI (port 8000)
    → LangChain retrieval QA
    → ChromaDB (top-k chunks)
    → Ollama (LLM + embeddings)
    → JSON answer + source filenames
    → GET /metrics (Prometheus)
```

---

## Tech stack

| Layer | Technology |
|--------|------------|
| LLM & embeddings | Ollama (e.g. `llama3.2`, `nomic-embed-text`) |
| RAG | LangChain |
| Vector store | ChromaDB (persisted under `./chroma_db`) |
| API | FastAPI |
| Metrics | Prometheus client (`/metrics`) |
| Container | Docker |
| Orchestration | Kubernetes manifests under `k8s/` |
| CI/CD | GitLab CI (`.gitlab-ci.yml`) |
| Dashboards | Grafana JSON under `monitoring/` |

---

## Prerequisites

- **Python 3.11+**
- **Ollama** installed and running, with models pulled (see below)
- **IT support docs** as `.txt` files under `docs/` (sample files included)

---

## Quick start (local)

### 1. Ollama

```bash
brew install ollama   # or install from https://ollama.com
ollama serve            # in a separate terminal, if not already running
ollama pull llama3.2
ollama pull nomic-embed-text
```

Default in `app.py`: LLM and embeddings use `http://localhost:11434`.

### 2. Python app

```bash
git clone https://github.com/sumanth-kondru/it-support-rag.git
cd it-support-rag
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

On startup the app loads `docs/**/*.txt`, builds embeddings, and persists Chroma data to `./chroma_db`.

### 3. Try the API

```bash
curl -s -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "My pod is in CrashLoopBackOff — what should I check?"}'

curl -s http://localhost:8000/health
curl -s http://localhost:8000/metrics | head
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Docker

```bash
docker build -t it-support-rag:latest .
docker run --rm -p 8000:8000 \
  -v "$(pwd)/docs:/app/docs" \
  -v "$(pwd)/chroma_db:/app/chroma_db" \
  it-support-rag:latest
```

**Note:** The app talks to Ollama at `localhost:11434` by default. Inside a container, `localhost` is the container itself. For local Docker, run Ollama on the host and pass an appropriate host URL (for example `host.docker.internal` on Docker Desktop) or run Ollama in the same Compose/Kubernetes network and point the app at that service. Kubernetes manifests use a secret key `ollama-url` for the service URL.

---

## Kubernetes

```bash
aws eks update-kubeconfig --name <cluster> --region <region>
kubectl apply -f k8s/deployment.yaml
kubectl get pods -n ai-apps
kubectl logs -f deployment/it-support-rag -n ai-apps
```

Edit `k8s/deployment.yaml` for your image registry (replace the placeholder ECR image name), storage class, and ingress/host as needed.

---

## Monitoring

Import `monitoring/grafana-dashboard.json` into Grafana. Scrape `http://<host>:8000/metrics`.

Notable metrics:

- `itsupport_questions_total`
- `itsupport_questions_success` / `itsupport_questions_failed`
- `itsupport_response_seconds`
- `itsupport_sessions_total`

---

## GitLab CI

Pipeline stages: test → security scan (Trivy) → build → push (ECR) → deploy (EKS). Set CI/CD variables such as `AWS_ACCOUNT_ID`, `AWS_REGION`, `EKS_CLUSTER_NAME`, and ensure AWS/GitLab runners can reach ECR and EKS.

The **test** job runs `pytest tests/`. Add a `tests/` package with tests if you want that stage to pass on every run.

---

## Security notes

- Default setup uses a **local** LLM; no cloud LLM API key is required.
- `.gitignore` excludes `.env`, `chroma_db/`, and `secrets.yaml`. Use your org’s standard (e.g. SOPS) for any real secrets in GitOps.
- Keep IT docs free of passwords and personal data; treat the knowledge base as non-sensitive operational guidance.

---

## Project layout

```
it-support-rag/
├── app.py                 # FastAPI + RAG
├── requirements.txt
├── Dockerfile
├── .gitlab-ci.yml
├── docs/                  # Knowledge base (*.txt)
├── k8s/deployment.yaml
└── monitoring/
    └── grafana-dashboard.json
```

---

## Roadmap (ideas)

- Streamlit or other UI for non-API users
- Slack or chat integration
- Prompt / retrieval evaluation and caching
- Org-specific fine-tuning or curated doc ingestion

---

## Author

**Sumanth Kondru** — DevOps / platform engineering background; building GenAI apps with production-style delivery.

- Email: kondru.sumanth@gmail.com
- LinkedIn: [linkedin.com/in/sumanthkondru](https://linkedin.com/in/sumanthkondru)

If this fork’s remote URL differs, change the clone URL in the Quick start section to match your GitHub user or organization.
