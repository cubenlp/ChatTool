import click
import pytest

import chattool.setup.interactive as interactive_policy
from chattool.setup.elements import SETUP_COMMAND_ELEMENTS


def test_normalize_interactive_default_source(monkeypatch):
    class DummyCtx:
        def get_parameter_source(self, _name):
            return click.core.ParameterSource.DEFAULT

    monkeypatch.setattr(interactive_policy.click, "get_current_context", lambda silent=True: DummyCtx())
    assert interactive_policy.normalize_interactive(True) is None


def test_resolve_interactive_mode_auto_prompt(monkeypatch):
    monkeypatch.setattr(interactive_policy.click, "get_current_context", lambda silent=True: None)
    monkeypatch.setattr(interactive_policy, "is_interactive_available", lambda: True)
    interactive, can_prompt, force_interactive, auto_interactive, need_prompt = interactive_policy.resolve_interactive_mode(
        interactive=None,
        auto_prompt_condition=True,
    )
    assert interactive is None
    assert can_prompt is True
    assert force_interactive is False
    assert auto_interactive is True
    assert need_prompt is True


def test_abort_if_force_without_tty():
    with pytest.raises(click.Abort):
        interactive_policy.abort_if_force_without_tty(
            force_interactive=True,
            can_prompt=False,
            usage="Usage: demo",
        )


def test_abort_if_missing_without_tty():
    with pytest.raises(click.Abort):
        interactive_policy.abort_if_missing_without_tty(
            missing_required=True,
            interactive=None,
            can_prompt=False,
            message="missing",
            usage="Usage: demo",
        )


def test_setup_frp_has_interactive_option():
    frp = next(item for item in SETUP_COMMAND_ELEMENTS if item.name == "frp")
    assert any("-i/-I" in option.param_decls for option in frp.options)
