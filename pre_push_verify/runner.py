"""Adaptive Test Runner Gate.

Automatically discovers project test runners (pytest, npm, pnpm, cargo, go)
and executes the relevant tests before allowing a git push.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestResult:
    runner_name: str
    command: list[str]
    passed: bool
    exit_code: int
    output: str


def detect_test_runner(repo_root: Path) -> list[list[str]]:
    """Detect available test runners based on repository manifest files."""
    commands: list[list[str]] = []

    # Python / Pytest
    if (repo_root / "pytest.ini").exists() or (repo_root / "pyproject.toml").exists() or (repo_root / "tests").exists():
        if shutil.which("pytest"):
            commands.append(["pytest", "-q"])
        elif shutil.which("python3"):
            commands.append(["python3", "-m", "unittest"])

    # Node / JS / TS
    if (repo_root / "package.json").exists():
        if (repo_root / "pnpm-lock.yaml").exists() and shutil.which("pnpm"):
            commands.append(["pnpm", "test"])
        elif (repo_root / "yarn.lock").exists() and shutil.which("yarn"):
            commands.append(["yarn", "test"])
        elif (repo_root / "bun.lockb").exists() and shutil.which("bun"):
            commands.append(["bun", "test"])
        elif shutil.which("npm"):
            commands.append(["npm", "test"])

    # Rust / Cargo
    if (repo_root / "Cargo.toml").exists() and shutil.which("cargo"):
        commands.append(["cargo", "test", "--quiet"])

    # Go
    if (repo_root / "go.mod").exists() and shutil.which("go"):
        commands.append(["go", "test", "./..."])

    return commands


def execute_tests(repo_root: Path, custom_cmd: str | None = None) -> list[TestResult]:
    """Execute detected or custom test commands."""
    results: list[TestResult] = []

    if custom_cmd:
        cmds = [custom_cmd.split()]
    else:
        cmds = detect_test_runner(repo_root)

    for cmd in cmds:
        runner_name = cmd[0]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(repo_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=180,
            )
            results.append(
                TestResult(
                    runner_name=runner_name,
                    command=cmd,
                    passed=(proc.returncode == 0),
                    exit_code=proc.returncode,
                    output=proc.stdout,
                )
            )
        except Exception as err:
            results.append(
                TestResult(
                    runner_name=runner_name,
                    command=cmd,
                    passed=False,
                    exit_code=1,
                    output=str(err),
                )
            )
    return results
