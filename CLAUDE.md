# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install for development
pip install -e .

# Run unit tests
pytest

# Run a single test file
pytest tests/serper/test_serpapi.py

# Run a single test by name
pytest tests/serper/test_serpapi.py::test_name

# Format code
make format   # or: black src/ tests/

# Lint
make lint     # or: flake8 src/ tests/

# Build package
make build
```

### Integration tests

Integration tests live in `tests/integration/` and **must be run manually** — they hit live external endpoints and require real API keys or network access. Do not run them as part of the normal test suite.

```bash
# Run as a script (direct output)
python tests/integration/integtest_duckduckgo.py
python tests/integration/integtest_scraper_markdown.py

# Or via pytest
pytest tests/integration/integtest_scraper_markdown.py
```

## Architecture

The library has two independent top-level components, both accessible from `surfhub`:

- **SERP** (`src/surfhub/serper/`) — query search engines, returns structured `SerpResponse(items, cached, metadata)`.
- **Scraper** (`src/surfhub/scraper/`) — fetch and extract content from URLs, returns `ScraperResponse(content, content_type, encoding, final_url, status_code)`.

### SERP layer

`BaseSerper` in `serper/model.py` handles the full request lifecycle: building params (`get_serp_params`), optional cache lookup, HTTP dispatch (`_fetch_and_parse` / `_async_fetch_and_parse`), and result assembly (`parse_result`). Each provider subclass only needs to implement `get_serp_params` and `parse_result`.

Caching is injected via `Cache` (abstract base in `cache/base.py`). `FileCache` wraps `diskcache`. The cache key is a hash of the full params dict plus the provider class name.

`DuckDuckGo` is the only provider that doesn't require an API key (uses HTML scraping + vqd token for pagination). Its response extends `SerpResponse` with a `vqd` field needed for page 2+.

### Scraper layer

`BaseScraper` in `scraper/model.py` handles retries (default 3), sync/async HTTP via `httpx`, and delegates to subclasses via `prepare_request` / `parse_response`. Retry logic uses `is_retriable_error` — retries on `httpx.TransportError` and HTTP 5xx.

`ScraperResponse.markdown()` converts content based on `content_type`:
- `text/html` → runs `trafilatura.extract(..., output_format='markdown')`
- `text/markdown` or `text/plain` → passes content through as-is (decode only)

`LocalScraper` runs scraping on the machine using `httpx` directly (no API key). All other scrapers proxy through a third-party service API.

### Factory functions

`get_serper(provider, cache=None, api_key=None, **kwargs)` and `get_scraper(provider, api_key=None, **kwargs)` are the main entry points, re-exported from `surfhub/__init__.py`.

### Test structure

- `tests/serper/` — unit tests for SERP providers (use `respx` to mock httpx)
- `tests/scaper/` — unit tests for scraper providers (note: directory has a typo, `scaper` not `scraper`)
- `tests/integration/` — live-network integration tests, run manually only
- `pytest.ini` sets `pythonpath = src` so imports work without installing
