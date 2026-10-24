"""Private creation, before writing data; no ACL changes to export parents."""
from contextlib import contextmanager
import os
from pathlib import Path
import stat
from .errors import MapperError


def reject_link(path):
    path = Path(path)
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise MapperError('UNSAFE_DATA_PATH')


def is_windows():
    return os.name == 'nt'


def windows_security():
    from .windows_security import WindowsSecurity
    return WindowsSecurity()


def protect(path, *, directory=False):
    path = Path(path)
    reject_link(path)
    mode = path.stat().st_mode
    if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
        raise MapperError('UNSAFE_DATA_PATH')
    if is_windows():
        windows_security().protect(path, directory=directory)
    else:
        path.chmod(0o700 if directory else 0o600)


def private_directory(path):
    path = Path(path)
    reject_link(path)
    # Only ancestors necessary for a new project/data root; never chmod them.
    path.parent.mkdir(parents=True, exist_ok=True)
    if is_windows():
        windows_security().mkdir(path)
    else:
        path.mkdir(mode=0o700)


@contextmanager
def private_file(path, *, newline=None):
    path = Path(path).expanduser()
    reject_link(path)
    if is_windows():
        fd = windows_security().create_file(path)
    else:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        f = os.fdopen(fd, 'w', encoding='utf-8', newline=newline)
    except BaseException:
        os.close(fd)
        raise
    with f:
        yield f


def prepare_file(path):
    with private_file(path):
        pass
