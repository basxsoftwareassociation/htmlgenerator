import copy
import html
from collections.abc import Iterable

from .lazy import Lazy, resolve_lazy

# for integration with the django safe string objects, optional
try:
    from django.utils.html import mark_safe
except ImportError:
    from .safestring import mark_safe


def render(root, basecontext):
    """ Shortcut to serialize an object tree into a string"""
    return "".join(root.render(basecontext))


class BaseElement(list):
    """The base render element
    All nodes used in a render tree should have this class as a base. Leaves in the tree may be strings or Lazy objects.
    """

    def __init__(self, *children):
        """Uses the given arguments to initialize the list which represents the child objects"""
        super().__init__(children)

    def _try_render(self, element, context):
        """Renders an element as a generator which yields strings"""
        while isinstance(element, Lazy):
            element = element.resolve(self, context)
        if hasattr(element, "render"):
            yield from element.render(context)
        elif element is not None:
            yield conditional_escape(element)

    def render_children(self, context):
        """Renders all elements inside the list. Can be used by subclassing elements if they need to controll where child elements are rendered."""
        for element in self:
            yield from self._try_render(element, context)

    def render(self, context):
        """Renders this element and its children. Can be overwritten by subclassing elements."""
        yield from self.render_children(context)

    def filter(self, filter_func):
        """Walks through the tree (self not including) and yields each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
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
        attrs = ", ".join(
            [
                i
                for i in dir(self)
                if not callable(getattr(self, i)) and not i.startswith("__")
            ]
        )
        children = ", ".join([i.__repr__() for i in self])
        return (
            f"{self.__class__.__name__}("
            + ", ".join([i for i in (attrs, children) if i])
            + ")"
        )


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
        assert type(base) == type
        return type(f"{cls.__name__}Consumer", (base, cls._ConsumerBase), {})

    def _consumerelements(self):
        return self.filter(
            lambda elem, ancestors: isinstance(elem, self._ConsumerBase)
            and not any(
                (isinstance(ancestor, type(self)) for ancestor in ancestors[1:])
            )
        )

    def render(self, context):
        value = resolve_lazy(self.value, self, context)
        for element in self._consumerelements():
            setattr(element, self.attributename, value)
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


class Iterator(BaseElement):
    class IteratorValueProvider(ValueProvider):
        attributename = "loopindex"

    def __init__(self, iterator, content, valueproviderclass=ValueProvider):
        """iterator: callable or context variable which returns an iterator
        content: content of the loop
        valueproviderclass: A class which inherits from valueprovider in order to set the iterator value on child elements when rendering"""
        assert isinstance(iterator, (Iterable, Lazy)) and not isinstance(
            iterator, str
        ), "iterator argument needs to be iterable or a Lazy object"
        super().__init__(content)
        self.iterator = iterator
        self.valueprovider = Iterator.IteratorValueProvider(
            None, valueproviderclass(None, content)
        )

    def render(self, context):
        for i, obj in enumerate(resolve_lazy(self.iterator, self, context)):
            self.valueprovider.value = i
            self.valueprovider[0].value = obj
            yield from self.valueprovider.render(context)


def conditional_escape(value):
    if hasattr(value, "__html__"):
        return value.__html__()
    else:
        return mark_safe(html.escape(str(value)))
