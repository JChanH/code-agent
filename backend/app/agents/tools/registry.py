"""Claude API 도구 레지스트리.

SDK가 내부적으로 제공하던 파일시스템 도구들을 직접 정의합니다.
각 도구는 Definition(JSON schema)과 Handler(실행 함수)로 구성됩니다.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Tool Definitions (Anthropic API에 전달할 JSON schema)
# ---------------------------------------------------------------------------

_DEFINITIONS: dict[str, dict[str, Any]] = {
    "read_file": {
        "name": "read_file",
        "description": "Read the contents of a file at the given path. Returns the file content as a string.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read.",
                }
            },
            "required": ["path"],
        },
    },
    "write_file": {
        "name": "write_file",
        "description": "Write content to a file, creating it (and any parent directories) if it does not exist. Overwrites existing content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to write.",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write into the file.",
                },
            },
            "required": ["path", "content"],
        },
    },
    "edit_file": {
        "name": "edit_file",
        "description": (
            "Replace an exact string in a file with a new string. "
            "The old_string must match exactly (including whitespace and indentation). "
            "Use replace_all=true to replace every occurrence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to edit.",
                },
                "old_string": {
                    "type": "string",
                    "description": "Exact string to find and replace.",
                },
                "new_string": {
                    "type": "string",
                    "description": "String to replace old_string with.",
                },
                "replace_all": {
                    "type": "boolean",
                    "description": "If true, replace all occurrences. Default: false.",
                },
            },
            "required": ["path", "old_string", "new_string"],
        },
    },
    "glob_files": {
        "name": "glob_files",
        "description": "Find files matching a glob pattern. Returns a newline-separated list of matching paths.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g. '**/*.py', 'src/**/*.ts').",
                },
                "base_dir": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to current working directory.",
                },
            },
            "required": ["pattern"],
        },
    },
    "grep_search": {
        "name": "grep_search",
        "description": "Search for a regex pattern in file contents. Returns matching lines with file path and line number.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regular expression pattern to search for.",
                },
                "path": {
                    "type": "string",
                    "description": "File or directory to search in. Defaults to current working directory.",
                },
                "glob": {
                    "type": "string",
                    "description": "Glob pattern to filter files (e.g. '*.py').",
                },
                "case_insensitive": {
                    "type": "boolean",
                    "description": "If true, search case-insensitively. Default: false.",
                },
            },
            "required": ["pattern"],
        },
    },
    "bash_exec": {
        "name": "bash_exec",
        "description": (
            "Execute a shell command and return stdout + stderr. "
            "Commands run with the project directory as the working directory. "
            "Timeout: 120 seconds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Shell command to execute.",
                },
            },
            "required": ["command"],
        },
    },
}


def get_tool_definitions(names: list[str]) -> list[dict[str, Any]]:
    """허용된 도구 이름 목록에 해당하는 definition 리스트를 반환합니다."""
    result = []
    for name in names:
        if name not in _DEFINITIONS:
            raise ValueError(f"Unknown tool: {name!r}. Available: {list(_DEFINITIONS)}")
        result.append(_DEFINITIONS[name])
    return result


# ---------------------------------------------------------------------------
# Tool Handlers (실제 실행 함수)
# ---------------------------------------------------------------------------

async def handle_read_file(input: dict[str, Any], working_dir: str | None = None) -> str:
    path = _resolve_path(input["path"], working_dir)
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"[Error: File not found: {path}]"
    except OSError as e:
        return f"[Error reading file: {e}]"


async def handle_write_file(input: dict[str, Any], working_dir: str | None = None) -> str:
    path = _resolve_path(input["path"], working_dir)
    content: str = input["content"]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Written {len(content)} characters to {path}"
    except OSError as e:
        return f"[Error writing file: {e}]"


async def handle_edit_file(input: dict[str, Any], working_dir: str | None = None) -> str:
    path = _resolve_path(input["path"], working_dir)
    old_string: str = input["old_string"]
    new_string: str = input["new_string"]
    replace_all: bool = input.get("replace_all", False)

    try:
        original = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return f"[Error: File not found: {path}]"
    except OSError as e:
        return f"[Error reading file: {e}]"

    if old_string not in original:
        return f"[Error: old_string not found in {path}]"

    if replace_all:
        updated = original.replace(old_string, new_string)
        count = original.count(old_string)
    else:
        updated = original.replace(old_string, new_string, 1)
        count = 1

    try:
        path.write_text(updated, encoding="utf-8")
        return f"Replaced {count} occurrence(s) in {path}"
    except OSError as e:
        return f"[Error writing file: {e}]"


async def handle_glob_files(input: dict[str, Any], working_dir: str | None = None) -> str:
    pattern: str = input["pattern"]
    base_dir_str: str | None = input.get("base_dir")

    if base_dir_str:
        base = Path(base_dir_str)
    elif working_dir:
        base = Path(working_dir)
    else:
        base = Path.cwd()

    try:
        matches = sorted(str(p) for p in base.glob(pattern))
        if not matches:
            return "[No files matched]"
        return "\n".join(matches)
    except Exception as e:
        return f"[Error: {e}]"


async def handle_grep_search(input: dict[str, Any], working_dir: str | None = None) -> str:
    pattern: str = input["pattern"]
    search_path: str | None = input.get("path")
    glob_filter: str | None = input.get("glob")
    case_insensitive: bool = input.get("case_insensitive", False)

    cmd = ["rg", "--line-number", "--with-filename"]
    if case_insensitive:
        cmd.append("-i")
    if glob_filter:
        cmd.extend(["--glob", glob_filter])
    cmd.append(pattern)

    if search_path:
        cmd.append(search_path)
    elif working_dir:
        cmd.append(working_dir)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if not output:
            return "[No matches found]"
        return output
    except FileNotFoundError:
        # rg가 없으면 grep 폴백
        return await _grep_fallback(pattern, search_path or working_dir, glob_filter, case_insensitive)
    except subprocess.TimeoutExpired:
        return "[Error: grep timed out]"
    except Exception as e:
        return f"[Error: {e}]"


async def _grep_fallback(
    pattern: str,
    search_path: str | None,
    glob_filter: str | None,
    case_insensitive: bool,
) -> str:
    """rg가 없을 때 Python으로 grep 구현."""
    import re

    flags = re.IGNORECASE if case_insensitive else 0
    try:
        regex = re.compile(pattern, flags)
    except re.error as e:
        return f"[Error: invalid regex: {e}]"

    base = Path(search_path) if search_path else Path.cwd()
    file_pattern = glob_filter or "**/*"

    lines: list[str] = []
    try:
        paths = list(base.glob(file_pattern)) if base.is_dir() else [base]
        for p in sorted(paths):
            if not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                for i, line in enumerate(text.splitlines(), 1):
                    if regex.search(line):
                        lines.append(f"{p}:{i}: {line}")
            except OSError:
                continue
    except Exception as e:
        return f"[Error: {e}]"

    if not lines:
        return "[No matches found]"
    return "\n".join(lines[:500])  # 최대 500줄


async def handle_bash_exec(input: dict[str, Any], working_dir: str | None = None) -> str:
    command: str = input["command"]
    cwd = working_dir or None

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=cwd,
        )
        output_parts = []
        if result.stdout:
            output_parts.append(result.stdout)
        if result.stderr:
            output_parts.append(f"[stderr]\n{result.stderr}")
        combined = "\n".join(output_parts).strip()
        if result.returncode != 0:
            combined = f"[exit code: {result.returncode}]\n{combined}"
        return combined or "[No output]"
    except subprocess.TimeoutExpired:
        return "[Error: command timed out after 120s]"
    except Exception as e:
        return f"[Error: {e}]"


# ---------------------------------------------------------------------------
# Handler 디스패치 테이블
# ---------------------------------------------------------------------------
TOOL_HANDLERS: dict[str, Any] = {
    "read_file": handle_read_file,
    "write_file": handle_write_file,
    "edit_file": handle_edit_file,
    "glob_files": handle_glob_files,
    "grep_search": handle_grep_search,
    "bash_exec": handle_bash_exec,
}


async def dispatch_tool(name: str, input: dict[str, Any], working_dir: str | None = None) -> str:
    """도구 이름과 입력으로 핸들러를 찾아 실행합니다."""
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return f"[Error: Unknown tool '{name}']"
    return await handler(input, working_dir=working_dir)


# ---------------------------------------------------------------------------
# 내부 유틸리티
# ---------------------------------------------------------------------------

def _resolve_path(path_str: str, working_dir: str | None) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    if working_dir:
        return Path(working_dir) / p
    return p
