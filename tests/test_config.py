import os
import tempfile
from pathlib import Path

from kobo2kindle.config import Config, load_config, save_config


class TestLoadConfig:
    def test_loads_config_with_password_cmd(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'kindle_email = "me@kindle.com"\n'
            'smtp_host = "smtp.gmail.com"\n'
            "smtp_port = 587\n"
            'smtp_user = "me@gmail.com"\n'
            'smtp_password_cmd = "op read op://Vault/Item/password"\n'
        )
        config = load_config(config_file)
        assert config.kindle_email == "me@kindle.com"
        assert config.smtp_host == "smtp.gmail.com"
        assert config.smtp_port == 587
        assert config.smtp_user == "me@gmail.com"
        assert config.smtp_password_cmd == "op read op://Vault/Item/password"

    def test_password_cmd_is_optional(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config_file.write_text(
            'kindle_email = "me@kindle.com"\n'
            'smtp_host = "smtp.gmail.com"\n'
            "smtp_port = 587\n"
            'smtp_user = "me@gmail.com"\n'
        )
        config = load_config(config_file)
        assert config.smtp_password_cmd is None

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
    def test_round_trips_with_password_cmd(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
            smtp_password_cmd="op read op://Vault/Item/password",
        )
        save_config(config, config_file)
        loaded = load_config(config_file)
        assert loaded.kindle_email == config.kindle_email
        assert loaded.smtp_host == config.smtp_host
        assert loaded.smtp_port == config.smtp_port
        assert loaded.smtp_user == config.smtp_user
        assert loaded.smtp_password_cmd == config.smtp_password_cmd

    def test_round_trips_without_password_cmd(self, tmp_path):
        config_file = tmp_path / "config.toml"
        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
        )
        save_config(config, config_file)
        loaded = load_config(config_file)
        assert loaded.smtp_password_cmd is None

    def test_creates_parent_dirs(self, tmp_path):
        config_file = tmp_path / "nested" / "dir" / "config.toml"
        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
            smtp_password_cmd="pass show smtp",
        )
        save_config(config, config_file)
        assert config_file.exists()


class TestGetSmtpPassword:
    def test_runs_password_cmd(self, monkeypatch):
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
            smtp_password_cmd="op read op://Vault/Item/password",
        )
        password = config.get_smtp_password()
        assert password == "my-secret-password"
        assert calls[0] == ["op", "read", "op://Vault/Item/password"]

    def test_env_var_overrides_cmd(self, monkeypatch):
        monkeypatch.setenv("KOBO2KINDLE_SMTP_PASSWORD", "env-password")

        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
            smtp_password_cmd="op read op://Vault/Item/password",
        )
        password = config.get_smtp_password()
        assert password == "env-password"

    def test_env_var_works_without_cmd(self, monkeypatch):
        monkeypatch.setenv("KOBO2KINDLE_SMTP_PASSWORD", "env-password")

        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
        )
        password = config.get_smtp_password()
        assert password == "env-password"

    def test_raises_when_no_cmd_and_no_env(self):
        config = Config(
            kindle_email="me@kindle.com",
            smtp_host="smtp.gmail.com",
            smtp_port=587,
            smtp_user="me@gmail.com",
        )
        try:
            config.get_smtp_password()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "KOBO2KINDLE_SMTP_PASSWORD" in str(e)
