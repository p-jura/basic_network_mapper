"""Native DACL creation for application-owned paths. Lazy Windows-only API."""
from contextlib import contextmanager
import ctypes as c
import os
import re
from .errors import MapperError

U32, BOOL, PTR = c.c_uint32, c.c_int32, c.c_void_p


class SecurityAttributes(c.Structure):
    _fields_ = [('length', U32), ('descriptor', PTR), ('inherit_handle', BOOL)]


class SidAttributes(c.Structure):
    _fields_ = [('sid', PTR), ('attributes', U32)]


def private_sddl(sid, directory=False):
    if not re.fullmatch(r'S-1-(?:[0-9]+-)*[0-9]+', sid):
        raise MapperError('FILE_PROTECTION_FAILED')
    flags = 'OICI' if directory else ''
    return 'D:P' + ''.join(f'(A;{flags};FA;;;{who})' for who in ['SY', 'BA', sid])


class WindowsSecurity:
    def __init__(self):
        if os.name != 'nt':
            raise MapperError('FILE_PROTECTION_UNAVAILABLE')
        try:
            self.kernel = c.WinDLL('kernel32.dll', use_last_error=True)
            self.adv = c.WinDLL('advapi32.dll', use_last_error=True)
            self._bind(self.kernel, 'GetCurrentProcess', [], PTR)
            self._bind(self.kernel, 'CloseHandle', [PTR], BOOL)
            self._bind(self.kernel, 'LocalFree', [PTR], PTR)
            self._bind(self.kernel, 'GetVolumePathNameW', [c.c_wchar_p, c.c_wchar_p, U32], BOOL)
            self._bind(self.kernel, 'GetVolumeInformationW', [c.c_wchar_p, c.c_wchar_p, U32, c.POINTER(U32), c.POINTER(U32), c.POINTER(U32), c.c_wchar_p, U32], BOOL)
            self._bind(self.kernel, 'CreateDirectoryW', [c.c_wchar_p, c.POINTER(SecurityAttributes)], BOOL)
            self._bind(self.kernel, 'CreateFileW', [c.c_wchar_p, U32, U32, c.POINTER(SecurityAttributes), U32, U32, PTR], PTR)
            self._bind(self.adv, 'OpenProcessToken', [PTR, U32, c.POINTER(PTR)], BOOL)
            self._bind(self.adv, 'GetTokenInformation', [PTR, U32, PTR, U32, c.POINTER(U32)], BOOL)
            self._bind(self.adv, 'ConvertSidToStringSidW', [PTR, c.POINTER(PTR)], BOOL)
            self._bind(self.adv, 'ConvertStringSecurityDescriptorToSecurityDescriptorW', [c.c_wchar_p, U32, c.POINTER(PTR), c.POINTER(U32)], BOOL)
            self._bind(self.adv, 'SetFileSecurityW', [c.c_wchar_p, U32, PTR], BOOL)
            self.sid = self._current_sid()
        except (OSError, AttributeError):
            raise MapperError('FILE_PROTECTION_UNAVAILABLE') from None

    @staticmethod
    def _bind(lib, name, args, result):
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result

    def _current_sid(self):
        token, size, string = PTR(), U32(), PTR()
        if not self.adv.OpenProcessToken(self.kernel.GetCurrentProcess(), 0x0008, c.byref(token)):
            raise MapperError('FILE_PROTECTION_FAILED')
        try:
            self.adv.GetTokenInformation(token, 1, None, 0, c.byref(size))
            if not 0 < size.value <= 65536:
                raise MapperError('FILE_PROTECTION_FAILED')
            buffer = c.create_string_buffer(size.value)
            if not self.adv.GetTokenInformation(token, 1, buffer, size, c.byref(size)):
                raise MapperError('FILE_PROTECTION_FAILED')
            sid = c.cast(buffer, c.POINTER(SidAttributes)).contents.sid
            if not self.adv.ConvertSidToStringSidW(sid, c.byref(string)):
                raise MapperError('FILE_PROTECTION_FAILED')
            return c.wstring_at(string)
        finally:
            if string.value:
                self.kernel.LocalFree(string)
            self.kernel.CloseHandle(token)

    @contextmanager
    def descriptor(self, directory=False):
        descriptor = PTR()
        if not self.adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(private_sddl(self.sid, directory), 1, c.byref(descriptor), None):
            raise MapperError('FILE_PROTECTION_FAILED')
        try:
            yield SecurityAttributes(c.sizeof(SecurityAttributes), descriptor, False)
        finally:
            self.kernel.LocalFree(descriptor)

    def _require_acl_volume(self, path):
        from pathlib import Path
        path = Path(path).absolute()
        existing = path if path.exists() else path.parent
        volume, flags = c.create_unicode_buffer(32768), U32()
        if not self.kernel.GetVolumePathNameW(str(existing), volume, len(volume)):
            raise MapperError('FILE_PROTECTION_UNAVAILABLE')
        if not self.kernel.GetVolumeInformationW(volume.value, None, 0, None, None, c.byref(flags), None, 0) or not flags.value & 0x8:
            raise MapperError('FILE_PROTECTION_UNAVAILABLE')

    def mkdir(self, path):
        self._require_acl_volume(path)
        with self.descriptor(directory=True) as attrs:
            if not self.kernel.CreateDirectoryW(str(path), c.byref(attrs)):
                if c.get_last_error() == 183:
                    raise FileExistsError(str(path))
                raise MapperError('FILE_PROTECTION_FAILED')

    def create_file(self, path):
        import msvcrt
        self._require_acl_volume(path)
        with self.descriptor() as attrs:
            # CREATE_NEW, not OPEN_ALWAYS: neither overwrite nor follow links.
            handle = self.kernel.CreateFileW(str(path), 0xC0000000, 0, c.byref(attrs), 1, 0x80, None)
            if handle in {None, c.c_void_p(-1).value}:
                if c.get_last_error() in {80, 183}:
                    raise FileExistsError(str(path))
                raise MapperError('FILE_PROTECTION_FAILED')
        try:
            return msvcrt.open_osfhandle(handle, os.O_WRONLY | os.O_BINARY)
        except BaseException:
            self.kernel.CloseHandle(handle)
            raise

    def protect(self, path, *, directory=False):
        self._require_acl_volume(path)
        with self.descriptor(directory) as attrs:
            # DACL_SECURITY_INFORMATION | PROTECTED_DACL_SECURITY_INFORMATION.
            if not self.adv.SetFileSecurityW(str(path), 0x80000004, attrs.descriptor):
                raise MapperError('FILE_PROTECTION_FAILED')
