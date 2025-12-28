from surfhub.serper import get_serper
from surfhub.serper.google import GoogleCustomSearch
from surfhub.serper.valueserp import ValueSerp
from surfhub.serper.you import YouSearch

def test_factory():
    serp = get_serper("google")
    assert isinstance(serp, GoogleCustomSearch)

    serp = get_serper("valueserp")
    assert isinstance(serp, ValueSerp)

    serp = get_serper("you")
    assert isinstance(serp, YouSearch)
