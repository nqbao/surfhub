from surfhub.scraper import get_scrapper
from surfhub.scraper.local import LocalScrapper
from surfhub.scraper.browserless import BrowserlessScrapper

def test_factory():
    scrapper = get_scrapper('local')
    assert isinstance(scrapper, LocalScrapper)

    scrapper = get_scrapper('browserless')
    assert isinstance(scrapper, BrowserlessScrapper)
