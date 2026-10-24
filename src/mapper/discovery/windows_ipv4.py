"""Thin IPv4 IP Helper adapter. No packets, sockets or DLLs on import.

Win32 types have fixed widths even when tests run on an LP64 Unix host.
The common 16-byte echo header avoids dereferencing returned data pointers.
"""
import asyncio
import ctypes as c
import ipaddress
import os
import socket
from ..errors import MapperError

U8, U16, U32, U64 = c.c_uint8, c.c_uint16, c.c_uint32, c.c_uint64
PTR = c.c_void_p


class Sockaddr4(c.Structure):
    _fields_ = [('family', U16), ('port', U16), ('address', U32), ('zero', U8 * 8)]


class Sockaddr6(c.Structure):
    _fields_ = [('family', U16), ('port', U16), ('flow', U32), ('address', U8 * 16), ('scope', U32)]


class Sockaddr(c.Union):
    _fields_ = [('v4', Sockaddr4), ('v6', Sockaddr6), ('family', U16)]


class Prefix(c.Structure):
    _fields_ = [('address', Sockaddr), ('length', U8)]


class RouteRow(c.Structure):
    _fields_ = [('luid', U64), ('index', U32), ('prefix', Prefix), ('next_hop', Sockaddr),
                ('site_prefix_length', U8), ('valid_lifetime', U32), ('preferred_lifetime', U32),
                ('metric', U32), ('protocol', U32), ('loopback', U8), ('autoconfigure', U8),
                ('publish', U8), ('immortal', U8), ('age', U32), ('origin', U32)]


class EchoHeader(c.Structure):
    _fields_ = [('address', U32), ('status', U32), ('rtt', U32), ('size', U16), ('reserved', U16)]


def address_number(value):
    # IPAddr stores network-order bytes in a Windows little-endian DWORD.
    return int.from_bytes(socket.inet_aton(str(ipaddress.IPv4Address(value))), 'little')


def sockaddr(value):
    result = Sockaddr()
    result.v4.family = socket.AF_INET
    result.v4.address = address_number(value)
    return result


class WindowsIPv4:
    def __init__(self, library=None, last_error=None):
        if library is None:
            if os.name != 'nt':
                raise MapperError('WINDOWS_IPV4_API_UNAVAILABLE')
            try:
                library = c.WinDLL('iphlpapi.dll', use_last_error=True)
            except OSError:
                raise MapperError('WINDOWS_IPV4_API_UNAVAILABLE') from None
        self.dll = library
        self.last_error = last_error or getattr(c, 'get_last_error', lambda: 0)
        signatures = {
            'ConvertInterfaceAliasToLuid': ([c.c_wchar_p, c.POINTER(U64)], U32),
            'ConvertInterfaceLuidToIndex': ([c.POINTER(U64), c.POINTER(U32)], U32),
            'GetBestRoute2': ([c.POINTER(U64), U32, c.POINTER(Sockaddr), c.POINTER(Sockaddr), U32, c.POINTER(RouteRow), c.POINTER(Sockaddr)], U32),
            'IcmpCreateFile': ([], PTR),
            'IcmpCloseHandle': ([PTR], c.c_int32),
            'IcmpSendEcho2Ex': ([PTR, PTR, PTR, PTR, U32, U32, PTR, U16, PTR, PTR, U32, U32], U32),
        }
        try:
            for name, (args, result) in signatures.items():
                fn = getattr(library, name)
                fn.argtypes, fn.restype = args, result
        except AttributeError:
            raise MapperError('WINDOWS_IPV4_API_UNAVAILABLE') from None

    def probe(self, ip, interface, source_ip, expected_index, timeout_ms):
        source, destination = sockaddr(source_ip), sockaddr(ip)
        luid, index, row, best_source = U64(), U32(), RouteRow(), Sockaddr()
        if self.dll.ConvertInterfaceAliasToLuid(interface, c.byref(luid)) or self.dll.ConvertInterfaceLuidToIndex(c.byref(luid), c.byref(index)):
            return 'skipped', 'ROUTE_OR_INTERFACE_CHANGED'
        if not index.value or (expected_index is not None and index.value != expected_index):
            return 'skipped', 'ROUTE_OR_INTERFACE_CHANGED'
        # Do not constrain the query to a preferred interface and hide a new VPN route.
        if self.dll.GetBestRoute2(None, 0, c.byref(source), c.byref(destination), 0, c.byref(row), c.byref(best_source)):
            return 'skipped', 'ROUTE_OR_INTERFACE_CHANGED'
        if (row.index != index.value or best_source.family != socket.AF_INET or
                best_source.v4.address != source.v4.address or row.next_hop.family != socket.AF_INET or
                row.next_hop.v4.address != 0 or row.loopback or not row.valid_lifetime):
            return 'skipped', 'ROUTE_OR_INTERFACE_CHANGED'
        handle = self.dll.IcmpCreateFile()
        if handle in {None, 0, c.c_void_p(-1).value}:
            return 'error', 'WINDOWS_ICMP_OPEN_FAILED'
        try:
            payload = c.create_string_buffer(b'mapper-ipv4')
            reply = c.create_string_buffer(256)
            count = self.dll.IcmpSendEcho2Ex(handle, None, None, None, source.v4.address, destination.v4.address,
                                            payload, len(payload) - 1, None, reply, len(reply), timeout_ms)
            if not count:
                return ('no_reply', None) if self.last_error() == 11010 else ('error', 'WINDOWS_ICMP_FAILED')
            header = EchoHeader.from_buffer_copy(reply.raw)
            if header.status == 11010:
                return 'no_reply', None
            if header.status or header.address != destination.v4.address or header.size != len(payload) - 1:
                return 'error', 'WINDOWS_ICMP_REPLY_NOT_CONFIRMED'
            return 'reply', None
        finally:
            self.dll.IcmpCloseHandle(handle)


async def probe(ip, interface, source_ip, expected_index, timeout, *, factory=WindowsIPv4):
    def call():
        try:
            return factory().probe(ip, interface, source_ip, expected_index, max(1, min(1000, int(timeout * 1000))))
        except OSError:
            return 'error', 'WINDOWS_IPV4_API_FAILED'
    task = asyncio.create_task(asyncio.to_thread(call))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        # The worker still owns its slot until the bounded native call releases
        # buffers and its handle. No detached ping on cancellation.
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                continue
            except Exception:
                break
        if task.done() and not task.cancelled():
            task.exception()  # consume any error after cancellation
        raise
