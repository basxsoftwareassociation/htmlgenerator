def render(root, basecontext):
    return "".join(root.render(basecontext))


def _try_render(elements, context):
    for element in elements:
        if isinstance(element, str):
            if "{" in element or "}" in element:
                yield htmlescape(element.format(**context))
            else:
                yield htmlescape(element)
        else:
            yield from element.render(context)


def htmlescape(s):
    return s


def flatattrs(attrs):
    """Converts a dictionary to a string of XML-attributes.
    Leading underscores are removed and underscores are replaced with dashes."""
    attlist = []
    for key, value in attrs.items():
        if key[0] == "_":
            key = key[1:]
        key = key.replace("_", "-")
        attlist.append(f'{key}="{value}"')
    return " ".join(attlist)


class BaseElement(tuple):
    def __new__(cls, *children):
        return tuple.__new__(cls, children)

    @property
    def children(self):
        return self

    def render(self, context):
        """Returns a list of strings which represents the output"""
        yield from _try_render(self.children, context)


class HTMLElement(BaseElement):
    tag = None

    def __new__(cls, *children, **attributes):
        return super().__new__(cls, attributes, *children)

    @property
    def children(self):
        return self[1:]

    @property
    def attributes(self):
        return self[0]

    def render(self, context):
        assert self.tag is not None
        yield f"<{self.tag} {flatattrs(self.attributes)}>"
        yield from super().render(context)
        yield f"</{self.tag}>"


class If(BaseElement):
    def __new__(cls, condition, true_child, false_child=""):
        return super().__new__(cls, condition, true_child, false_child)

    def render(self, context):
        if self[0](context):
            yield from _try_render((self[1],), context)
        elif len(self) > 2:
            yield from _try_render((self[2],), context)
        else:
            yield ""


class Iterate(BaseElement):
    def __new__(cls, iterator, variablename, *children):
        return super().__new__(cls, iterator, variablename, *children)

    @property
    def children(self):
        return self[2:]

    def render(self, context):
        c = dict(context)
        for obj in self[0]:
            c[self[1]] = obj
            yield from super().render(c)
