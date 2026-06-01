"""A small accessible **web form** helper for modal input dialogs.

Quill is standardizing dialogs on two kinds (see issue #73): native
``wx.MessageDialog`` for confirms/messages, and the accessible WebView (the
same surface the Ask Quill chat uses) for anything that displays rich content
or captures input. This module provides :func:`show_web_form` so the many
input dialogs can share one consistent, screen-reader-friendly implementation
instead of each hand-rolling its own ``wx.Dialog`` with bespoke focus and
button handling.

A field is a plain dict::

    {"name": "title", "label": "Title", "type": "text", "value": ""}
    {"name": "body", "label": "Note", "type": "textarea", "value": "", "rows": 12}
    {"name": "enabled", "label": "Enable X", "type": "checkbox", "value": True}
    {"name": "style", "label": "Prompt style", "type": "select",
     "value": "balanced", "options": [("balanced", "Balanced"), ...]}

:func:`show_web_form` returns a ``{name: value}`` dict on Save, or ``None`` if
the user cancels. It renders on :class:`AccessibleWebView` when a WebView
backend is available and falls back to native wx controls otherwise, so input
always works.
"""

from __future__ import annotations

import html
import json

FieldSpec = dict


def show_web_form(
    parent: object,
    wx: object,
    *,
    title: str,
    fields: list[FieldSpec],
    intro: str = "",
    save_label: str = "Save",
    cancel_label: str = "Cancel",
    size: tuple[int, int] = (720, 560),
) -> dict | None:
    """Show a modal accessible web form; return values on save or ``None``."""
    dialog = _WebFormDialog(
        parent,
        wx,
        title=title,
        fields=fields,
        intro=intro,
        save_label=save_label,
        cancel_label=cancel_label,
        size=size,
    )
    return dialog.show()


