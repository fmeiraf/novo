"""Tests for the pure SeedPicker row builder."""

from novo.models.scoped_seed import ScopedSeed
from novo.models.seed import Seed
from novo.tui.widgets.seed_picker import build_picker_rows


def _scoped(name: str, scope: str, *, remote: str | None = None, description: str = "") -> ScopedSeed:
    return ScopedSeed(
        seed=Seed(name=name, description=description),
        scope=scope,
        remote=remote,
    )


def _label(row) -> str:
    return row.label.plain


def test_build_rows_empty_returns_empty():
    assert build_picker_rows([]) == []


def test_build_rows_inserts_header_per_scope_in_order():
    seeds = [
        _scoped("alpha", "local"),
        _scoped("beta", "user"),
        _scoped("gamma", "remote", remote="team"),
        _scoped("delta", "builtin"),
    ]
    rows = build_picker_rows(seeds)
    # 4 headers + 4 seeds + 3 between-section spacers
    assert len(rows) == 11
    # Section headers carry a colored block prefix (`█ `); filter spacer rows
    # (empty labels) out before checking title order.
    headers = [r for r in rows if r.disabled and _label(r).strip()]
    assert _label(headers[0]) == "█ WORKSPACE"
    assert _label(headers[1]) == "█ USER"
    assert _label(headers[2]) == "█ REMOTE: team"
    assert _label(headers[3]) == "█ BUILTIN"


def test_build_rows_inserts_spacer_between_sections():
    # The Seeds tab and the New Experiment modal both ran together visually
    # because adjacent sections had no breathing room. A disabled spacer row
    # with an empty label sits between sections; navigation skips it.
    seeds = [_scoped("alpha", "user"), _scoped("beta", "builtin")]
    rows = build_picker_rows(seeds)
    # USER header, alpha, SPACER, BUILTIN header, beta
    assert len(rows) == 5
    assert rows[2].disabled is True
    assert _label(rows[2]) == ""


def test_build_rows_no_spacer_before_first_section():
    # The leading section should not have a spacer above it (that would
    # waste a row at the top of the picker).
    seeds = [_scoped("alpha", "user")]
    rows = build_picker_rows(seeds)
    # USER header + alpha, nothing else.
    assert len(rows) == 2
    assert _label(rows[0]).startswith("█ USER")


def test_build_rows_seed_row_has_identifier_as_id():
    seeds = [_scoped("alpha", "user")]
    rows = build_picker_rows(seeds)
    assert rows[0].disabled is True  # header
    assert rows[1].id == "user:alpha"
    assert rows[1].disabled is False


def test_build_rows_includes_description_when_present():
    seeds = [_scoped("alpha", "user", description="my seed")]
    rows = build_picker_rows(seeds)
    assert "my seed" in _label(rows[1])


def test_build_rows_marks_default():
    seeds = [_scoped("default", "builtin")]
    rows = build_picker_rows(seeds, default_identifier="builtin:default")
    assert "(default)" in _label(rows[1])


def test_build_rows_does_not_mark_non_default():
    seeds = [_scoped("default", "builtin"), _scoped("other", "user")]
    rows = build_picker_rows(seeds, default_identifier="builtin:default")
    # Find the "other" row and check no (default) badge.
    other = next(r for r in rows if r.id == "user:other")
    assert "(default)" not in _label(other)


def test_build_rows_filter_keeps_matching_name():
    seeds = [_scoped("alpha", "user"), _scoped("beta", "user")]
    rows = build_picker_rows(seeds, filter_query="alp")
    # 1 header + 1 match
    assert len(rows) == 2
    assert rows[1].id == "user:alpha"


def test_build_rows_filter_matches_description():
    seeds = [
        _scoped("a", "user", description="machine learning"),
        _scoped("b", "user", description="web app"),
    ]
    rows = build_picker_rows(seeds, filter_query="machine")
    assert len(rows) == 2
    assert rows[1].id == "user:a"


def test_build_rows_filter_hides_empty_section():
    seeds = [_scoped("alpha", "user"), _scoped("beta", "builtin")]
    rows = build_picker_rows(seeds, filter_query="alp")
    # Only USER section + alpha; BUILTIN header dropped entirely. No spacer
    # because there's only one section after filtering.
    assert len(rows) == 2
    assert _label(rows[0]).endswith("USER")


def test_build_rows_remote_badge_includes_remote_name():
    seeds = [_scoped("etl", "remote", remote="team")]
    rows = build_picker_rows(seeds)
    assert "[remote:team]" in _label(rows[1])


def test_build_rows_compact_drops_description_from_label():
    # The Seeds tab renders description in a side detail pane, so the
    # row itself stays terse. Make sure compact=True actually strips
    # it (otherwise rows balloon and the list panel looks crammed).
    seeds = [_scoped("alpha", "user", description="machine learning starter")]
    compact_rows = build_picker_rows(seeds, compact=True)
    full_rows = build_picker_rows(seeds, compact=False)
    assert "machine learning starter" not in _label(compact_rows[1])
    assert "machine learning starter" in _label(full_rows[1])
    # Compact still keeps the badge.
    assert "[user]" in _label(compact_rows[1])


def test_build_rows_hide_workspace_drops_local_section():
    seeds = [
        _scoped("alpha", "local"),
        _scoped("beta", "user"),
    ]
    rows = build_picker_rows(seeds, hide_workspace=True)
    assert all("WORKSPACE" not in _label(r) for r in rows if r.disabled)
    assert len(rows) == 2
    assert rows[1].id == "user:beta"
