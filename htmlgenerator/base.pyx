import copy
import cython

from htmlgenerator.lazy cimport Lazy, resolve_lazy

EXCEPTION_HANDLER_NAME = "_htmlgenerator_exception_handler"
"Must be a function without arguments, will be called when an exception happens during rendering an element"

# for integration with the django safe string objects, optional
try:
    from django.utils.html import conditional_escape
except ImportError:
    from .safestring import conditional_escape


cdef class BaseElement(list):
    """The base render element
    All nodes used in a render tree should have this class as a base. Leaves in the tree may be strings or Lazy objects.
    """

    def __init__(self, *children):
        """Uses the given arguments to initialize the list which represents the child objects"""
        super().__init__(children)
        from . import DEBUG

        if DEBUG:
            import inspect

            # This will add the source location of where this element has been instantiated as a data attributte
            # and a python attribute _src_location with (filename, linenumber, functionname) to this object
            for frame in inspect.stack():
                if frame.function != "__init__":
                    break
            if hasattr(self, "attributes"):
                self.attributes[
                    "data_source_location"
                ] = f"{frame.filename}:{frame.lineno} in {frame.function}"
            self._src_location = (frame.filename, frame.lineno, frame.function)

    cdef _try_render(self, element, context, stringify):
        """Renders an element as a generator which yields strings
        The stringify parameter should normally be true in order return
        escaped strings. In some circumstances if is however desirable to
        get the actual value and not a string returned. For such cases
        stringify can be set to ``False``. An example are HTML attribute values
        which us a ``hg.If`` element and return ``True`` or ``False`` to dynamically
        control the appearance of the attribute.
        The render_children method will use a default of ``True`` for strinfigy.
        That behaviour should only be overriden by elements which consciously want
        to be able to return non-string objects during rendering.
        """
        while isinstance(element, Lazy):
            element = element.resolve(context, self)
        if isinstance(element, BaseElement):
            return element.render(context)
        elif element is not None:
            return conditional_escape(element) if stringify else element

    cdef render_children(self, context, stringify=True):
        """Renders all elements inside the list. Can be used by subclassing elements if they need to controll where child elements are rendered."""
        return "".join(self._try_render(element, context, stringify) for element in self)

    cpdef render(self, context, stringify=True):
        """Renders this element and its children. Can be overwritten by subclassing elements."""
        try:
            return self.render_children(context, stringify)
        except (Exception, RuntimeError) as e:
            import sys
            import traceback

            last_obj = None
            indent = 0
            message = []
            for i in traceback.StackSummary.extract(
                traceback.walk_tb(sys.exc_info()[2]), capture_locals=True
            ):
                if (
                    i.locals is not None
                    and "self" in i.locals
                    and i.locals["self"] != last_obj
                ):
                    message.append(" " * indent + str(i.locals["self"]))
                    last_obj = i.locals["self"]
                    indent += 2
            message.append(" " * indent + str(e))
            message = "\n".join(message)

            context.get(EXCEPTION_HANDLER_NAME, default_handler)(context, message)

            return (
                '<pre style="border: solid 1px red; color: red; padding: 1rem; background-color: #ffdddd">'
                f"    <code>~~~ Exception: {conditional_escape(e)} ~~~</code>"
                "</pre>"
                f'<script>alert("Error: {conditional_escape(e)}")</script>'
            )

    """
    Tree functions
    Tree functions can be used to modify or gathering information from the sub-tree of a BaseElement.
    Tree functions walk the tree with the calling BaseElement as root. The root is not walked itself.
    Tree functions always take an argument filter_func which has the signature (element, ancestors) => bool where ancestors is a tuple of all elements
    filter_func will determine which Child elements inside the sub-tree should be considered.
    Tree functions:
    - filter
    - wrap
    - delete
    """

    cdef filter(self, filter_func):
        """Walks through the tree (including self) and yields each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        returns: A generater which yields the matching elements
        """

        return treewalk(BaseElement(self), (), filter_func=filter_func)

    cdef wrap(
        self,
        filter_func,
        wrapperelement,
    ):
        """Walks through the tree (including self) and wraps each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        wrapper: the element which will wrap the
        """

        def wrappingfunc(container, i, e):
            wrapper = wrapperelement.copy()
            wrapper.append(container[i])
            container[i] = wrapper

        return list(
            treewalk(BaseElement(self), (), filter_func=filter_func, apply=wrappingfunc)
        )

    cdef delete(self, filter_func):
        """Walks through the tree (including self) and removes each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        """

        def delfunc(container, i, e):
            container.remove(e)

        return list(
            treewalk(BaseElement(self), (), filter_func=filter_func, apply=delfunc)
        )

    # untested code
    cdef _replace(self, select_func, replacement, all=False):
        """Replaces an element which matches a certain condition with another element"""
        from .htmltags import HTMLElement

        class ReachFirstException(Exception):
            pass

        def walk(element, ancestors):
            replacment_indices = []
            for i, e in enumerate(element):
                if isinstance(e, BaseElement):
                    if select_func(e, ancestors):
                        replacment_indices.append(i)
                    if isinstance(e, HTMLElement):
                        walk(list(e.attributes.values()), ancestors=ancestors + (e,))
                    walk(e, ancestors=ancestors + (e,))
            for i in replacment_indices:
                element.pop(i)
                if replacement is not None:
                    element.insert(i, replacement)
                if not all:
                    raise ReachFirstException()

        try:
            walk(self, (self,))
        except ReachFirstException:
            pass

    cdef copy(self):
        return copy.deepcopy(self)


