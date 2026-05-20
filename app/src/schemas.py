from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    priority: int = Field(default=3, ge=1, le=5)
    due_date: date | None = None
    status: TaskStatus = TaskStatus.todo


class TaskCreate(TaskBase):
    pass


class TaskReplace(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    priority: int | None = Field(default=None, ge=1, le=5)
    due_date: date | None = None
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def validate_at_least_one_field(self):
        if (
            self.title is None
            and self.description is None
            and self.priority is None
            and self.due_date is None
            and self.status is None
        ):
            raise ValueError("At least one field must be provided for update")
        return self


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[TaskRead]


class ErrorResponse(BaseModel):
    detail: str
