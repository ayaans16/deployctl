# Contributing to deployctl

Thanks for considering contributing to `deployctl`! This doc covers how to get set up, the conventions the codebase follows, and how to submit changes.

## Getting Started

1. Fork and clone the repo
2. Create a virtual environment and install with dev dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Copy the example config/env files and fill in your own values for local testing:
   ```bash
   cp deployctl.example.conf deployctl.conf
   cp .env.example .env
   ```
   Both `deployctl.conf` and `.env` are gitignored — never commit real credentials or VPS details.

## Running Checks Locally

Before opening a PR, make sure these all pass — they're exactly what CI runs:

```bash
ruff check app/ tests/
pytest tests/ -v
```

If you're touching the `Dockerfile`, also verify it builds:

```bash
docker build -t deployctl:local .
docker run --rm deployctl:local --help
```

## Project Conventions

- **Every SSH/Docker/subprocess call must fail cleanly, never crash.** Every function that touches the network, a subprocess, or a config file follows the same pattern: try/except around the risky call, print a clear message, `return False` (or `None` for config loaders) on failure. Don't let a raw traceback reach the user.
- **Config-driven, not auto-detected.** We don't try to guess unit test runners, start commands, or app ports — the user declares them explicitly in `deployctl.conf`. Keep new features consistent with that philosophy rather than adding heuristic detection.
- **Resolve paths with `app.paths.resource_path()`**, never hardcode relative paths or use `__file__`-relative resolution. It resolves relative to the directory the user runs `deployctl` from, which is what makes the tool work correctly when installed and run against an arbitrary project.
- **Load config fresh inside each function**, not as a module-level constant — config path resolution depends on the current working directory at call time, and module-level constants get evaluated once at import and go stale.
- **`~` in remote paths only expands in shell contexts** (`exec_command`, `bash -c "..."`), never in raw SFTP calls (`sftp.put()`, etc.) — SFTP has no shell. Resolve `~` to an absolute path first if you need it in an SFTP call.
- **Blind `except Exception` is intentional** in this codebase, not an oversight — it's how we guarantee a clean failure message instead of a crash. `ruff`'s config in `pyproject.toml` deliberately excludes the blind-except lint rule for this reason.

## Testing Guidelines

- New modules that talk to SSH/Docker/the network should be tested with mocks (see `tests/test_screen.py` or `tests/test_rollback.py` for the pattern) — tests should never require a live VPS.
- Use `monkeypatch.chdir(tmp_path)` plus a real written `deployctl.conf` fixture to test config-loading logic — see `tests/test_config_loading.py`.
- If you fix a bug, add a regression test for it. `tests/test_paths.py`'s `resource_path()` test exists specifically because that exact bug shipped once already.

## Submitting a Pull Request

1. Create a branch off `main` (e.g. `fix/nginx-symlink-race`, `feat/kubernetes-target`)
2. Keep PRs scoped to one change — a bug fix, one new module, one doc update. Large mixed PRs are harder to review and harder to revert if something's wrong.
3. Make sure `ruff check` and `pytest` both pass locally before pushing (CI will run both, but catch it early)
4. Write a clear PR description: what changed and why, not just what — the "why" is what future contributors actually need
5. If your change affects `deployctl.example.conf`'s schema (a new config key), update the README's config table too

## Reporting Bugs / Requesting Features

Open a GitHub issue with:
- What you expected to happen vs. what actually happened
- Your `deployctl.conf` (with secrets/domains redacted) and the exact command you ran
- Relevant output — `deployctl` is designed to fail with a clear message rather than a raw traceback, so include that message

## Code of Conduct

Be respectful, assume good intent, and keep feedback focused on the code, not the person.