cdef class If(BaseElement):

    def __init__(
        self,
        condition,
        true_child,
        false_child=None,
    ):
        """condition: Value which determines which child to render (true_child or false_child. Can also be ContextValue or ContextFunction"""
        super().__init__(true_child, false_child)
        self.condition = condition

    cpdef render(self, context, stringify=True):
        """The stringy argument can be set to False in order to get a python object
        instead of a rendered string returned. This is usefull when evaluating"""
        if resolve_lazy(self.condition, context, self):
            return self._try_render(self[0], context, stringify)
        elif len(self) > 1:
            return self._try_render(self[1], context, stringify)


cdef class Iterator(BaseElement):
    def __init__(
        self,
        iterator,
        loopvariable,
        content,
    ):
        self.iterator = iterator
        self.loopvariable = loopvariable
        super().__init__(content)

    cpdef render(self, context, stringify=True):
        context = dict(context)
        for i, value in enumerate(resolve_lazy(self.iterator, context, self)):
            context[self.loopvariable] = value
            context[self.loopvariable + "_index"] = i
            return self.render_children(context, stringify)


cdef class WithContext(BaseElement):
    """
    Pass additional names into the context.
    The additional context names are namespaced to the current element and its child elements.
    It can be helpfull for shadowing or aliasing names in the context.
    This element is required because context is otherwise only set by the render function and the loop-variable of Iterator which can be limiting.
    """

    cdef dict additional_context

    def __init__(self, *children, **kwargs):
        self.additional_context = kwargs
        super().__init__(*children)

    cpdef render(self, context, stringify=True):
        return super().render({**context, **self.additional_context})


def treewalk(element, ancestors, filter_func, apply=None):
    from .htmltags import HTMLElement

    matchelements = []

    for i, e in enumerate(list(element)):
        if isinstance(e, BaseElement):
            if filter_func is None or filter_func(e, ancestors):
                yield e
                matchelements.append((i, e))
            if isinstance(e, HTMLElement):
                yield from treewalk(
                    list(e.attributes.values()),
                    ancestors + (e,),
                    filter_func=filter_func,
                    apply=apply,
                )
            yield from treewalk(
                e, ancestors + (e,), filter_func=filter_func, apply=apply
            )

    if apply:
        for i, e in matchelements:
            apply(element, i, e)


def render(root, basecontext):
    """Shortcut to serialize an object tree into a string"""
    return root.render(basecontext)


html_id_cache = set()


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
    #         function is hard to reverse (https://en.wikipedia.org/wiki/SipHash)
    # 4. str: Because html-ids need to be strings we convert again to string
    # 5. [1:]: in order to prevent negative numbers we remove the first character which might be a "-"
    _id = prefix + "-" + str(hash(str(id(object))))[1:]
    n = 0
    nid = _id
    while nid in html_id_cache:
        nid = f"{_id}-{n}"
        n += 1
    html_id_cache.add(nid)
    return nid

cdef default_handler(context, message):
    import traceback, sys
    traceback.print_exc()
    print(message, file=sys.stderr)
