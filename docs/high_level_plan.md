**1. Objectives & Constraints**  
Build a self-contained FastAPI microservice that (a) proxies chat requests to OpenAI, (b) enforces a 3‑strike blocking policy, (c) supports manual + automatic unblocking, and (d) ships with clear tests and docs. One developer, five days, using a lightweight PostgreSQL database for persistence, pure Python ≥3.12, docker‑runnable in a single command. Code must be idiomatic, async, type‑annotated, and simple enough for instant reviewer onboarding; non‑functional goals: 80 % test coverage, <200 ms p95 latency on local hardware.

---

**2. Proposed Tech Stack**

- **Runtime** – Python 3.12, FastAPI + Uvicorn (ASGI).  
- **Async HTTP** – HTTPX for OpenAI calls.  
- **Database** – PostgreSQL 16 accessed via SQLAlchemy async engine.
- **Testing** – Pytest, pytest‑asyncio, httpx `MockTransport`.  
- **Tooling** – Ruff (lint), Black (format), MyPy (type‑check), Pre‑commit.  
- **Packaging** – Poetry, Dockerfile, docker‑compose with a Postgres container.
- **CI** – GitHub Actions: lint, type‑check, tests.

---

**3. Architecture Diagram (ASCII)**  
```
┌──────────┐  POST /chat/{id}   ┌──────────────┐     ┌──────────────┐
│  Client  ├───────────────────►│  API Router  ├────►│ Service Layer│
└──────────┘                   └──────────────┘     └─────┬────────┘
       ▲             PUT /admin/unblock/{id}              │
       │                                                  │
       │                    ┌──────────────┐              │
       └────────────────────┤  Error JSON  │◄─────────────┘
                            └──────────────┘
                                    │ violates?
                                    ▼
                            ┌─────────────────┐
                             │PostgreSQL DB    │
                             └─────────────────┘
                                    │
                                    ▼
                          async ►┌────────┐
                                 │OpenAI  │
                                 └────────┘
```

---

**4. Directory Layout**

```
project/
├─ src/
│  ├─ api/          # FastAPI routers
│  ├─ models/       # Pydantic schemas
│  ├─ services/     # business logic & OpenAI client
│  ├─ db/           # SQLAlchemy models & session
│  ├─ core/         # settings, deps, error handling
│  └─ main.py       # app factory
├─ tests/           # unit + integration
├─ Dockerfile
├─ docker-compose.yml (includes Postgres)
├─ pyproject.toml
└─ README.md
```

---

**5. Key Components**

| Module | Role |
|--------|------|
| **core/config.py** | env var parsing (OpenAI key, block span). |
| **db/models.py** | ORM models for users. |
| **db/session.py** | Async database session factory. |
| **models/schemas.py** | Request/response & error DTOs. |
| **services/moderation.py** | Violation detection, strike counter. |
| **services/openai_client.py** | Thin async wrapper around HTTPX → OpenAI. |
| **api/chat.py** | `/chat/{user_id}` route, orchestrates moderation → OpenAI. |
| **api/admin.py** | `/admin/unblock/{user_id}` route. |
| **main.py** | FastAPI instance, lifespan events, middleware, OpenAPI tweaks. |
| **tests/** | isolated modules, fixture for DB session, mocked OpenAI. |

---

**6. Day‑by‑Day Plan (5 days)**

| Day | Focus | Checkpoints |
|-----|-------|-------------|
| **1** | Scaffolding & Tooling | directory layout, CI, Dockerfile, config class, empty FastAPI app starts. |
| **2** | Core Domain | Implement DB models and repository, moderation logic, happy‑path `/chat`. Unit tests ≥60 %. |
| **3** | Blocking Flows | Add strike logic, automatic‑unblock check, admin route; negative tests + 403 handling. |
| **4** | OpenAI Integration & Docs | Async client with retry/back‑off, env injection; update `/chat`; draft README, finish OpenAPI tags. |
| **5** | Hardening & Buffer | Load‑test with `locust`, improve p95 latency, reach 90 % coverage, polish README. Extra buffer ≈ 0.5 day for surprises. |

---

**7. Basic Test Strategy**

- **Unit**: pure functions (moderation, DB repository). Mock time with `freezegun`.
- **Service**: httpx `MockTransport` for OpenAI; FastAPI `TestClient` for routes.  
- **Integration**: docker‑compose job spins up FastAPI + Postgres containers with a stubbed OpenAI echo service.
- **Coverage gate**: fail CI <80 %.  

---

**8. README Outline**

1. **Project Overview** – what & why.  
2. **Quick Start**  
   ```bash
   docker build -t chat-gw . && docker run -p 8000:8000 -e OPENAI_API_KEY=sk-... chat-gw
   ```  
3. **API Reference** – schemas + curl samples.  
4. **Design Decisions** – strike policy, auto‑unblock rationale, async stack.  
5. **Running Tests** – `poetry run pytest -q`.  
6. **Extending** – switching to another database engine; adding auth.
7. **License & Contact**

---

**9. Risks & Mitigations**

- **Database downtime or misconfig** → document Postgres health checks and provide simple recovery steps.
- **Async edge‑cases (cancelled tasks, timeouts)** → retries + 3 s default timeout, circuit‑breaker decorator.  
- **OpenAI quota / downtime** → mock in tests; exponential back‑off in production calls.  
- **Schedule slip** → ½‑day buffer, CI gate blocks regressions early.
