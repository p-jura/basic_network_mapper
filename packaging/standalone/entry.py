"""PyInstaller entry; do not import CLI until runtime search paths are ready."""
import sys
from mapper.frozen_runtime import initialize

if __name__ == '__main__':
    try:
        initialize()
        from mapper.standalone import main
        result = main()
    except Exception:
        print('{"error":"RUNTIME_INITIALIZATION_FAILED"}', file=sys.stderr)
        result = 2
    if result not in (0, 130) and sys.platform == 'win32' and sys.stdin.isatty():
        try:
            input('Uruchomienie nieudane. Enter zamyka okno. ')
        except (EOFError, KeyboardInterrupt):
            pass
    raise SystemExit(result)
