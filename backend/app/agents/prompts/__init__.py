"""에이전트 프롬프트 템플릿 로더."""

from pathlib import Path
from string import Template

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """prompts/ 디렉토리에서 .md 템플릿을 로드하고 $variable 자리에 값을 치환합니다.

    - 알 수 없는 $variable은 그대로 둡니다 (safe_substitute).
    - 마크다운 내 {중괄호} 표기와 충돌하지 않습니다.
    """
    template_text = (_PROMPTS_DIR / name).read_text(encoding="utf-8")
    return Template(template_text).safe_substitute(**kwargs)


def load_text(name: str) -> str:
    """prompts/ 디렉토리에서 .md 파일을 변수 치환 없이 그대로 로드합니다."""
    return (_PROMPTS_DIR / name).read_text(encoding="utf-8")
