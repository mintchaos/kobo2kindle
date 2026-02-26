# kobokindle CLI Tool Design

## Problem

Get DRM-protected purchased Kobo ebooks onto a Kindle with a single command.

## Solution

A Python CLI that wraps `kobodl` (download + DRM removal) and sends the resulting DRM-free EPUB to a Kindle via email. Amazon handles EPUB-to-Kindle conversion server-side.

## Usage

```
kobokindle setup            # one-time: configure Kindle email, SMTP, authenticate with Kobo
kobokindle list              # show your Kobo library
kobokindle send "Guards"     # find book, download, strip DRM, email to Kindle
kobokindle download "Guards" # just download, don't send
```

## Architecture

### Pipeline

```
kobodl (download + strip DRM) → DRM-free EPUB → email to @kindle.com
```

### Components

1. **kobodl wrapper** - Calls `kobodl` as a subprocess for auth, listing, and downloading. No need to reinvent its Kobo API integration.

2. **Book finder** - Fuzzy-matches user input against the Kobo library so you don't need exact titles or revision IDs. Shows the match and asks for confirmation before proceeding.

3. **Kindle emailer** - Sends EPUB as an attachment to the configured `@kindle.com` address via SMTP. Uses Python stdlib (`smtplib`, `email`).

4. **Config** - TOML file at `~/.config/kobokindle/config.toml`. SMTP password fetched from 1Password at runtime via `op read`.

### Config file

```toml
kindle_email = "yourname@kindle.com"
smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "you@gmail.com"
op_smtp_password_ref = "op://Vault/ItemName/password"
```

No secrets stored on disk. Kobo auth tokens are managed by `kobodl` in its own config.

### Flow: `kobokindle send "Guards"`

1. Run `kobodl book list` and parse output
2. Fuzzy match "Guards" against titles
3. Show match, ask confirmation (skip with `--yes`)
4. Run `kobodl book get <revision-id>` to download DRM-free EPUB
5. Fetch SMTP password via `op read`
6. Email EPUB to Kindle address
7. Clean up temp file (keep with `--keep`)

## Dependencies

- Python 3.11+
- `kobodl` (via pip/pipx)
- `op` CLI (1Password, already installed)
- Email account with app password in 1Password

## Scope boundaries

- No GUI, no Calibre, no format conversion
- No library management - one-way pipe from Kobo to Kindle
- No batch processing in v1 (one book at a time)
- Approach A chosen over heavier Calibre-based pipelines

## Key decisions

- **kobodl over Kobo web download**: Web download gives ACSM files requiring Adobe Digital Editions. kobodl uses Kobo's API directly and strips KDRM in one step.
- **Email over Send-to-Kindle app**: Email is scriptable with stdlib, no extra app install needed.
- **No format conversion**: Amazon accepts EPUB natively via Send-to-Kindle email. Server-side conversion is good enough.
- **1Password for credentials**: `op read` at runtime, no secrets on disk.
