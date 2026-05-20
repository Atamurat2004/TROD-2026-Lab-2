from src.database import Database
from src.schemas import TaskCreate, TaskReplace, TaskStatus, TaskUpdate


class TaskRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list_tasks(
        self,
        *,
        status: TaskStatus | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[dict]]:
        where_clauses: list[str] = []
        params: list[str | int] = []

        if status is not None:
            where_clauses.append("status = %s")
            params.append(status.value)

        if search:
            where_clauses.append("title ILIKE %s")
            params.append(f"%{search}%")

        where = ""
        if where_clauses:
            where = " WHERE " + " AND ".join(where_clauses)

        with self.database.cursor() as cur:
            count_query = f"SELECT COUNT(*) AS total FROM tasks{where}"
            cur.execute(count_query, tuple(params))
            total = int(cur.fetchone()["total"])

            list_query = f"""
                SELECT id, title, description, priority, due_date, status, created_at, updated_at
                FROM tasks
                {where}
                ORDER BY id
                LIMIT %s OFFSET %s
            """
            cur.execute(list_query, tuple(params + [limit, offset]))
            rows = cur.fetchall()
            return total, rows

    def get_task(self, task_id: int) -> dict | None:
        with self.database.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, description, priority, due_date, status, created_at, updated_at
                  FROM tasks
                 WHERE id = %s;
                """,
                (task_id,),
            )
            return cur.fetchone()

    def create_task(self, payload: TaskCreate) -> dict:
        with self.database.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (title, description, priority, due_date, status)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id, title, description, priority, due_date, status, created_at, updated_at;
                """,
                (
                    payload.title,
                    payload.description,
                    payload.priority,
                    payload.due_date,
                    payload.status.value,
                ),
            )
            return cur.fetchone()

    def replace_task(self, task_id: int, payload: TaskReplace) -> dict | None:
        with self.database.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                   SET title = %s,
                       description = %s,
                       priority = %s,
                       due_date = %s,
                       status = %s
                 WHERE id = %s
             RETURNING id, title, description, priority, due_date, status, created_at, updated_at;
                """,
                (
                    payload.title,
                    payload.description,
                    payload.priority,
                    payload.due_date,
                    payload.status.value,
                    task_id,
                ),
            )
            return cur.fetchone()

    def update_task(self, task_id: int, payload: TaskUpdate) -> dict | None:
        update_parts: list[str] = []
        params: list[str | int | None] = []

        if payload.title is not None:
            update_parts.append("title = %s")
            params.append(payload.title)
        if payload.description is not None:
            update_parts.append("description = %s")
            params.append(payload.description)
        if payload.priority is not None:
            update_parts.append("priority = %s")
            params.append(payload.priority)
        if payload.due_date is not None:
            update_parts.append("due_date = %s")
            params.append(payload.due_date)
        if payload.status is not None:
            update_parts.append("status = %s")
            params.append(payload.status.value)

        set_expression = ", ".join(update_parts)
        params.append(task_id)

        with self.database.cursor() as cur:
            cur.execute(
                f"""
                UPDATE tasks
                   SET {set_expression}
                 WHERE id = %s
             RETURNING id, title, description, priority, due_date, status, created_at, updated_at;
                """,
                tuple(params),
            )
            return cur.fetchone()

    def delete_task(self, task_id: int) -> bool:
        with self.database.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            return cur.fetchone() is not None
