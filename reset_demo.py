#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset and preload the ORE demo.")
    parser.add_argument(
        "--local",
        action="store_true",
        help="Try the backend reset module directly before falling back to Docker Compose.",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent
    if args.local:
        interpreter = _local_python(repo_root)
        if not _has_backend_dependencies(interpreter):
            print(
                "Local backend dependencies are unavailable; falling back to Docker Compose.",
                flush=True,
            )
            return _docker_reset(repo_root)
        env = {
            **os.environ,
            "PYTHONPATH": str(repo_root / "backend"),
        }
        return subprocess.call(
            [interpreter, "-m", "app.seed.reset_demo"],
            cwd=repo_root,
            env=env,
        )

    return _docker_reset(repo_root)


def _docker_reset(repo_root: Path) -> int:
    return subprocess.call(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "backend",
            "python",
            "-m",
            "app.seed.reset_demo",
        ],
        cwd=repo_root,
    )


def _local_python(repo_root: Path) -> str:
    venv_python = repo_root / "backend" / ".venv" / "bin" / "python"
    if venv_python.exists() and _supports_backend_type_syntax(str(venv_python)):
        return str(venv_python)
    return sys.executable


def _supports_backend_type_syntax(interpreter: str) -> bool:
    return (
        subprocess.call(
            [
                interpreter,
                "-c",
                "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


def _has_backend_dependencies(interpreter: str) -> bool:
    return (
        subprocess.call(
            [
                interpreter,
                "-c",
                "import neo4j, sqlalchemy, pydantic, pydantic_settings",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        == 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
