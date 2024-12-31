from surfhub.scraper import get_scraper
from surfhub.scraper.local import LocalScraper
from surfhub.scraper.browserless import BrowserlessScraper

def test_factory():
    scraper = get_scraper('local')
    assert isinstance(scraper, LocalScraper)

    scraper = get_scraper('browserless')
    assert isinstance(scraper, BrowserlessScraper)
