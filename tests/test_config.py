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
