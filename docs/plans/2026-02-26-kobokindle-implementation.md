# kobokindle Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that downloads purchased Kobo ebooks and sends them to a Kindle via email.

**Architecture:** Python CLI wrapping `kobodl`'s Python API for Kobo download + DRM removal, stdlib `smtplib` for email delivery, `difflib` for fuzzy title matching. Config in TOML, secrets fetched from 1Password at runtime via `op` CLI.

**Tech Stack:** Python 3.11+, `uv` for project/dep management, `kobodl` for Kobo API, `argparse` for CLI, stdlib for everything else.

**Design doc:** `docs/plans/2026-02-26-kobokindle-design.md`

---

## Project Structure

```
kobokindle/
├── pyproject.toml
├── src/
│   └── kobokindle/
│       ├── __init__.py
│       ├── cli.py          # CLI entry point (argparse)
│       ├── config.py        # Config loading + 1Password
│       ├── kobo.py          # kobodl wrapper
│       ├── matcher.py       # Fuzzy book matching
│       └── kindle.py        # Email to Kindle
├── tests/
│   ├── conftest.py
│   ├── test_config.py
│   ├── test_matcher.py
│   ├── test_kindle.py
│   └── test_cli.py
└── docs/
    └── plans/
```

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `src/kobokindle/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Initialize project with uv**

```bash
cd /Users/christian.metts/repos/kobokindle
uv init --lib --name kobokindle
```

This creates `pyproject.toml` and `src/kobokindle/__init__.py`.

**Step 2: Edit pyproject.toml**

Set up the project metadata, dependencies, and script entry point:

```toml
[project]
name = "kobokindle"
version = "0.1.0"
description = "Get Kobo ebooks onto your Kindle"
requires-python = ">=3.11"
dependencies = [
    "kobodl>=0.13.0",
]

[project.scripts]
kobokindle = "kobokindle.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.backends"

[tool.hatch.build.targets.wheel]
packages = ["src/kobokindle"]
```

**Step 3: Install dependencies and verify**

```bash
uv sync
uv run python -c "import kobokindle; print('ok')"
```

Expected: `ok`

**Step 4: Add dev dependencies**

```bash
uv add --dev pytest
```

**Step 5: Create empty test conftest and run pytest**

Create `tests/conftest.py`:
```python
```

```bash
uv run pytest -v
```

Expected: `no tests ran` (0 collected, no errors)

**Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/ tests/conftest.py
git commit -m "scaffold: initialize project with uv, kobodl dep, pytest"
```

---

### Task 2: Config Module

**Files:**
- Create: `src/kobokindle/config.py`
- Create: `tests/test_config.py`

The config module loads a TOML config file and fetches the SMTP password from 1Password at runtime.

**Step 1: Write failing tests**

Create `tests/test_config.py`:

```python
import os
import tempfile
from pathlib import Path

from kobokindle.config import Config, load_config, save_config


class TestLoadConfig:
    def test_loads_valid_config(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'kindle_email = "me@kindle.com"\n'
            'smtp_host = "smtp.gmail.com"\n'
            "smtp_port = 587\n"
            'smtp_user = "me@gmail.com"\n'
            'op_smtp_password_ref = "op://Vault/Item/password"\n'
        )
        config = load_config(config_file)
        assert config.kindle_email == "me@kindle.com"
        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.smtp_user == "me@gmail.com"
        assert config.op_smtp_password_ref == "op://Vault/Item/password"

    def test_raises_on_missing_file(self, tmp_path):
        missing = tmp_path / "nope.toml"
        try:
            load_config(missing)
            assert False, "Should have raised"
        except FileNotFoundError:
            pass

    def test_raises_on_missing_required_field(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text('kindle_email = "me@kindle.com"\n')
        try:
            load_config(config_file)
            assert False, "Should have raised"
        except KeyError:
            pass


class TestSaveConfig:
    def test_round_trips(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
            op_smtp_password_ref="op://Vault/Item/password",
        )
        save_config(config, config_file)
        loaded = load_config(config_file)
        assert loaded.kindle_email == config.kindle_email
        assert loaded.smtp_host == config.smtp_host
        assert loaded.smtp_port == config.smtp_port
        assert loaded.smtp_user == config.smtp_user
        assert loaded.op_smtp_password_ref == config.op_smtp_password_ref

    def test_creates_parent_dirs(self, tmp_path):
        config_file = tmp_path / "nested" / "dir" / "config.toml"
        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
            op_smtp_password_ref="op://Vault/Item/password",
        )
        save_config(config, config_file)
        assert config_file.exists()


class TestGetSmtpPassword:
    def test_calls_op_read(self, monkeypatch):
        """Test that get_smtp_password shells out to `op read` with the configured ref."""
        import subprocess

        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)

            class Result:
                stdout = "my-secret-password"
                returncode = 0

            return Result()

        monkeypatch.setattr(subprocess, "run", fake_run)

        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
            op_smtp_password_ref="op://Vault/Item/password",
        )
        password = config.get_smtp_password()
        assert password == "my-secret-password"
        assert calls[0] == ["op", "read", "op://Vault/Item/password"]
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_config.py -v
```

