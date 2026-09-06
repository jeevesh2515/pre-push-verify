"""Ponytail Anti-Overengineering Review Engine.

Inspects changes against the 5 Ponytail Pruning Laws:
  1. delete : Dead code, temporary debug logging, commented-out blocks, speculative code.
  2. stdlib : Reinvented standard library helpers.
  3. native : Platform primitives over heavy dependencies.
  4. yagni  : Single-implementation interfaces, empty wrappers, premature abstractions.
  5. shrink : Logic condensation without sacrificing clarity or security invariants.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

DEBUG_PATTERNS = [
    (re.compile(r"^\+\s*print\(.+debug", re.IGNORECASE), "delete", "Temporary debug print statement"),
    (re.compile(r"^\+\s*console\.log\(.+debug", re.IGNORECASE), "delete", "Temporary debug console.log"),
    (re.compile(r"^\+\s*#\s*(TODO|FIXME|TEMP|DEBUG):?\s*", re.IGNORECASE), "delete", "Unresolved temporary TODO / DEBUG tag"),
    (re.compile(r"^\+\s*(//|#)\s*(var|let|const|def|import|from|class|function)\s+"), "delete", "Commented-out code"),
]

STDLIB_REINVENTION_PATTERNS = [
    (re.compile(r"def\s+join_paths?\(", re.IGNORECASE), "stdlib", "Use os.path.join or pathlib.Path instead of custom path joiner"),
    (re.compile(r"def\s+is_even\(", re.IGNORECASE), "stdlib", "Use n % 2 == 0 directly"),
    (re.compile(r"def\s+is_empty\(", re.IGNORECASE), "stdlib", "Use not sequence directly"),
    (re.compile(r"def\s+to_json\(", re.IGNORECASE), "stdlib", "Use json.dumps standard library directly"),
]

YAGNI_PATTERNS = [
    (re.compile(r"class\s+Base[A-Z0-9_]+Handler\(ABC\):"), "yagni", "Premature abstract base class with single implementation"),
    (re.compile(r"class\s+I[A-Z0-9_]+Factory\(Protocol\):"), "yagni", "Premature factory interface; prefer direct constructors"),
]


@dataclass
class PonytailFinding:
    tag: str  # delete | stdlib | native | yagni | shrink
    line_number: int
    file_path: str
    message: str
    code_snippet: str
    replacement: str = ""


def analyze_diff(diff_text: str) -> tuple[list[PonytailFinding], int]:
    """Analyze a git diff and return Ponytail findings and removable line count."""
    findings: list[PonytailFinding] = []
    current_file = ""
    line_num = 0
    removable_lines = 0

    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                current_file = parts[3].lstrip("b/")
            continue
        elif line.startswith("@@"):
            # Extract line number from hunk header: @@ -1,5 +1,10 @@
            match = re.search(r"\+(\d+)", line)
            if match:
                line_num = int(match.group(1))
            continue
        elif line.startswith("+++") or line.startswith("---"):
            continue

        if line.startswith("+"):
            line_num += 1
            added_content = line[1:]

            # 1. Check for debug / dead code
            for pat, tag, msg in DEBUG_PATTERNS:
                if pat.search(line):
                    findings.append(
                        PonytailFinding(
                            tag=tag,
                            line_number=line_num,
                            file_path=current_file,
                            message=msg,
                            code_snippet=added_content.strip(),
                            replacement="Remove line",
                        )
                    )
                    removable_lines += 1
                    break

            # 2. Check for stdlib reinventions
            for pat, tag, msg in STDLIB_REINVENTION_PATTERNS:
                if pat.search(added_content):
                    findings.append(
                        PonytailFinding(
                            tag=tag,
                            line_number=line_num,
                            file_path=current_file,
                            message=msg,
                            code_snippet=added_content.strip(),
                            replacement="Use standard library primitive",
                        )
                    )
                    removable_lines += 3
                    break

            # 3. Check for premature abstractions (YAGNI)
            for pat, tag, msg in YAGNI_PATTERNS:
                if pat.search(added_content):
                    findings.append(
                        PonytailFinding(
                            tag=tag,
                            line_number=line_num,
                            file_path=current_file,
                            message=msg,
                            code_snippet=added_content.strip(),
                            replacement="Inline or flatten hierarchy",
                        )
                    )
                    removable_lines += 5
                    break
        elif not line.startswith("-"):
            line_num += 1

    return findings, removable_lines
