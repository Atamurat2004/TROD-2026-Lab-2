from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse

from src.config import get_settings
from src.database import Database
from src.errors import TaskNotFoundError
from src.repository import TaskRepository
from src.schemas import ErrorResponse, TaskCreate, TaskListResponse, TaskRead, TaskReplace, TaskStatus, TaskUpdate
from src.service import TaskService

settings = get_settings()
database = Database(settings=settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env != "test":
        database.connect()
    yield
    if settings.app_env != "test":
        database.disconnect()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
    description="Sports store inventory API for Docker lab demonstration.",
)


def get_task_service() -> TaskService:
    return TaskService(TaskRepository(database))


@app.exception_handler(TaskNotFoundError)
async def handle_not_found(_: Request, exc: TaskNotFoundError):
    return JSONResponse(status_code=404, content=ErrorResponse(detail=str(exc)).model_dump())


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home_page() -> str:
    return """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Lab-1 Sports Store Inventory</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #0b1220; color: #e5e7eb; }
    .container { max-width: 1100px; margin: 0 auto; }
    .card { background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 16px; }
    h1, h2 { margin: 0 0 12px; }
    .grid { display: grid; grid-template-columns: 2fr 2fr 1fr 1fr; gap: 8px; }
    input, select, button { padding: 10px; border-radius: 8px; border: 1px solid #374151; background: #0f172a; color: #e5e7eb; }
    button { cursor: pointer; background: #2563eb; border: none; }
    button.secondary { background: #374151; }
    table { width: 100%; border-collapse: collapse; }
    th, td { border-bottom: 1px solid #1f2937; padding: 10px; text-align: left; }
    .muted { color: #9ca3af; font-size: 14px; }
    .row-actions { display: flex; gap: 8px; flex-wrap: wrap; }
  </style>
</head>
<body>
  <div class=\"container\">
    <div class=\"card\">
      <h1>Sports Store Product Panel</h1>
      <p class=\"muted\">Manage sport shop inventory in real time. API docs: <a href=\"/docs\" target=\"_blank\">/docs</a></p>
    </div>

    <div class=\"card\">
      <h2>Add product</h2>
      <div class=\"grid\">
        <input id=\"title\" placeholder=\"Product name (e.g., Nike Running Shoes)\" />
        <input id=\"description\" placeholder=\"Category / brand (e.g., Footwear)\" />
        <select id=\"priority\"><option>1</option><option>2</option><option selected>3</option><option>4</option><option>5</option></select>
        <select id=\"status\"><option value=\"todo\">in_stock</option><option value=\"in_progress\">low_stock</option><option value=\"done\">out_of_stock</option></select>
      </div>
      <div style=\"margin-top: 8px; display: flex; gap: 8px;\">
        <button onclick=\"createTask()\">Add product</button>
        <button class=\"secondary\" onclick=\"loadTasks()\">Refresh</button>
      </div>
    </div>

    <div class=\"card\">
      <h2>Products</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Name</th><th>Category</th><th>Availability</th><th>Stock (1-5)</th><th>Actions</th>
          </tr>
        </thead>
        <tbody id=\"tasksBody\"></tbody>
      </table>
    </div>
  </div>

  <script>
    function presentStatus(value) {
      if (value === 'todo') return 'in_stock';
      if (value === 'in_progress') return 'low_stock';
      return 'out_of_stock';
    }

    async function loadTasks() {
      const resp = await fetch('/products?limit=100&offset=0');
      const data = await resp.json();
      const body = document.getElementById('tasksBody');
      body.innerHTML = '';
      for (const t of data.items) {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${t.id}</td>
          <td>${t.title}</td>
          <td>${t.description ?? ''}</td>
          <td>${presentStatus(t.status)}</td>
          <td>${t.priority}</td>
          <td>
            <div class=\"row-actions\">
              <button onclick=\"updateStatus(${t.id}, 'todo')\">In stock</button>
              <button onclick=\"updateStatus(${t.id}, 'in_progress')\">Low stock</button>
              <button onclick=\"updateStatus(${t.id}, 'done')\">Out of stock</button>
              <button class=\"secondary\" onclick=\"removeTask(${t.id})\">Delete</button>
            </div>
          </td>
        `;
        body.appendChild(tr);
      }
    }

    async function createTask() {
      const payload = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value || null,
        priority: Number(document.getElementById('priority').value),
        status: document.getElementById('status').value,
      };
      const resp = await fetch('/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        alert('Failed to add product');
        return;
      }
      document.getElementById('title').value = '';
      document.getElementById('description').value = '';
      await loadTasks();
    }

    async function updateStatus(id, status) {
      const resp = await fetch(`/products/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status }),
      });
      if (!resp.ok) {
        alert('Failed to update product');
        return;
      }
      await loadTasks();
    }

    async function removeTask(id) {
      const resp = await fetch(`/products/${id}`, { method: 'DELETE' });
      if (!resp.ok) {
        alert('Failed to delete product');
        return;
      }
      await loadTasks();
    }

    loadTasks();
  </script>
</body>
</html>
    """


