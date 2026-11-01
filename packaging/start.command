#!/bin/sh
set -eu
TASK_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -f "$TASK_DIR/.venv/.mapper-installed.json" ]; then
  echo "Najpierw wykonaj: sh install.sh" >&2
  exit 1
fi
exec "$TASK_DIR/.venv/bin/python" -I "$TASK_DIR/bundle.py" start "$@"
