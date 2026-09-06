"""Unit tests for pre_push_verify.cli."""
import subprocess
import sys


def test_cli_help_flag():
    proc = subprocess.run([sys.executable, "-m", "pre_push_verify.cli", "--help"], stdout=subprocess.PIPE, text=True)
    assert proc.returncode == 0
    assert "Autonomous Pre-Push Guardrail" in proc.stdout


def test_cli_json_output():
    proc = subprocess.run([sys.executable, "-m", "pre_push_verify.cli", "--json", "--skip-tests"], stdout=subprocess.PIPE, text=True)
    assert proc.returncode == 0
    assert '"clean":' in proc.stdout


def test_cli_version_flag():
    proc = subprocess.run([sys.executable, "-m", "pre_push_verify.cli", "--version"], stdout=subprocess.PIPE, text=True)
    assert proc.returncode == 0
    assert "pre-push-verify 1.0.0" in proc.stdout
