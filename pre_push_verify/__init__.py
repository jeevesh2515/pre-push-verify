"""Autonomous Pre-Push Guardrail & Anti-Overengineering Engine."""

__version__ = "1.0.0"
__author__ = "Jeevesh Singale"

from .ponytail import analyze_diff
from .runner import execute_tests
from .scanner import scan_text

__all__ = ["scan_text", "analyze_diff", "execute_tests"]
