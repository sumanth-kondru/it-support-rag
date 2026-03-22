# 🤖 IT Support RAG Chatbot

> **GenAI-powered IT helpdesk using local LLM — no data leaves your network**

Built by **Sumanth Kondru** | Senior DevOps → GenAI/MLOps Engineer

---

## 🏗️ Architecture

```
User Question (HTTP POST)
        ↓
FastAPI REST API (port 8000)
        ↓
LangChain RAG Pipeline
        ↓
ChromaDB Vector Store ──── Search top 3 relevant IT docs
        ↓
Ollama LLM (local, free, private)
        ↓
IT Support Answer (JSON response)
        ↓
Prometheus /metrics ──── Grafana Dashboard
```

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **LLM** | Ollama + Llama 3.2 (local) | Free, private, no API key, runs on-prem |
| **RAG Framework** | LangChain | Industry standard for RAG pipelines |
| **Vector Database** | ChromaDB | Lightweight, no external service needed |
| **API Framework** | FastAPI | High-performance Python REST API |
| **Containerization** | Docker | Same as production Spring Boot deployments |
| **Orchestration** | Kubernetes (EKS) | Production-grade scaling |
| **CI/CD** | GitLab CI | Automated build → scan → push → deploy |
| **Monitoring** | Prometheus + Grafana | Full AI observability stack |
| **Security** | Trivy + SOPS | Container scanning + secrets encryption |

---

## 🚀 Quick Start — Run Locally on Mac

### Step 1: Install Ollama (free local LLM)
```bash
# Download from ollama.com or use brew
brew install ollama

# Start Ollama service
ollama serve

# Pull the LLM model (one time, ~2GB download)
ollama pull llama3.2

# Pull embedding model
ollama pull nomic-embed-text
```

### Step 2: Set up Python environment
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/it-support-rag.git
cd it-support-rag

# Create virtual environment (like a clean container for Python)
python3 -m venv venv
source venv/bin/activate

# Install dependencies (like mvn install for Spring Boot)
pip install -r requirements.txt
```

### Step 3: Run the application
```bash
# Start the FastAPI app
uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# You should see:
# ✅ Loaded 4 documents
# ✅ Split into X chunks
# ✅ Vector store created
# ✅ RAG pipeline ready!
# ✅ Application ready to serve requests
```

### Step 4: Test it!
```bash
# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "My pod is stuck in CrashLoopBackOff, how do I fix it?"}'

# Check health (like Spring Actuator)
curl http://localhost:8000/health

# View Prometheus metrics
curl http://localhost:8000/metrics

# Open Swagger UI (FastAPI auto-generates this — like Swagger in Spring Boot)
open http://localhost:8000/docs
```

---

## 🐳 Docker Deployment

```bash
# Build image (same as Spring Boot Docker build)
docker build -t it-support-rag:latest .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/docs:/app/docs \
  -v $(pwd)/chroma_db:/app/chroma_db \
  it-support-rag:latest

# Test
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text": "How do I reset my password?"}'
```

---

## ☸️ Kubernetes Deployment (AWS EKS)

```bash
# Configure kubectl for your EKS cluster
aws eks update-kubeconfig --name your-cluster --region us-east-1

# Deploy everything
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -n ai-apps
kubectl logs -f deployment/it-support-rag -n ai-apps

# Check HPA is working
kubectl get hpa -n ai-apps
```

---

## 📊 Monitoring

Import `monitoring/grafana-dashboard.json` into your Grafana instance.

Metrics available at `/metrics`:
- `itsupport_questions_total` — total questions asked
- `itsupport_questions_success` — successful answers
- `itsupport_questions_failed` — failed requests
- `itsupport_response_seconds` — response time histogram

---

## 💬 Example Questions to Ask

```
"My laptop is running slow, what should I do?"
"How do I reset my company password?"
"My pod is stuck in CrashLoopBackOff"
"VPN is not connecting"
"GitLab CI pipeline is failing"
"ImagePullBackOff error in Kubernetes"
"Terraform apply is failing"
"External monitor not detected"
```

---

## 🔐 Security Features

- **Local LLM** — no data sent to external APIs
- **SOPS encryption** — secrets management for any API keys
- **Trivy scanning** — container vulnerability scanning in CI/CD
- **Kubernetes RBAC** — least-privilege access control
- **No PII in vector store** — only IT support documentation

---

## 📁 Project Structure

```
it-support-rag/
├── app.py                    # FastAPI + LangChain RAG pipeline
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container build (same pattern as Spring Boot)
├── .gitlab-ci.yml            # CI/CD pipeline (build → scan → push → deploy)
├── docs/                     # IT support knowledge base
│   ├── password-account-issues.txt
│   ├── network-connectivity.txt
│   ├── kubernetes-devops.txt
│   └── hardware-laptop.txt
├── k8s/
│   └── deployment.yaml       # K8s Deployment + Service + HPA + Ingress
└── monitoring/
    └── grafana-dashboard.json
```

---

## 👤 About The Author

**Sumanth Kondru** — Senior DevOps Engineer transitioning to GenAI/MLOps Engineering

- 13+ years enterprise infrastructure experience
- Expert in Kubernetes (EKS/AKS), Docker, GitLab CI, Terraform, AWS/Azure
- Building GenAI applications combining LLM deployment with production-grade DevOps

📧 kondru.sumanth@gmail.com
🔗 linkedin.com/in/sumanth-kondru

---

## 🗺️ Roadmap

- [ ] Add Streamlit web UI for non-technical users
- [ ] Integrate with Slack for helpdesk bot
- [ ] Add MLflow experiment tracking for prompt optimization
- [ ] Fine-tune on company-specific IT documentation
- [ ] Add Redis caching for repeated questions (cost optimization)
- [ ] Multi-language support
