# kobokindle

Get your purchased Kobo ebooks onto your Kindle.

Downloads books from your Kobo library, strips DRM, and emails them to your Kindle — all in one command.

## Setup

Requires Python 3.11-3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd kobokindle
uv sync
uv run kobokindle setup
```

`setup` walks you through:
- Configuring your Kindle email address and SMTP credentials
- Authenticating with your Kobo account (browser-based activation flow)

## Usage

```bash
# List your Kobo library
kobokindle list

# Send a book to your Kindle
kobokindle send "Guards Guards"

# Skip confirmation prompt
kobokindle send "Night Watch" --yes

# Keep a local copy of the EPUB
kobokindle send "Small Gods" --keep

# Download without sending
kobokindle download "Mort"
kobokindle download "Pyramids" --output ~/Books/
```

Book titles are fuzzy-matched — you don't need the exact title.

## How it works

1. **kobodl** downloads the book from Kobo's API and strips Kobo DRM
2. The DRM-free EPUB is emailed to your `@kindle.com` address
3. Amazon converts it to Kindle format server-side

## Config

Stored at `~/.config/kobokindle/config.toml`:

```toml
kindle_email = "you@kindle.com"
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "you@gmail.com"
smtp_password_cmd = "op read op://Vault/Item/password"
```

Kobo auth tokens are managed by kobodl at `~/.config/kobodl.json`.

### SMTP password

The `smtp_password_cmd` field runs a shell command at send time to fetch your password. Examples:

```toml
# 1Password
smtp_password_cmd = 'op read "op://Vault/Item/password"'

# pass (GNU Password Store)
smtp_password_cmd = "pass show email/smtp"

# macOS Keychain
smtp_password_cmd = "security find-generic-password -s kobokindle-smtp -w"

# gpg-encrypted file
smtp_password_cmd = "gpg --quiet --decrypt ~/.smtp-password.gpg"
```

Alternatively, skip `smtp_password_cmd` and set the `KOBOKINDLE_SMTP_PASSWORD` environment variable. The env var takes priority if both are set.

## Dependencies

- [kobodl](https://github.com/subdavis/kobo-book-downloader) — Kobo API client + DRM removal
- Python stdlib for everything else (email, config, fuzzy matching)
