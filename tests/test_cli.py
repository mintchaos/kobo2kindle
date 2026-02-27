import sys

from kobokindle.cli import build_parser


class TestArgParsing:
    def setup_method(self):
        self.parser = build_parser()

    def test_list_command(self):
        args = self.parser.parse_args(["list"])
        assert args.command == "list"

    def test_send_command_with_query(self):
        args = self.parser.parse_args(["send", "Guards"])
        assert args.command == "send"
        assert args.query == "Guards"

    def test_send_with_yes_flag(self):
        args = self.parser.parse_args(["send", "--yes", "Guards"])
        assert args.command == "send"
        assert args.yes is True

    def test_send_with_keep_flag(self):
        args = self.parser.parse_args(["send", "--keep", "Guards"])
        assert args.command == "send"
        assert args.keep is True

    def test_download_command_with_query(self):
        args = self.parser.parse_args(["download", "Guards"])
        assert args.command == "download"
        assert args.query == "Guards"

    def test_download_with_output_dir(self):
        args = self.parser.parse_args(["download", "--output", "/tmp/books", "Guards"])
        assert args.command == "download"
        assert args.output == "/tmp/books"

    def test_setup_command(self):
        args = self.parser.parse_args(["setup"])
        assert args.command == "setup"
