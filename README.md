# Chat Gateway

Minimal FastAPI service used for the home assignment. The project is split into
`src/`, `tests/` and `infra/` following the project plan.

## Approach & Design Notes

This repository contains a self‑contained microservice that proxies user
messages to the OpenAI API while enforcing a three‑strike blocking policy.  The
design aims to be easy to read and run:

- **FastAPI + Uvicorn** provide an asynchronous HTTP server.
- **HTTPX** is used for non‑blocking calls to OpenAI.
- **PostgreSQL** (via SQLAlchemy) stores user state so blocks survive restarts.
- **Pytest** drives the test suite and uses an in‑memory SQLite database for
  speed.
- **Black**, **Ruff** and **MyPy** enforce consistent style and typing.

The code is organised under `src/` where routers, services and persistence
layers live.  `ModerationService` implements the strike logic, while
`UserRepository` handles user records.  Both endpoints are minimal:

- `POST /chat/{user_id}` – checks the message for other user IDs, increments the
  strike counter when needed and forwards valid text to OpenAI.
- `PUT /admin/unblock/{user_id}` – resets the counter and clears the block
  status.

Blocked users have a `blocked_until` timestamp.  Each chat request verifies if a
block has expired and automatically unblocks the user when the time window has
passed.  This avoids background tasks and keeps the service single‑process.

Docker and docker‑compose make the whole stack (API + Postgres) runnable with a
single command, so reviewers can start testing immediately.

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

The stack now includes a small PostgreSQL container used for persistence. Default
credentials live in `.env.example` and should be overridden in `.env`.

```bash
cp .env.example .env  # copy defaults then tweak values
```

Database tables are created automatically when the service starts up.

The compose file automatically builds the image and reads environment variables
from the project-level `.env` file.  If `OPENAI_API_KEY` is set there, the
service will run in **real** mode.  Set `USE_MOCK_OPENAI=1` (and omit the key)
to run entirely offline.

## Development

### Local setup without Docker Compose

1. **Create a dedicated dotenv for bare-metal work**

```bash
   cp .env.example .env.local  # start from the defaults
   ```

   Open `.env.local` and make sure it contains *at minimum*:

   ```dotenv
   USE_MOCK_OPENAI=1                                # echo mode – no API key needed
   DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/chatdb
   ```

2. **Launch a throw-away Postgres container that listens on localhost**

```bash
   docker run --rm -d -p 5432:5432 \
     -e POSTGRES_USER=user \
     -e POSTGRES_PASSWORD=pass \
     -e POSTGRES_DB=chatdb \
     --name pg-dev postgres:16
   ```

   The port mapping exposes Postgres on `localhost:5432`, matching the `DATABASE_URL` above.

3. **Install dependencies and start the FastAPI app**

```bash
   poetry install         # only needed once
   poetry run uvicorn src.main:app --reload --env-file .env.local
   ```

   `uvicorn` reads the variables from `.env.local`, so you keep your global
   environment clean.  If you previously exported conflicting variables (e.g.
   `DATABASE_URL` or `USE_MOCK_OPENAI`) make sure to `unset` them or start a
   fresh shell so that the env-file values win.

### Switching to real OpenAI locally

1. Comment-out `USE_MOCK_OPENAI` and add your key to `.env.local`:

   ```dotenv
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
   # USE_MOCK_OPENAI=1
   ```

2. Keep the same `uvicorn` command – the gateway will now proxy to OpenAI
   while still using the local Postgres.


## Strike Policy & Blocking

The service enforces a simple **three-strike** content-violation rule:

1. If your message references another user's ID, it counts as a strike.
2. On the **third** strike the request is still answered with HTTP 200, but the
   user is flagged as blocked.
3. Any subsequent request while blocked is rejected with HTTP 403.

Block duration is controlled by the `BLOCK_MINUTES` environment variable
(default **1440 min = 24 h**).  Once the timer expires the next request will
automatically unblock the user.

Example **403** error response:

```json
{
  "detail": {
    "error": "User is blocked",
    "code": "USER_BLOCKED",
    "details": "You have been temporarily blocked due to policy violations. Try again later or contact support."
  }
}
```

Use the admin endpoint to unblock manually:

```bash
curl -X PUT http://localhost:8000/admin/unblock/alice
```

### Additional environment variables

- `OPENAI_TIMEOUT` – request timeout in seconds (default `30`)
- `OPENAI_RETRIES` – number of retry attempts for OpenAI calls (default `3`)
- `DATABASE_URL` – SQLAlchemy URL for the Postgres instance
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` – credentials for the DB

## Load testing

A tiny [Locust](https://locust.io/) script is included for quick stress checks.
Start the stack (ideally in mock mode) and run:

```bash
locust -f locustfile.py --host http://localhost:8000
```

Open the browser at <http://localhost:8089> to launch users. The default task
repeatedly posts to `/chat/locust`.

## Test coverage

Running `poetry run pytest --cov=src` reports more than **90 %** coverage. The OpenAI
client connections are now cached and reused for better latency under load.

