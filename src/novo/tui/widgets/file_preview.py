"""File content preview widget with syntax highlighting."""

from __future__ import annotations

from pathlib import Path

from pygments.lexers import guess_lexer_for_filename
from pygments.util import ClassNotFound
from rich.syntax import Syntax
from rich.text import Text

from textual.widgets import Static

MAX_PREVIEW_BYTES = 200 * 1024  # 200KB
BINARY_SAMPLE_BYTES = 1024


def is_binary(sample: bytes) -> bool:
    """Heuristic: a NUL byte in the first chunk usually means binary."""
    return b"\x00" in sample


def detect_lexer(filename: str, content: str) -> str:
    """Return a Pygments lexer alias suitable for `rich.syntax.Syntax`."""
    try:
        lexer = guess_lexer_for_filename(filename, content)
    except ClassNotFound:
        return "text"
    return lexer.aliases[0] if lexer.aliases else "text"


class FilePreview(Static):
    """Renders a syntax-highlighted preview of a file."""

    DEFAULT_CSS = """
    FilePreview {
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self.current_path: Path | None = None

    def show_path(self, path: Path | None) -> None:
        """Update the preview to show `path`, or a placeholder."""
        self.current_path = path
        if path is None:
            self.update(Text("(no file selected)", style="dim italic"))
            return
        if not path.exists():
            self.update(Text(f"(not found: {path})", style="dim italic"))
            return
        if not path.is_file():
            self.update(Text("(not a file)", style="dim italic"))
            return

        try:
            size = path.stat().st_size
        except OSError as exc:
            self.update(Text(f"(stat failed: {exc})", style="dim italic"))
            return

        if size > MAX_PREVIEW_BYTES:
            self.update(
                Text(
                    f"(file too large to preview: {size:,} bytes)",
                    style="dim italic",
                )
            )
            return

        try:
            data = path.read_bytes()
        except OSError as exc:
            self.update(Text(f"(read failed: {exc})", style="dim italic"))
            return

        if is_binary(data[:BINARY_SAMPLE_BYTES]):
            self.update(Text("(binary file)", style="dim italic"))
            return

        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            self.update(Text("(non-UTF-8 file)", style="dim italic"))
            return

        lexer = detect_lexer(path.name, text)
        self.update(
            Syntax(
                text,
                lexer,
                theme="monokai",
                line_numbers=True,
                word_wrap=False,
                background_color="default",
            )
        )

    def clear(self) -> None:
        self.current_path = None
        self.update(Text("(no file selected)", style="dim italic"))
