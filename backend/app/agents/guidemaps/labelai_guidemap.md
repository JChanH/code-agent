I now have all the information needed to compile the guidemap. Here is the complete markdown:

---

# Existing Project Guide

## Directory Guide

```
backend/                        — Application root; contains main.py, run.py, exceptions.py, requirements.txt
backend/core/                   — App-wide infrastructure: config, constants, lifespan, auth dependency
backend/router/                 — FastAPI APIRouter handlers; one file per domain, assembled in __init__.py
backend/service/                — Business logic layer; module-level async functions (no class wrapper)
backend/repository/             — Data access layer; classes with static async methods backed by SQLAlchemy
backend/models/db/              — SQLAlchemy ORM model definitions (one class per table, all inherit Base)
backend/models/result.py        — Shared ApiResponse[T] generic wrapper (single file, not a directory)
backend/models/product_model/   — Pydantic request/response DTOs for the product domain
backend/models/user_model/      — Pydantic request/response DTOs for the user domain
backend/models/ocr_model/       — Pydantic DTOs for OCR extraction results
backend/models/racc_model/      — Pydantic DTOs for RACC recommendation results
backend/models/allergen_model/  — Pydantic DTOs for allergen detection results
backend/models/file_upload/     — Pydantic DTOs for file upload requests
backend/models/label/           — Pydantic DTOs for label assembly output
backend/dtos/ai/                — DTOs for AI agent output (e.g. RACC, Prop65 recommendations)
backend/dtos/label/             — DTOs for label-level structured data (product info, label reasons)
backend/agents/                 — LLM agent wrappers (one file per AI capability)
backend/agents/prompt/          — Prompt file loader and prompt type enum
backend/cache/                  — Redis cache layer; BaseCache base class + domain-specific cache classes
backend/utils/                  — Shared utility modules: DB, Redis, JWT, email, file storage, calculations
backend/tools/                  — Low-level tool integrations (e.g. OpenSearch embeddings)
backend/scripts/                — One-off operational scripts (e.g. seeding embeddings to OpenSearch)
backend/spec_generator/         — OpenAPI spec export and DOCX report generation utilities
backend/tests/                  — pytest test files
```

---

## Naming Conventions

### File Naming
- All files use **snake_case**.
- Suffix rules by layer:
  - Routers: `*_router.py`
  - Services: `*_service.py`
  - Repositories: `*_repo.py`
  - ORM models: plain noun (e.g. `product.py`, `user.py`)
  - Pydantic DTOs: `*_dto.py`
  - Agents: `*_agent.py`
  - Utilities/handlers: `*_handler.py`
- The shared response wrapper is a standalone file: `models/result.py`
- The base exception file is a standalone file: `exceptions.py`

### Class Naming
- **PascalCase** throughout.
- Repository classes end with `Repository` (e.g. `ProductRepository`, `ApiLogRepository`).
- ORM model classes use plain domain nouns (e.g. `Product`, `NutritionFact`, `Ingredient`).
- Cache classes end with `Cache` (e.g. `AuthCache`, `UserCache`); base is `BaseCache`.
- Exception classes end with `Exception` or `Error` (e.g. `BusinessException`, `OCRProcessingError`).
- Pydantic DTO response classes typically end with `Response` or `Request` (e.g. `ProductCreateResponse`, `ProductListGetResponse`).
- Infrastructure managers use `Manager` or `Handler` (e.g. `DBManager`, `RedisHandler`).

### Method Naming
- **snake_case** throughout.
- Repository methods follow CRUD conventions: `save`, `save_model`, `save_all_models`, `find_by_id`, `find_by_user_id`, `find_all_by_product_id`, `upsert`, `update_*`.
- Service functions are module-level `async def` with descriptive verb-noun names (e.g. `product_init`, `get_product_list`, `change_product_status`, `duplicate_product`).
- Router handler functions mirror the service function names they delegate to.

---

## Response Format

