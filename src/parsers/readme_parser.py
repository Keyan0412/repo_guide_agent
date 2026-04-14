from __future__ import annotations

import re


def extract_run_commands(readme_text: str) -> list[str]:
    commands: list[str] = []
    for line in readme_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("$ ", "python ", "uvicorn ", "npm ", "poetry ", "make ", "docker-compose ", "docker compose ")):
            commands.append(stripped.removeprefix("$ ").strip())
    return commands[:10]


def extract_project_purpose(readme_text: str) -> str:
    for line in readme_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if len(stripped) > 20:
            return re.sub(r"\s+", " ", stripped)
    return ""
