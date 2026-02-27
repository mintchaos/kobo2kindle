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
