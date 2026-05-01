import pytest
from surfhub.serper import get_serper
from surfhub.scraper import get_scraper
from surfhub.serper.model import BaseSerper, SerpApi
from surfhub.scraper.model import Scraper


class TestGetSerper:
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_serper("nonexistent")

    def test_empty_provider_raises(self):
        with pytest.raises(ValueError, match="provider"):
            get_serper("")

    def test_none_provider_raises(self):
        with pytest.raises(ValueError, match="provider"):
            get_serper(None)

    def test_serper_provider(self):
        s = get_serper("serper", api_key="test_key")
        assert isinstance(s, BaseSerper)

    def test_duckduckgo_provider(self):
        s = get_serper("duckduckgo")
        assert isinstance(s, SerpApi)

    def test_google_provider(self):
        s = get_serper("google", api_key="cx:key")
        assert isinstance(s, BaseSerper)


class TestGetScraper:
    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown scraper"):
            get_scraper("nonexistent")

    def test_local_provider(self):
        s = get_scraper("local")
        assert isinstance(s, Scraper)

    def test_browserless_provider(self):
        s = get_scraper("browserless", api_key="test_key")
        assert isinstance(s, Scraper)
