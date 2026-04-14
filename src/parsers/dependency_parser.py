from __future__ import annotations

import json
import re
from pathlib import Path


def detect_frameworks(root: Path) -> list[str]:
    frameworks: list[str] = []
    pyproject = root / "pyproject.toml"
    requirements = root / "requirements.txt"
    package_json = root / "package.json"

    blob = ""
    for candidate in (pyproject, requirements):
        if candidate.exists():
            blob += candidate.read_text(encoding="utf-8", errors="ignore") + "\n"
    markers = {
        "fastapi": "FastAPI",
        "flask": "Flask",
        "django": "Django",
        "typer": "Typer",
        "click": "Click",
        "pytest": "Pytest",
        "torch": "PyTorch",
        "transformers": "Transformers",
        "streamlit": "Streamlit",
        "gradio": "Gradio",
    }
    lowered = blob.lower()
    for marker, label in markers.items():
        if marker in lowered:
            frameworks.append(label)

    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pkg = {}
        deps = " ".join((pkg.get("dependencies") or {}).keys()) + " " + " ".join((pkg.get("devDependencies") or {}).keys())
        for marker, label in {
            "react": "React",
            "next": "Next.js",
            "express": "Express",
            "vue": "Vue",
            "vite": "Vite",
        }.items():
            if re.search(rf"\b{re.escape(marker)}\b", deps):
                frameworks.append(label)
    return sorted(set(frameworks))
