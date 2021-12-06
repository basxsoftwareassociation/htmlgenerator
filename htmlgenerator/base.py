from __future__ import annotations

import copy
import inspect
import string
import typing

from .lazy import Lazy, resolve_lazy

EXCEPTION_HANDLER_NAME = "_htmlgenerator_exception_handler"
"Must be a function without arguments, will be called when an "
"exception happens during rendering an element"

# for integration with the django safe string objects, optional
try:
    from django.utils.html import conditional_escape, mark_safe  # type: ignore
except ImportError:
    from .safestring import conditional_escape, mark_safe


class BaseElement(list):
    """The base render element
    All nodes used in a render tree should have this class as a base.
    Leaves in the tree may be strings or Lazy objects.
    """

    def __init__(self, *children):
        """
        Uses the given arguments to initialize the list which
        represents the child objects
        """
        super().__init__(children)
        from . import DEBUG

        if DEBUG:
            # This will add the source location of where this element has
            # been instantiated as a data attributte and a python attribute
            # _src_location with (filename, linenumber, functionname) to this object
            for frame in inspect.stack():
                if frame.function != "__init__":
                    break
            if hasattr(self, "attributes"):
                self.attributes[
                    "data_source_location"
                ] = f"{frame.filename}:{frame.lineno} in {frame.function}"
            self._src_location = (frame.filename, frame.lineno, frame.function)

    def _try_render(
        self, element: typing.Any, context: dict, stringify: bool
    ) -> typing.Generator[str, None, None]:
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
        try:
            while isinstance(element, Lazy):
                element = element.resolve(context)
            if isinstance(element, BaseElement):
                yield from element.render(context)
            elif element is not None:
                yield conditional_escape(element) if stringify else element
        except (Exception, RuntimeError) as e:
            yield from _handle_exception(e, context)

    def render_children(
        self, context: dict, stringify: bool = True
    ) -> typing.Generator[str, None, None]:
        """
        Renders all elements inside the list.
        Can be used by subclassing elements if they need to controll
        where child elements are rendered.
        """
        for element in self:
            yield from self._try_render(element, context, stringify)

    def render(
        self, context: dict, stringify: bool = True
    ) -> typing.Generator[str, None, None]:
        """
        Renders this element and its children.
        Can be overwritten by subclassing elements.
        """
        yield from self.render_children(context, stringify)

    """
    Tree functions
    Tree functions can be used to modify or gathering information from
    the sub-tree of a BaseElement.
    Tree functions walk the tree with the calling BaseElement as root.
    The root is not walked itself.
    Tree functions always take an argument filter_func which has the
    signature (element, ancestors) => bool where ancestors is a tuple of all elements
    filter_func will determine which Child elements inside the sub-tree should be
    considered.
    Tree functions:
    - filter
    - wrap
    - delete
    """

    def filter(
        self,
        filter_func: typing.Callable[
            [BaseElement, typing.Tuple[BaseElement, ...]], bool
        ],
    ) -> typing.Generator[BaseElement, None, None]:
        """
        Walks through the tree (including self) and yields each
        element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        returns: A generater which yields the matching elements
        """

        return treewalk(BaseElement(self), (), filter_func=filter_func)

    def wrap(
        self,
        filter_func: typing.Callable[
            [BaseElement, typing.Tuple[BaseElement, ...]], bool
        ],
        wrapperelement: BaseElement,
    ) -> list[BaseElement]:
        """
        Walks through the tree (including self) and wraps each element
        for which a call to filter_func evaluates to True.
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

    def delete(
        self,
        filter_func: typing.Callable[
            [BaseElement, typing.Tuple[BaseElement, ...]], bool
        ],
    ) -> list[BaseElement]:
        """
        Walks through the tree (including self) and removes each element
        for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        """

        def delfunc(container, i, e):
            container.remove(e)

        return list(
            treewalk(BaseElement(self), (), filter_func=filter_func, apply=delfunc)
        )

    def replace(self, *args, **kwargs):
        return self._replace(*args, **kwargs)

    # untested code
    def _replace(
        self, select_func: typing.Callable, replacement: BaseElement, all: bool = False
    ):
        """Replaces an element which matches a certain condition with another element"""
        from .htmltags import HTMLElement

        class ReachFirstException(Exception):
            pass

        def walk(element: typing.List, ancestors: typing.Tuple[BaseElement, ...]):
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

    def copy(self) -> BaseElement:
        return copy.deepcopy(self)


class If(BaseElement):
    def __init__(
        self,
        condition: typing.Union[bool, Lazy],
        true_child: typing.Any,
        false_child: typing.Any = None,
    ):
        """
        condition: Value which determines which child to render
                   (true_child or false_child. Can also be ContextValue or
                   ContextFunction
        """
        super().__init__(true_child, false_child)
        self.condition = condition

    def render(self, context: dict, stringify=True):
        """The stringy argument can be set to False in order to get a python object
        instead of a rendered string returned. This is usefull when evaluating"""
        if resolve_lazy(self.condition, context):
            yield from self._try_render(self[0], context, stringify)
        elif len(self) > 1:
            yield from self._try_render(self[1], context, stringify)


class Iterator(BaseElement):
    def __init__(
        self,
        iterator: typing.Union[typing.Iterable, Lazy],
        loopvariable: str,
        content: BaseElement,
    ):
        self.iterator = iterator
        self.loopvariable = loopvariable
        super().__init__(content)

    def render(self, context: dict, stringify: bool = True):
        context = dict(context)
        for i, value in enumerate(resolve_lazy(self.iterator, context)):
            context[self.loopvariable] = value
            context[self.loopvariable + "_index"] = i
            yield from self.render_children(context, stringify)


class WithContext(BaseElement):
    """
    Pass additional names into the context.
    The additional context names are namespaced to the current element
    and its child elements.
    It can be helpfull for shadowing or aliasing names in the context.
    This element is required because context is otherwise only set by the
    render function and the loop-variable of Iterator which can be limiting.
    """

    additional_context: dict = {}

    def __init__(self, *children, **kwargs):
        self.additional_context = kwargs
        super().__init__(*children)

    def render(self, context):
        return super().render({**context, **self.additional_context})


def treewalk(
    element: typing.List,
    ancestors: typing.Tuple[BaseElement, ...],
    filter_func: typing.Optional[
        typing.Callable[[BaseElement, typing.Tuple[BaseElement, ...]], bool]
    ],
    apply: typing.Optional[
        typing.Callable[[BaseElement, int, BaseElement], None]
    ] = None,
) -> typing.Generator[BaseElement, None, None]:
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


def render(root: BaseElement, basecontext: dict) -> str:
    """Shortcut to serialize an object tree into a string"""
    return "".join(root.render(basecontext))


html_id_cache = set()


def html_id(object: typing.Any, prefix: str = "id") -> str:
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
    # 5. [1:]: in order to prevent negative numbers we remove the first character which
    #          might be a "-"
    _id = prefix + "-" + str(hash(str(id(object))))[1:]
    n = 0
    nid = _id
    while nid in html_id_cache:
        nid = f"{_id}-{n}"
        n += 1
    html_id_cache.add(nid)
    return nid


class ContextFormatter(string.Formatter):
    context: dict

    def __init__(self, context: dict):
        super().__init__()
        self.context = context

    def format(self, format_string, *args, **kwargs):
        return mark_safe(super().format(format_string, *args, **kwargs))

    def parse(self, format_string):
        for literal_text, field_name, format_spec, conversion in super().parse(
            format_string
        ):
            yield conditional_escape(literal_text), field_name, format_spec, conversion

    def get_value(self, key, args, kwds):
        return conditional_escape(
            super().get_value(
                key,
                [resolve_lazy(arg, self.context) for arg in args],
                {k: resolve_lazy(v) for k, v in kwds.items()},
            )
        )


class FormatString(BaseElement):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        yield from self._try_render(
            ContextFormatter(context).format(*self.args, **self.kwargs),
            context,
            stringify=True,
        )


def format(*args, **kwargs):
    return FormatString(*args, **kwargs)


def _handle_exception(exception, context):
    import sys
    import traceback

    def default_handler(context, message):
        traceback.print_exc()
        print(message, file=sys.stderr)

    last_obj = None
    indent = 0
    message = []
    # extract can fail in some circumstances, therefore try first
    try:
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
    except Exception as e:
        message.append(str(e))
    message.append(" " * indent + str(exception))
    message = "\n".join(message)

    context.get(EXCEPTION_HANDLER_NAME, default_handler)(context, message)

    yield (
        '<pre style="border: solid 1px red; color: red; padding: 1rem; '
        'background-color: #ffdddd">'
        f"    <code>~~~ Exception: {conditional_escape(exception)} ~~~</code>"
        "</pre>"
        f'<script>alert("Error: {conditional_escape(exception)}")</script>'
    )