Expected: FAIL (module not found)

**Step 3: Implement config module**

Create `src/kobokindle/config.py`:

```python
from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "kobokindle" / "config.toml"

REQUIRED_FIELDS = [
    "kindle_email",
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "op_smtp_password_ref",
]


@dataclass
class Config:
    kindle_email: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    op_smtp_password_ref: str

    def get_smtp_password(self) -> str:
        result = subprocess.run(
            ["op", "read", self.op_smtp_password_ref],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise KeyError(f"Missing required config field: {field}")
    return Config(
        kindle_email=data["kindle_email"],
        smtp_host=data["smtp_host"],
        smtp_port=data["smtp_port"],
        smtp_user=data["smtp_user"],
        op_smtp_password_ref=data["op_smtp_password_ref"],
    )


def save_config(config: Config, path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'kindle_email = "{config.kindle_email}"',
        f'smtp_host = "{config.smtp_host}"',
        f"smtp_port = {config.smtp_port}",
        f'smtp_user = "{config.smtp_user}"',
        f'op_smtp_password_ref = "{config.op_smtp_password_ref}"',
    ]
    path.write_text("\n".join(lines) + "\n")
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_config.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add src/kobokindle/config.py tests/test_config.py
git commit -m "feat: add config module with TOML loading and 1Password integration"
```

---

### Task 3: Matcher Module

**Files:**
- Create: `src/kobokindle/matcher.py`
- Create: `tests/test_matcher.py`

Pure function: takes a query string and a list of books, returns ranked matches. No external dependencies.

**Step 1: Write failing tests**

Create `tests/test_matcher.py`:

```python
from dataclasses import dataclass

from kobokindle.matcher import find_books


@dataclass
class FakeBook:
    Title: str
    Author: str
    RevisionId: str


BOOKS = [
    FakeBook(Title="Guards! Guards!", Author="Terry Pratchett", RevisionId="aaa"),
    FakeBook(Title="Equal Rites", Author="Terry Pratchett", RevisionId="bbb"),
    FakeBook(Title="A Hat Full of Sky", Author="Terry Pratchett", RevisionId="ccc"),
    FakeBook(Title="Carpe Jugulum", Author="Terry Pratchett", RevisionId="ddd"),
    FakeBook(Title="The Guard", Author="Someone Else", RevisionId="eee"),
]


class TestFindBooks:
    def test_exact_substring_match(self):
        results = find_books("Guards! Guards!", BOOKS)
        assert len(results) >= 1
        assert results[0][0].Title == "Guards! Guards!"

    def test_partial_match(self):
        results = find_books("Guards", BOOKS)
        assert len(results) >= 1
        assert results[0][0].Title == "Guards! Guards!"

    def test_case_insensitive(self):
        results = find_books("guards", BOOKS)
        assert len(results) >= 1
        assert results[0][0].Title == "Guards! Guards!"

    def test_no_match_returns_empty(self):
        results = find_books("zzzznotabook", BOOKS)
        assert results == []

    def test_returns_multiple_ranked(self):
        results = find_books("Guard", BOOKS)
        assert len(results) >= 2
        # "Guards! Guards!" should rank above "The Guard" (substring match)
        titles = [r[0].Title for r in results]
        assert "Guards! Guards!" in titles

    def test_max_results_limits_output(self):
        results = find_books("t", BOOKS, max_results=2)
        assert len(results) <= 2

    def test_score_is_between_0_and_1(self):
        results = find_books("Guards", BOOKS)
        for _, score in results:
            assert 0.0 <= score <= 1.0
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_matcher.py -v
```

