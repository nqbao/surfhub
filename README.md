# surfhub
A python library for surfing and crawling website


Example to use serper

```
import surhub.serp as serp
s = serp.get_serp("valueserp", api_key="yourkey")
s.serp("hello world")
```

Supported SERP provider:
  * [ValueSerp](https://valueserp.com/)
  * Google Custom Search
  * [Serper](https://serper.dev/)

TODO: [SerpAPI](https://serpapi.com/), DuckDuckGo


Example to use scrapper

```
import surfhub.scrapper as scapper

s = serp.get_scrapper("browserless", api_key="yourkey")
s.scrape("https://webscraper.io/test-sites/e-commerce/allinone")
```

Supported Scrapper provider
  * Local (run on your laptop) with proxy support
  * Browserless
  * Zyte
  * Crawlspace

TODO: ScrappingBee
