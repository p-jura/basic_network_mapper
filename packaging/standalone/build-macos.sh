#!/bin/sh
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
exec python3.13 "$SCRIPT_DIR/bootstrap.py" "$@"