Expected: FAIL (module not found)

**Step 3: Implement matcher module**

Create `src/kobokindle/matcher.py`:

```python
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def find_books(
    query: str,
    books: list[Any],
    threshold: float = 0.3,
    max_results: int = 5,
) -> list[tuple[Any, float]]:
    """Find books matching a query string, ranked by relevance.

    Each book must have a .Title attribute.
    Returns list of (book, score) tuples, highest score first.
    """
    query_lower = query.lower()
    scored = []

    for book in books:
        title_lower = book.Title.lower()

        if query_lower in title_lower:
            # Substring match: score based on how much of the title the query covers
            score = len(query_lower) / len(title_lower)
            # Ensure substring matches always rank above fuzzy-only matches
            score = max(score, 0.5)
        else:
            score = SequenceMatcher(None, query_lower, title_lower).ratio()

        scored.append((book, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [(book, score) for book, score in scored[:max_results] if score >= threshold]
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_matcher.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add src/kobokindle/matcher.py tests/test_matcher.py
git commit -m "feat: add fuzzy book title matcher using difflib"
```

---

### Task 4: Kindle Emailer Module

**Files:**
- Create: `src/kobokindle/kindle.py`
- Create: `tests/test_kindle.py`

Constructs a MIME email with the EPUB attached and sends via SMTP. Tests verify email construction without actually sending.

**Step 1: Write failing tests**

Create `tests/test_kindle.py`:

```python
import email
from email import policy
from pathlib import Path

from kobokindle.kindle import build_kindle_email


class TestBuildKindleEmail:
    def test_builds_email_with_epub_attachment(self, tmp_path):
        epub_file = tmp_path / "test-book.epub"
        epub_file.write_bytes(b"fake epub content")

        msg = build_kindle_email(
            from_addr="me@gmail.com",
            to_addr="me@kindle.com",
            epub_path=epub_file,
        )

        assert msg["From"] == "me@gmail.com"
        assert msg["To"] == "me@kindle.com"
        assert msg["Subject"] == "convert"

        # Should have an attachment
        attachments = [
            part
            for part in msg.walk()
            if part.get_content_disposition() == "attachment"
        ]
        assert len(attachments) == 1
        assert attachments[0].get_filename() == "test-book.epub"
        assert attachments[0].get_payload(decode=True) == b"fake epub content"

    def test_subject_is_convert_for_kindle(self, tmp_path):
        """Amazon converts EPUB to Kindle format when subject is 'convert'."""
        epub_file = tmp_path / "book.epub"
        epub_file.write_bytes(b"data")

        msg = build_kindle_email(
            from_addr="me@gmail.com",
            to_addr="me@kindle.com",
            epub_path=epub_file,
        )
        assert msg["Subject"] == "convert"

    def test_attachment_content_type_is_epub(self, tmp_path):
        epub_file = tmp_path / "book.epub"
        epub_file.write_bytes(b"data")

        msg = build_kindle_email(
            from_addr="me@gmail.com",
            to_addr="me@kindle.com",
            epub_path=epub_file,
        )
        attachments = [
            part
            for part in msg.walk()
            if part.get_content_disposition() == "attachment"
        ]
        assert attachments[0].get_content_type() == "application/epub+zip"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_kindle.py -v
```

Expected: FAIL (module not found)

**Step 3: Implement kindle emailer**

