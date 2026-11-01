"""One executable dispatch for panel, existing CLI and offline maintenance."""
import json
from pathlib import Path
import sys


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    try:
        if args[:1] == ['maintenance']:
            from .maintenance import main as maintenance
            return maintenance(args[1:])
        if args[:1] == ['verify']:
            if len(args) != 1:
                raise ValueError('INVALID_VERIFY_ARGUMENTS')
            from .standalone_manifest import verify
            root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else None
            if root is None:
                raise ValueError('VERIFY_REQUIRES_STANDALONE')
            manifest = verify(root)
            print(json.dumps({'status': 'verified', 'version': manifest['version'], 'sends_probes': False}))
            return 0
        from .cli import main as cli
        return cli(args or ['panel'])
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        # No raw exception or argv: may contain mistakenly pasted credentials.
        from .standalone_manifest import ManifestError
        code = str(exc) if isinstance(exc, ManifestError) else 'STANDALONE_FAILED'
        print(json.dumps({'error': code, 'sends_probes': False}), file=sys.stderr)
        return 2
