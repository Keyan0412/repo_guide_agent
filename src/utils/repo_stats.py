from __future__ import annotations

from collections import Counter
from pathlib import Path


def collect_extension_stats(root: Path, max_files: int = 2000) -> dict[str, int]:
    counts: Counter[str] = Counter()
    seen = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        counts[path.suffix.lower() or "<no_ext>"] += 1
        seen += 1
        if seen >= max_files:
            break
    return dict(counts.most_common())
