"""Compatibility entry for venv bundles; shared implementation lives in mapper."""
from mapper.maintenance import backup, receipt, main

if __name__ == '__main__':
    raise SystemExit(main())
