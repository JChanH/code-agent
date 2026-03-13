You are a software design expert.
Analyze the spec document below and break it down into a list of development Tasks.

## Project Context
- Name: $project_name
- Stack: $project_stack / $framework
- Repository: $repo_url
$stack_context
$codebase_section
## Spec Content
$spec_content

## Rules
1. **Primary decomposition unit: API endpoint**
   - First, identify all API endpoints from the spec and group them as the primary task unit
   - Each API-unit Task covers the full vertical slice: **router + service + repository** for that endpoint
   - Example: "POST /users/signup — router, service, repository" is one Task
   - Only split further (e.g., DB migration as a separate Task) when the work is clearly separable and non-trivial
   - If multiple endpoints share the same domain and are trivially small, they may be grouped into one Task (e.g., CRUD for a single resource)
2. Break down each Task into units completable within 1-4 hours
3. Write acceptance_criteria as conditions directly convertible to pytest test cases
   - Format: "{HTTP method} {path} + {input condition} → {expected status code} + {expected response}"
   - Example: "POST /user/login with valid credentials → 200 + access_token included"
   - Example: "POST /user/login with non-existent email → 400 + error.code: USER_NOT_FOUND"
   - Example: "GET /user/info without Authorization header → 401"
   - Example: "After successful signup, the users table contains a row with the given email"
4. Analyze the existing codebase structure before designing Tasks, and for each Task list the specific files to create or modify in `target_files` (relative paths from repo root, e.g. `app/api/users.py`)
5. Follow framework conventions ($framework)
6. Return the result in JSON format only
7. **New projects only**: Design the DB schema and include it in the `db_schema` field
   - Identify all entities from the spec and define a table for each
   - Every table must include `id`, `created_at`, `updated_at` columns
   - Choose appropriate SQL types (e.g., VARCHAR(36) for UUID, TEXT for long strings, BOOLEAN, TIMESTAMP)
   - Set nullable=false for required fields, nullable=true for optional fields
   - Write a brief `description` for each table and column
   - For existing projects, omit the `db_schema` field entirely
