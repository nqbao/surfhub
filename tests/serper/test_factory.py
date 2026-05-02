from surfhub.serper import get_serper
from surfhub.serper.google import GoogleCustomSearch
from surfhub.serper.valueserp import ValueSerp
from surfhub.serper.you import YouSearch
from surfhub.serper.brave import BraveSearch
from surfhub.serper.exa import ExaSearch
from surfhub.serper.perplexity import PerplexitySearch
from surfhub.serper.jina import JinaSearch


def test_factory():
    serp = get_serper("google")
    assert isinstance(serp, GoogleCustomSearch)

    serp = get_serper("valueserp")
    assert isinstance(serp, ValueSerp)

    serp = get_serper("you")
    assert isinstance(serp, YouSearch)

    serp = get_serper("brave")
    assert isinstance(serp, BraveSearch)

    serp = get_serper("exa")
    assert isinstance(serp, ExaSearch)

    serp = get_serper("perplexity")
    assert isinstance(serp, PerplexitySearch)

    serp = get_serper("jina")
    assert isinstance(serp, JinaSearch)
