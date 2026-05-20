import pytest
from pydantic import ValidationError

from src.schemas import TaskUpdate


def test_task_update_requires_at_least_one_field() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate()
