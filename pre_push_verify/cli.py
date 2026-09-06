"""Command Line Interface for pre-push-verify.

Usage:
  pre-push-verify [OPTIONS]

Options:
  --strict          Fail on any secret warning or over-engineering finding.
  --skip-tests      Skip running automated test suite.
  --install-hook    Install pre-push git hook into .git/hooks/pre-push.
  --json            Output results as JSON for CI/CD pipelines.
  --help            Show help message.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from .ponytail import analyze_diff
from .runner import execute_tests
from .scanner import scan_text

# Terminal Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner() -> None:
    banner = f"""{CYAN}{BOLD}
   ___  ___ ___     ___  _   _ ___ _  _   _   _____ ___ ___ ___ _   _ 
  | _ \ _ \ __|___ | _ \| | | / __| || | | | | | __| _ \_ _| __| | | |
  |  _/   / _|____ |  _/| |_| \__ \ __ | | |_| | _||   /| || _|| |_| |
  |_| |_|_\___|    |_|   \___/|___/_||_|  \___/|___|_|_\___|_|   \___/ 
{RESET}{DIM}  Autonomous Pre-Push Guardrail & Anti-Overengineering Engine v1.0.0{RESET}
"""
    print(banner)


def get_git_root() -> Path:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
        return Path(out)
    except Exception:
        return Path.cwd()


def get_working_diff() -> str:
    """Get unstaged and staged diff compared to HEAD."""
    try:
        # Get diff against HEAD (covers staged and unstaged)
        out = subprocess.check_output(["git", "diff", "HEAD"], text=True)
        if not out.strip():
            # If no commit exists yet, just get working diff
            out = subprocess.check_output(["git", "diff"], text=True)
        return out
    except Exception:
        return ""


def get_untracked_files() -> list[str]:
    """List untracked files in the repository."""
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        untracked = []
        for line in out.splitlines():
            if line.startswith("??"):
                untracked.append(line[3:].strip())
        return untracked
    except Exception:
        return []


def install_git_hook(git_root: Path) -> int:
    hooks_dir = git_root / ".git" / "hooks"
    if not hooks_dir.exists():
        print(f"{RED}Error: .git/hooks directory not found in {git_root}{RESET}")
        return 1

    hook_path = hooks_dir / "pre-push"
    hook_script = """#!/usr/bin/env bash
# pre-push-verify hook installed automatically
pre-push-verify --strict
"""
    hook_path.write_text(hook_script)
    hook_path.chmod(0o755)
    print(f"{GREEN}✓ Successfully installed pre-push hook to:{RESET} {hook_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Autonomous Pre-Push Guardrail & Anti-Overengineering Engine")
    parser.add_argument("--strict", action="store_true", help="Fail if any secret or ponytail finding exists")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running automated test suite")
    parser.add_argument("--install-hook", action="store_true", help="Install pre-push git hook")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()
    git_root = get_git_root()

    if args.install_hook:
        return install_git_hook(git_root)

    if not args.json:
        print_banner()

    diff = get_working_diff()
    untracked = get_untracked_files()

    # 1. Check for .env file leaks
    env_leaks = [f for f in untracked if f.endswith(".env") or ".env." in f]
    try:
        tracked_env = subprocess.check_output(["git", "ls-files"], text=True).splitlines()
        env_leaks.extend([f for f in tracked_env if f.endswith(".env") and not f.endswith(".env.example")])
    except Exception:
        pass

    # 2. Scan secrets in diff
    secret_findings = scan_text(diff)

    # 3. Ponytail anti-overengineering review
    ponytail_findings, removable_lines = analyze_diff(diff)

    # 4. Run test suites
    test_results = []
    if not args.skip_tests:
        if not args.json:
            print(f"{CYAN}🧪 Executing detected test suites...{RESET}")
        test_results = execute_tests(git_root)

    tests_failed = any(not t.passed for t in test_results)
    secrets_failed = len(secret_findings) > 0 or len(env_leaks) > 0
    ponytail_failed = len(ponytail_findings) > 0 and args.strict

    if args.json:
        report = {
            "clean": not (secrets_failed or tests_failed or (args.strict and ponytail_failed)),
            "env_leaks": env_leaks,
            "secrets": [
                {
                    "rule": f.rule_name,
                    "snippet": f.snippet,
                    "line": f.line_number,
                    "entropy": f.entropy,
                }
                for f in secret_findings
            ],
            "ponytail": {
                "verdict": "Lean already. Ship." if not ponytail_findings else "Pruning recommended",
                "removable_lines": removable_lines,
                "findings": [
                    {
                        "tag": f.tag,
                        "file": f.file_path,
                        "line": f.line_number,
                        "message": f.message,
                        "snippet": f.code_snippet,
                    }
                    for f in ponytail_findings
                ],
            },
            "tests": [
                {
                    "runner": t.runner_name,
                    "passed": t.passed,
                    "exit_code": t.exit_code,
                }
                for t in test_results
            ],
        }
        print(json.dumps(report, indent=2))
        return 1 if (secrets_failed or tests_failed or ponytail_failed) else 0

    # Human-readable formatting
    print(f"{BOLD}1. 🛡️ Secret & Credential Vulnerability Scan{RESET}")
    if env_leaks:
        print(f"   {RED}✗ BLOCKED: Untracked or committed .env files detected:{RESET}")
        for leak in env_leaks:
            print(f"     - {leak}")
    if secret_findings:
        print(f"   {RED}✗ BLOCKED: Sensitive credentials detected in working diff:{RESET}")
        for sf in secret_findings:
            print(f"     - Line {sf.line_number}: [{sf.rule_name}] {sf.snippet}")
    if not env_leaks and not secret_findings:
        print(f"   {GREEN}✓ No credentials, private keys, or .env files detected.{RESET}")

    print(f"\n{BOLD}2. ✂️ Ponytail Anti-Overengineering Review{RESET}")
    if ponytail_findings:
        print(f"   {YELLOW}⚠ Over-engineering findings detected ({removable_lines} lines removable):{RESET}")
        for pf in ponytail_findings:
            print(f"     L{pf.line_number}: [{pf.tag}] {pf.file_path}: {pf.message} -> {DIM}{pf.code_snippet}{RESET}")
    else:
        print(f"   {GREEN}✓ Lean already. Ship.{RESET}")

    print(f"\n{BOLD}3. 🧪 Automated Regression Testing Gate{RESET}")
    if not test_results:
        print(f"   {DIM}• No test runners detected or tests skipped (--skip-tests){RESET}")
    else:
        for tr in test_results:
            status_icon = f"{GREEN}✓ PASSED{RESET}" if tr.passed else f"{RED}✗ FAILED (exit {tr.exit_code}){RESET}"
            print(f"   • {tr.runner_name}: {status_icon}")
            if not tr.passed:
                print(f"{DIM}{tr.output[-400:]}{RESET}")

    print(f"\n{BOLD}{'═' * 60}{RESET}")
    if secrets_failed:
        print(f"{RED}{BOLD}🚨 PUSH BLOCKED: Resolve credential leaks before pushing.{RESET}")
        return 1
    elif tests_failed:
        print(f"{RED}{BOLD}🚨 PUSH BLOCKED: Fix failing tests before pushing.{RESET}")
        return 1
    elif ponytail_failed:
        print(f"{RED}{BOLD}🚨 PUSH BLOCKED: Strict mode tripped on over-engineering findings.{RESET}")
        return 1
    else:
        print(f"{GREEN}{BOLD}✨ All pre-push gates verified! Ready to ship.{RESET}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
