"""Judge tests for the api_server scenario.

20 tests covering CRUD, validation, filtering, and error handling.
Uses Flask's test client for fast, no-network testing.
"""

import sys
from pathlib import Path

import pytest

# Add workdir to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def client():
    """Create a Flask test client."""
    from app import app
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def sample_book():
    """A valid book payload."""
    return {"title": "Dune", "author": "Frank Herbert", "genre": "fiction", "year": 1965}


# --- GET /books (3 tests) ---

def test_list_books_empty(client):
    resp = client.get("/books")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_list_books_after_create(client, sample_book):
    client.post("/books", json=sample_book)
    resp = client.get("/books")
    assert resp.status_code == 200
    books = resp.get_json()
    assert len(books) == 1
    assert books[0]["title"] == "Dune"


def test_list_books_filter_genre(client, sample_book):
    client.post("/books", json=sample_book)
    client.post("/books", json={"title": "Cosmos", "author": "Carl Sagan", "genre": "science"})
    # Filter by genre (case-insensitive)
    resp = client.get("/books?genre=Fiction")
    books = resp.get_json()
    assert len(books) == 1
    assert books[0]["title"] == "Dune"


# --- GET /books/<id> (2 tests) ---

def test_get_book_exists(client, sample_book):
    create_resp = client.post("/books", json=sample_book)
    book_id = create_resp.get_json()["id"]
    resp = client.get(f"/books/{book_id}")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Dune"


def test_get_book_not_found(client):
    resp = client.get("/books/999")
    assert resp.status_code == 404
    assert "error" in resp.get_json()


# --- POST /books (6 tests) ---

def test_create_book_full(client, sample_book):
    resp = client.post("/books", json=sample_book)
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["id"] == 1
    assert data["title"] == "Dune"
    assert data["author"] == "Frank Herbert"
    assert data["genre"] == "fiction"
    assert data["year"] == 1965


def test_create_book_defaults(client):
    resp = client.post("/books", json={"title": "Test", "author": "Author"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["genre"] == "unknown"
    assert isinstance(data["year"], int)
    assert 2020 <= data["year"] <= 2100


def test_create_book_auto_id(client, sample_book):
    r1 = client.post("/books", json=sample_book)
    r2 = client.post("/books", json={"title": "Book2", "author": "Auth2"})
    assert r1.get_json()["id"] == 1
    assert r2.get_json()["id"] == 2


def test_create_book_missing_title(client):
    resp = client.post("/books", json={"author": "Author"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_create_book_empty_title(client):
    resp = client.post("/books", json={"title": "", "author": "Author"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_create_book_invalid_year(client):
    resp = client.post("/books", json={"title": "T", "author": "A", "year": 500})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# --- PUT /books/<id> (4 tests) ---

def test_update_book_partial(client, sample_book):
    create_resp = client.post("/books", json=sample_book)
    book_id = create_resp.get_json()["id"]
    resp = client.put(f"/books/{book_id}", json={"title": "Dune Messiah"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["title"] == "Dune Messiah"
    assert data["author"] == "Frank Herbert"  # unchanged


def test_update_book_not_found(client):
    resp = client.put("/books/999", json={"title": "X"})
    assert resp.status_code == 404


def test_update_book_invalid_year(client, sample_book):
    create_resp = client.post("/books", json=sample_book)
    book_id = create_resp.get_json()["id"]
    resp = client.put(f"/books/{book_id}", json={"year": 9999})
    assert resp.status_code == 400


def test_update_book_empty_title(client, sample_book):
    create_resp = client.post("/books", json=sample_book)
    book_id = create_resp.get_json()["id"]
    resp = client.put(f"/books/{book_id}", json={"title": ""})
    assert resp.status_code == 400


# --- DELETE /books/<id> (2 tests) ---

def test_delete_book(client, sample_book):
    create_resp = client.post("/books", json=sample_book)
    book_id = create_resp.get_json()["id"]
    resp = client.delete(f"/books/{book_id}")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] is True
    # Verify it's gone
    get_resp = client.get(f"/books/{book_id}")
    assert get_resp.status_code == 404


def test_delete_book_not_found(client):
    resp = client.delete("/books/999")
    assert resp.status_code == 404


# --- GET /stats (3 tests) ---

def test_stats_empty(client):
    resp = client.get("/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["by_genre"] == {}


def test_stats_with_books(client):
    client.post("/books", json={"title": "A", "author": "X", "genre": "fiction"})
    client.post("/books", json={"title": "B", "author": "Y", "genre": "fiction"})
    client.post("/books", json={"title": "C", "author": "Z", "genre": "science"})
    resp = client.get("/stats")
    data = resp.get_json()
    assert data["total"] == 3
    assert data["by_genre"]["fiction"] == 2
    assert data["by_genre"]["science"] == 1


def test_stats_after_delete(client):
    r = client.post("/books", json={"title": "A", "author": "X", "genre": "fiction"})
    book_id = r.get_json()["id"]
    client.delete(f"/books/{book_id}")
    resp = client.get("/stats")
    data = resp.get_json()
    assert data["total"] == 0
