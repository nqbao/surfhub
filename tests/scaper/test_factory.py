from surfhub.scraper import get_scraper
from surfhub.scraper.local import LocalScraper
from surfhub.scraper.browserless import BrowserlessScraper
from surfhub.scraper.exa import ExaScraper

def test_factory():
    scraper = get_scraper('local')
    assert isinstance(scraper, LocalScraper)

    scraper = get_scraper('browserless')
    assert isinstance(scraper, BrowserlessScraper)

    scraper = get_scraper('exa', api_key='test_key')
    assert isinstance(scraper, ExaScraper)
