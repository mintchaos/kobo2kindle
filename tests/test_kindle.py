import email
from email import policy
from pathlib import Path

from kobokindle.kindle import build_kindle_email


class TestBuildKindleEmail:
    def test_builds_email_with_epub_attachment(self, tmp_path):
        epub_file = tmp_path / "test-book.epub"
        epub_file.write_bytes(b"fake epub content")

        msg = build_kindle_email(
            from_addr="me@gmail.com",
            to_addr="me@kindle.com",
            epub_path=epub_file,
        )

        assert msg["From"] == "me@gmail.com"
        assert msg["To"] == "me@kindle.com"
        assert msg["Subject"] == "convert"

        attachments = [
            part
            for part in msg.walk()
            if part.get_content_disposition() == "attachment"
        ]
        assert len(attachments) == 1
        assert attachments[0].get_filename() == "test-book.epub"
        assert attachments[0].get_payload(decode=True) == b"fake epub content"

    def test_subject_is_convert_for_kindle(self, tmp_path):
        """Amazon converts EPUB to Kindle format when subject is 'convert'."""
        epub_file = tmp_path / "book.epub"
        epub_file.write_bytes(b"data")

        msg = build_kindle_email(
            from_addr="me@gmail.com",
            to_addr="me@kindle.com",
            epub_path=epub_file,
        )
        assert msg["Subject"] == "convert"

    def test_attachment_content_type_is_epub(self, tmp_path):
        epub_file = tmp_path / "book.epub"
        epub_file.write_bytes(b"data")

        msg = build_kindle_email(
            from_addr="me@gmail.com",
            to_addr="me@kindle.com",
            epub_path=epub_file,
        )
        attachments = [
            part
            for part in msg.walk()
            if part.get_content_disposition() == "attachment"
        ]
        assert attachments[0].get_content_type() == "application/epub+zip"
