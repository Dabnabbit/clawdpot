"""Task manager application with intentional bugs."""


class TaskManager:
    """Simple in-memory task manager."""

    def __init__(self):
        self._tasks: list[dict] = []
        self._next_id = 1

    def add_task(self, title: str, priority: int = 0) -> dict:
        """Add a new task and return it."""
        task = {
            "id": self._next_id,
            "title": title,
            "priority": priority,
            "completed": False,
        }
        self._next_id += 1
        self._tasks.append(task)
        return task

    def complete_task(self, task_id: int) -> bool:
        """Mark a task as completed. Returns True if found."""
        for task in self._tasks:
            if task["id"] == task_id:
                task["completed"] = True
                return True
        return False

    def get_pending(self) -> list[dict]:
        """Return uncompleted tasks sorted by priority (highest first)."""
        pending = [t for t in self._tasks if not t["completed"]]
        # BUG 4: Sorts ascending instead of descending (highest priority first)
        pending.sort(key=lambda t: t["priority"])
        return pending

    def search(self, query: str) -> list[dict]:
        """Case-insensitive search in task titles."""
        # BUG 5: Case-sensitive comparison — lowercases query but not title
        return [t for t in self._tasks if query.lower() in t["title"]]

    def stats(self) -> dict:
        """Return task statistics."""
        total = len(self._tasks)
        completed = sum(1 for t in self._tasks if t["completed"])
        return {
            "total": total,
            "completed": completed,
            "pending": total - completed,
        }