class _WebFormDialog:
    def __init__(
        self,
        parent: object,
        wx: object,
        *,
        title: str,
        fields: list[FieldSpec],
        intro: str,
        save_label: str,
        cancel_label: str,
        size: tuple[int, int],
    ) -> None:
        self._wx = wx
        self._fields = fields
        self._save_label = save_label
        self._cancel_label = cancel_label
        self._result: dict | None = None
        self._native_controls: dict = {}

        self.dialog = wx.Dialog(
            parent,
            title=title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        self.dialog.SetSize(size)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._webview = None
        try:
            from wx_accessible_webview import AccessibleWebView

            self._webview = AccessibleWebView(
                self.dialog,
                title=title,
                handler_name="awv",
                on_message=self._on_message,
                on_close=self._cancel,
                escape_to_close=True,
                initial_html=self._form_html(intro),
            )
        except Exception:  # noqa: BLE001
            self._webview = None

        if self._webview is not None and self._webview.using_webview:
            sizer.Add(self._webview.control, 1, wx.EXPAND)
        else:
            self._build_native(sizer, intro)
        self.dialog.SetSizer(sizer)

    def show(self) -> dict | None:
        self.dialog.CentreOnParent()
        if self._native_controls:
            first = next(iter(self._native_controls.values()))
            self._wx.CallAfter(first.SetFocus)
        try:
            if self.dialog.ShowModal() != self._wx.ID_OK:
                return None
            if self._native_controls:
                return self._read_native()
            return self._result
        finally:
            self.dialog.Destroy()

    # -- web rendering -----------------------------------------------------

    def _form_html(self, intro: str) -> str:
        parts: list[str] = [f"<h1>{html.escape(self.dialog.GetTitle())}</h1>"]
        if intro:
            parts.append(f"<p>{html.escape(intro)}</p>")
        first_id = ""
        for field in self._fields:
            field_id = "field-" + str(field["name"])
            if not first_id:
                first_id = field_id
            label = html.escape(str(field.get("label", field["name"])))
            ftype = field.get("type", "text")
            if ftype == "textarea":
                rows = int(field.get("rows", 10))
                value = html.escape(str(field.get("value", "")))
                parts.append(
                    f"<p><label for='{field_id}'>{label}</label><br>"
                    f"<textarea id='{field_id}' rows='{rows}' "
                    f"style='width:100%;font-size:1rem;padding:6px'>{value}</textarea></p>"
                )
            elif ftype == "checkbox":
                checked = " checked" if field.get("value") else ""
                parts.append(
                    f"<p><label><input type='checkbox' id='{field_id}'{checked}> "
                    f"{label}</label></p>"
                )
            elif ftype == "select":
                options = []
                current = str(field.get("value", ""))
                for opt_value, opt_label in field.get("options", []):
                    selected = " selected" if str(opt_value) == current else ""
                    options.append(
                        f'<option value="{html.escape(str(opt_value), quote=True)}"{selected}>'
                        f"{html.escape(str(opt_label))}</option>"
                    )
                parts.append(
                    f"<p><label for='{field_id}'>{label}</label><br>"
                    f"<select id='{field_id}' style='font-size:1rem;padding:6px'>"
                    f"{''.join(options)}</select></p>"
                )
            else:  # text
                value = html.escape(str(field.get("value", "")), quote=True)
                parts.append(
                    f"<p><label for='{field_id}'>{label}</label><br>"
                    f"<input id='{field_id}' type='text' value=\"{value}\" "
                    "style='width:100%;font-size:1rem;padding:6px'></p>"
                )
        parts.append(
            f"<p><button type='button' id='form-save'>{html.escape(self._save_label)}</button> "
            f"<button type='button' id='form-cancel'>{html.escape(self._cancel_label)}</button></p>"
        )
        names = [str(field["name"]) for field in self._fields]
        types = {str(field["name"]): field.get("type", "text") for field in self._fields}
        parts.append(
            "<script>(function(){"
            "function post(o){if(window.awv&&window.awv.postMessage)"
            "{window.awv.postMessage(JSON.stringify(o));}}"
            f"var names={json.dumps(names)};var types={json.dumps(types)};"
            "function collect(){var v={};names.forEach(function(n){"
            "var el=document.getElementById('field-'+n);if(!el)return;"
            "v[n]=(types[n]==='checkbox')?el.checked:el.value;});return v;}"
            "document.getElementById('form-save').addEventListener('click',function(){"
            "post({type:'save',values:collect()});});"
            "document.getElementById('form-cancel').addEventListener('click',function(){"
            "post({type:'cancel'});});"
            f"setTimeout(function(){{var f=document.getElementById({json.dumps(first_id)});"
            "if(f){f.focus();if(f.select)f.select();}},60);"
            "})();</script>"
        )
        return "".join(parts)

    def _on_message(self, data: object) -> None:
        if not isinstance(data, dict):
            return
        kind = data.get("type")
        if kind == "save":
            values = data.get("values")
            self._result = values if isinstance(values, dict) else {}
            self.dialog.EndModal(self._wx.ID_OK)
        elif kind in ("cancel", "close"):
            self.dialog.EndModal(self._wx.ID_CANCEL)

    def _cancel(self) -> None:
        self.dialog.EndModal(self._wx.ID_CANCEL)

    # -- native fallback ---------------------------------------------------

    def _build_native(self, sizer: object, intro: str) -> None:
        wx = self._wx
        if intro:
            sizer.Add(wx.StaticText(self.dialog, label=intro), 0, wx.EXPAND | wx.ALL, 8)
        for field in self._fields:
            name = str(field["name"])
            label = str(field.get("label", name))
            ftype = field.get("type", "text")
            if ftype == "checkbox":
                control = wx.CheckBox(self.dialog, label=label)
                control.SetValue(bool(field.get("value")))
                sizer.Add(control, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)
            elif ftype == "select":
                sizer.Add(
                    wx.StaticText(self.dialog, label=label), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8
                )
                opts = list(field.get("options", []))
                control = wx.Choice(self.dialog, choices=[str(label) for _, label in opts])
                current = str(field.get("value", ""))
                for index, (opt_value, _label) in enumerate(opts):
                    if str(opt_value) == current:
                        control.SetSelection(index)
                        break
                control._wf_options = opts  # type: ignore[attr-defined]
                sizer.Add(control, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
            else:
                sizer.Add(
                    wx.StaticText(self.dialog, label=label), 0, wx.LEFT | wx.RIGHT | wx.TOP, 8
                )
                style = wx.TE_MULTILINE | wx.TE_PROCESS_TAB if ftype == "textarea" else 0
                control = wx.TextCtrl(self.dialog, value=str(field.get("value", "")), style=style)
                proportion = 1 if ftype == "textarea" else 0
                sizer.Add(control, proportion, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)
            self._native_controls[name] = control
        buttons = self.dialog.CreateButtonSizer(wx.OK | wx.CANCEL)
        if buttons is not None:
            ok_button = buttons.FindWindowById(wx.ID_OK)
            if ok_button is not None:
                ok_button.SetLabel(self._save_label)
            sizer.Add(buttons, 0, wx.EXPAND | wx.ALL, 8)

    def _read_native(self) -> dict:
        values: dict = {}
        for field in self._fields:
            name = str(field["name"])
            control = self._native_controls.get(name)
            if control is None:
                continue
            ftype = field.get("type", "text")
            if ftype == "checkbox":
                values[name] = bool(control.GetValue())
            elif ftype == "select":
                opts = getattr(control, "_wf_options", [])
                index = control.GetSelection()
                values[name] = str(opts[index][0]) if 0 <= index < len(opts) else ""
            else:
                values[name] = control.GetValue()
        return values
