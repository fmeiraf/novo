"""Filterable experiment list widget with keyboard navigation."""

from textual.app import ComposeResult
from textual.binding import Binding
from textual.message import Message
from textual.widgets import OptionList
from textual.widgets.option_list import Option

from novo.models.experiment import Experiment


class ExperimentList(OptionList):
    """A navigable list of experiments."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]

    class Selected(Message):
        """Posted when an experiment is selected."""

        def __init__(self, experiment: Experiment) -> None:
            self.experiment = experiment
            super().__init__()

    class Activated(Message):
        """Posted when an experiment is activated (Enter)."""

        def __init__(self, experiment: Experiment) -> None:
            self.experiment = experiment
            super().__init__()

    def __init__(self, experiments: list[Experiment] | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._experiments: list[Experiment] = experiments or []
        self._filtered: list[Experiment] = list(self._experiments)

    def on_mount(self) -> None:
        self._refresh_options()

    def set_experiments(self, experiments: list[Experiment]) -> None:
        """Update the experiment list."""
        self._experiments = experiments
        self._filtered = list(experiments)
        self._refresh_options()

    def filter(self, query: str) -> None:
        """Filter experiments by query."""
        if not query:
            self._filtered = list(self._experiments)
        else:
            query_lower = query.lower()
            self._filtered = [
                e
                for e in self._experiments
                if query_lower in e.name.lower()
                or query_lower in e.description.lower()
                or any(query_lower in t.lower() for t in e.tags)
            ]
        self._refresh_options()

    def _refresh_options(self) -> None:
        """Rebuild the option list."""
        self.clear_options()
        for exp in self._filtered:
            tags = f" [{', '.join(exp.tags)}]" if exp.tags else ""
            self.add_option(Option(f"{exp.dir_name}{tags}", id=exp.dir_name))

        if self._filtered and self.option_count > 0:
            self.highlighted = 0
            self.post_message(self.Selected(self._filtered[0]))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """When highlight changes, post Selected message."""
        if event.option and event.option_index < len(self._filtered):
            self.post_message(self.Selected(self._filtered[event.option_index]))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """When Enter is pressed, post Activated message."""
        if event.option and event.option_index < len(self._filtered):
            self.post_message(self.Activated(self._filtered[event.option_index]))

    def get_selected_experiment(self) -> Experiment | None:
        """Get the currently highlighted experiment."""
        if self.highlighted is not None and self.highlighted < len(self._filtered):
            return self._filtered[self.highlighted]
        return None
