# Task: Build a REST API Server

Create a Flask REST API in `app.py` that manages a collection of **books**.

## Setup

A `requirements.txt` is provided. First install dependencies:
```bash
pip install -r requirements.txt
```

## Endpoints

### 1. `GET /books`
- Returns JSON array of all books
- Supports optional query parameter `?genre=fiction` to filter by genre (case-insensitive)
- Response: `200` with `[{"id": 1, "title": "...", "author": "...", "genre": "...", "year": 2024}, ...]`

### 2. `GET /books/<id>`
- Returns a single book by ID
- Response: `200` with book object, or `404` with `{"error": "not found"}`

### 3. `POST /books`
- Creates a new book
- Request body (JSON): `{"title": "...", "author": "...", "genre": "...", "year": 2024}`
- **Validation rules:**
  - `title` is required and must be a non-empty string
  - `author` is required and must be a non-empty string
  - `genre` is optional (defaults to `"unknown"`)
  - `year` is optional (defaults to current year), must be an integer between 1000 and 2100
- Response: `201` with created book (including auto-generated `id`), or `400` with `{"error": "..."}` on validation failure

### 4. `PUT /books/<id>`
- Updates an existing book (partial update — only provided fields are changed)
- Same validation rules as POST for provided fields
- Response: `200` with updated book, or `404` with `{"error": "not found"}`

### 5. `DELETE /books/<id>`
- Deletes a book by ID
- Response: `200` with `{"deleted": true}`, or `404` with `{"error": "not found"}`

### 6. `GET /stats`
- Returns statistics about the collection
- Response: `200` with `{"total": N, "by_genre": {"fiction": 3, "science": 2, ...}}`

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
