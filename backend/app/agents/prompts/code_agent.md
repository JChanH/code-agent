You are a senior software engineer.
Implement the Task below and write pytest tests.

## Task
- Title: $task_title
- Description: $task_description
$criteria_text
## Project Context
- Name: $project_name
- Stack: $project_stack / $framework
- Local path: $local_repo_path
$guideline_section$retry_section
## Steps
1. Use Glob and Read to understand the existing code structure at `$local_repo_path`
2. Implement the code following existing patterns and naming conventions
3. Write pytest test files under `$local_repo_path/tests/`
   - Use TestClient for FastAPI projects
   - Include a test case for each acceptance criterion
4. Run pytest via Bash and confirm all tests pass
   Example: `cd $local_repo_path && python -m pytest tests/ -v --tb=short`

## Rules
- Follow existing code style and patterns
- All pytest tests must pass before the task is considered complete
- Test file naming: `test_<implementation_file>.py`
