# AI Tech Consultant
**BusinessLabs / Anthropic Applied AI Engineering Capstone — October 2026**

The **AI Tech Consultant** is a production-grade, testable enterprise system designed to automate technical consulting, customer email triage, and commercial project scoping for the **Brilliant Directories** ecosystem.

---

## Architecture Summary

The application is composed of three decoupled microservices communicating over HTTP, backed by PostgreSQL + pgvector and surfaced via a responsive React dashboard:

1. **Task 1: Knowledge Brain (Python / FastAPI)**: The central knowledge hub. Features polite sitemap crawling, multimodal screenshot extraction, pgvector hybrid search, grounded RAG answering with verifiable citations, daily incremental delta sync, and human escalation ticket queues.
2. **Task 2: Inbox Agent (TypeScript / Node.js)**: Customer email classification and drafting agent. Consumes Task 1 solely via its HTTP API. Enforces financial safety guards, refusal of unauthorized pricing/refunds, and implements the **20-consecutive-unchanged-send autonomy engine**.
3. **Task 3: Meeting to Scope of Work (Python / FastAPI)**: A controlled multi-agent pipeline (`Transcript Analyst` → `Product Feasibility` → `Scope Agent` → `Estimation Agent` → `Proposal Agent` → `Scope Diff Agent`). Compares follow-up meetings against baselines and enforces strict backend human approval gates before proposals can be sent.
4. **Shared Dashboard (React + Vite + TypeScript)**: Responsive UI providing visibility into evidence citations, email drafting, 20-send streak tracking, 3-point hour estimates, and scope diffs.

---

## Quickstart & One-Command Startup

### Prerequisites
- Docker and Docker Compose (Docker 24+)
- Or for local native development: Python 3.12+ (or `uv`), Node.js 20+

### One-Command Startup
```bash
# 1. Clone repository and enter project root
cd ai-tech-consultant

# 2. Copy environment template
cp .env.example .env

# 3. Start all services via Docker Compose
docker compose up --build
```

### Access URLs
- **Web Dashboard**: http://localhost:3000
- **Task 1 Knowledge Brain API**: http://localhost:8001 (Swagger docs: http://localhost:8001/docs)
- **Task 2 Inbox Agent API**: http://localhost:8002
- **Task 3 Meeting to Scope API**: http://localhost:8003 (Swagger docs: http://localhost:8003/docs)

---

## Running the Automated Test Suites

All tests run reproducibly without requiring live external API credits:

```bash
# Run Task 1 tests (Pytest - 16 unit & integration tests)
cd task1-knowledge-brain
pytest tests

# Run Task 2 tests (Vitest - 12 unit & autonomy engine tests)
cd ../task2-inbox-agent
npm test

# Run Task 3 tests (Pytest - 8 multi-agent & approval tests)
cd ../task3-meeting-to-scope
pytest tests

# Run Full Evaluation Benchmark & Model Comparison (69 total test cases)
cd ..
python scripts/run_evaluations.py
```

---

## Key Business Safeguards & Limitations

- **Autonomy Safety Gate**: High-risk categories (`refund_cancellation`, `complaint_urgent`, `quote_request`, `adversarial_injection`) are permanently locked from autonomous sending, regardless of counter streaks.
- **Commercial Approval Gate**: Backend logic forbids commercial proposal dispatch without human reviewer sign-off.
- **Grounding Fidelity**: When knowledge evidence is insufficient, Task 1 abstains honestly and generates an escalation ticket rather than hallucinating.
