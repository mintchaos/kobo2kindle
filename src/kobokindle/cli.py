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

    sub.add_parser("setup", help="Configure kobokindle (one-time setup)")
    sub.add_parser("list", help="List your Kobo library")

    send_parser = sub.add_parser("send", help="Download a book and send to Kindle")
    send_parser.add_argument("query", help="Book title to search for")
    send_parser.add_argument(
        "--yes", "-y", action="store_true", help="Skip confirmation prompt"
    )
    send_parser.add_argument(
        "--keep", action="store_true", help="Keep downloaded EPUB after sending"
    )

    dl_parser = sub.add_parser("download", help="Download a book (don't send)")
    dl_parser.add_argument("query", help="Book title to search for")
    dl_parser.add_argument("--output", "-o", default=".", help="Output directory")

    return parser


def cmd_setup() -> None:
    from kobokindle.kobo import initiate_login, complete_login

    print("=== kobokindle setup ===\n")

    kindle_email = input("Kindle email (e.g. you_123@kindle.com): ").strip()
    smtp_host = input("SMTP host [smtp.gmail.com]: ").strip() or "smtp.gmail.com"
    smtp_port_str = input("SMTP port [587]: ").strip() or "587"
    smtp_user = input("SMTP username (your email): ").strip()

    print("\nSMTP password command (runs at send time to fetch your password).")
    print("Examples:")
    print('  op read "op://Vault/Item/password"       (1Password)')
    print("  pass show email/smtp                     (pass)")
    print("  security find-generic-password -s smtp -w (macOS Keychain)")
    print()
    print("Leave blank to use KOBOKINDLE_SMTP_PASSWORD env var instead.")
    password_cmd = input("Password command: ").strip() or None

    config = Config(
        kindle_email=kindle_email,
        smtp_host=smtp_host,
        smtp_port=int(smtp_port_str),
        smtp_user=smtp_user,
        smtp_password_cmd=password_cmd,
    )
    save_config(config)
    print(f"\nConfig saved to {DEFAULT_CONFIG_PATH}")

    print("\n--- Kobo Authentication ---")
    check_url, code = initiate_login()
    print(f"\n1. Open: https://www.kobo.com/activate")
    print(f"2. Log in and enter this code: {code}")
    input("\nPress Enter when done...")
    if complete_login(check_url):
        print("Kobo authentication successful!")
    else:
        print(
            "Authentication failed. Try running 'kobokindle setup' again.",
            file=sys.stderr,
        )
        sys.exit(1)


def cmd_list() -> None:
    from kobokindle.kobo import list_books

    books = list_books()
    if not books:
        print("No books found.")
        return

    for book in books:
        print(f"  {book.Title}  —  {book.Author}")


def cmd_send(query: str, yes: bool = False, keep: bool = False) -> None:
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
