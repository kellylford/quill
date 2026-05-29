from quill.platform.windows.sr_detect import detect_screen_reader


def test_detect_screen_reader_nvda() -> None:
    snapshot = '"nvda.exe","1234","Console","1","10,000 K"\n'
    result = detect_screen_reader(snapshot)
    assert result.detected is True
    assert result.name == "NVDA"


def test_detect_screen_reader_none() -> None:
    snapshot = '"explorer.exe","111","Console","1","10,000 K"\n'
    result = detect_screen_reader(snapshot)
    assert result.detected is False
    assert result.name == "none"
