<p align="center">
  <img src="frontend/public/logo/PURPLECLAW-DARK.svg" width="120"/>
</p>

<h1 align="center">PurpleClaw</h1>

<p align="center">
  <b>SOC + NOC Security Validation Platform</b><br/>
  Detect • Score • Prioritize • Act
</p>

<p align="center">
  <img src="https://img.shields.io/badge/backend-FastAPI-009688" />
  <img src="https://img.shields.io/badge/frontend-React-61DAFB" />
  <img src="https://img.shields.io/badge/database-SQLite-blue" />
  <img src="https://img.shields.io/badge/docker-ready-blue" />
</p>

---

## Overview
PurpleClaw is a security validation platform that combines SOC + NOC visibility to identify vulnerabilities, misconfigurations, and risks across systems.

It is designed to help you understand:
- what is wrong
- how bad it is
- what should be fixed first
- which assets are riskiest

---

## Capabilities

- Collects telemetry (Prometheus)
- Detects:
  - vulnerabilities
  - misconfigurations
  - exposure risks
- Assigns risk scores (0–100)
- Prioritizes findings automatically

---

## Architecture

```text
Frontend (UI)
      │
      ▼
Backend (FastAPI)
      │
      ▼
Detection + Scoring Engine
      │
      ▼
Telemetry (Prometheus)
      │
      ▼
SQLite Database
```

---

🚀 6. Make “Run” Section Look Premium
## Run

```bash
docker compose up --build -d
```

- Service	URL

```UI	http://localhost:8080```

```API	http://localhost:8000/docs```

