#!/usr/bin/env bash
# Copy this case's fixtures into the run's working directory: the eval sandbox lets the shell
# (and so the bundled scripts) read the working directory, but not extra read-only folders.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
cp -R "$here/gsc-data" .
