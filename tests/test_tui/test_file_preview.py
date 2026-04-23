"""Tests for the FilePreview helpers."""

from novo.tui.widgets.file_preview import detect_lexer, is_binary


def test_is_binary_detects_nul_byte():
    assert is_binary(b"hello\x00world")
    assert is_binary(b"\x00")


def test_is_binary_text_is_not_binary():
    assert not is_binary(b"plain text content\n# python comment")


def test_detect_lexer_python():
    assert detect_lexer("foo.py", "def foo(): pass") == "python"


def test_detect_lexer_toml():
    lexer = detect_lexer("seed.toml", "[seed]\nname = 'x'")
    # pygments may report this as "toml"
    assert lexer == "toml"


def test_detect_lexer_unknown_falls_back_to_text():
    assert detect_lexer("file.unknownext", "anything") == "text"
