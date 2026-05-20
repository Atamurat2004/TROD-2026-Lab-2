from contextlib import contextmanager
from datetime import UTC, datetime

from src.repository import TaskRepository
from src.schemas import TaskCreate, TaskReplace, TaskStatus, TaskUpdate

_ROW = {
    "id": 1,
    "title": "Football",
    "description": "Gear",
    "priority": 2,
    "due_date": None,
    "status": "todo",
    "created_at": datetime.now(UTC),
    "updated_at": datetime.now(UTC),
}


class RecordingCursor:
    def __init__(self, *, fetchone_results: list | None = None, fetchall_results: list | None = None) -> None:
        self.fetchone_results = list(fetchone_results or [])
        self.fetchall_results = list(fetchall_results or [])
        self.executed: list[tuple[str, tuple | None]] = []

    def execute(self, query: str, params=None) -> None:
        self.executed.append((query.strip(), params))

    def fetchone(self):
        return self.fetchone_results.pop(0) if self.fetchone_results else None

    def fetchall(self):
        return self.fetchall_results.pop(0) if self.fetchall_results else []


class FakeDatabase:
    def __init__(self, cursor: RecordingCursor) -> None:
        self._cursor = cursor

    @contextmanager
    def cursor(self):
        yield self._cursor


def test_repository_list_without_filters() -> None:
    cur = RecordingCursor(fetchone_results=[{"total": 1}], fetchall_results=[[_ROW]])
    repo = TaskRepository(FakeDatabase(cur))

    total, rows = repo.list_tasks(status=None, search=None, limit=10, offset=0)

    assert total == 1
    assert rows == [_ROW]
    assert "COUNT" in cur.executed[0][0]


def test_repository_list_with_status_and_search() -> None:
    cur = RecordingCursor(fetchone_results=[{"total": 0}], fetchall_results=[[]])
    repo = TaskRepository(FakeDatabase(cur))

    total, rows = repo.list_tasks(status=TaskStatus.done, search="nike", limit=5, offset=2)

    assert total == 0
    assert rows == []
    _, params = cur.executed[0]
    assert params == ("done", "%nike%")


def test_repository_get_task() -> None:
    cur = RecordingCursor(fetchone_results=[_ROW, None])
    repo = TaskRepository(FakeDatabase(cur))

    assert repo.get_task(1) == _ROW
    assert repo.get_task(999) is None


def test_repository_create_task() -> None:
    cur = RecordingCursor(fetchone_results=[_ROW])
    repo = TaskRepository(FakeDatabase(cur))
    payload = TaskCreate(title="Ball", description=None, priority=1, status=TaskStatus.todo)

    created = repo.create_task(payload)

    assert created["title"] == "Football"
    assert cur.executed[0][1][0] == "Ball"


def test_repository_replace_and_update() -> None:
    cur = RecordingCursor(fetchone_results=[_ROW, _ROW])
    repo = TaskRepository(FakeDatabase(cur))
    replace = TaskReplace(title="New", description="d", priority=4, status=TaskStatus.in_progress)

    assert repo.replace_task(1, replace) == _ROW

    cur2 = RecordingCursor(fetchone_results=[_ROW])
    repo2 = TaskRepository(FakeDatabase(cur2))
    updated = repo2.update_task(1, TaskUpdate(title="X", priority=2))

    assert updated == _ROW
    assert "title = %s" in cur2.executed[0][0]


def test_repository_delete_task() -> None:
    cur_ok = RecordingCursor(fetchone_results=[{"id": 1}])
    repo_ok = TaskRepository(FakeDatabase(cur_ok))
    assert repo_ok.delete_task(1) is True

    cur_miss = RecordingCursor(fetchone_results=[None])
    repo_miss = TaskRepository(FakeDatabase(cur_miss))
    assert repo_miss.delete_task(99) is False
