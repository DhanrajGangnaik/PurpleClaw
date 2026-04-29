<p align="center">
  <img src="frontend/public/logo/PURPLECLAW-DARK.svg" width="120"/>
</p>

<h1 align="center">PurpleClaw</h1>

<p align="center">
  <b>Unified Purple Team Security Operations Platform</b><br/>
  Red Team · Blue Team · SOC · NOC · Threat Intel · Compliance
</p>

<p align="center">
  <img src="https://img.shields.io/badge/backend-FastAPI-009688" />
  <img src="https://img.shields.io/badge/frontend-React-61DAFB" />
  <img src="https://img.shields.io/badge/database-SQLite-blue" />
  <img src="https://img.shields.io/badge/docker-ready-2496ED" />
  <img src="https://img.shields.io/badge/license-MIT-green" />
</p>

---

## Quick Start

```bash
git clone https://github.com/DhanrajGangnaik/PurpleClaw.git
cd PurpleClaw
docker compose up --build -d
```

| Service | URL |
|---------|-----|
| UI | http://localhost:8080 |
| API Docs | http://localhost:8000/docs |

**Default credentials:** `admin` / `admin`

---

## What Is PurpleClaw?

PurpleClaw is a self-hosted purple team platform that combines offensive and defensive security operations in a single dashboard. It lets small security teams run attack simulations, detect threats, manage vulnerabilities, and measure compliance — all from one place.

---

## Pages

| Section | Page | Route |
|---------|------|-------|
| **Operations** | Dashboard | `/` |
| | Alerts | `/soc/alerts` |
| | Incidents | `/soc/incidents` |
| | Cases | `/soc/cases` |
| | SIEM | `/soc/siem` |
| **Network & Assets** | Assets | `/noc/assets` |
| | Network | `/noc/network` |
| **Red Team** | Attack Plans | `/redteam/plans` |
| | Executions | `/redteam/executions` |
| | Recon | `/redteam/recon` |
| | Payloads | `/redteam/payloads` |
| **Blue Team** | Detection Rules | `/blueteam/rules` |
| | Threat Hunting | `/blueteam/hunting` |
| | EDR Events | `/blueteam/edr` |
| | FIM | `/blueteam/fim` |
| **Purple Team** | Exercises | `/purpleteam/exercises` |
| | ATT&CK Coverage | `/purpleteam/coverage` |
| **Threat Intel** | IOCs | `/intel/iocs` |
| | Threat Actors | `/intel/actors` |
| | Campaigns | `/intel/campaigns` |
| | Feeds | `/intel/feeds` |
| **Vulnerabilities** | Vulnerabilities | `/vulns/list` |
| | Findings | `/vulns/findings` |
| | Scans | `/vulns/scans` |
| **Incident Response** | Playbooks | `/ir/playbooks` |
| | IR Executions | `/ir/executions` |
| **Compliance** | Frameworks | `/compliance/frameworks` |
| **Platform** | Reports | `/reports` |
| | Users | `/settings/users` |
| | Audit Log | `/settings/audit` |
| | System | `/settings/system` |
| | Engine Status | `/settings/engine` |

---

## Architecture

```
Browser (React + Vite)
        │  HTTP / REST
        ▼
   nginx :80 → :8080
        │  proxy /api/v1/
        ▼
  FastAPI :8000
        │  SQLAlchemy ORM
        ▼
   SQLite (./data/purpleclaw.db)
```

The autonomous engine runs background jobs that:
1. Discover services on the configured network range
2. Generate threat assessments and alerts
3. Execute auto-response actions (configurable level)

---

## Environment Variables

Set these in `docker-compose.yml` or a `.env` file in the project root.

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `changeme` | JWT signing key — **change in production** |
| `SEED_DEMO_DATA` | `true` | Populate the database with demo data on first start |
| `SCAN_NETWORK_ENABLED` | `false` | Enable live network scanning |
| `AUTO_RESPONSE_ENABLED` | `false` | Enable autonomous threat response |
| `AUTO_RESPONSE_LEVEL` | `low` | Response aggressiveness: `low` / `medium` / `high` |
| `NETWORK_RANGE` | `192.168.1.0/24` | CIDR range for asset discovery |
| `DATABASE_URL` | `sqlite:///./data/purpleclaw.db` | SQLAlchemy database URL |

---

## Development

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev        # dev server on :5173
npm run build      # production build → dist/
npm run typecheck  # tsc --noEmit
```

---

## Optional Integrations

| Integration | How to enable |
|-------------|---------------|
| **Prometheus metrics** | Scrape `http://localhost:8000/metrics` |
| **Loki / Grafana** | Point Loki at container stdout; import the bundled dashboard |
| **Kubernetes** | Use the `k8s/` manifests (replace SQLite with Postgres via `DATABASE_URL`) |

---

## License

MIT — see [LICENSE](LICENSE).
