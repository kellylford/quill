from __future__ import annotations

from quill.ui.preview_dialog import _build_accessible_dialog_body


def test_dialog_body_injects_content_focus_script() -> None:
    html = _build_accessible_dialog_body("<h1>About</h1>")

    assert "document.getElementById('content')" in html
    assert "c.setAttribute('tabindex','0');c.focus();" in html


def test_dialog_body_injects_enter_guard_for_static_content() -> None:
    html = _build_accessible_dialog_body("<p>Read me</p>")

    assert "document.addEventListener('keydown'" in html
    assert "if(e.key!=='Enter'){return;}" in html
    assert "if(!interactive){e.preventDefault();}" in html


def test_dialog_body_scrolls_to_anchor_when_provided() -> None:
    html = _build_accessible_dialog_body("<h2 id='startup'>Startup</h2>", start_anchor="startup")

    assert "var a=\"startup\";" in html
    assert "if(a){var n=document.getElementById(a);if(n){n.scrollIntoView();}}" in html
