#!/bin/sh
set -eu
TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if ! command -v python3.13 >/dev/null 2>&1; then
  echo "Wymagany Python 3.13 dla macOS ARM. Zainstaluj go przed instalacją mappera." >&2
  exit 1
fi
exec python3.13 -I "$TASK_DIR/bundle.py" install
