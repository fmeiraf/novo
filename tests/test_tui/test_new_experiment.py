"""Tests for the NewExperimentScreen modal."""

import inspect

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
