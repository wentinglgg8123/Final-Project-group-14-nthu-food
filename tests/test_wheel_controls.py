from unittest.mock import Mock

from food_picker import wheel_controls
from food_picker.defaults import load_default_catalog


def test_wheel_loads_new_script_without_reimporting_module(monkeypatch, tmp_path):
    script = tmp_path / "wheel.js"
    first_version = "export default function () { /* original */ }"
    second_version = "export default function () { /* updated */ }"
    register = Mock(side_effect=[Mock(), Mock()])
    monkeypatch.setattr(wheel_controls, "component", register)
    monkeypatch.setattr(wheel_controls, "_WHEEL_SCRIPT", script)
    restaurant = load_default_catalog().restaurants[0]

    wheel_controls._wheel_component.cache_clear()
    try:
        script.write_text(first_version, encoding="utf-8")
        wheel_controls.render_wheel([restaurant], None, None, None)
        wheel_controls.render_wheel([restaurant], None, None, None)
        assert register.call_count == 1

        script.write_text(second_version, encoding="utf-8")
        wheel_controls.render_wheel([restaurant], None, None, None)
        first, second = register.call_args_list
        assert first.args[0] != second.args[0]
        assert first.kwargs["js"] == first_version
        assert second.kwargs["js"] == second_version
    finally:
        wheel_controls._wheel_component.cache_clear()
