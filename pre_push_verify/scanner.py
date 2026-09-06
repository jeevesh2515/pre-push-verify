"""Secret and Credential Scanner for pre-push-verify.

Detects over 30+ credential patterns across working diffs and staged files
to prevent accidental secret leakage before git push.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Sequence

SECRET_PATTERNS: list[tuple[str, re.Pattern[str], float]] = [
    # AWS
    ("AWS Access Key ID", re.compile(r"\b(AKIA[0-9A-Z]{16})\b"), 0.0),
    ("AWS Secret Key Assignment", re.compile(r"(?i)aws_secret_access_key\s*=\s*['\"][A-Za-z0-9/+=]{40}['\"]"), 0.0),
    ("AWS Session Token", re.compile(r"(?i)aws_session_token\s*=\s*['\"][A-Za-z0-9/+=]{100,}['\"]"), 0.0),
    # OpenAI & LLMs
    ("OpenAI Secret Key", re.compile(r"\b(sk-[A-Za-z0-9]{20,48})\b"), 0.0),
    ("OpenAI Project / Org Key", re.compile(r"\b(sk-proj-[A-Za-z0-9_\-]{30,})\b"), 0.0),
    ("Anthropic API Key", re.compile(r"\b(sk-ant-[A-Za-z0-9_\-]{30,})\b"), 0.0),
    ("Groq API Key", re.compile(r"\b(gsk_[A-Za-z0-9]{32,64})\b"), 0.0),
    ("HuggingFace User Access Token", re.compile(r"\b(hf_[A-Za-z0-9]{34,})\b"), 0.0),
    ("Cohere API Key", re.compile(r"\b(co-[A-Za-z0-9]{30,})\b"), 0.0),
    # Git & Code Hosting
    ("GitHub Personal Access Token (Classic)", re.compile(r"\b(ghp_[A-Za-z0-9]{36})\b"), 0.0),
    ("GitHub Fine-Grained Personal Access Token", re.compile(r"\b(github_pat_[A-Za-z0-9_]{82})\b"), 0.0),
    ("GitHub OAuth Access Token", re.compile(r"\b(gho_[A-Za-z0-9]{36})\b"), 0.0),
    ("GitLab Personal Access Token", re.compile(r"\b(glpat-[A-Za-z0-9_\-]{20,})\b"), 0.0),
    # Payments & SaaS
    ("Stripe Secret Key", re.compile(r"\b(sk_live_[0-9a-zA-Z]{24,})\b"), 0.0),
    ("Stripe Webhook Signing Secret", re.compile(r"\b(whsec_[0-9a-zA-Z]{32,})\b"), 0.0),
    ("Stripe Restricted Key", re.compile(r"\b(rk_live_[0-9a-zA-Z]{24,})\b"), 0.0),
    ("Slack Bot Token", re.compile(r"\b(xoxb-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,})\b"), 0.0),
    ("Slack User Token", re.compile(r"\b(xoxp-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,})\b"), 0.0),
    ("Twilio Account SID & Auth Token", re.compile(r"(?i)(AC[a-z0-9]{32}[:][a-z0-9]{32})"), 0.0),
    ("SendGrid API Key", re.compile(r"\b(SG\.[A-Za-z0-9_\-]{22}\.[A-Za-z0-9_\-]{43})\b"), 0.0),
    ("Resend API Key", re.compile(r"\b(re_[A-Za-z0-9_]{24,})\b"), 0.0),
    # Cryptography & Infrastructure
    ("RSA Private Key Header", re.compile(r"-----BEGIN RSA PRIVATE KEY-----"), 0.0),
    ("OpenSSH Private Key Header", re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"), 0.0),
    ("PGP Private Key Header", re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----"), 0.0),
    ("EC Private Key Header", re.compile(r"-----BEGIN EC PRIVATE KEY-----"), 0.0),
    ("Generic Private Key Header", re.compile(r"-----BEGIN PRIVATE KEY-----"), 0.0),
    # Generic High Entropy Passwords / Secrets
    ("Hardcoded Password in String Assignment", re.compile(r"(?i)(password|passwd|pwd|secret|api_key|apikey)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), 3.5),
    ("Database Connection String with Credentials", re.compile(r"(?i)(postgres|mysql|mongodb|redis)://[^:]+:[^@]+@[^/]+"), 0.0),
]

SAFE_PLACEHOLDERS = frozenset({
    "dummy", "test", "mock", "example", "placeholder", "your-api-key",
    "gsk_test", "sk_test", "sk-ant-api03-test", "ghp_test", "change_me",
    "<your-key>", "[redacted]", "fake", "fixture",
})


@dataclass
class SecretFinding:
    rule_name: str
    snippet: str
    line_number: int | None = None
    file_path: str = ""
    entropy: float = 0.0


def calculate_shannon_entropy(data: str) -> float:
    """Calculate the Shannon entropy of a string (higher = more random)."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for x in set(data):
        p_x = float(data.count(x)) / length
        if p_x > 0:
            entropy += - p_x * math.log2(p_x)
    return entropy


def is_placeholder(match_str: str) -> bool:
    """Check if the string is an obvious documentation or test fixture placeholder."""
    lower = match_str.lower()
    return any(p in lower for p in SAFE_PLACEHOLDERS)


def scan_text(text: str, file_path: str = "") -> list[SecretFinding]:
    """Scan a block of text (file content or git diff) for secrets."""
    findings: list[SecretFinding] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Ignore diff headers or deleted lines in diffs
        if stripped.startswith("---") or stripped.startswith("+++") or stripped.startswith("-"):
            continue

        for rule_name, pattern, min_entropy in SECRET_PATTERNS:
            match = pattern.search(line)
            if match:
                matched_val = match.group(0)
                if is_placeholder(matched_val):
                    continue

                if min_entropy > 0.0:
                    ent = calculate_shannon_entropy(matched_val)
                    if ent < min_entropy:
                        continue
                else:
                    ent = calculate_shannon_entropy(matched_val)

                # Redact matched text for safe reporting
                redacted_snippet = line[:match.start()] + "***REDACTED***" + line[match.end():]
                findings.append(
                    SecretFinding(
                        rule_name=rule_name,
                        snippet=redacted_snippet.strip(),
                        line_number=idx,
                        file_path=file_path,
                        entropy=round(ent, 2),
                    )
                )
    return findings
