# Task: Extend the REST API Server (Phase 2 — Validation & Advanced Features)

An `app.py` already exists with basic CRUD endpoints (GET, POST, DELETE /books and GET /stats). Extend it with validation, partial updates, genre filtering, and full stats.

**Do not rewrite app.py from scratch.** Read the existing code and add the missing features.

## New/Modified Endpoints

### 1. `GET /books` — Add genre filtering
- Add optional query parameter `?genre=fiction` to filter by genre (case-insensitive)
- Example: `GET /books?genre=Fiction` returns only books with genre "fiction"
- Without the parameter, return all books (existing behavior)

### 2. `POST /books` — Add input validation
- `title` is required and must be a **non-empty string** (reject `""`)
- `author` is required and must be a **non-empty string** (reject missing or `""`)
- `year` must be an integer between **1000 and 2100** (reject values outside this range)
- Return `400` with `{"error": "..."}` on validation failure

### 3. `PUT /books/<id>` — New endpoint for partial updates
- Updates an existing book — only provided fields are changed
- Same validation rules as POST for any provided fields:
  - If `title` is provided, it must be non-empty
  - If `year` is provided, it must be 1000-2100
- Response: `200` with updated book, or `404` with `{"error": "not found"}`
- `400` with `{"error": "..."}` on validation failure

### 4. `GET /stats` — Full stats with genre breakdown
- Ensure stats returns `{"total": N, "by_genre": {"fiction": 3, "science": 2, ...}}`
- `by_genre` must reflect current state (updated after creates and deletes)

## Constraints

- Modify the existing `app.py` — do not create a new file
- Keep all existing functionality working
- Python 3.10+ compatible
