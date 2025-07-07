# Chat Gateway

Minimal FastAPI service used for the home assignment. The project is split into
`src/`, `tests/`, `docs/`, and `infra/` following the project plan.

## Quick start

```bash
docker compose -f infra/docker-compose.yml up -d --build
```

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