Create `src/kobokindle/kindle.py`:

```python
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from pathlib import Path


def build_kindle_email(
    from_addr: str,
    to_addr: str,
    epub_path: Path,
) -> EmailMessage:
    """Build an email with EPUB attached, subject 'convert' for Kindle."""
    msg = EmailMessage()
    msg["From"] = from_addr
    msg["To"] = to_addr
    msg["Subject"] = "convert"

    epub_data = epub_path.read_bytes()
    msg.add_attachment(
        epub_data,
        maintype="application",
        subtype="epub+zip",
        filename=epub_path.name,
    )
    return msg


def send_to_kindle(
    smtp_host: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    from_addr: str,
    kindle_email: str,
    epub_path: Path,
) -> None:
    """Send an EPUB to a Kindle email address via SMTP."""
    msg = build_kindle_email(from_addr, kindle_email, epub_path)
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_kindle.py -v
```

Expected: all PASS

**Step 5: Commit**

```bash
git add src/kobokindle/kindle.py tests/test_kindle.py
git commit -m "feat: add Kindle emailer with EPUB attachment"
```

---

### Task 5: Kobo Wrapper Module

**Files:**
- Create: `src/kobokindle/kobo.py`

This is a thin wrapper around kobodl's Python API. Since it requires real Kobo authentication to test, we keep it minimal and test it at integration level in Task 7.

**Step 1: Implement kobo wrapper**

Create `src/kobokindle/kobo.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Any


def list_books() -> list[Any]:
    """List all books in the user's Kobo library.

    Returns kobodl Book objects with .Title, .Author, .RevisionId attributes.
    """
    from kobodl import actions
    from kobodl.globals import Globals

    Globals.load()
    users = Globals.Settings.UserList.users
    if not users:
        raise RuntimeError(
            "No Kobo users configured. Run 'kobokindle setup' first."
        )
    return actions.ListBooks(users, listAll=False, exportFile=None)


def download_book(revision_id: str, output_dir: Path) -> Path:
    """Download a book by revision ID, stripping DRM. Returns path to EPUB."""
    from kobodl import actions
    from kobodl.globals import Globals

    Globals.load()
    users = Globals.Settings.UserList.users
    if not users:
        raise RuntimeError(
            "No Kobo users configured. Run 'kobokindle setup' first."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    result = actions.GetBookOrBooks(
        user=users[0],
        outputPath=str(output_dir),
        formatStr="{Author} - {Title}",
        productId=revision_id,
    )
    if result is None:
        raise RuntimeError(f"Failed to download book {revision_id}")
    return Path(result)


def initiate_login() -> tuple[str, str]:
    """Start Kobo device activation. Returns (activation_url, code).

    The user must open the URL in a browser, log in, and enter the code.
    """
    from kobodl import actions
    from kobodl.globals import Globals
    from kobodl.kobodl import User

    Globals.load()
    user = User()
    Globals.Settings.UserList.users.append(user)
    url, code = actions.InitiateLogin(user)
    return url, code


def complete_login() -> bool:
    """Poll for login completion. Returns True if activation succeeded."""
    from kobodl import actions
    from kobodl.globals import Globals

    Globals.load()
    users = Globals.Settings.UserList.users
    user = users[-1]  # most recently added
    return actions.CheckActivation(user)
```

> **Note to implementer:** The kobodl internal API may differ slightly from what's documented here. When implementing this task, verify the actual import paths and function signatures by checking `kobodl`'s source code after installing it. The key functions to verify:
> - How `Settings` / `Globals` is loaded
> - `actions.ListBooks` signature
> - `actions.GetBookOrBooks` signature and return type
> - `actions.InitiateLogin` and `actions.CheckActivation` signatures
> - The `User` class constructor

**Step 2: Verify it imports without error**

```bash
uv run python -c "from kobokindle.kobo import list_books, download_book; print('ok')"
```

