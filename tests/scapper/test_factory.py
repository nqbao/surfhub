from surfhub.scrapper import get_scrapper
from surfhub.scrapper.local import LocalScrapper

def test_factory():
    scrapper = get_scrapper('local')
    assert isinstance(scrapper, LocalScrapper)
