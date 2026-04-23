"""Tests for the FileTreeWidget tree-builder."""

from io import StringIO

from rich.console import Console

from novo.tui.widgets.file_tree import build_tree


def _render(tree) -> str:
    buf = StringIO()
    Console(file=buf, width=120, color_system=None).print(tree)
    return buf.getvalue()


def test_build_tree_includes_files_and_dirs(tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("")

    out = _render(build_tree(tmp_path))

    assert "a.py" in out
    assert "sub/" in out
    assert "b.py" in out


def test_build_tree_excludes_default_patterns(tmp_path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib").mkdir()
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "thing.pyc").write_text("")
    (tmp_path / "keep.py").write_text("")

    out = _render(build_tree(tmp_path))

    assert "keep.py" in out
    assert ".venv" not in out
    assert "__pycache__" not in out
    assert "thing.pyc" not in out


def test_build_tree_respects_max_depth(tmp_path):
    deep = tmp_path / "l1" / "l2" / "l3" / "l4"
    deep.mkdir(parents=True)
    (deep / "deep.txt").write_text("")
    (tmp_path / "l1" / "shallow.txt").write_text("")

    out = _render(build_tree(tmp_path, max_depth=2))

    assert "shallow.txt" in out
    assert "deep.txt" not in out


def test_build_tree_truncates_large_dirs(tmp_path):
    for i in range(10):
        (tmp_path / f"f{i:02d}.txt").write_text("")

    out = _render(build_tree(tmp_path, max_entries=3))

    assert "f00.txt" in out
    assert "f02.txt" in out
    assert "f09.txt" not in out
    assert "more" in out  # the "… (N more)" placeholder


def test_build_tree_dirs_sort_before_files(tmp_path):
    (tmp_path / "zzz_file.txt").write_text("")
    (tmp_path / "aaa_dir").mkdir()

    out = _render(build_tree(tmp_path))

    # Directory should appear before the file even though it sorts later alphabetically
    assert out.index("aaa_dir") < out.index("zzz_file.txt")
