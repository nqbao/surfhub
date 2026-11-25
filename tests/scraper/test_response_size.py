import gzip
import zlib

import httpx
import pytest
import respx

from surfhub import ResponseTooLargeError, get_scraper


class RecordingStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    def __init__(self, *chunks):
        self.chunks = chunks
        self.read_count = 0
        self.closed = False

    def __iter__(self):
        for chunk in self.chunks:
            self.read_count += 1
            yield chunk

    async def __aiter__(self):
        for chunk in self:
            yield chunk

    def close(self):
        self.closed = True

    async def aclose(self):
        self.close()


def test_local_limit_rejects_declared_size_before_reading():
    url = "https://example.com/file"
    stream = RecordingStream(b"large")
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, headers={"Content-Length": "500"}, stream=stream))
        with pytest.raises(ResponseTooLargeError, match="4-byte"):
            get_scraper("local", max_bytes=4).scrape(url)

    assert stream.read_count == 0
    assert stream.closed


def test_local_redirect_body_is_closed_without_reading():
    start = "https://example.com/start"
    stream = RecordingStream(b"large")
    with respx.mock:
        respx.get(start).mock(return_value=httpx.Response(302, headers={"Location": "/end"}, stream=stream))
        respx.get("https://example.com/end").respond(200, content=b"1234")
        assert get_scraper("local", max_bytes=4).scrape(start).content == b"1234"

    assert stream.read_count == 0
    assert stream.closed


@pytest.mark.anyio
@pytest.mark.parametrize(("provider", "status"), [("local", 200), ("jina", 503)])
async def test_streaming_stops_at_limit_without_retrying(provider, status):
    url = "https://example.com/file"
    endpoint = url if provider == "local" else f"https://r.jina.ai/{url}"
    stream = RecordingStream(b"123", b"456", b"never read")
    with respx.mock:
        route = respx.get(endpoint).mock(return_value=httpx.Response(status, stream=stream))
        with pytest.raises(ResponseTooLargeError):
            await get_scraper(provider, max_bytes=4).async_scrape(url)

    assert route.call_count == 1
    assert route.calls.last.request.headers["Accept-Encoding"] == "gzip, deflate"
    assert stream.read_count == 2
    assert stream.closed


def test_gzip_accepts_decoded_content_at_the_limit():
    url = "https://example.com/file"
    payload = gzip.compress(b"12") + gzip.compress(b"34")
    stream = RecordingStream(payload[:7], payload[7:])
    with respx.mock:
        respx.get(url).mock(
            return_value=httpx.Response(
                200, headers={"Content-Encoding": "gzip", "Content-Length": str(len(payload))}, stream=stream
            )
        )
        assert get_scraper("local", max_bytes=4).scrape(url).content == b"1234"

    assert stream.closed


@pytest.mark.anyio
@pytest.mark.parametrize("wbits", [zlib.MAX_WBITS, -zlib.MAX_WBITS])
async def test_provider_decodes_deflate_once(wbits):
    url = "https://example.com/file"
    encoder = zlib.compressobj(wbits=wbits)
    payload = encoder.compress(b"<html>Page</html>") + encoder.flush()
    stream = RecordingStream(payload[:1], payload[1:])
    with respx.mock:
        respx.get(f"https://r.jina.ai/{url}").mock(
            return_value=httpx.Response(200, headers={"Content-Encoding": "deflate"}, stream=stream)
        )
        response = await get_scraper("jina").async_scrape(url)

    assert response.content == b"<html>Page</html>"
    assert stream.closed


def test_gzip_stops_decompressing_at_the_limit():
    url = "https://example.com/file"
    payload = gzip.compress(b"x" * (1024 * 1024))
    stream = RecordingStream(payload, b"never read")
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, headers={"Content-Encoding": "gzip"}, stream=stream))
        with pytest.raises(ResponseTooLargeError, match="32-byte"):
            get_scraper("local", max_bytes=32).scrape(url)

    assert stream.read_count == 1
    assert stream.closed


def test_gzip_caps_wire_bytes_when_decoded_output_is_empty():
    url = "https://example.com/file"
    chunk = gzip.compress(b"") * 2000
    stream = RecordingStream(chunk, chunk, b"never read")
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, headers={"Content-Encoding": "gzip"}, stream=stream))
        with pytest.raises(ResponseTooLargeError):
            get_scraper("local", max_bytes=32).scrape(url)

    assert stream.read_count == 2
    assert stream.closed


def test_truncated_gzip_is_rejected():
    url = "https://example.com/file"
    stream = RecordingStream(gzip.compress(b"Page")[:-4])
    with respx.mock:
        respx.get(url).mock(return_value=httpx.Response(200, headers={"Content-Encoding": "gzip"}, stream=stream))
        with pytest.raises(httpx.DecodingError, match="Incomplete gzip"):
            get_scraper("local").scrape(url)

    assert stream.closed
