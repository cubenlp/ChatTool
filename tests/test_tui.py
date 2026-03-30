from chattool.utils.tui import _normalize_choice


def test_normalize_choice_keeps_plain_string_title():
    normalized = _normalize_choice("Select all")

    assert normalized == {
        "title": "Select all",
        "value": "Select all",
        "checked": False,
        "separator": False,
    }
