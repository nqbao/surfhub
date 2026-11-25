import ipaddress
import socket
import ssl

import anyio
import httpcore
import httpx
import sniffio


def _public_addresses(host, port):
    try:
        records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise httpcore.ConnectError(str(exc)) from exc

    addresses = []
    for _, _, _, _, sockaddr in records:
        address = ipaddress.ip_address(sockaddr[0])
        if isinstance(address, ipaddress.IPv6Address):
            if address.ipv4_mapped is not None:
                address = address.ipv4_mapped
            elif address.scope_id or address not in ipaddress.IPv6Network("2000::/3"):
                raise httpcore.ConnectError(f"Non-public destination blocked for {host}")
            elif address.sixtofour or address.teredo or address in ipaddress.IPv6Network("2001::/23"):
                raise httpcore.ConnectError(f"Non-public destination blocked for {host}")
        if not address.is_global or address.is_multicast or address.is_reserved:
            raise httpcore.ConnectError(f"Non-public destination blocked for {host}")
        if str(address) not in addresses:
            addresses.append(str(address))
    if not addresses:
        raise httpcore.ConnectError(f"No public address found for {host}")
    return addresses


class _PublicSyncBackend(httpcore.SyncBackend):
    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        addresses = _public_addresses(host, port)
        for address in addresses:
            try:
                return super().connect_tcp(address, port, timeout, local_address, socket_options)
            except (httpcore.ConnectError, httpcore.ConnectTimeout) as exc:
                last_error = exc
        raise last_error


class _PublicAsyncBackend(httpcore.AsyncNetworkBackend):
    @staticmethod
    def _backend():
        if sniffio.current_async_library() == "trio":
            return httpcore.TrioBackend()
        return httpcore.AnyIOBackend()

    async def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        addresses = await anyio.to_thread.run_sync(_public_addresses, host, port)
        backend = self._backend()
        for address in addresses:
            try:
                return await backend.connect_tcp(address, port, timeout, local_address, socket_options)
            except (httpcore.ConnectError, httpcore.ConnectTimeout) as exc:
                last_error = exc
        raise last_error

    async def sleep(self, seconds):
        await anyio.sleep(seconds)


def _ssl_context(verify):
    return httpx.create_ssl_context(verify=verify, trust_env=False)


class PublicHTTPTransport(httpx.HTTPTransport):
    def __init__(self, verify: bool):
        # HTTPX handles redirects and TLS hostnames. The pool connects to the
        # exact IP checked by the backend, without resolving the hostname again.
        self._pool = httpcore.ConnectionPool(
            ssl_context=_ssl_context(verify), network_backend=_PublicSyncBackend()
        )


class PublicAsyncHTTPTransport(httpx.AsyncHTTPTransport):
    def __init__(self, verify: bool):
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=_ssl_context(verify), network_backend=_PublicAsyncBackend()
        )
