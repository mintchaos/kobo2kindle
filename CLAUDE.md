# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

kobo2kindle is a CLI tool that downloads purchased ebooks from Kobo, strips DRM (via kobodl), and emails them to a Kindle address. The pipeline: `kobodl downloads+decrypts → stdlib emails EPUB → Amazon converts server-side`.

## Commands

```bash
uv sync                          # Install all dependencies
uv run pytest                    # Run all tests (28 tests)
uv run pytest tests/test_config.py -v          # Run one test file
uv run pytest tests/test_matcher.py::TestFindBooks::test_exact_substring_match -v  # Run one test
uv run kobo2kindle list          # Run the CLI
```

Uses `uv` (not pip). Build backend is hatchling. Python 3.11-3.12 only (kobodl breaks on 3.13+).

## Architecture

```
cli.py  →  kobo.py    (wraps kobodl: download, DRM strip, auth)
        →  matcher.py (fuzzy title search via difflib)
        →  kindle.py  (build email + SMTP send)
        →  config.py  (TOML at ~/.config/kobo2kindle/config.toml)
```

- **cli.py**: argparse with 4 subcommands (setup, list, send, download). All heavy imports deferred inside command functions.
- **kobo.py**: Lazy-loads kobodl globals. `_load_settings()` initializes `Globals.Settings` on first use. The kobodl API has quirks — `ListBooks` returns a generator, `CheckActivation` needs the polling URL, `User` lives in `kobodl.settings` not `kobodl.kobodl`.
- **matcher.py**: Two-tier scoring — substring matches score 0.7-1.0, fuzzy matches cap at 0.69. This ensures substring always ranks above fuzzy.
- **kindle.py**: Email subject must be `"convert"` — this is Amazon's trigger for server-side EPUB→Kindle conversion.
- **config.py**: Password retrieval chain: `KOBO2KINDLE_SMTP_PASSWORD` env var → `smtp_password_cmd` shell command → error. The cmd is `shlex.split` and run via `subprocess.run`.

## Testing

Tests use pytest with `tmp_path` for filesystem tests and `monkeypatch` for subprocess/env mocking. Class-based test organization. No kobo.py tests exist (would require mocking kobodl internals). Config password tests mock `subprocess.run` to avoid running real commands.

## Key Constraints

- kobodl manages its own auth state at `~/.config/kobodl.json` — don't try to manage this file directly.
- kobodl only works on Python 3.9-3.12. PyCryptodome (used for DRM decryption) has padding errors on 3.13+.
- The `src/` layout means imports are `from kobo2kindle.module import thing`.
