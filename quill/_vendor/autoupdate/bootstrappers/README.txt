Bootstrapper binaries
=====================

This directory holds the platform-specific bootstrapper executables that
apply updates to a running QUILL installation:

  bootstrap.exe       Windows
  bootstrap-mac.sh    macOS
  bootstrap-lin.sh    Linux

These files are NOT checked into the repository because they are native
binaries maintained by the AccessibleApps project:

  https://github.com/accessibleapps/app_updater

How to obtain them
------------------
Download from a tagged release of app_updater, or clone the repo and
copy the files from autoupdate/bootstrappers/:

  git clone https://github.com/accessibleapps/app_updater
  cp app_updater/autoupdate/bootstrappers/* \
     quill/_vendor/autoupdate/bootstrappers/

They are bundled into the Windows installer and portable ZIP by
scripts/build_windows_distribution.py. See the deployment guide
(docs/deployment.md) for details.
