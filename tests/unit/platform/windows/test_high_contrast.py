from __future__ import annotations

from types import SimpleNamespace

from quill.platform.windows import high_contrast


def test_is_high_contrast_enabled_false_without_ctypes(monkeypatch) -> None:
    monkeypatch.setattr(high_contrast, "ctypes", None)
    assert high_contrast.is_high_contrast_enabled() is False


def test_is_high_contrast_enabled_reads_win32_flag(monkeypatch) -> None:
    class FakeUser32:
        def SystemParametersInfoW(self, action, cb_size, buffer, flags):  # noqa: N802
            buffer.dwFlags = high_contrast.HCF_HIGHCONTRASTON
            return True

    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(user32=FakeUser32()),
        Structure=object,
        wintypes=SimpleNamespace(UINT=int, DWORD=int, LPWSTR=str),
        sizeof=lambda _: 0,
        byref=lambda value: value,
    )
    monkeypatch.setattr(high_contrast, "ctypes", fake_ctypes)

    assert high_contrast.is_high_contrast_enabled() is True
