"""Print the SHA-256 of the file given as argv[1].

Used by run-from-source.bat / run-from-source.sh to detect when
requirements.txt changes (so dependencies are reinstalled only after a real
change). Kept as a standalone script — not an inline ``python -c`` one-liner —
because the parentheses in ``open(...).read()`` break Windows ``cmd`` parsing
when embedded inside a ``for /f`` / ``if ( ... )`` block.
"""

import hashlib
import sys

with open(sys.argv[1], "rb") as handle:
    print(hashlib.sha256(handle.read()).hexdigest())
