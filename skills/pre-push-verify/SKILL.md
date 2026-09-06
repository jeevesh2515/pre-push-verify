---
name: pre-push-verify
description: Comprehensive pre-push security audit, Ponytail anti-overengineering review, test execution, and safe git push workflow for AI coding agents.
category: workflow
metadata:
  author: Jeevesh Singale
  version: 1.0.0
  tags: [security, code-pruning, ponytail, pre-push, git, testing]
---

# Pre-Push Verification & Anti-Overengineering Guardrail

Autonomous pre-push review skill designed for AI coding agents (Claude Code, Google Antigravity, OpenCode, Cursor, Windsurf, Devin). It prevents secret leaks, prunes speculative abstractions, runs regression tests, and guarantees clean, lean commits before every push.

## When to Execute
- **Mandatory Trigger**: Immediately after completing implementation or bugfixes, and **BEFORE** staging or running `git push`.
- **Target Scope**: The working diff (`git diff HEAD`), staged changes, and newly created files.

---

## The 4 Verification Pillars

### 1. 🛡️ Secret & Credential Vulnerability Scan
Inspect working diff and unstaged files for sensitive tokens:
- **Cloud & AI Keys**: AWS (`AKIA`), OpenAI (`sk-`), Anthropic (`sk-ant-`), Groq (`gsk_`), Hugging Face (`hf_`), Cohere (`co-`).
- **Access & Auth Tokens**: GitHub PATs (`ghp_`, `github_pat_`), GitLab tokens, Slack tokens (`xoxb-`), Stripe keys (`sk_live_`).
- **Private Keys**: RSA, OpenSSH, PGP, and EC private key blocks.
- **Environment Files**: Ensure `.env` is never committed or tracked.

### 2. ✂️ Ponytail Anti-Overengineering Review (`/ponytail-review`)
Inspect changes against the 5 Ponytail Pruning Laws:
1. `delete` (Dead Code & Speculative Features):
   - Remove unused imports, variables, unreachable functions, and temporary debug logging (`print`, `console.log`).
   - Delete speculative code built for hypothetical future requirements.
2. `stdlib` (Reinvented Wheels):
   - Replace hand-rolled utilities or algorithms with language standard library functions.
3. `native` (Platform Over Dependency):
   - Replace external packages or wrappers where native runtime or platform primitives already suffice.
4. `yagni` (Premature Abstractions):
   - Flatten single-implementation interfaces, empty wrapper classes, and superfluous indirection layers.
5. `shrink` (Logic Condensation):
   - Simplify verbose logic and boilerplate into concise, idiomatic expressions without sacrificing clarity.

### 3. 🧪 Automated Test Verification
- Run project test suites (`pytest`, `npm test`, `cargo test`, `go test`).
- Enforce 100% passing tests. Never push on test regression.

### 4. 📝 Documentation & Context Sync
- Verify project tracking or learning files reflect latest architectural changes.
- Ensure `README.md` documents new capabilities with zero credential exposure.

---

## Execution Command

Run the bundled CLI tool:
```bash
pre-push-verify --strict
```
If clean: **"Lean already. Ship."** Proceed to `git commit` and `git push`.
