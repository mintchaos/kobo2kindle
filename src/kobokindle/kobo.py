from __future__ import annotations

from pathlib import Path
from typing import Any


def _load_settings() -> None:
    """Ensure Globals.Settings is initialized from the default config path."""
    from kobodl.globals import Globals
    from kobodl.settings import Settings

    if Globals.Settings is None:
        Globals.Settings = Settings()


def _get_users() -> list[Any]:
    from kobodl.globals import Globals

    _load_settings()
    users = Globals.Settings.UserList.users
    if not users:
        raise RuntimeError(
            "No Kobo users configured. Run 'kobokindle setup' first."
        )
    return users


def list_books() -> list[Any]:
    """Return all unread books across all configured Kobo users."""
    from kobodl import actions

    users = _get_users()
    return list(actions.ListBooks(users, listAll=False, exportFile=None))


def download_book(revision_id: str, output_dir: Path) -> Path:
    """Download a single book by revision ID into output_dir. Returns the output file path."""
    from kobodl import actions

    users = _get_users()
    output_dir.mkdir(parents=True, exist_ok=True)
    result = actions.GetBookOrBooks(
        user=users[0],
        outputPath=str(output_dir),
        productId=revision_id,
    )
    if result is None:
        raise RuntimeError(f"Failed to download book {revision_id}")
    return Path(result)


def initiate_login() -> tuple[str, str]:
    """Start the Kobo web activation flow.

    Returns (check_url, activation_code). The check_url is needed
    by complete_login to poll for activation status.
    """
    from kobodl.globals import Globals
    from kobodl.settings import User

    from kobodl import actions

    _load_settings()
    user = User()
    check_url, code = actions.InitiateLogin(user)
    # Stash the user so complete_login can find it
    Globals.Settings.UserList.users.append(user)
    return check_url, code


def complete_login(check_url: str) -> bool:
    """Poll the Kobo activation endpoint. Returns True if login succeeded.

    The check_url must be the URL returned by initiate_login().
    """
    from kobodl import actions
    from kobodl.globals import Globals

    _load_settings()
    users = Globals.Settings.UserList.users
    if not users:
        raise RuntimeError("No pending user. Call initiate_login() first.")
    user = users[-1]
    success = actions.CheckActivation(user, check_url)
    if success:
        Globals.Settings.Save()
    return success
