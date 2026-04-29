from surfhub.scraper import get_scraper
from surfhub.scraper.local import LocalScraper
from surfhub.scraper.browserless import BrowserlessScraper
from surfhub.scraper.exa import ExaScraper
from surfhub.scraper.jina import JinaScraper
from surfhub.scraper.firecrawl import FirecrawlScraper
from surfhub.scraper.scrapingbee import ScrapingBeeScraper

def test_factory():
    scraper = get_scraper('local')
    assert isinstance(scraper, LocalScraper)

    scraper = get_scraper('browserless')
    assert isinstance(scraper, BrowserlessScraper)

    scraper = get_scraper('exa', api_key='test_key')
    assert isinstance(scraper, ExaScraper)

    scraper = get_scraper('jina', api_key='test_key')
    assert isinstance(scraper, JinaScraper)

    scraper = get_scraper('firecrawl', api_key='test_key')
    assert isinstance(scraper, FirecrawlScraper)

    scraper = get_scraper('scrapingbee', api_key='test_key')
    assert isinstance(scraper, ScrapingBeeScraper)
