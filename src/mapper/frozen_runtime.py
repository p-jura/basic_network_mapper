"""Frozen runtime initialization; never launches probes or changes network settings."""
import os
from pathlib import Path
import sys

_DLL_HANDLES = []


def initialize():
    if not getattr(sys, 'frozen', False):
        return
    sys.dont_write_bytecode = True
    if sys.platform == 'win32':
        import ctypes
        root = Path(sys._MEIPASS)
        # Python >=3.8 loads extensions with LoadLibraryEx and explicit search
        # flags. AddDllDirectory handles stay alive; this list is not inherited
        # by children. Reset bootloader SetDllDirectory once, before workers.
        directories = {root}
        for pattern in ('*.pyd', '*.dll'):
            directories.update(p.parent for p in root.rglob(pattern))
        for directory in sorted(directories):
            _DLL_HANDLES.append(os.add_dll_directory(str(directory)))
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        reset = kernel.SetDllDirectoryW
        reset.argtypes = [ctypes.c_wchar_p]
        reset.restype = ctypes.c_int
        if not reset(None):
            raise OSError('DLL_SEARCH_RESET_FAILED')


def child_environment():
    env = dict(os.environ)
    if getattr(sys, 'frozen', False):
        root = str(Path(sys._MEIPASS).resolve())
        for key in ('DYLD_LIBRARY_PATH', 'DYLD_FRAMEWORK_PATH', 'LD_LIBRARY_PATH'):
            if key in env:
                env[key] = os.pathsep.join(p for p in env[key].split(os.pathsep)
                    if p and not Path(p).resolve().is_relative_to(root))
                if not env[key]:
                    env.pop(key)
    return env


def open_browser(url):
    if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
        import subprocess
        try:
            return subprocess.run(['/usr/bin/open', url], env=child_environment(),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5, check=False).returncode == 0
        except subprocess.TimeoutExpired:
            return False
    import webbrowser
    return webbrowser.open(url)
