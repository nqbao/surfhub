# surfhub
A Python library for SERP and web scraping with multiple provider integration.

Requires Python 3.11+.

This library provides two basic components:

* **SERP** — query search engines and get structured results (title, link, snippet). Supports 11 providers.
* **Scraper** — extract content from any URL. Supports 8 providers with sync & async APIs.

To start, you can visit [Serper](https://serper.dev) to get a free account.

```python
from surfhub import get_serper

s = get_serper("serper", api_key="yourkey")
print(s.serp("hello world").items)
```

## SERP Providers

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

## Scraper Providers

| Provider | Key | Notes |
|---|---|---|
| Local | `local` | Runs on your machine, proxy support |
| [Browserless](https://browserless.io) | `browserless` | Headless Chrome via API |
| [Zyte](https://zyte.com) | `zyte` | Browser HTML extraction |
| [Crawlbase](https://crawlbase.com) | `crawlbase` | Token-based auth, status validation |
| [Exa](https://exa.ai) | `exa` | Cleaned page text via Contents API |
| [Jina](https://jina.ai) | `jina` | Reader API, supports `format` (html/markdown/text) and `engine` (direct/browser) |
| [Firecrawl](https://firecrawl.dev) | `firecrawl` | Markdown output |
| [ScrapingBee](https://scrapingbee.com) | `scrapingbee` | Headless browser, JS rendering, premium proxies |

```python
from surfhub import get_scraper

s = get_scraper("browserless", api_key="yourkey")
s.scrape("https://example.com")
```

## Caching

All SERP providers support optional caching via `FileCache`:

```python
from surfhub.cache import FileCache

cache = FileCache("cache.db")
s = get_serper("serper", api_key="yourkey", cache=cache)
```

## Options

```python
from surfhub import SerpRequestOptions

options = SerpRequestOptions(
    lang="en",
    country="us",
    time_range="m",          # DAY, WEEK, MONTH, YEAR
    date_start="2025-01-01",
    date_end="2025-12-31",
)
s.serp("query", num=10, options=options)
```

## TODO

- [ ] Add safe search option
- [ ] CLI support
- [ ] Enable as MCP later
- [ ] Add markdown conversion support
- [ ] Make beautifulsoup optional for DuckDuckGo
