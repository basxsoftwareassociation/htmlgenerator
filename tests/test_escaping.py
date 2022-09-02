import htmlgenerator as hg


def test_escaping():
    LT = "&lt;"
    GT = "&gt;"
    AMP = "&amp;"
    testdata = (
        # test basic behaviour
        (hg.format("xkcd and xhtml are great"), "xkcd and xhtml are great"),
        (hg.format('"'), "&quot;"),
        (hg.format(hg.mark_safe('"')), '"'),
        (hg.format("<>"), f"{LT}{GT}"),
        (hg.format("&"), AMP),
        (hg.format(hg.mark_safe("<&>")), "<&>"),
        # test with argument
        (hg.format("test: {}", "field1"), "test: field1"),
        (hg.format("<>: {}", "field1"), f"{LT}{GT}: field1"),
        (hg.format("<>: {}", "&"), f"{LT}{GT}: {AMP}"),
        # test format string with save string
        (hg.format(hg.mark_safe("<>: {}"), "&"), f"<>: {AMP}"),
        # test argument with save string
        (hg.format("<>: {}", hg.mark_safe("&")), f"{LT}{GT}: &"),
        # test format string and argument with save string
        (hg.format(hg.mark_safe("<>: {}"), hg.mark_safe("&")), "<>: &"),
        # test with keyword args
        (hg.format(hg.mark_safe("<>: {test}"), test=hg.mark_safe("&")), "<>: &"),
        (hg.DIV("hello world", id=1), '<div id="1">hello world</div>'),
        (hg.DIV(attr='"'), '<div attr="&quot;"></div>'),
        (hg.DIV(attr=hg.mark_safe('"')), '<div attr="""></div>'),
    )
    for input, output in testdata:
        assert hg.render(input, {}) == output
