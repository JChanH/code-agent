I now have all the information needed. Here is the complete guidemap document:

---

# Existing Project Guide

## Directory Guide

`backend/` — Root of the backend application; contains `main.py`, `run.py`, and `exceptions.py` at the top level.

`backend/router/` — FastAPI `APIRouter` handlers. Each file defines one `router` instance, registers HTTP endpoints, resolves auth via `Depends(get_current_user)`, calls the service layer, and wraps results in `ApiResponse.ok()`.

`backend/service/` — Business-logic layer. Implemented as module-level async functions (not classes). Services call repository methods, raise `BusinessException` subclasses on failure, and return domain-specific DTO/model objects.

`backend/repository/` — Data-access layer. Each file is a class with `@staticmethod` async methods that interact with the database through `db_conn.transaction()`. All write operations use `flush()` inside the transaction block.

`backend/models/db/` — SQLAlchemy ORM model definitions. Every table model inherits from `Base` (`models/db/base.py`). DDL is managed manually; the ORM handles reads and writes only.

`backend/models/result.py` — Shared HTTP response wrapper (`ApiResponse[T]` and `ErrorDetail`). Used project-wide by every router.

`backend/models/product_model/` — Pydantic DTOs for product-related request and response shapes.

`backend/models/ocr_model/` — Pydantic DTOs for OCR extraction results (nutrition, ingredients).

`backend/models/allergen_model/` — Pydantic DTOs for allergen detection results.

`backend/models/racc_model/` — Pydantic DTOs for RACC recommendation results.

`backend/models/label/` — Pydantic DTOs for label-specific data structures.

`backend/models/file_upload/` — Pydantic DTOs for file upload requests/responses.

`backend/models/user_model/` — Pydantic DTOs for user-related data.

`backend/dtos/` — Additional Pydantic DTOs, subdivided by domain (`ai/`, `label/`). Used for AI agent inputs/outputs and label processing data.

`backend/agents/` — LLM agent implementations (OCR, structuring, RACC, allergen, translation, Prop65). Each agent encapsulates a specific AI pipeline step.

`backend/agents/prompt/` — Prompt loading utilities and prompt-type enumerations used by agents.

`backend/cache/` — Redis-backed cache wrappers. `base.py` provides `BaseCache` (prefix + client access); domain caches (e.g., `auth_cache.py`, `user_cache.py`) subclass it.

`backend/core/` — Application infrastructure: config (`config.py`), startup/shutdown lifecycle (`lifespan.py`), global constants (`constants.py`), and auth dependency injection (`user_dependencies.py`).

`backend/utils/` — Shared utility modules: DB handler, Redis handler, JWT handler, email handler, file storage, image converter, OpenSearch handler, nutrition calculators, Prometheus handler.

`backend/tools/` — Standalone tools such as embedding generation (`embeddings.py`).

`backend/spec_generator/` — Scripts for exporting OpenAPI spec and generating DOCX specification documents.

`backend/scripts/` — One-off data migration / preparation scripts (e.g., product-name embedding generation).

`backend/tests/` — Test files (e.g., `test_ocr.py`).

---

## Naming Conventions

### File naming
- All file names use **snake_case**.
- Routers: `<domain>_router.py` (e.g., `product_router.py`)
- Services: `<domain>_service.py` (e.g., `product_service.py`, `ai_service.py`)
- Repositories: `<domain>_repo.py` (e.g., `product_repo.py`, `nutrition_facts_repo.py`)
- DB ORM models: plain noun, snake_case (e.g., `product.py`, `nutrition_fact.py`, `uploaded_file.py`)
- Pydantic DTOs: `<domain>_dto.py` (e.g., `product_dto.py`, `label_dto.py`, `prop65_dto.py`)
- Utility handlers: `<technology>_handler.py` (e.g., `db_handler_sqlalchemy.py`, `redis_handler.py`, `jwt_handler.py`)
- Agents: `<domain>_agent.py` (e.g., `ocr_agent.py`, `allergen_agent.py`)
- Caches: `<domain>_cache.py` (e.g., `auth_cache.py`, `user_cache.py`)

### Class naming
- All classes use **PascalCase**.
- Repository classes: `<Domain>Repository` (e.g., `ProductRepository`, `IngredientRepository`)
- ORM model classes: singular noun matching the table concept (e.g., `Product`, `NutritionFact`, `UploadedFile`)
- Exception classes: descriptive name ending in `Exception` or `Error` (e.g., `ProductNotFoundException`, `OCRProcessingError`)
- Pydantic DTO classes: `<Domain><Purpose>Request` / `<Domain><Purpose>Response` (e.g., `DetectProp65Request`, `ProductCreateResponse`)
- Utility/handler classes: `<Technology>Handler` or `<Technology>Manager` (e.g., `DBManager`, `RedisHandler`)
- Cache classes: `<Domain>Cache` (e.g., `BaseCache`, `AuthCache`)

