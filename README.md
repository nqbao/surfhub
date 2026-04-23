# surfhub
A python library for surfing and crawling website. 

This library provides two basic components for you to run google search and getting result

* **SERP** is an API that provides structured data from Google search results. There are many SERP providers such as ValueSerp, Serper, etc.
* **Scraper** is an API that extracts HTML from websites. You can run it on your own laptop, but it's better to use providers such as Zyte or Browserless.

To start, you can visit [Serper](https://serper.dev) to get a free account.

```
from surfhub import get_serper

s = get_serper("serper", api_key="yourkey")
print(s.serp("hello world").items)
```

Supported SERP provider:
  * [ValueSerp](https://valueserp.com/)
  * Google Custom Search
  * [Serper](https://serper.dev/)
  * [SerpApi](https://serpapi.com/)
  * Duckduckgo
  * [Tavily](https://tavily.com/)
  * [You.com](https://you.com/)
  * [Brave](https://brave.com)
  * [Exa](https://exa.ai)


Example to use scraper

```
from surfhub import get_scraper

s = serp.get_scraper("browserless", api_key="yourkey")
s.scrape("https://webscraper.io/test-sites/e-commerce/allinone")
```

Supported Scraper provider
  * Local (run on your laptop) with proxy support
  * Browserless
  * Zyte
  * Crawlbase
  * [Exa](https://exa.ai)

# TODO

- [ ] Support ScrappingBee
- [ ] Add safe search option
- [ ] Enable as MCP later
- [ ] Add markdown converstion support
- [ ] Make beautiful soup optional for duckduckgo