Expected: `ok` (the lazy imports mean it won't fail even without Kobo auth)

**Step 3: Commit**

```bash
git add src/kobokindle/kobo.py
git commit -m "feat: add thin kobodl wrapper for listing and downloading books"
```

---

### Task 6: CLI Module

**Files:**
- Create: `src/kobokindle/cli.py`
- Create: `tests/test_cli.py`

argparse-based CLI with subcommands: `setup`, `list`, `send`, `download`.

**Step 1: Write failing tests**

Create `tests/test_cli.py`:

```python
import sys

from kobokindle.cli import build_parser


class TestArgParsing:
    def setup_method(self):
        self.parser = build_parser()

    def test_list_command(self):
        args = self.parser.parse_args(["list"])
        assert args.command == "list"

    def test_send_command_with_query(self):
        args = self.parser.parse_args(["send", "Guards"])
        assert args.command == "send"
        assert args.query == "Guards"

    def test_send_with_yes_flag(self):
        args = self.parser.parse_args(["send", "--yes", "Guards"])
        assert args.command == "send"
        assert args.yes is True

    def test_send_with_keep_flag(self):
        args = self.parser.parse_args(["send", "--keep", "Guards"])
        assert args.command == "send"
        assert args.keep is True

    def test_download_command_with_query(self):
        args = self.parser.parse_args(["download", "Guards"])
        assert args.command == "download"
        assert args.query == "Guards"

    def test_download_with_output_dir(self):
        args = self.parser.parse_args(["download", "--output", "/tmp/books", "Guards"])
        assert args.command == "download"
        assert args.output == "/tmp/books"

    def test_setup_command(self):
        args = self.parser.parse_args(["setup"])
        assert args.command == "setup"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: FAIL (module not found)

**Step 3: Implement CLI module**

Create `src/kobokindle/cli.py`:

```python
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from kobokindle.config import Config, DEFAULT_CONFIG_PATH, load_config, save_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kobokindle",
        description="Get Kobo ebooks onto your Kindle",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # setup
    sub.add_parser("setup", help="Configure kobokindle (one-time setup)")

    # list
    sub.add_parser("list", help="List your Kobo library")

    # send
    send_parser = sub.add_parser("send", help="Download a book and send to Kindle")
    send_parser.add_argument("query", help="Book title to search for")
    send_parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    send_parser.add_argument(
        "--keep", action="store_true", help="Keep downloaded EPUB after sending"
    )

    # download
    dl_parser = sub.add_parser("download", help="Download a book (don't send)")
    dl_parser.add_argument("query", help="Book title to search for")
    dl_parser.add_argument("--output", "-o", default=".", help="Output directory")

    return parser


def cmd_setup() -> None:
    """Interactive setup: configure SMTP, authenticate with Kobo."""
    from kobokindle.kobo import initiate_login, complete_login

    print("=== kobokindle setup ===\n")

    kindle_email = input("Kindle email (e.g. you_123@kindle.com): ").strip()
    smtp_host = input("SMTP host [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
    smtp_port_str = input("SMTP port [587]: ").strip() or "587"
    smtp_user = input("SMTP username (your email): ").strip()
    op_ref = input("1Password ref for SMTP password (op://...): ").strip()

    config = Config(
        kindle_email=kindle_email,
        smtp_host=smtp_host,
        smtp_port=int(smtp_port_str),
        smtp_user=smtp_user,
        op_smtp_password_ref=op_ref,
    )
    save_config(config)
    print(f"\nConfig saved to {DEFAULT_CONFIG_PATH}")

    print("\n--- Kobo Authentication ---")
    print("This will open a browser-based login flow.")
    url, code = initiate_login()
    print(f"\n1. Open this URL: {url}")
    print(f"2. Log in and enter this code: {code}")
    input("\nPress Enter when done...")
    if complete_login():
        print("Kobo authentication successful!")
    else:
        print("Authentication failed. Try running 'kobokindle setup' again.", file=sys.stderr)
        sys.exit(1)


def cmd_list() -> None:
    """List books in Kobo library."""
    from kobokindle.kobo import list_books

    books = list_books()
    if not books:
        print("No books found.")
        return

    for book in books:
        print(f"  {book.Title}  —  {book.Author}")


def cmd_send(query: str, yes: bool = False, keep: bool = False) -> None:
    """Find a book, download it, and send to Kindle."""
    from kobokindle.kindle import send_to_kindle
    from kobokindle.kobo import download_book, list_books
    from kobokindle.matcher import find_books

    config = load_config()
    books = list_books()
    matches = find_books(query, books)

    if not matches:
        print(f"No books matching '{query}' found.")
        sys.exit(1)

    book, score = matches[0]
    if not yes:
        print(f"Found: {book.Title} by {book.Author}")
        confirm = input("Send to Kindle? [Y/n] ").strip().lower()
        if confirm and confirm != "y":
            print("Cancelled.")
            return

    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Downloading '{book.Title}'...")
        epub_path = download_book(book.RevisionId, Path(tmpdir))
        print(f"Downloaded: {epub_path.name}")

        print(f"Sending to {config.kindle_email}...")
        password = config.get_smtp_password()
        send_to_kindle(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_user=config.smtp_user,
            smtp_password=password,
            from_addr=config.smtp_user,
            kindle_email=config.kindle_email,
            epub_path=epub_path,
        )
        print("Sent!")

        if keep:
            dest = Path.cwd() / epub_path.name
            epub_path.rename(dest)
            print(f"Kept: {dest}")


def cmd_download(query: str, output: str = ".") -> None:
    """Find a book and download it."""
    from kobokindle.kobo import download_book, list_books
    from kobokindle.matcher import find_books

    books = list_books()
    matches = find_books(query, books)

    if not matches:
        print(f"No books matching '{query}' found.")
        sys.exit(1)

    book, score = matches[0]
    print(f"Found: {book.Title} by {book.Author}")

    print(f"Downloading '{book.Title}'...")
    epub_path = download_book(book.RevisionId, Path(output))
    print(f"Downloaded: {epub_path}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup()
    elif args.command == "list":
        cmd_list()
    elif args.command == "send":
        cmd_send(args.query, yes=args.yes, keep=args.keep)
    elif args.command == "download":
        cmd_download(args.query, output=args.output)
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: all PASS

**Step 5: Verify CLI entry point works**

```bash
uv run kobokindle --help
uv run kobokindle send --help
```

Expected: help output showing subcommands and flags

**Step 6: Commit**

```bash
git add src/kobokindle/cli.py tests/test_cli.py
git commit -m "feat: add CLI with setup, list, send, download commands"
```

---

### Task 7: Integration Test — End to End

**Files:** None new — uses the tool as built.

This task verifies the full pipeline works with a real Kobo account and a real book.

**Step 1: Ensure kobodl is authenticated**

If not already done during `kobokindle setup`:

```bash
uv run kobodl user list
```

If no users, run:

```bash
uv run kobokindle setup
```

Follow the browser-based auth flow.

**Step 2: List books**

```bash
uv run kobokindle list
```

Expected: A list of Terry Pratchett books (and others) from the Kobo library.

**Step 3: Download Guards! Guards!**

```bash
uv run kobokindle download "Guards Guards"
```

Expected: Downloads DRM-free EPUB to current directory. Verify the file exists and is a valid EPUB (it's a zip file):

```bash
file *.epub
```

**Step 4: Send Guards! Guards! to Kindle**

```bash
uv run kobokindle send "Guards Guards" --yes
```

Expected: Downloads, emails to Kindle address. Check Kindle device/app for the book.

**Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: All unit tests pass.

**Step 6: Commit any fixes**

```bash
git add -A  # after reviewing git status
git commit -m "fix: integration test adjustments"
```

---

### Task 8: Add .gitignore and Final Cleanup

**Files:**
- Create: `.gitignore`

**Step 1: Create .gitignore**

```
__pycache__/
*.pyc
*.egg-info/
dist/
.venv/
*.epub
```

**Step 2: Run full test suite one last time**

```bash
uv run pytest -v
```

Expected: All pass.

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore"
```
