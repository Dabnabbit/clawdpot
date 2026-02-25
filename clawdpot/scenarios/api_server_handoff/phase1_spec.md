# Task: Build a REST API Server (Phase 1 — Core CRUD)

Create a Flask REST API in `app.py` that manages a collection of **books**.

## Setup

A `requirements.txt` is provided. First install dependencies:
```bash
pip install -r requirements.txt
```

## Endpoints

### 1. `GET /books`
- Returns JSON array of all books
- Response: `200` with `[{"id": 1, "title": "...", "author": "...", "genre": "...", "year": 2024}, ...]`

### 2. `GET /books/<id>`
- Returns a single book by ID
- Response: `200` with book object, or `404` with `{"error": "not found"}`

### 3. `POST /books`
- Creates a new book
- Request body (JSON): `{"title": "...", "author": "...", "genre": "...", "year": 2024}`
- `title` and `author` are required
- `genre` is optional (defaults to `"unknown"`)
- `year` is optional (defaults to current year)
- Response: `201` with created book (including auto-generated `id`)

### 4. `DELETE /books/<id>`
- Deletes a book by ID
- Response: `200` with `{"deleted": true}`, or `404` with `{"error": "not found"}`

### 5. `GET /stats`
- Returns statistics about the collection
- Response: `200` with `{"total": N, "by_genre": {...}}`
- When empty: `{"total": 0, "by_genre": {}}`

## Requirements

- Use Flask (already in requirements.txt)
- In-memory storage only (no database)
- All responses must be JSON (use `Content-Type: application/json`)
- Auto-increment IDs starting from 1
- The app must be importable: `from app import app` (for testing)
- The app should also run standalone: `python app.py` starts on port 5000

## Constraints

- Single file: `app.py`
- Only dependencies from requirements.txt
- Python 3.10+ compatible
