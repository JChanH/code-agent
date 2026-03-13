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
1. Break down each Task into units completable within 1-4 hours
2. Write acceptance_criteria as conditions directly convertible to pytest test cases
   - Format: "{HTTP method} {path} + {input condition} → {expected status code} + {expected response}"
   - Example: "POST /user/login with valid credentials → 200 + access_token included"
   - Example: "POST /user/login with non-existent email → 400 + error.code: USER_NOT_FOUND"
   - Example: "GET /user/info without Authorization header → 401"
   - Example: "After successful signup, the users table contains a row with the given email"
3. Analyze the existing codebase structure before designing Tasks
4. Follow framework conventions ($framework)
5. Return the result in JSON format only
