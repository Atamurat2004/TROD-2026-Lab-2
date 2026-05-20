from src.errors import TaskNotFoundError
from src.repository import TaskRepository
from src.schemas import TaskCreate, TaskListResponse, TaskRead, TaskReplace, TaskStatus, TaskUpdate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def list_tasks(
        self,
        *,
        status: TaskStatus | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> TaskListResponse:
        total, items = self.repository.list_tasks(
            status=status,
            search=search,
            limit=limit,
            offset=offset,
        )
        return TaskListResponse(total=total, limit=limit, offset=offset, items=items)

    def get_task(self, task_id: int) -> TaskRead:
        task = self.repository.get_task(task_id)
        if task is None:
            raise TaskNotFoundError("Task not found")
        return TaskRead(**task)

    def create_task(self, payload: TaskCreate) -> TaskRead:
        return TaskRead(**self.repository.create_task(payload))

    def replace_task(self, task_id: int, payload: TaskReplace) -> TaskRead:
        task = self.repository.replace_task(task_id, payload)
        if task is None:
            raise TaskNotFoundError("Task not found")
        return TaskRead(**task)

    def update_task(self, task_id: int, payload: TaskUpdate) -> TaskRead:
        task = self.repository.update_task(task_id, payload)
        if task is None:
            raise TaskNotFoundError("Task not found")
        return TaskRead(**task)

    def delete_task(self, task_id: int) -> None:
        deleted = self.repository.delete_task(task_id)
        if not deleted:
            raise TaskNotFoundError("Task not found")
