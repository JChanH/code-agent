"""Default security profiles per project stack.

These define which commands and file paths are allowed/blocked
when the agent operates within a user's worktree.
"""

DEFAULT_PROFILES: dict[str, dict] = {
    "python": {
        "allowed_commands": [
            "pip install", "pip list", "pip freeze",
            "pytest", "python -m pytest",
            "ruff check", "ruff format",
            "mypy", "black", "isort",
            "uvicorn",
            "python -c", "python -m",
        ],
        "blocked_commands": [
            "rm -rf /", "rm -rf ~", "rm -rf .",
            "sudo", "chmod 777", "chown",
            "curl | bash", "curl | sh",
            "wget | bash", "wget | sh",
            "pip install --user",
            "shutdown", "reboot",
        ],
        "allowed_path_patterns": [
            "app/**", "src/**",
            "tests/**", "test/**",
            "requirements.txt", "requirements-*.txt",
            "pyproject.toml", "setup.py", "setup.cfg",
            "*.py", "*.pyi",
            "*.md", "*.rst", "*.txt",
            "*.yaml", "*.yml", "*.toml", "*.json",
        ],
        "blocked_path_patterns": [
            ".env", ".env.*",
            "*.pem", "*.key", "*.cert",
            ".git/**",
            "venv/**", ".venv/**",
            "__pycache__/**",
            "*.pyc",
        ],
    },
    "java": {
        "allowed_commands": [
            "mvn compile", "mvn test", "mvn package",
            "mvn clean", "mvn install", "mvn verify",
            "gradle build", "gradle test", "gradle clean",
            "gradle compileJava", "gradle compileTestJava",
            "java", "javac",
        ],
        "blocked_commands": [
            "rm -rf /", "rm -rf ~", "rm -rf .",
            "sudo", "chmod 777", "chown",
            "curl | bash", "curl | sh",
            "shutdown", "reboot",
        ],
        "allowed_path_patterns": [
            "src/**",
            "test/**", "tests/**",
            "pom.xml", "build.gradle", "build.gradle.kts",
            "settings.gradle", "settings.gradle.kts",
            "gradle.properties",
            "*.java", "*.kt", "*.kts",
            "*.xml", "*.yaml", "*.yml", "*.json",
            "*.properties",
            "*.md", "*.rst", "*.txt",
        ],
        "blocked_path_patterns": [
            ".env", ".env.*",
            "*.pem", "*.key", "*.cert",
            ".git/**",
            "target/**",
            "build/**",
            ".gradle/**",
            "*.class", "*.jar",
        ],
    },
    "other": {
        "allowed_commands": [],
        "blocked_commands": [
            "rm -rf /", "rm -rf ~",
            "sudo", "chmod 777",
            "shutdown", "reboot",
        ],
        "allowed_path_patterns": ["**"],
        "blocked_path_patterns": [
            ".env", ".env.*",
            "*.pem", "*.key",
            ".git/**",
        ],
    },
}
