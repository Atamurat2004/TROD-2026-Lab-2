from datetime import UTC, datetime

from src.errors import TaskNotFoundError
from src.schemas import TaskCreate, TaskStatus, TaskUpdate
from src.service import TaskService


class RepoStub:
    def __init__(self):
        self.items = {
            1: {
                "id": 1,
                "title": "Task",
                "description": None,
                "priority": 3,
                "due_date": None,
                "status": "todo",
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
        }

    def list_tasks(self, **_kwargs):
        return 1, [self.items[1]]

    def get_task(self, task_id: int):
        return self.items.get(task_id)

    def create_task(self, payload: TaskCreate):
        return {
            "id": 2,
            "title": payload.title,
            "description": payload.description,
            "priority": payload.priority,
            "due_date": payload.due_date,
            "status": payload.status.value,
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

    def replace_task(self, task_id, _payload):
        return self.items.get(task_id)

    def update_task(self, task_id, _payload):
        return self.items.get(task_id)

    def delete_task(self, task_id):
        return task_id in self.items


def _expect_raises(exc_type, fn):
    try:
        fn()
    except exc_type:
        return
    raise AssertionError(f"Expected {exc_type.__name__} to be raised")


def test_service_create():
    service = TaskService(RepoStub())
    item = service.create_task(TaskCreate(title="new", description=None, priority=1, status=TaskStatus.todo))
    assert item.id == 2
    assert item.status == TaskStatus.todo


def test_service_not_found():
    service = TaskService(RepoStub())
    _expect_raises(TaskNotFoundError, lambda: service.get_task(999))


def test_service_list():
    service = TaskService(RepoStub())
    response = service.list_tasks(status=None, search=None, limit=10, offset=0)
    assert response.total == 1
    assert response.items[0].id == 1


def test_service_update_not_found():
    service = TaskService(RepoStub())
    _expect_raises(TaskNotFoundError, lambda: service.update_task(999, TaskUpdate(title="x")))
