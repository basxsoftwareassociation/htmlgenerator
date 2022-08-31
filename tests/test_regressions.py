import htmlgenerator as hg


def test_str_format_zero():
    assert hg.render(hg.format("1{}", hg.C("value")), {"value": 0}) == "10"
