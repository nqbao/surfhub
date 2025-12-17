# surfhub
A python library for surfing and crawling website. 

This library provides two basic components for you to run google search and getting result

* Seprer is a API to provide structured data from Google search. There are many serper providers such as ValueSerp, Serper, etc
* Scraper is an API to extract HTML from website. You can run it on your own laptop, but it is better to use providers such as Zyte, or Browserless

To start, you can visit [Serper](https://serper.dev) to get a free account.

```
import surfhub import get_serper

s = get_serper("serper", api_key="yourkey")
print(s.serp("hello world").items)
```

Supported SERP provider:
  * [ValueSerp](https://valueserp.com/)
  * Google Custom Search
  * [Serper](https://serper.dev/)
  * Duckduckgo


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

# TODO

- [ ] Support ScrappingBee
- [ ] Support [SerpAPI](https://serpapi.com/)
