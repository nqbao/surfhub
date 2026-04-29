"""Integration test for DDG pagination (hits live endpoint).

Usage:
    python tests/integration/integtest_duckduckgo.py
    pytest tests/integration/integtest_duckduckgo.py
"""
from surfhub.serper.duckduckgo import DuckDuckGo
from surfhub.errors import SerpApiError


def test_page1_returns_vqd():
    ddg = DuckDuckGo()
    page1 = ddg.serp("climate change")
    assert len(page1.items) > 0, "page 1 should have results"
    assert page1.vqd, "page 1 must return vqd"
    return page1


def test_page2_uses_vqd():
    ddg = DuckDuckGo()
    page1 = ddg.serp("climate change")
    page2 = ddg.serp("climate change", page=2, vqd=page1.vqd)
    assert len(page2.items) > 0, "page 2 should have results"
    page1_links = {r.link for r in page1.items}
    assert any(r.link not in page1_links for r in page2.items), \
        "page 2 should have different results from page 1"


def test_page2_without_vqd_raises():
    ddg = DuckDuckGo()
    try:
        ddg.serp("climate change", page=2)
        assert False, "should raise SerpApiError"
    except SerpApiError:
        pass


def test_pagination_offset():
    ddg = DuckDuckGo()
    page1 = ddg.serp("climate change")
    page3 = ddg.serp("climate change", page=3, vqd=page1.vqd)
    assert len(page3.items) > 0, "page 3 should have results"


if __name__ == "__main__":
    print("Page 1 vqd check...")
    page1 = test_page1_returns_vqd()
    print(f"  OK — {len(page1.items)} results, vqd={page1.vqd}")

    print("Page 2 with vqd...")
    test_page2_uses_vqd()
    print("  OK")

    print("Page 2 without vqd raises...")
    test_page2_without_vqd_raises()
    print("  OK")

    print("Page 3 offset...")
    test_pagination_offset()
    print("  OK")

    print("\nAll integration tests passed!")
