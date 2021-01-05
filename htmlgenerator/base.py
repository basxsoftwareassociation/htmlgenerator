import copy
from collections.abc import Iterable

from .lazy import Lazy, resolve_lazy

# for integration with the django safe string objects, optional
try:
    from django.utils.html import conditional_escape
except ImportError:
    from .safestring import conditional_escape


class RenderException(Exception):
    def __init__(self, elementtype, origin):
        self.trace = (elementtype, origin)
        if isinstance(origin, RenderException):
            self.trace = (elementtype,) + origin.trace

    def __str__(self):
        ret = []
        for i, traceitem in enumerate(self.trace):
            ret.append("    " * i + f"{traceitem}")
        return "\n".join(ret)


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
            element = element.resolve(context, self)
        if isinstance(element, BaseElement):
            yield from element.render(context)
        elif element is not None:
            yield conditional_escape(element)

    def render_children(self, context):
        """Renders all elements inside the list. Can be used by subclassing elements if they need to controll where child elements are rendered."""
        for element in self:
            yield from self._try_render(element, context)

    def render(self, context):
        """Renders this element and its children. Can be overwritten by subclassing elements."""
        try:
            yield from self.render_children(context)
        except (Exception, RuntimeError) as e:
            raise RenderException(self, e)

    def filter(self, filter_func):
        """Walks through the tree (self not including) and yields each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        """

        def walk(element, ancestors):
            for e in element:
                if isinstance(e, BaseElement):
                    if filter_func(e, ancestors):
                        yield e
                    if hasattr(e, "attributes"):
                        yield from walk(
                            e.attributes.values(), ancestors=ancestors + (e,)
                        )
                    yield from walk(e, ancestors=ancestors + (e,))

        return walk(self, (self,))

    # TODO: test this function
    def replace(self, select_func, replacement, only_first_match=True):
        """Replaces an element which matches a certain condition with another element"""
        first_done = False

        def walk(element, ancestors):
            global first_done
            if only_first_match and first_done:
                return
            replacment_indices = []
            for e, i in enumerate(element):
                if isinstance(e, BaseElement):
                    if select_func(e, ancestors):
                        replacment_indices.append(i)
                    if hasattr(e, "attributes"):
                        walk(e.attributes.values(), ancestors=ancestors + (e,))
                    walk(e, ancestors=ancestors + (e,))
            for i in replacment_indices:
                if only_first_match and first_done:
                    break
                first_done = True
                element.pop(i)
                element.insert(i, replacement)

        return walk(self, (self,))

    def copy(self):
        return copy.deepcopy(self)

    def __repr__(self):
        try:
            attrs = ", ".join(
                [
                    f"{i}: {getattr(self, i)}"
                    for i in dir(self)
                    if not callable(getattr(self, i)) and not i.startswith("__")
                ]
            )
            return (
                f"{self.__class__.__name__}("
                + ", ".join([i for i in (attrs, f"{len(self)} children") if i])
                + ")"
            )
        except (Exception, RuntimeError):
            # sometimes our nice serialization fails and we reverte to the dead-safe method of just printing the type of the object
            return str(type(self))


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

    def _consumerfilter(self, element, ancestors):
        # Design decision: Should values be provided to consumers of any depth?
        # Problem: if yes, nested ValueProviders of the same type will be messed up
        # Problem: if no, children always need to explicitly know their ValueProvider class
        # Decision: will go with answer "no" for now
        return isinstance(element, self._ConsumerBase) and not any(
            (isinstance(ancestor, type(self)) for ancestor in ancestors[1:])
        )

    def render(self, context):
        value = resolve_lazy(self.value, context, self)
        for element in self.filter(self._consumerfilter):
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
        if resolve_lazy(self.condition, context, self):
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
        for i, obj in enumerate(resolve_lazy(self.iterator, context, self)):
            self.valueprovider.value = i
            self.valueprovider[0].value = obj
            yield from self.valueprovider.render(context)


def html_id(object, prefix="id"):
    """Generate a unique HTML id from an object"""
    # Explanation of the chained call:
    # 1. id: We want a guaranteed unique ID. Since the lifespan of an HTML-response is
    #       shorted than that of the working process, this should be fine. Python
    #       might re-use objects and their according memory, but it seems unlikely
    #       that this will be an issue.
    # 2. str: passing an int (from the id function) into the hash-function will result
    #        in the int beeing passed back. We need to convert the id to a string in
    #        order have the hash function doing some actual hashing.
    # 3. hash: Prevent the leaking of any memory layout information. The python hash
    #         function is very hard to reverse (https://en.wikipedia.org/wiki/SipHash)
    # 4. str: Because html-ids are strings we convert again to string
    # 5. [1:]: in case there is a leading "-" we remove the first character
    return prefix + "-" + str(hash(str(id(object))))[1:]
