from __future__ import annotations

from pathlib import Path


def main() -> None:
    print(f"Repo root: {Path.cwd()}")


if __name__ == "__main__":
    main()
