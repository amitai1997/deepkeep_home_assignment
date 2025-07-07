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

## API Reference

### Chat Endpoint

`POST /chat/{user_id}`

Send a message to OpenAI through the gateway with content moderation.

**Request:**
```json
{
  "message": "Hello, how can I help you?"
}
```

**Success Response (200):**
```json
{
  "response": "I'm here to help! What would you like to know?",
  "user_id": "alice"
}
```

**Blocked User Response (403):**
```json
{
  "detail": {
    "error": "User is blocked",
    "code": "USER_BLOCKED", 
    "details": "You have been temporarily blocked due to policy violations. Try again later or contact support."
  }
}
```

**Content Moderation:**
- Messages are checked for mentions of other user IDs in the system
- Users receive a "strike" for each violation
- After 3 strikes, users are blocked for 24 hours (configurable via `BLOCK_MINUTES`)
- Blocked users automatically unblock after the timeout period

### Admin Unblock Endpoint

`PUT /admin/unblock/{user_id}`

Manually unblock a user and reset their violation count.

**Success Response (200):**
```json
{
  "user_id": "alice",
  "violation_count": 0,
  "is_blocked": false,
  "blocked_until": null,
  "last_violation": "2024-01-15T10:30:00Z",
  "created_at": "2024-01-15T09:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z"
}
```

**User Not Found Response (404):**
```json
{
  "detail": {
    "error": "User not found",
    "code": "USER_NOT_FOUND",
    "details": "User alice does not exist in the system"
  }
}
```

### Example Usage

```bash
# Send a normal message
curl -X POST http://localhost:8000/chat/alice \
     -H 'Content-Type: application/json' \
     -d '{"message":"Hello world"}'

# Send a message with violation (mentioning another user)
curl -X POST http://localhost:8000/chat/alice \
     -H 'Content-Type: application/json' \
     -d '{"message":"Hey bob, how are you?"}'

# Check if user is blocked (after 3 violations)
curl -X POST http://localhost:8000/chat/alice \
     -H 'Content-Type: application/json' \
     -d '{"message":"Just a normal message"}'

# Manually unblock a user
curl -X PUT http://localhost:8000/admin/unblock/alice
```

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

## Design Decisions

### Three-Strike Policy
Users who violate content moderation rules (mentioning other users) receive strikes. After 3 strikes, they are temporarily blocked. This provides a balance between enforcement and giving users a chance to correct their behavior.

### Automatic Unblocking
Blocked users are automatically unblocked after a configurable timeout period (default: 24 hours). This is implemented by checking the `blocked_until` timestamp on each request, avoiding the need for background tasks or cron jobs.

### In-Memory Storage
User data is stored in memory for simplicity. This means data is lost on restart, but keeps the service self-contained and easy to deploy. For production use, this could be replaced with Redis or a database.

### Content Moderation
The current implementation checks if messages contain any other user IDs in the system. This is a simple rule that demonstrates the moderation framework and can be extended with more sophisticated checks.

## Running Tests

```bash
poetry run pytest -v
```

For coverage report:

```bash
poetry run pytest --cov=src --cov-report=html
```

## Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required unless using mock mode)
- `USE_MOCK_OPENAI`: Set to `1` to use mock OpenAI client
- `BLOCK_MINUTES`: Duration in minutes for user blocks (default: 1440 = 24 hours)

## License

MIT

