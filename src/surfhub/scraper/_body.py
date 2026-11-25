import zlib

import httpx

from surfhub.errors import ResponseTooLargeError, ScrapingError


ACCEPT_ENCODING = "gzip, deflate"


def check_size(size: int, max_bytes: int) -> None:
    if size > max_bytes:
        raise ResponseTooLargeError(max_bytes)


class _BodyReader:
    def __init__(self, response: httpx.Response, max_bytes: int):
        self.encoding = response.headers.get("content-encoding", "").strip().lower() or "identity"
        if self.encoding not in ("identity", "gzip", "deflate"):
            raise ScrapingError(f"Unsupported Content-Encoding: {self.encoding}", status_code=response.status_code)

        self.max_bytes = max_bytes
        self.max_wire_bytes = max_bytes
        if self.encoding != "identity":
            # Allow for framing and incompressible data while bounding downloads
            # that produce little or no decompressed output.
            self.max_wire_bytes += max(64 * 1024, max_bytes // 100)
        try:
            declared_size = int(response.headers.get("content-length", ""))
        except ValueError:
            declared_size = 0
        check_size(declared_size, self.max_wire_bytes)

        self.wire_bytes = 0
        self.body = bytearray()
        self.deflate_prefix = b""
        self.decoder = zlib.decompressobj(16 + zlib.MAX_WBITS) if self.encoding == "gzip" else None

    def append(self, chunk: bytes) -> None:
        self.wire_bytes += len(chunk)
        check_size(self.wire_bytes, self.max_wire_bytes)
        if self.encoding == "identity":
            self.body.extend(chunk)
            return

        if self.decoder is None:
            chunk = self.deflate_prefix + chunk
            if len(chunk) < 2:
                self.deflate_prefix = chunk
                return
            cmf, flg = chunk[:2]
            has_zlib_wrapper = (cmf & 0x0F) == 8 and (cmf >> 4) <= 7 and ((cmf << 8) | flg) % 31 == 0
            self.decoder = zlib.decompressobj(zlib.MAX_WBITS if has_zlib_wrapper else -zlib.MAX_WBITS)
            self.deflate_prefix = b""

        try:
            while chunk:
                if self.decoder.eof:
                    if self.encoding != "gzip":
                        raise httpx.DecodingError("Unexpected data after the deflate stream")
                    self.decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
                remaining = self.max_bytes - len(self.body)
                decoded = self.decoder.decompress(chunk, remaining + 1)
                check_size(len(self.body) + len(decoded), self.max_bytes)
                self.body.extend(decoded)
                chunk = self.decoder.unused_data if self.decoder.eof else self.decoder.unconsumed_tail
        except zlib.error as exc:
            raise httpx.DecodingError(f"Invalid {self.encoding} response: {exc}") from exc

    def finish(self) -> bytes:
        if self.encoding != "identity" and self.wire_bytes and (self.decoder is None or not self.decoder.eof):
            raise httpx.DecodingError(f"Incomplete {self.encoding} response")
        return bytes(self.body)


def read_body(response: httpx.Response, max_bytes: int) -> bytes:
    if response.status_code in (204, 304):
        return b""
    reader = _BodyReader(response, max_bytes)
    if response.is_stream_consumed:
        check_size(len(response.content), max_bytes)
        return response.content
    for chunk in response.iter_raw():
        reader.append(chunk)
    return reader.finish()


async def async_read_body(response: httpx.Response, max_bytes: int) -> bytes:
    if response.status_code in (204, 304):
        return b""
    reader = _BodyReader(response, max_bytes)
    if response.is_stream_consumed:
        check_size(len(response.content), max_bytes)
        return response.content
    async for chunk in response.aiter_raw():
        reader.append(chunk)
    return reader.finish()


def buffered_response(response: httpx.Response, body: bytes) -> httpx.Response:
    headers = response.headers.copy()
    if "content-encoding" in headers:
        del headers["content-encoding"]
        headers["Content-Length"] = str(len(body))
    return httpx.Response(
        status_code=response.status_code,
        headers=headers,
        content=body,
        request=response.request,
        extensions=response.extensions,
        history=response.history,
    )
