"""Read-only file tree preview widget."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from rich.text import Text
from rich.tree import Tree

from textual.widgets import Static

DEFAULT_EXCLUDES: tuple[str, ...] = (
    ".venv",
    ".git",
    "__pycache__",
    "*.pyc",
    ".DS_Store",
    "node_modules",
)

DEFAULT_MAX_DEPTH = 3
DEFAULT_MAX_ENTRIES = 200


def _excluded(name: str, patterns: tuple[str, ...]) -> bool:
    return any(fnmatch(name, p) for p in patterns)


def _label(path: Path, *, is_dir: bool) -> Text:
    label = Text()
    if is_dir:
        label.append(f"{path.name}/", style="#5DE4C7 bold")
    else:
        label.append(path.name)
    return label


def build_tree(
    root: Path,
    *,
    max_depth: int = DEFAULT_MAX_DEPTH,
    excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
    max_entries: int = DEFAULT_MAX_ENTRIES,
) -> Tree:
    """Build a Rich Tree for the given directory, depth-limited and filtered."""
    tree = Tree(_label(root, is_dir=True), guide_style="dim")
    _populate(
        root,
        tree,
        depth=0,
        max_depth=max_depth,
        excludes=excludes,
        max_entries=max_entries,
    )
    return tree


def _populate(
    path: Path,
    branch: Tree,
    *,
    depth: int,
    max_depth: int,
    excludes: tuple[str, ...],
    max_entries: int,
) -> None:
    if depth >= max_depth:
        return

    try:
        entries = sorted(
            path.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower()),
        )
    except (PermissionError, OSError):
        branch.add(Text("(unreadable)", style="dim italic"))
        return

    visible = [e for e in entries if not _excluded(e.name, excludes)]
    truncated = max(0, len(visible) - max_entries)
    shown = visible[:max_entries] if truncated else visible

    for entry in shown:
        if entry.is_dir():
            sub = branch.add(_label(entry, is_dir=True))
            _populate(
                entry,
                sub,
                depth=depth + 1,
                max_depth=max_depth,
                excludes=excludes,
                max_entries=max_entries,
            )
        else:
            branch.add(_label(entry, is_dir=False))

    if truncated:
        branch.add(Text(f"… ({truncated} more)", style="dim italic"))


class FileTreeWidget(Static):
    """Render a depth-limited, filtered tree of a directory."""

    DEFAULT_CSS = """
    FileTreeWidget {
        padding: 0 2;
        height: auto;
    }
    """

    def __init__(
        self,
        *,
        max_depth: int = DEFAULT_MAX_DEPTH,
        excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
        max_entries: int = DEFAULT_MAX_ENTRIES,
        **kwargs,
    ) -> None:
        super().__init__("", **kwargs)
        self._max_depth = max_depth
        self._excludes = excludes
        self._max_entries = max_entries

    def show_path(self, path: Path | None) -> None:
        """Update the widget to render the tree rooted at `path`."""
        if path is None:
            self.update(Text("(no path)", style="dim italic"))
            return
        if not path.exists():
            self.update(Text(f"(not found: {path})", style="dim italic"))
            return
        if not path.is_dir():
            self.update(Text(f"(not a directory: {path})", style="dim italic"))
            return

        self.update(
            build_tree(
                path,
                max_depth=self._max_depth,
                excludes=self._excludes,
                max_entries=self._max_entries,
            )
        )

    def clear(self) -> None:
        """Clear the displayed tree."""
        self.update("")