### Method naming
- All methods use **snake_case**.
- Repository read methods: `find_by_<field>`, `find_all_by_<field>` (e.g., `find_by_id`, `find_all_by_product_id`)
- Repository write methods: `save`, `save_model`, `save_all_models`, `upsert`
- Service functions: verb-first descriptive name (e.g., `product_init`, `get_product_list`, `change_product_status`, `duplicate_product`)

---

## Response Format

**Class name and location:** `ApiResponse[T]` — `backend/models/result.py`. Also uses nested class `ErrorDetail` defined in the same file.

**Field names and their purpose:**

| Field | Type | Purpose |
|---|---|---|
| `success` | `bool` | `True` for successful responses, `False` for errors |
| `data` | `Optional[T]` | Payload on success; `None` on error |
| `error` | `Optional[ErrorDetail]` | Error detail object on failure; `None` on success |
| `error.message` | `str` | Human-readable error message |
| `error.code` | `str` | Machine-readable error code (typically the exception class name) |
| `error.path` | `Optional[str]` | Request URL path where the error occurred |

**Constructing responses:**
- **Success:** call `ApiResponse.ok(data=<payload>)` — sets `success=True`, populates `data`, leaves `error` as `None`.
- **Error:** call `ApiResponse.fail(message=<str>, code=<str>, path=<str|None>)` — sets `success=False`, populates `error`, leaves `data` as `None`.

---

## Exception Handling

**Base exception class:** `BusinessException` — `backend/exceptions.py` — `__init__(self, message: str, status_code: int = 400)`

**Pattern for raising exceptions:** Raise directly inside service functions or repository methods. `BusinessException` subclasses are caught by the `business_exception_handler` registered globally in `main.py`, which serialises them with `ApiResponse.fail()` using the exception's class name as `code` and the HTTP status from `exc.status_code`. Services re-raise `BusinessException` instances explicitly when re-caught inside broad `except Exception` blocks to prevent them being swallowed.

---

## DB / ORM Patterns

**ORM library:** SQLAlchemy async ORM with the `aiomysql` driver (`mysql+aiomysql://`), using `mapped_column` / `Mapped` typed declarations. All ORM models inherit from `Base` (`models/db/base.py`, extends `DeclarativeBase`).

**Transaction pattern:** `async with db_conn.transaction(session) as session` — if no session is passed a new session is created and auto-committed/rolled-back on exit; if an existing session is passed a savepoint (`begin_nested`) is used for nesting. The `db_conn` singleton (`DBManager`) is imported from `utils/db_handler_sqlalchemy.py`.

**Repository pattern:** All repository methods are `@staticmethod` async functions. Within a transaction block, writes always call `await session.flush()` (not `commit`) — the commit is delegated to the `DBManager` context manager at transaction boundary. No instance state is held; repositories are used by calling the class directly (e.g., `ProductRepository.save_model(...)`).

---

## Key Files Reference

| Relative Path | Description |
|---|---|
| `backend/main.py` | FastAPI app creation, CORS/logging middleware, global exception handlers, router registration, static file mount |
| `backend/run.py` | Uvicorn launch entry point; accepts `--workers`, `--host`, `--port` CLI args |
| `backend/core/config.py` | `Settings` class loading all env vars (DB, Redis, JWT, SMTP, LLM keys); exposes `settings` singleton |
| `backend/core/lifespan.py` | Async `lifespan` context manager that pings DB and Redis on startup and disposes resources on shutdown |
| `backend/core/constants.py` | Global HTTP status code and message string constants |
| `backend/core/user_dependencies.py` | `get_current_user` FastAPI dependency and `CurrentUser` dataclass for JWT-based auth injection |
| `backend/exceptions.py` | `BusinessException` base class and all domain exception subclasses |
| `backend/models/result.py` | `ApiResponse[T]` generic response wrapper and `ErrorDetail` — used in every router return type |
| `backend/utils/db_handler_sqlalchemy.py` | `DBManager` class (async SQLAlchemy engine + session factory, transaction context manager/decorator); exposes `db_conn` singleton |
| `backend/utils/redis_handler.py` | `RedisHandler` class (async Redis client lifecycle, `set_json`/`get_json`, pipeline); exposes `redis_conn` singleton |