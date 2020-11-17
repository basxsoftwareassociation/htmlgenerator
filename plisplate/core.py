import collections
import copy
from collections.abc import Iterable

from django.utils import html


def render(root, basecontext):
    """ Shortcut to serialize an object tree into a string"""
    return html.mark_safe("".join(root.render(basecontext)))


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
        if isinstance(element, Lazy):
            element = element.resolve(self, context)
        if hasattr(element, "render"):
            yield from element.render(context)
        elif callable(element):
            yield html.conditional_escape(element(context) or "")
        elif element is not None:
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
        """Walks through the tree (self not including) and yields each element for which a call to filter_func evaluates to True.
        filter_func expects the element and a tuple of all ancestors as arguments.
        """

        def walk(element, ancestors):
            for e in element:
                if isinstance(e, BaseElement):
                    if filter_func(e, ancestors):
                        yield e
                    yield from walk(e, ancestors=ancestors + (e,))

        return walk(self, (self,))

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


# TODO: check whether we should use the lazy-evaluation systme of django here.
class Lazy:
    """Lazy values will be evaluated at render time. Elements which need to get values a render time need to """

    pass


def resolve_lazy(value, element, context):
    return value.resolve(element, context) if isinstance(value, Lazy) else value


class ContextValue(Lazy):
    def __init__(self, value):
        assert isinstance(
            value, collections.Hashable
        ), "ContextValue needs to be hashable"
        self.value = value

    def resolve(self, element, context):
        if isinstance(self.value, str):
            # TODO: Test
            for accessor in self.value.split("."):
                if hasattr(context, accessor):
                    context = getattr(context, accessor)
                else:
                    context = context.get(accessor)
            return context
        return context[self.value]


class ContextFunction(Lazy):
    def __init__(self, func):
        assert callable(func), "ContextFunction needs to be callable"
        self.func = func

    def resolve(self, element, context):
        return self.func(element, context)


class ElementAttribute(Lazy):
    """Get an attribute from an element, usefull for consumers of ValueProvider"""

    def __init__(self, attribname):
        self.attribname = attribname

    def resolve(self, element, context):
        return getattr(element, self.attribname)


# shortcuts
C = ContextValue
ATR = ElementAttribute
F = ContextFunction


class ValueProvider(BaseElement):
    """Helper class to provide explicit defined values to "marked" child elements
    The object-generating element needs to subclass this class. Any "direct" child
    element which inherits from the "Binding"-class will have an attribute
    (defined by attributename) set with the according value.
    ("direct" means any level deeper but no nested Object Provider)
    """

    attributename = "value"
    "The name through which bound children will be able to access the value, should be changed when subclassed"
    _ConsumerBase = type("ValueConsumer", (), {})

    def __init__(self, value, *children):
        """
        value: value which will be passed to all Consumer children at render time, can be Lazy
        """
        assert self.attributename is not None
        super().__init__(*children)
        self.value = value

    @classmethod
    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls._ConsumerBase = type(f"{cls.__name__}Consumer", (), {})

    @classmethod
    def Binding(cls, base=BaseElement):
        """Bind an class to this ValueProvider class. All bound instances which are a an decendant of an instance of this class will have the according attribute set
        before the render function is called."""
        return type(f"{cls.__name__}Consumer", (base, cls._ConsumerBase), {})

    def _consumerelements(self):
        return self.filter(
            lambda elem, ancestors: isinstance(elem, self._ConsumerBase)
            and not any(
                (isinstance(ancestor, type(self)) for ancestor in ancestors[1:])
            )
        )

    def render(self, context):
        for element in self._consumerelements():
            setattr(
                element, self.attributename, resolve_lazy(self.value, element, context)
            )
        return super().render(context)


class If(BaseElement):
    def __init__(self, condition, true_child, false_child=None):
        """condition: Value which determines which child to render (true_child or false_child. Can also be ContextValue or ContextFunction"""
        super().__init__()
        self.condition = condition
        self.true_child = true_child
        self.false_child = false_child

    def render(self, context):
        if resolve_lazy(self.condition, self, context):
            yield from self._try_render(self.true_child, context)
        elif self.false_child is not None:
            yield from self._try_render(self.false_child, context)


class IteratorValueProvider(ValueProvider):
    attributename = "loopindex"


class Iterator(BaseElement):
    def __init__(self, iterator, valueproviderclass, *children):
        """iterator: callable or context variable which returns an iterator
        valueproviderclass: A class which inherits from valueprovider in order to set the iterator value on child elements when rendering"""
        assert isinstance(iterator, (Iterable, Lazy)) and not isinstance(
            iterator, str
        ), "iterator argument needs to be iterable or a Lazy object"
        super().__init__(*children)
        self.iterator = iterator
        self.valueprovider = IteratorValueProvider(
            None, valueproviderclass(None, *children)
        )

    def render(self, context):
        for i, obj in enumerate(resolve_lazy(self.iterator, self, context)):
            self.valueprovider.value = i
            self.valueprovider[0].value = obj
            yield from self.valueprovider.render(context)
