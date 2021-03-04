import unittest

import htmlgenerator as hg


class TestHTMLGeneratorID(unittest.TestCase):
    def test(self):
        self.assertNotEqual(hg.html_id(object()), hg.html_id(object()))
        o = object()
        self.assertNotEqual(hg.html_id(o), hg.html_id(o))


if __name__ == "__main__":
    unittest.main()
