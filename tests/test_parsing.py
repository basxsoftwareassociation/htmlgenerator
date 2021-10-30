import os

import htmlgenerator as hg
from htmlgenerator.contrib.convertfromhtml import parsehtml


def test_parsing():
    with open(os.path.join(os.path.dirname(__file__), "parsing_test.html"), "r") as f:
        html = f.read()
    for formatting in [True, False]:
        for compact in [True, False]:
            _local = {}
            exec(parsehtml(html, formatting, compact), {}, _local)
            assert isinstance(_local["html"], hg.BaseElement)
