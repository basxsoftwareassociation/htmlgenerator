import copy

from django.utils import html


def render(root, basecontext):
    """ Shortcut to serialize an object tree into a string"""
    return "".join(root.render(basecontext))


def flatattrs(attrs):
    """Converts a dictionary to a string of HTML-attributes.
    Leading underscores are removed and underscores are replaced with dashes."""
    attlist = []
    for key, value in attrs.items():
        if key[0] == "_":
            key = key[1:]
        key = key.replace("_", "-")
        if isinstance(value, bool) and key != "value":
            if value is True:
                attlist.append(f"{key}")
        else:
            attlist.append(f'{key}="{value}"')
    return " ".join(attlist)


class BaseElement(list):
    """The base render element
    Normally all objects used in a render tree should have this class as a base.
    Exceptions are strings and callables.

    """

    def __init__(self, *children):
        """Uses the given arguments to initialize the list which represents the child objects"""
        super().__init__(children)

    def _try_render(self, element, context):
        """Renders an element. The output will always be escaped but considers djangos safe-strings
        The following atempts will be made to render an object:
        1. If the element is a string return it escaped.
        2. If the element has an attribute 'render' call it with the context as argument and return the result.
        3. If the element is a callable call the element itself with the context as argument and return the result. The output here will not be escaped because it is assumed that a render method does its own escaping (which is true for all elements defined in this package).
        4. Convert the element to a string and return the result.
        """
        if isinstance(element, str):
            yield html.conditional_escape(element)
        elif hasattr(element, "render"):
            yield from element.render(context)
        elif callable(element):
            yield html.conditional_escape(element(context))
        else:
            yield html.conditional_escape(str(element))

    def render_children(self, context):
        """Renders all elements inside the list. Can be used by subclassing elements if they need to render wrapping code and then the child elements."""
        for element in self:
            yield from self._try_render(element, context)

    def render(self, context):
        """The base implementation whill just render all children.
        Subclassing methods can use this method to modify the element or its children and use the data from context
        """
        yield from self.render_children(context)

    def filter(self, filter_func):
        def walk(element):
            for e in element:
                if isinstance(e, BaseElement):
                    if filter_func(e):
                        yield e
                    yield from walk(e)

        return walk(self)

    def copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        children = ", ".join([i.__repr__() for i in self])
        return f"{self.__class__.__name__}({children})"


class HTMLElement(BaseElement):
    """The base for all HTML tags."""

    tag = None

    def __init__(self, *children, **attributes):
        assert self.tag is not None
        super().__init__(*children)
        self.attributes = attributes

    def render(self, context):
        yield f"<{self.tag} {flatattrs(self.attributes)}>"
        yield from super().render_children(context)
        yield f"</{self.tag}>"


class VoidElement(HTMLElement):
    """Wrapper for elements without a closing tag, cannot have children"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self, context):
        yield f"<{self.tag} {flatattrs(self.attributes)} />"


class If(BaseElement):
    def __init__(self, condition, true_child, false_child=None):
        """Condition: callable which will be evaluated to True or False. Depending on the result true_child or false_child will be rendered"""
        super().__init__()
        self.condition = condition
        self.true_child = true_child
        self.false_child = false_child

    def render(self, context):
        if self.condition(context):
            yield from self._try_render(self.true_child, context)
        elif self.false_child is not None:
            yield from self._try_render(self.false_child, context)


class Iterator(BaseElement):
    def __init__(self, iterator, variablename, *children):
        """iterator: can be a string which will be looked up in the context, a python iterator or a callable which accepts the current context as argument and returns an iterator"""
        super().__init__(*children)
        self.iterator = iterator
        self.variablename = variablename

    def render(self, context):
        c = dict(context)
        if isinstance(self.iterator, str):
            iterator = context[self.iterator]
        elif callable(self.iterator):
            iterator = self.iterator(c)
        else:
            iterator = self.iterator
        for obj in iterator:
            c[self.variablename] = obj
            yield from super().render_children(c)
