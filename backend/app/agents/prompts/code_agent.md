You are a senior software engineer.
Implement the Task below. Tests will be written and executed by a separate review agent.

## Task
- Title: $task_title
- Description: $task_description
$criteria_text
## Project Context
- Name: $project_name
- Stack: $project_stack / $framework
- Local path: $local_repo_path
$guideline_section$target_files_section$retry_section
## Steps
1. Read the target files and their neighboring files to understand existing patterns
   - If no target files are specified above, use Glob to explore `$local_repo_path` first
2. Implement the code following existing patterns and naming conventions

## Rules
- Follow existing code style and patterns
- Do NOT write test files — tests are handled by the review agent
- Do NOT run pytest
