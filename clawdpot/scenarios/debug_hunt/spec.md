# Task: Debug Hunt

The files `app.py` and `utils.py` in the current directory contain **5 bugs** that cause the test suite to fail. Your job is to find and fix all 5 bugs.

## Rules

1. **Only modify `app.py` and `utils.py`** — do not create new files or modify test files
2. Do not rewrite the files from scratch — fix the specific bugs
3. All existing function signatures must stay the same
4. The test suite in `tests/` is the source of truth — make the tests pass

## What the code should do

### `utils.py`
- `slugify(text: str) -> str` — Convert text to URL-friendly slug (lowercase, hyphens, strip leading/trailing hyphens)
- `truncate(text: str, max_len: int) -> str` — Truncate text to max_len chars, adding "..." if truncated. The "..." counts toward max_len.
- `parse_csv_line(line: str) -> list[str]` — Parse a single CSV line respecting quoted fields

### `app.py`
- `TaskManager` class with:
  - `add_task(title: str, priority: int = 0) -> dict` — Add a task, return it
  - `complete_task(task_id: int) -> bool` — Mark task complete, return success
  - `get_pending() -> list[dict]` — Return uncompleted tasks sorted by priority (highest first)
  - `search(query: str) -> list[dict]` — Case-insensitive search in task titles
  - `stats() -> dict` — Return {"total": N, "completed": N, "pending": N}

## Hints

The bugs are subtle — look for:
- Off-by-one errors
- Wrong comparison operators
- Missing edge case handling
- Incorrect string operations
- Logic inversions
