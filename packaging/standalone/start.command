#!/bin/sh
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
"$APP_DIR/Mapper" "$@"
RESULT=$?
if [ "$RESULT" -ne 0 ] && [ "$RESULT" -ne 130 ]; then
    printf '\nUruchomienie nieudane (kod %s). Enter zamyka okno. ' "$RESULT"
    read -r REPLY
fi
exit "$RESULT"
