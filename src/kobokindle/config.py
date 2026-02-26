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
