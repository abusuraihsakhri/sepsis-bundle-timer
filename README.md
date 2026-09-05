# Sepsis Bundle Timer

> **Domain:** Privacy-Preserving Healthcare & Federated Computing  
> **Reference Guidelines & Standards:** `HIPAA Safe Harbor §164.514 & Differential Privacy RDP`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Sepsis Bundle Compliance Timer — Surviving Sepsis 1h/3h bundle compliance timer from triage, lactate, and antibiotic timestamps. Provides a stdlib parser/mapper with batch CSV processing and single-lookup capabilities.

The project includes:
- **Core lookup engine** (`sepsis_timer.py`): Token-overlap + substring scoring for sepsis-related terms (lactate, antibiotics, fluids, vasopressors, etc.)
- **Enterprise agent framework** (`agents/`): Multi-worker evaluation system with PHI guard, HMAC-SHA256 audit trail, and FastAPI REST API
- **CLI** (`cli.py`): Command-line interface for audit, chat, batch processing, and server modes
- **Simulator** (`simulator.py`): High-throughput stress testing with adversarial PHI injection

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Functions

- **`lookup(query)`**: Single lookup using token overlap + substring scoring (no external dependencies). Returns top hits from a built-in sepsis terminology bank.
- **`process_csv(inp, out)`**: Batch CSV processing — reads input, looks up each row's query column, and writes enriched results.
- **`build_parser()`**: CLI argument parser for single and batch modes.

### 🛡️ Security & Audit

- **`PHIGuard`**: Zero-PHI outbound interceptor — blocks SSNs, MRNs, phone numbers, emails, and patient identifiers.
- **`AuditTrail`**: Tamper-evident HMAC-SHA256 chained audit log for every evaluation and state transition.
- **`SystemSupervisor`**: Multi-worker orchestrator with PHI validation on all inputs.

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/sepsis-bundle-timer.git
cd sepsis-bundle-timer

# Install dependencies
pip install fastapi uvicorn pydantic pytest

# Set audit secret (recommended for production)
export AUDIT_SECRET_KEY="your-secret-key-here"
```

---

## 🚀 Usage

### 1. Single Lookup (Core Module)
```bash
python -c "from sepsis_timer import lookup; print(lookup('lactate'))"
```

### 2. Batch CSV Processing (Core Module)
```bash
python -c "from sepsis_timer import process_csv; process_csv('sample.csv', 'output.csv')"
```

### 3. Enterprise CLI — Audit
```bash
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 4. Enterprise CLI — Batch
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 5. Enterprise CLI — Verify Audit Trail
```bash
python cli.py verify-audit
```

### 6. Enterprise CLI — Chat
```bash
python cli.py chat "What is the lactate threshold?"
```

### 7. Start REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### 8. Run Simulation
```bash
python simulator.py 100
```

---

## 📐 Lookup Scoring Logic

```text
score = 0
if key in query:           score += 10    # substring match
overlap = tokens(query) ∩ tokens(label)
score += overlap * 2                      # token overlap bonus
```

---

## 🛡️ Security Features

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, emails, DOB, and patient names.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **Path Traversal Protection:** All file paths are resolved and validated before access.
* **Input Validation:** All public functions validate inputs and raise clear errors.
* **Ephemeral Key Fallback:** When `AUDIT_SECRET_KEY` is not set, a random key is generated (with a warning) instead of using a hardcoded default.

---

## 🧪 Testing & Verification

Run the full test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest -v --cov=sepsis_timer --cov=agents
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker Compose
export AUDIT_SECRET_KEY="your-production-secret-key"
docker-compose up --build

# Or with Docker directly
docker build -t sepsis-bundle-timer .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY="your-key" sepsis-bundle-timer
```

---

## 📁 Project Structure

```
sepsis-bundle-timer/
├── agents/                  # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # PHI guard, audit trail, security
│   ├── learning.py         # Bayesian calibration engine
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics collector
│   ├── models.py           # Pydantic data models
│   ├── streamer.py         # WebSocket telemetry broadcaster
│   ├── supervisor.py       # Multi-worker orchestrator
│   └── workers.py          # Specialized evaluation workers
├── web/
│   └── index.html          # Web interface
├── cli.py                  # Enterprise CLI entry point
├── sepsis_timer.py         # Core lookup and CSV processing
├── simulator.py            # Stress testing simulator
├── enrichment.py           # Extended clinical feature engines
├── test_sepsis_timer.py    # Core module tests
├── test_sepsis_timer_extended.py  # Extended core tests
├── test_agents.py          # Agent framework tests
├── sample.csv              # Sample input data
├── Dockerfile              # Container build config
├── docker-compose.yml      # Container orchestration
└── openapi_spec.json       # OpenAPI 3.1 specification
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
