"""An accessibility-focused wrapper around wx.html2.WebView for the chat.

wx.html2.WebView is a factory-created native control (Edge WebView2 / WKWebView
/ WebKitGTK), so it can't be meaningfully subclassed — but its accessibility is
driven by the HTML it renders. This wrapper renders chat messages into a
semantic, screen-reader-friendly document:

  * an ARIA live region (``role="log" aria-live="polite"``) so new messages are
    announced automatically,
  * an assertive ``role="status"`` region used to announce transient state
    ("Quill is responding…"),
  * each message as an ``<article>`` with a heading (speaker) for heading nav,
  * ``lang``, viewport, readable + high-contrast/forced-colors CSS.

The first message can be baked straight into the page so there is no visible
"empty then rendered" flash on open.
"""
from __future__ import annotations

import html
import json


class AccessibleWebView:
    def __init__(self, parent: object, title: str = "Conversation", intro: tuple | None = None) -> None:
        import wx
        import wx.html2 as webview

        self._wx = wx
        self.view = webview.WebView.New(parent)
        self.view.SetName(title)
        self._title = title
        self._ready = False
        self._pending: list[str] = []
        intro_html = ""
        if intro is not None:
            intro_html = self._article_html(intro[0], intro[1])
        self.view.Bind(webview.EVT_WEBVIEW_LOADED, self._on_loaded)
        self.view.SetPage(self._skeleton(intro_html), "")

    @property
    def control(self):
        return self.view

    def _article_html(self, speaker: str, markdown_text: str) -> str:
        from quill.core.browser_preview import _render_markdown

        body = _render_markdown(markdown_text or "")
        css_class = "you" if speaker.lower().startswith("you") else "quill"
        return (
            f'<article class="{css_class}" aria-label="{html.escape(speaker)} message">'
            f"<h2>{html.escape(speaker)}</h2>{body}</article>"
        )

    def _skeleton(self, intro_html: str = "") -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(self._title)}</title>
<style>
  :root {{ color-scheme: light dark; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; font-size: 1.05rem; line-height: 1.5;
          padding: 12px; }}
  main#log {{ display: block; }}
  article {{ margin: 0 0 14px 0; padding: 10px 12px; border-radius: 8px;
             border: 1px solid GrayText; }}
  article.you {{ background: Field; }}
  article h2 {{ font-size: 0.95rem; margin: 0 0 6px 0; }}
  article p {{ margin: 0.4em 0; }}
  pre {{ background: Field; padding: 8px; overflow-x: auto; }}
  code {{ font-family: ui-monospace, monospace; }}
  a {{ color: LinkText; }}
  :focus {{ outline: 2px solid Highlight; outline-offset: 2px; }}
  .visually-hidden {{ position: absolute; width: 1px; height: 1px; overflow: hidden;
                      clip: rect(0 0 0 0); white-space: nowrap; }}
  @media (forced-colors: active) {{ article {{ border: 1px solid CanvasText; }} }}
</style>
</head>
<body>
<div id="status" role="status" aria-live="assertive" class="visually-hidden"></div>
<main id="log" role="log" aria-live="polite" aria-label="{html.escape(self._title)}" tabindex="0">
{intro_html}
</main>
</body>
</html>"""

    def _on_loaded(self, _event: object) -> None:
        self._ready = True
        pending, self._pending = self._pending, []
        for article in pending:
            self._inject(article)

    def append_message(self, speaker: str, markdown_text: str) -> None:
        article = self._article_html(speaker, markdown_text)
        if self._ready:
            self._inject(article)
        else:
            self._pending.append(article)

    def set_status(self, text: str) -> None:
        """Update the assertive status region (announced by screen readers)."""
        if not self._ready:
            return
        payload = json.dumps(text)
        self._run(f"var s=document.getElementById('status'); if(s){{s.textContent={payload};}}")

    def _inject(self, article_html: str) -> None:
        payload = json.dumps(article_html)
        self._run(
            "var log=document.getElementById('log');"
            "var tmp=document.createElement('div');"
            f"tmp.innerHTML={payload};"
            "while(tmp.firstChild){log.appendChild(tmp.firstChild);}"
            "window.scrollTo(0, document.body.scrollHeight);"
        )

    def _run(self, script: str) -> None:
        try:
            self.view.RunScript(script)
        except Exception:  # noqa: BLE001
            pass

    def clear(self) -> None:
        self._ready = False
        self._pending = []
        self.view.SetPage(self._skeleton(), "")

    def focus(self) -> None:
        self.view.SetFocus()
