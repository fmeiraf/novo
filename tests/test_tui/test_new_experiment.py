"""Tests for the NewExperimentScreen modal."""

import inspect

import pytest
from textual.app import App
from textual.widgets import OptionList

from novo.tui.screens import new_experiment


def test_create_call_propagates_detached_mode():
    # The modal must pass detached=is_detached() to core.experiment.create.
    # If it doesn't, a `novo --detached` launch silently falls through to
    # workspace mode and the experiment lands wherever cwd's walk-up
    # happens to find a `.novo/` marker, which has surprised users in
    # the field. Guard with a source-level check so the kwarg can't get
    # dropped again in a refactor.
    src = inspect.getsource(new_experiment.NewExperimentScreen._create_experiment)
    assert "is_detached" in src, (
        "NewExperimentScreen._create_experiment must consult is_detached() — "
        "otherwise detached-mode launches will silently use workspace mode"
    )
    assert "detached=" in src, (
        "NewExperimentScreen._create_experiment must pass `detached=` to "
        "core.experiment.create()"
    )


def test_form_body_scrolls_on_short_terminals():
    # The form has enough fields (name, description, tags, seed picker,
    # python select, checkbox) that on short terminals (≲ 24 rows) the
    # modal hits max-height: 90% and the bottom (checkbox + Create/Cancel)
    # is clipped invisibly unless the body scrolls. Guard the structure so
    # a refactor can't drop the VerticalScroll wrapper without it failing.
    src = inspect.getsource(new_experiment.NewExperimentScreen.compose)
    assert "VerticalScroll(" in src, (
        "NewExperimentScreen.compose() must wrap form fields in a "
        "VerticalScroll — otherwise the modal clips its bottom widgets on "
        "short terminals"
    )

    css = new_experiment.NewExperimentScreen.DEFAULT_CSS
    assert "max-width:" in css, (
        "NewExperimentScreen modal must set max-width so it fits terminals "
        "narrower than its fixed nominal width"
    )
    assert "height: 1fr" in css, (
        "NewExperimentScreen form body must use height: 1fr so the buttons "
        "stay pinned at the bottom while the form scrolls"
    )


@pytest.mark.asyncio
async def test_seed_list_opens_scrolled_to_top():
    # The seed list previously auto-highlighted the default seed
    # (`builtin:default`, which lives at the bottom of the scope order
    # local → user → remote → builtin). Textual's OptionList scrolls the
    # viewport to keep the highlighted row visible, so the picker opened
    # scrolled past the WORKSPACE / USER sections — hiding the first line
    # of the list. Guard the open-state contract with a real Textual
    # pilot so a future refactor can't quietly reintroduce the auto-scroll.

    class _App(App):
        def on_mount(self) -> None:
            self.push_screen(new_experiment.NewExperimentScreen())

    async with _App().run_test(size=(120, 40)) as pilot:
        await pilot.pause()
        await pilot.pause()
        opts = pilot.app.screen.query_one("#seed-options", OptionList)
        assert opts.scroll_y == 0, (
            f"Seed list must open scrolled to the top; got scroll_y={opts.scroll_y}"
        )
        assert opts.highlighted is None, (
            "Seed list must open with no auto-highlight — auto-highlighting "
            "the default scrolls the viewport past the first section"
        )
