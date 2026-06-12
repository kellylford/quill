"""autoupdate — vendored from accessibleapps/app_updater (MIT).

See LICENSE in this directory and THIRD_PARTY_NOTICES.md at the repo root.
Upstream: https://github.com/accessibleapps/app_updater
"""

import glob
import os.path
import platform


def find_datafiles():
    system = platform.system()
    if system == "Windows":
        file_ext = "*.exe"
    else:
        file_ext = "*.sh"
    path = os.path.abspath(os.path.join(__path__[0], "bootstrappers", file_ext))
    return [("", glob.glob(path))]
