"""Scope-aware seed picker — sections, badges, type-ahead filter."""

from dataclasses import dataclass

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option

from novo.models.scoped_seed import ScopedSeed

_SCOPE_TITLES = {
    "local": ("WORKSPACE", "bold cyan"),
    "user": ("USER", "bold blue"),
    "remote": ("REMOTE", "bold yellow"),
    "builtin": ("BUILTIN", "bold"),
}


@dataclass
class PickerRow:
    """One row in the picker.

    Header rows have id=None and disabled=True; selectable rows carry the
    scoped seed identifier as their id.
    """

    label: Text
    id: str | None = None
    disabled: bool = False


def _scope_header(scope: str, remote: str | None) -> Text:
    title, style = _SCOPE_TITLES.get(scope, (scope.upper(), "bold"))
    text = Text(title, style=style)
    if scope == "remote" and remote:
        text.append(f": {remote}", style=style)
    return text


def _option_label(scoped: ScopedSeed, is_default: bool) -> Text:
    """Format one seed as `name  description  [scope]  (default)`."""
    text = Text()
    text.append(scoped.seed.name, style="cyan")
    desc = (scoped.seed.description or "").strip()
    if desc:
        text.append("  ")
        text.append(desc)
    badge = scoped.scope if scoped.scope != "remote" else f"remote:{scoped.remote}"
    text.append("  ")
    text.append(f"[{badge}]", style="dim")
    if is_default:
        text.append("  ")
        text.append("(default)", style="bold green")
    return text


def build_picker_rows(
    seeds: list[ScopedSeed],
    default_identifier: str | None = None,
    filter_query: str = "",
    *,
    hide_workspace: bool = False,
) -> list[PickerRow]:
    """Group and label seeds for the SeedPicker's OptionList.

    Returns header + entry rows in scope order. Sections that filter out
    to zero entries are omitted (no orphan headers).
    """
    q = filter_query.strip().lower()

    if hide_workspace:
        seeds = [s for s in seeds if s.scope != "local"]

    if q:
        seeds = [
            s
            for s in seeds
            if q in s.seed.name.lower() or q in (s.seed.description or "").lower()
        ]

    rows: list[PickerRow] = []
    last_key: tuple[str, str | None] | None = None
    for scoped in seeds:
        key = (scoped.scope, scoped.remote)
        if key != last_key:
            rows.append(
                PickerRow(
                    label=_scope_header(scoped.scope, scoped.remote),
                    id=None,
                    disabled=True,
                )
            )
            last_key = key
        is_default = scoped.identifier == default_identifier
        rows.append(PickerRow(label=_option_label(scoped, is_default), id=scoped.identifier))
    return rows


class SeedPicker(Vertical):
    """Scope-aware seed picker with a type-ahead filter."""

    DEFAULT_CSS = """
    SeedPicker {
        height: auto;
    }
    SeedPicker Input {
        margin-bottom: 0;
    }
    SeedPicker OptionList {
        height: 10;
        margin-top: 0;
    }
    """

    def __init__(self, *, hide_workspace: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._hide_workspace = hide_workspace
        self._all_seeds: list[ScopedSeed] = []
        self._default_id: str | None = None
        self._filter = ""

    def compose(self) -> ComposeResult:
        yield Input(placeholder="Filter seeds…", id="seed-filter")
        yield OptionList(id="seed-options")

    def on_mount(self) -> None:
        self.refresh_seeds()

    def refresh_seeds(self) -> None:
        from novo.core.config import load_config
        from novo.core.seed import list_seeds, resolve_seed

        self._all_seeds = list_seeds()
        try:
            scoped = resolve_seed(load_config().defaults.seed)
            self._default_id = scoped.identifier
        except ValueError:
            self._default_id = None

        self._rebuild()

    def _rebuild(self) -> None:
        opts = self.query_one("#seed-options", OptionList)
        opts.clear_options()

        rows = build_picker_rows(
            self._all_seeds,
            default_identifier=self._default_id,
            filter_query=self._filter,
            hide_workspace=self._hide_workspace,
        )

        default_index: int | None = None
        for i, row in enumerate(rows):
            opts.add_option(Option(row.label, id=row.id, disabled=row.disabled))
            if row.id is not None and row.id == self._default_id:
                default_index = i

        if default_index is not None:
            opts.highlighted = default_index

    @on(Input.Changed, "#seed-filter")
    def _on_filter_changed(self, event: Input.Changed) -> None:
        self._filter = event.value
        self._rebuild()

    @property
    def selected_identifier(self) -> str | None:
        """Currently highlighted seed identifier, or None for header/empty."""
        opts = self.query_one("#seed-options", OptionList)
        if opts.highlighted is None:
            return None
        try:
            opt = opts.get_option_at_index(opts.highlighted)
        except IndexError:
            return None
        if opt.disabled:
            return None
        return opt.id
