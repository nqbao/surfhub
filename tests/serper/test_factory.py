from surfhub.serper import get_serp
from surfhub.serper.google import GoogleCustomSearch
from surfhub.serper.valueserp import ValueSerp

def test_factory():
    serp = get_serp("google")
    assert isinstance(serp, GoogleCustomSearch)

    serp = get_serp("valueserp")
    assert isinstance(serp, ValueSerp)
