from __future__ import annotations

import os
import shlex
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "kobo2kindle" / "config.toml"

ENV_VAR = "KOBO2KINDLE_SMTP_PASSWORD"

REQUIRED_FIELDS = [
    "kindle_email",
    "smtp_host",
    "smtp_port",
    "smtp_user",
]


@dataclass
class Config:
    kindle_email: str
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password_cmd: str | None = None

    def get_smtp_password(self) -> str:
        env_password = os.environ.get(ENV_VAR)
        if env_password:
            return env_password

        if self.smtp_password_cmd:
            result = subprocess.run(
                shlex.split(self.smtp_password_cmd),
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()

        raise RuntimeError(
            f"No SMTP password configured. Either set {ENV_VAR} or add "
            "smtp_password_cmd to your config file."
        )


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> Config:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    for field_name in REQUIRED_FIELDS:
        if field_name not in data:
            raise KeyError(f"Missing required config field: {field_name}")
    return Config(
        kindle_email=data["kindle_email"],
        smtp_host=data["smtp_host"],
        smtp_port=data["smtp_port"],
        smtp_user=data["smtp_user"],
        smtp_password_cmd=data.get("smtp_password_cmd"),
    )


def save_config(config: Config, path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f'kindle_email = "{config.kindle_email}"',
        f'smtp_host = "{config.smtp_host}"',
        f"smtp_port = {config.smtp_port}",
        f'smtp_user = "{config.smtp_user}"',
    ]
    if config.smtp_password_cmd:
        lines.append(f'smtp_password_cmd = "{config.smtp_password_cmd}"')
    path.write_text("\n".join(lines) + "\n")
