import htmlgenerator as hg


def test_tons_of_stuff():
    LT = "&lt;"
    GT = "&gt;"
    AMP = "&amp;"

    # format of testdata: (element, context, correct output)
    testdata = (
        #### Test virtual elements ####
        (hg.If(True, "true", "false"), {}, "true"),
        (hg.If(False, "true"), {}, ""),
        (hg.If(False, "true", "false"), {}, "false"),
        (hg.If(hg.C("cond"), "true", "false"), {"cond": False}, "false"),
        (hg.Iterator(hg.C("count"), "i", hg.C("i")), {"count": range(6)}, "012345"),
        (hg.WithContext(hg.C("additional"), additional=42), {}, "42"),
        (
            hg.WithContext(hg.DIV(hg.C("additional")), additional=42),
            {},
            "<div>42</div>",
        ),
        (hg.DIV(_class="less"), {}, '<div class="less"></div>'),
        (hg.DIV(_class=hg.If(True, "active")), {}, '<div class="active"></div>'),
        (hg.DIV(_class=hg.If(False, "active")), {}, "<div></div>"),
        (
            hg.DIV(_class=hg.If(hg.C("isactive"), "active")),
            {"isactive": True},
            '<div class="active"></div>',
        ),
        (
            hg.DIV(_class=hg.If(hg.C("isactive"), "active")),
            {"isactive": False},
            "<div></div>",
        ),
        #### test string formatting, be carefull about escaping! ####
        # test basic behaviour
        (hg.format("xkcd and xhtml are great"), {}, "xkcd and xhtml are great"),
        (hg.format('"'), {}, "&quot;"),
        (hg.format(hg.mark_safe('"')), {}, '"'),
        (hg.format("<>"), {}, f"{LT}{GT}"),
        (hg.format("&"), {}, AMP),
        (hg.format(hg.mark_safe("<&>")), {}, "<&>"),
        # test with argument
        (hg.format("test: {}", "field1"), {}, "test: field1"),
        (hg.format("<>: {}", "field1"), {}, f"{LT}{GT}: field1"),
        (hg.format("<>: {}", "&"), {}, f"{LT}{GT}: {AMP}"),
        # test format string with save string
        (hg.format(hg.mark_safe("<>: {}"), "&"), {}, f"<>: {AMP}"),
        # test argument with save string
        (hg.format("<>: {}", hg.mark_safe("&")), {}, f"{LT}{GT}: &"),
        # test format string and argument with save string
        (hg.format(hg.mark_safe("<>: {}"), hg.mark_safe("&")), {}, "<>: &"),
        # test with keyword args
        (hg.format(hg.mark_safe("<>: {test}"), test=hg.mark_safe("&")), {}, "<>: &"),
        (hg.DIV("hello world", id=1), {}, '<div id="1">hello world</div>'),
        (hg.DIV(attr='"'), {}, '<div attr="&quot;"></div>'),
        (hg.DIV(attr=hg.mark_safe('"')), {}, '<div attr="""></div>'),
        #### regression tests ####
        # error where zero was would not produce output
        (hg.format("1{}", hg.C("zero")), {"zero": 0}, "10"),
    )
    for input, context, output in testdata:
        assert hg.render(input, context) == output


def test_html_id():
    assert hg.html_id(object()) != hg.html_id(object())
    o = object()
    assert hg.html_id(o) != hg.html_id(o)


def test_fragments():
    tree = hg.DIV(
        hg.Fragment("redpill", hg.DIV("RED!")), hg.Fragment("bluepill", hg.DIV("BLUE!"))
    )
    output_nofragment = "<div><div>RED!</div><div>BLUE!</div></div>"
    output_fragment_red = "<div>RED!</div>"
    output_fragment_blue = "<div>BLUE!</div>"
    output_fragment_other = ""
    assert hg.render(tree, {}) == output_nofragment, "no fragment"
    assert (
        hg.render(tree, {}, fragment="redpill") == output_fragment_red
    ), "red fragment"
    assert (
        hg.render(tree, {}, fragment="bluepill") == output_fragment_blue
    ), "blue fragment"
    assert (
        hg.render(tree, {}, fragment="greenpill") == output_fragment_other
    ), "unknown fragment"
