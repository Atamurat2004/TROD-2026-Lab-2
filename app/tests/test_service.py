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
        if task_id not in self.items:
            return False
        del self.items[task_id]
        return True


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


def test_service_replace_and_delete_success() -> None:
    service = TaskService(RepoStub())
    from src.schemas import TaskReplace, TaskStatus

    replaced = service.replace_task(
        1,
        TaskReplace(title="R", description=None, priority=2, status=TaskStatus.done),
    )
    assert replaced.id == 1

    service.delete_task(1)
    _expect_raises(TaskNotFoundError, lambda: service.delete_task(1))


def test_service_replace_and_update_not_found() -> None:
    class EmptyRepo(RepoStub):
        def replace_task(self, task_id, _payload):
            return None

        def update_task(self, task_id, _payload):
            return None

        def delete_task(self, task_id):
            return False

    broken = TaskService(EmptyRepo())
    from src.schemas import TaskReplace, TaskStatus

    _expect_raises(
        TaskNotFoundError,
        lambda: broken.replace_task(1, TaskReplace(title="x", description=None, priority=1, status=TaskStatus.todo)),
    )
    _expect_raises(TaskNotFoundError, lambda: broken.update_task(1, TaskUpdate(title="y")))
    _expect_raises(TaskNotFoundError, lambda: broken.delete_task(1))
