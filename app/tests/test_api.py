import os
from datetime import UTC, datetime

from fastapi.testclient import TestClient

os.environ["APP_ENV"] = "test"

from src.main import app, get_task_service  # noqa: E402
from src.schemas import TaskCreate, TaskListResponse, TaskRead, TaskReplace, TaskStatus, TaskUpdate  # noqa: E402


class InMemoryService:
    def __init__(self):
        self._items: dict[int, TaskRead] = {}
        self._next_id = 1

    def list_tasks(self, *, status, search, limit, offset):
        items = list(self._items.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        if search:
            items = [item for item in items if search.lower() in item.title.lower()]
        paginated = items[offset : offset + limit]
        return TaskListResponse(total=len(items), limit=limit, offset=offset, items=paginated)

    def get_task(self, task_id: int):
        item = self._items.get(task_id)
        if item is None:
            from src.errors import TaskNotFoundError

            raise TaskNotFoundError("Task not found")
        return item

    def create_task(self, payload: TaskCreate):
        now = datetime.now(UTC)
        item = TaskRead(
            id=self._next_id,
            title=payload.title,
            description=payload.description,
            priority=payload.priority,
            due_date=payload.due_date,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )
        self._items[self._next_id] = item
        self._next_id += 1
        return item

    def replace_task(self, task_id: int, payload: TaskReplace):
        current = self.get_task(task_id)
        item = current.model_copy(
            update={
                "title": payload.title,
                "description": payload.description,
                "priority": payload.priority,
                "due_date": payload.due_date,
                "status": payload.status,
                "updated_at": datetime.now(UTC),
            }
        )
        self._items[task_id] = item
        return item

    def update_task(self, task_id: int, payload: TaskUpdate):
        current = self.get_task(task_id)
        update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
        item = current.model_copy(update={**update_data, "updated_at": datetime.now(UTC)})
        self._items[task_id] = item
        return item

    def delete_task(self, task_id: int):
        if task_id not in self._items:
            from src.errors import TaskNotFoundError

            raise TaskNotFoundError("Task not found")
        del self._items[task_id]


def test_crud_flow():
    service = InMemoryService()
    app.dependency_overrides[get_task_service] = lambda: service

    with TestClient(app) as client:
        created = client.post(
            "/tasks",
            json={
                "title": "Prepare demo",
                "description": "Run docker compose and API checks",
                "priority": 2,
                "status": "todo",
            },
        )
        assert created.status_code == 201
        task_id = created.json()["id"]

        fetched = client.get(f"/tasks/{task_id}")
        assert fetched.status_code == 200
        assert fetched.json()["title"] == "Prepare demo"

        updated = client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
        assert updated.status_code == 200
        assert updated.json()["status"] == TaskStatus.in_progress.value

        listed = client.get("/tasks?status=in_progress&limit=10&offset=0")
        assert listed.status_code == 200
        assert listed.json()["total"] == 1
        assert listed.json()["items"][0]["id"] == task_id

        deleted = client.delete(f"/tasks/{task_id}")
        assert deleted.status_code == 204

        missing = client.get(f"/tasks/{task_id}")
        assert missing.status_code == 404

    app.dependency_overrides.clear()


def test_liveness_endpoint():
    with TestClient(app) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