- **Class name and location:** `ApiResponse[T]` — `backend/models/result.py`
- This class is a generic Pydantic `BaseModel` parameterised by `TypeVar T`.
- **Fields:**
  - `success: bool` — `True` on success, `False` on any error
  - `data: Optional[T]` — payload on success; `None` on error
  - `error: Optional[ErrorDetail]` — populated on error; `None` on success
    - `ErrorDetail.message: str` — human-readable error description
    - `ErrorDetail.code: str` — machine-readable error code (typically the exception class name)
    - `ErrorDetail.path: Optional[str]` — request URL path where the error occurred
- **Constructing a success response:** call `ApiResponse.ok(data=<payload>)`
- **Constructing an error response:** call `ApiResponse.fail(message=<str>, code=<str>, path=<str|None>)`
- Routers always return `ApiResponse.ok(data=result)` after delegating to the service; error responses are produced exclusively in `main.py` exception handlers by calling `ApiResponse.fail(...)`.

---

## Exception Handling

- **Base exception class:** `BusinessException` — `backend/exceptions.py` — `__init__(self, message: str, status_code: int = 400)`
- All domain exception subclasses extend `BusinessException` and fix a `status_code` in their own `__init__`, accepting only a `message` argument.
- **Pattern for raising:** exceptions are raised directly inside service functions and repository methods (no try/except suppression for business errors); the service layer re-raises `BusinessException` subclasses and wraps unexpected lower-level exceptions in a plain `Exception` or `BusinessException`.
- **Handling in main.py:** three global handlers registered on the `FastAPI` app instance:
  1. `BusinessException` → returns `ApiResponse.fail(...)` with `exc.status_code`
  2. `RequestValidationError` → returns `ApiResponse.fail(...)` with HTTP 400 and code `"VALIDATION_ERROR"`
  3. `Exception` (catch-all) → returns `ApiResponse.fail(...)` with HTTP 500 and code `"InternalServerError"`

---

## DB / ORM Patterns

- **ORM library:** SQLAlchemy (async) with the `aiomysql` driver; models use `DeclarativeBase` (`Base` in `models/db/base.py`) and `Mapped`/`mapped_column` typed columns.
- **Transaction pattern:** `async with db_conn.transaction(session) as session:` — if `session` is `None` a new session and `BEGIN` are created automatically; if an existing session is passed, a `SAVEPOINT` (nested transaction) is used; the context manager auto-commits on clean exit and auto-rolls back on exception.
- **Repository pattern:** all repository methods are `@staticmethod` async functions; they call `flush()` (not `commit()`) inside the `transaction()` context manager because `commit` is handled by the context manager on exit; an optional `session` parameter allows callers to compose multiple repository calls inside a single outer transaction (see `product_service.duplicate_product`).

---

## Key Files Reference

| Relative Path | Description |
|---|---|
| `backend/main.py` | FastAPI app factory; registers CORS middleware, API-log middleware, all three global exception handlers, and all routers |
| `backend/run.py` | Uvicorn startup script; parses `--workers`, `--host`, `--port` CLI args and calls `uvicorn.run("main:app", ...)` |
| `backend/core/config.py` | `Settings` class that reads all environment variables via `python-dotenv`; exposes singleton `settings` instance |
| `backend/core/lifespan.py` | FastAPI `lifespan` context manager; pings DB and both Redis connections on startup, disposes them on shutdown |
| `backend/core/constants.py` | Global HTTP status code integers and success/failure string constants |
| `backend/core/user_dependencies.py` | `get_current_user` FastAPI dependency + `CurrentUser` data class; extracts and validates JWT Bearer token |
| `backend/models/result.py` | `ApiResponse[T]` generic Pydantic wrapper with `ok()` and `fail()` class methods; `ErrorDetail` nested model |
| `backend/models/db/base.py` | SQLAlchemy `Base(DeclarativeBase)` shared by all ORM models; provides `to_dict()` helper |
| `backend/utils/db_handler_sqlalchemy.py` | `DBManager` class with `get_db()`, `transaction()`, and `transaction_decorator()`; singleton `db_conn` instance |
| `backend/utils/redis_handler.py` | `RedisHandler` class with `get_client()`, `set_json()`, `get_json()`, `ping()`; singletons `redis_conn` and `redis_error_conn` |