@app.get("/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    return {"status": "ok" if database.ping() else "degraded"}


@app.get("/tasks", response_model=TaskListResponse, tags=["tasks"])
def list_tasks(
    status: TaskStatus | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=settings.default_limit, ge=1, le=settings.max_limit),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
):
    return service.list_tasks(status=status, search=search, limit=limit, offset=offset)


@app.get("/tasks/{task_id}", response_model=TaskRead, responses={404: {"model": ErrorResponse}}, tags=["tasks"])
def get_task(task_id: int, service: TaskService = Depends(get_task_service)):
    return service.get_task(task_id)


@app.post("/tasks", response_model=TaskRead, status_code=201, tags=["tasks"])
def create_task(payload: TaskCreate, service: TaskService = Depends(get_task_service)):
    return service.create_task(payload)


@app.put("/tasks/{task_id}", response_model=TaskRead, responses={404: {"model": ErrorResponse}}, tags=["tasks"])
def replace_task(task_id: int, payload: TaskReplace, service: TaskService = Depends(get_task_service)):
    return service.replace_task(task_id, payload)


@app.patch("/tasks/{task_id}", response_model=TaskRead, responses={404: {"model": ErrorResponse}}, tags=["tasks"])
def patch_task(task_id: int, payload: TaskUpdate, service: TaskService = Depends(get_task_service)):
    return service.update_task(task_id, payload)


@app.delete("/tasks/{task_id}", status_code=204, responses={404: {"model": ErrorResponse}}, tags=["tasks"])
def delete_task(task_id: int, service: TaskService = Depends(get_task_service)):
    service.delete_task(task_id)


@app.get("/products", response_model=TaskListResponse, tags=["products"])
def list_products(
    status: TaskStatus | None = None,
    search: str | None = Query(default=None, min_length=1, max_length=255),
    limit: int = Query(default=settings.default_limit, ge=1, le=settings.max_limit),
    offset: int = Query(default=0, ge=0),
    service: TaskService = Depends(get_task_service),
):
    return service.list_tasks(status=status, search=search, limit=limit, offset=offset)


@app.get(
    "/products/{product_id}", response_model=TaskRead, responses={404: {"model": ErrorResponse}}, tags=["products"]
)
def get_product(product_id: int, service: TaskService = Depends(get_task_service)):
    return service.get_task(product_id)


@app.post("/products", response_model=TaskRead, status_code=201, tags=["products"])
def create_product(payload: TaskCreate, service: TaskService = Depends(get_task_service)):
    return service.create_task(payload)


@app.put(
    "/products/{product_id}", response_model=TaskRead, responses={404: {"model": ErrorResponse}}, tags=["products"]
)
def replace_product(product_id: int, payload: TaskReplace, service: TaskService = Depends(get_task_service)):
    return service.replace_task(product_id, payload)


@app.patch(
    "/products/{product_id}", response_model=TaskRead, responses={404: {"model": ErrorResponse}}, tags=["products"]
)
def patch_product(product_id: int, payload: TaskUpdate, service: TaskService = Depends(get_task_service)):
    return service.update_task(product_id, payload)


@app.delete("/products/{product_id}", status_code=204, responses={404: {"model": ErrorResponse}}, tags=["products"])
def delete_product(product_id: int, service: TaskService = Depends(get_task_service)):
    service.delete_task(product_id)
