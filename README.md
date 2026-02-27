# kobokindle

Get your purchased Kobo ebooks onto your Kindle.

Downloads books from your Kobo library, strips DRM, and emails them to your Kindle — all in one command.

## Setup

Requires Python 3.11-3.12, [uv](https://docs.astral.sh/uv/), and [1Password CLI](https://developer.1password.com/docs/cli/) (`op`).

```bash
git clone <repo-url>
cd kobokindle
uv sync
uv run kobokindle setup
```

`setup` walks you through:
- Configuring your Kindle email address and SMTP credentials
- Authenticating with your Kobo account (browser-based activation flow)

SMTP password is fetched from 1Password at runtime via `op read` — no secrets stored on disk.

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
op_smtp_password_ref = "op://Vault/Item/password"
```

Kobo auth tokens are managed by kobodl at `~/.config/kobodl.json`.

## Dependencies

- [kobodl](https://github.com/subdavis/kobo-book-downloader) — Kobo API client + DRM removal
- Python stdlib for everything else (email, config, fuzzy matching)
