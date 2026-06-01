from __future__ import annotations

import time

import pytest

from quill.core.safe_xml import UnsafeXMLError
from quill.core.safe_xml import fromstring as safe_xml_fromstring

# Classic "billion laughs" entity-expansion payload.
_BILLION_LAUGHS = """<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
]>
<lolz>&lol4;</lolz>"""


def test_well_formed_xml_still_parses() -> None:
    root = safe_xml_fromstring("<root><a>1</a><b>2</b></root>")
    assert root.tag == "root"
    assert [child.text for child in root] == ["1", "2"]


def test_billion_laughs_is_rejected_quickly() -> None:
    start = time.monotonic()
    with pytest.raises(UnsafeXMLError):
        safe_xml_fromstring(_BILLION_LAUGHS)
    # The payload must be refused, not expanded; this should be near-instant.
    assert time.monotonic() - start < 1.0


def test_external_entity_doctype_is_rejected() -> None:
    payload = (
        '<?xml version="1.0"?>'
        '<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
        "<foo>&xxe;</foo>"
    )
    with pytest.raises(UnsafeXMLError):
        safe_xml_fromstring(payload)


def test_accepts_bytes_input() -> None:
    root = safe_xml_fromstring(b"<root>hi</root>")
    assert root.tag == "root"
    assert root.text == "hi"
