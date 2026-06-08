from __future__ import annotations

from pathlib import Path


def _main_frame_source() -> str:
    # The QUILL-key / Quick-Nav handling was extracted into the QuillKeyMixin
    # module (CQ-1); read both so these wiring contracts hold wherever the code
    # physically lives.
    ui = Path(__file__).resolve().parents[3] / "quill" / "ui"
    return "\n".join(
        (ui / name).read_text(encoding="utf-8")
        for name in ("main_frame.py", "main_frame_quill_key.py")
    )


def test_quill_key_m_invokes_paste_html_as_markdown() -> None:
    source = _main_frame_source()
    assert 'key_code in (ord("M"), ord("m"))' in source
    assert "self.paste_html_as_markdown()" in source


def test_power_tools_mixin_is_wired_into_main_frame() -> None:
    source = _main_frame_source()
    assert "from quill.ui.main_frame_power_tools import PowerToolsActionsMixin" in source
    assert "PowerToolsActionsMixin" in source.split("class MainFrame(")[1].split(")")[0]


def test_prefix_message_advertises_markdown_paste() -> None:
    source = _main_frame_source()
    assert "M to paste HTML as Markdown" in source
