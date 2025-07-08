# Chat Gateway

Minimal FastAPI service used for the home assignment. The project is split into
`src/`, `tests/`, `docs/`, and `infra/` following the project plan.

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

The stack now includes a small PostgreSQL container used for persistence. Default
credentials live in `.env.example` and can be overridden in `.env`.

Database tables are created automatically when the service starts up.

The compose file automatically builds the image and reads environment variables
from the project-level `.env` file.  If `OPENAI_API_KEY` is set there, the
service will run in **real** mode.  Set `USE_MOCK_OPENAI=1` (and omit the key)
to run entirely offline.

## Development

Install dependencies with Poetry and run the app:

```bash
poetry install
poetry run uvicorn src.main:app --reload
```

### Using the Mock OpenAI Client

Local development no longer requires a real OpenAI key.  Set

```bash
export USE_MOCK_OPENAI=1   # echoes your prompt instead of calling the API
# optional – suppress the key altogether
unset OPENAI_API_KEY

# run as usual
poetry run uvicorn src.main:app --reload
```

The service will return responses like `[MOCK] Echo: <your message>`, allowing
you to exercise moderation logic and chat routing without incurring usage
charges.

**Why**

* Speeds up local iterations – no network latency.
* Eliminates cost while writing tests or exploring the code.
* Keeps the same public interface, so switching back to the real API is just a
  matter of unsetting `USE_MOCK_OPENAI` and providing `OPENAI_API_KEY`.

### Running with Docker Compose – Real vs Mock

Real OpenAI mode (requires a valid key in `.env` or your shell):

```bash
# ensure OPENAI_API_KEY is exported or present in .env
docker compose -f infra/docker-compose.yml up -d
```

Mock mode (no key needed – echoes your prompt):

```bash
USE_MOCK_OPENAI=1 docker compose -f infra/docker-compose.yml up -d
```

Stop & remove the stack when finished:

```bash
docker compose -f infra/docker-compose.yml down
```

### Local Uvicorn – Real vs Mock

Real mode:

```bash
export OPENAI_API_KEY=<your-key>
poetry run uvicorn src.main:app --reload
```

Mock mode:

```bash
export USE_MOCK_OPENAI=1
poetry run uvicorn src.main:app --reload
```

### Example request

Send a chat message to verify the service is up (replace `alice` with any user id):

```bash
curl -X POST http://localhost:8000/chat/alice \
     -H 'Content-Type: application/json' \
     -d '{"message":"hello"}'
```

Expected output

* **Mock** – `{"response":"[MOCK] Echo: hello","user_id":"alice"}`
* **Real** – A natural-language answer from the OpenAI model.

Use these quick checks whenever you switch between modes to ensure the gateway is wired correctly.

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

Running `pytest --cov=src` reports more than **90 %** coverage. The OpenAI
client connections are now cached and reused for better latency under load.

