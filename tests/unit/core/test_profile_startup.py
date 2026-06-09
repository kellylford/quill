"""Startup / per-file profile selection logic (issue #138)."""

from __future__ import annotations

import pytest

from quill.core import profile_startup as ps
from quill.core.features import PROFILE_DEFINITIONS, PROFILE_ESSENTIAL
from quill.core.profile_startup import ProfileStartupConfig

_ANY_PROFILE = PROFILE_ESSENTIAL
_OTHER_PROFILE = next(pid for pid in PROFILE_DEFINITIONS if pid != PROFILE_ESSENTIAL)


def test_normalize_extension() -> None:
    assert ps.normalize_extension("Py") == ".py"
    assert ps.normalize_extension(".MD") == ".md"
    assert ps.normalize_extension("  txt ") == ".txt"
    assert ps.normalize_extension("") == ""


def test_should_prompt_when_always_on() -> None:
    config = ProfileStartupConfig(prompt_on_startup=True, prompt_on_modifier=False)
    assert ps.should_prompt_on_startup(config, modifier_held=False) is True


def test_should_prompt_only_with_modifier() -> None:
    config = ProfileStartupConfig(prompt_on_startup=False, prompt_on_modifier=True)
    assert ps.should_prompt_on_startup(config, modifier_held=True) is True
    assert ps.should_prompt_on_startup(config, modifier_held=False) is False


def test_no_prompt_when_both_disabled() -> None:
    config = ProfileStartupConfig(prompt_on_startup=False, prompt_on_modifier=False)
    assert ps.should_prompt_on_startup(config, modifier_held=True) is False


def test_profile_for_path_uses_extension_map() -> None:
    config = ProfileStartupConfig(extension_map={".py": _OTHER_PROFILE})
    assert ps.profile_for_path("/home/me/script.py", config) == _OTHER_PROFILE
    assert ps.profile_for_path("/home/me/notes.md", config) is None
    assert ps.profile_for_path(None, config) is None


def test_profile_for_path_ignores_unknown_profile() -> None:
    config = ProfileStartupConfig(extension_map={".py": "no-such-profile"})
    assert ps.profile_for_path("x.py", config) is None


def test_with_extension_normalises_and_copies() -> None:
    config = ProfileStartupConfig()
    updated = config.with_extension("PY", _ANY_PROFILE)
    assert updated.extension_map == {".py": _ANY_PROFILE}
    assert config.extension_map == {}  # original untouched


@pytest.fixture
def temp_app_data(tmp_path, monkeypatch):
    monkeypatch.setattr(ps, "app_data_dir", lambda: tmp_path)
    return tmp_path


def test_config_round_trip(temp_app_data) -> None:
    config = ProfileStartupConfig(
        prompt_on_startup=True,
        prompt_on_modifier=False,
        extension_map={".py": _OTHER_PROFILE},
    )
    ps.save_profile_startup_config(config)
    loaded = ps.load_profile_startup_config()
    assert loaded.prompt_on_startup is True
    assert loaded.prompt_on_modifier is False
    assert loaded.extension_map == {".py": _OTHER_PROFILE}


def test_load_drops_stale_extension_mapping(temp_app_data) -> None:
    ps.save_profile_startup_config(ProfileStartupConfig(extension_map={".py": _OTHER_PROFILE}))
    # Simulate the mapped profile disappearing by writing a bad value directly.
    (temp_app_data / "profile_startup.json").write_text(
        '{"extension_map": {".py": "gone"}}', encoding="utf-8"
    )
    assert ps.load_profile_startup_config().extension_map == {}


def test_load_defaults_when_missing(temp_app_data) -> None:
    config = ps.load_profile_startup_config()
    assert config.prompt_on_startup is False
    assert config.prompt_on_modifier is True
    assert config.extension_map == {}
