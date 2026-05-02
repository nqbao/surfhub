"""Integration test for DDG pagination (hits live endpoint).

Usage:
    python tests/integration/integtest_duckduckgo.py
"""
import time
from surfhub.serper.duckduckgo import DuckDuckGo
from surfhub.errors import SerpApiError

_DELAY = 3


if __name__ == "__main__":
    ddg = DuckDuckGo()

    print("Page 1 vqd check...")
    page1 = ddg.serp("climate change")
    assert len(page1.items) > 0, "page 1 should have results"
    assert page1.vqd, "page 1 must return vqd"
    print(f"  OK — {len(page1.items)} results, vqd={page1.vqd[:20]}...")

    time.sleep(_DELAY)
    print("Page 2 with vqd...")
    page2 = ddg.serp("climate change", page=2, vqd=page1.vqd)
    assert len(page2.items) > 0, "page 2 should have results"
    page1_links = {r.link for r in page1.items}
    assert any(r.link not in page1_links for r in page2.items), \
        "page 2 should have different results from page 1"
    print("  OK")

    time.sleep(_DELAY)
    print("Page 3 offset...")
    page3 = ddg.serp("climate change", page=3, vqd=page1.vqd)
    assert len(page3.items) > 0, "page 3 should have results"
    print("  OK")

    time.sleep(_DELAY)
    print("Page 2 without vqd raises...")
    try:
        ddg.serp("climate change", page=2)
        assert False, "should raise SerpApiError"
    except SerpApiError:
        print("  OK")

    ddg.close()
    print("\nAll integration tests passed!")
