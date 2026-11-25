# surfhub

A Python library for querying search engines and scraping web pages through local and hosted providers.

Requires Python 3.11.5 or newer. To install from this checkout, run `python -m pip install .`.

## Search

Search providers return a `SerpResponse` with structured titles, links, and snippets in `items`. Use `serp()` in synchronous code and `async_serp()` in async code.

```python
from surfhub import get_serper

search = get_serper("serper", api_key="yourkey")
print(search.serp("hello world").items)
```

### Search providers

| Provider | Key | Notes |
|---|---|---|
| [ValueSerp](https://valueserp.com/) | `valueserp` | Time range & custom date support |
| Google Custom Search | `google` | `api_key` format: `cx:key` |
| [Serper](https://serper.dev/) | `serper` | lang, country, location, domain |
| [SerpApi](https://serpapi.com/) | `serpapi` | Custom date ranges, pagination |
| [DuckDuckGo](https://duckduckgo.com) | `duckduckgo` | No API key required (HTML scraping) |
| [Tavily](https://tavily.com/) | `tavily` | `answer` field, time range |
| [You.com](https://you.com/) | `you` | Web + News results, time filtering |
| [Brave](https://brave.com) | `brave` | Web + News results, freshness |
| [Exa](https://exa.ai) | `exa` | Neural/keyword/auto search types |
| [Perplexity](https://perplexity.ai) | `perplexity` | Sonar model, citations & `answer` |
| [Jina](https://jina.ai) | `jina` | LLM-optimized SERP results |

## Scraping

Scrapers return a `ScraperResponse` with the response bytes, content type, encoding, final URL, and status code. Use `scrape()` or `async_scrape()`.

Scrapers follow redirects and accept 2xx responses. Other statuses raise `ScrapingError` with `status_code` and `raw_body`, including target failures reported by providers. Provider billing/quota failures raise `InsufficientFundsError`. Transport failures, HTTP 429, and 5xx responses are retried immediately, with three total attempts by default. Set `scraper.retries = 1` to disable retries, or another positive integer to change the total attempt limit. This applies to local HTTP/browser fetching and API scrapers, sync and async. Local error pages now raise instead of being returned as successful results.

| Provider | Key | Notes |
|---|---|---|
| Local | `local` | Direct HTTP requests or optional Playwright rendering |
| [Browserless](https://browserless.io) | `browserless` | Headless Chrome via API |
| [Zyte](https://zyte.com) | `zyte` | Direct HTTP or browser HTML extraction |
| [Crawlbase](https://crawlbase.com) | `crawlbase` | Token-based auth, status validation |
| [Exa](https://exa.ai) | `exa` | Cleaned page text via Contents API |
| [Jina](https://jina.ai) | `jina` | Reader API, supports `format` (html/markdown/text) and `engine` (direct/browser) |
| [Firecrawl](https://firecrawl.dev) | `firecrawl` | Markdown output |
| [ScrapingBee](https://scrapingbee.com) | `scrapingbee` | Headless browser, JS rendering, premium proxies |

```python
from surfhub import get_scraper

scraper = get_scraper("local")
response = scraper.scrape("https://example.com")
print(response.markdown())
```

### Markdown conversion

`response.markdown()` uses Trafilatura for HTML. If its first pass finds no content, it retries with higher recall and then tries plain-text extraction. When Content-Type is missing, an opening `<html>` tag or HTML doctype at the start of the body is enough to select the HTML converter. Markdown, other `text/*` types, and JSON are decoded as-is. PDF, image, and other unsupported types return an empty string. The raw bytes are still available as `response.content`.

Set `markdown_engine` when creating a scraper to use your own converter for every HTML response. The converter accepts HTML bytes and returns a Markdown string or `None`.

```python
scraper = get_scraper("local", markdown_engine=convert_html)
response = scraper.scrape("https://example.com")
print(response.markdown())
```

For a single conversion, pass `response.markdown(engine=another_converter)` to override the scraper's engine.

### Response size

HTTP scrapers stream up to 10 MiB of decoded content per response by default. Pass `max_bytes` to `get_scraper()` to change the limit, for example `get_scraper("local", max_bytes=2 * 1024 * 1024)`. The limit applies during gzip and deflate decompression. Exceeding it raises `ResponseTooLargeError`. In local browser mode, the limit applies to the rendered HTML returned by Chromium. Chromium manages its own network downloads.

### Local scraper

Local HTTP requests follow redirects and check that each connection uses a public IP address. Apply your service's outbound network policy when running the scraper in a service. For trusted URLs and content, set `allow_private_network=True` when you need private destinations, configured proxies, or browser rendering. For browser rendering, install the browser extra with `python -m pip install '.[browser]'`, run `python -m playwright install chromium`, and pass `use_browser=True` to the scrape call.

The default HTTP User-Agent is `surfhub/<version> (https://github.com/nqbao/surfhub)`. Set `user_agent` to identify your application in both sync and async HTTP requests.

```python
from surfhub import get_scraper

scraper = get_scraper("local", user_agent="ResearchAgent/1.0 (https://example.com/contact)")
```

## Caching

Both factories accept an optional `FileCache`.

```python
from surfhub import get_scraper, get_serper
from surfhub.cache import FileCache

cache = FileCache(".surfhub-cache")

search = get_serper("serper", api_key="yourkey", cache=cache)
scraper = get_scraper("local", cache=cache)
```

`FileCache` stores Surfhub responses, bytes, and JSON-compatible values. Scrapers cache only HTTP 2xx responses. Existing DiskCache entries are treated as cache misses and repopulate on demand.

## Search options

Options vary by provider. SerpApi supports explicit start and end dates.

```python
from surfhub import SerpRequestOptions, get_serper

search = get_serper("serpapi", api_key="yourkey")
options = SerpRequestOptions(
    lang="en",
    country="us",
    date_start="2025-01-01",
    date_end="2025-12-31",
)
results = search.serp("query", num=10, options=options)
```

## TODO

- [ ] Add safe search option
- [ ] CLI support
- [ ] Enable as MCP later
- [ ] Make beautifulsoup optional for DuckDuckGo
