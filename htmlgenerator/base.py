from __future__ import annotations

import copy
import inspect
import typing

from .lazy import Lazy, resolve_lazy

"Turning on this flag will add html attributes with information about the source of the generated html output"

# for integration with the django safe string objects, optional
try:
    from django.utils.html import conditional_escape  # type: ignore
except ImportError:
    from .safestring import conditional_escape


class BaseElement(list):
    """The base render element
    All nodes used in a render tree should have this class as a base. Leaves in the tree may be strings or Lazy objects.
    """

    def __init__(self, *children):
        """Uses the given arguments to initialize the list which represents the child objects"""
        super().__init__(children)
        from . import __DEBUG__

        if __DEBUG__:
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

    def _try_render(
        self, element: typing.Any, context: dict
    ) -> typing.Generator[str, None, None]:
        """Renders an element as a generator which yields strings"""
        while isinstance(element, Lazy):
            element = element.resolve(context, self)
        if isinstance(element, BaseElement):
            yield from element.render(context)
        elif element is not None:
            yield conditional_escape(element)

    def render_children(self, context: dict) -> typing.Generator[str, None, None]:
        """Renders all elements inside the list. Can be used by subclassing elements if they need to controll where child elements are rendered."""
        for element in self:
            yield from self._try_render(element, context)

    def render(self, context: dict) -> typing.Generator[str, None, None]:
        """Renders this element and its children. Can be overwritten by subclassing elements."""
        try:
            yield from self.render_children(context)
        except (Exception, RuntimeError) as e:
            import traceback

            traceback.print_exc()
            raise RenderException(self, e)

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

    def filter(
        self,
        filter_func: typing.Callable[
            [BaseElement, typing.Tuple[BaseElement, ...]], bool
        ],
    ) -> typing.Generator[BaseElement, None, None]:
        """Walks through the tree (including self) and yields each element for which a call to filter_func evaluates to True.
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

    def delete(
        self,
        filter_func: typing.Callable[
            [BaseElement, typing.Tuple[BaseElement, ...]], bool
        ],
    ) -> list[BaseElement]:
        """Walks through the tree (including self) and removes each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        """

        def delfunc(container, i, e):
            container.remove(e)

        return list(
            treewalk(BaseElement(self), (), filter_func=filter_func, apply=delfunc)
        )

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


class If(BaseElement):
    def __init__(
        self,
        condition: typing.Union[bool, Lazy],
        true_child: BaseElement,
        false_child: typing.Optional[BaseElement] = None,
    ):
        """condition: Value which determines which child to render (true_child or false_child. Can also be ContextValue or ContextFunction"""
        super().__init__(true_child, false_child)
        self.condition = condition

    def render(self, context: dict):
        if resolve_lazy(self.condition, context, self):
            yield from self._try_render(self[0], context)
        elif len(self) > 1:
            yield from self._try_render(self[1], context)


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

    def render(self, context: dict):
        context = dict(context)
        for i, value in enumerate(resolve_lazy(self.iterator, context, self)):
            context[self.loopvariable] = value
            context[self.loopvariable + "_index"] = i
            yield from self.render_children(context)


class WithContext(BaseElement):
    """
    Pass additional names into the context.
    The additional context names are namespaced to the current element and its child elements.
    It can be helpfull for shadowing or aliasing names in the context.
    This element is required because context is otherwise only set by the render function and the loop-variable of Iterator which can be limiting.
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


class RenderException(Exception):
    def __init__(self, elementtype: BaseElement, origin: BaseException):
        self.trace: typing.Tuple[typing.Any, ...] = (
            elementtype,
            origin,
        )
        if isinstance(origin, RenderException):
            self.trace = (elementtype,) + origin.trace

    def __str__(self) -> str:
        ret = []
        for i, traceitem in enumerate(self.trace):
            ret.append("    " * i + f"{traceitem}")
        return "\n".join(ret)


def print_logical_tree(root: BaseElement) -> None:
    from .htmltags import HTMLElement

    def print_node(node: BaseElement, level: int) -> None:
        attrlist = [
            f"{attr}: {getattr(node, attr)}"
            for attr in dir(node)
            if not attr.startswith("_")
            and not callable(getattr(node, attr))
            and attr not in ("attributes", "tag")
        ]
        attrs = ", ".join(attrlist)
        name = type(node).__name__
        if name == "__proxy__":
            name = "str"
        neednewlevel = False
        if isinstance(node, str):
            print(level * "    " + f'"{node}"')
            neednewlevel = True
        elif HTMLElement not in type(node).__bases__:
            print(level * "    " + f"{name}({attrs})")
            neednewlevel = True
        if isinstance(node, BaseElement):
            for child in node:
                if child is not None:
                    print_node(child, level + (1 if neednewlevel else 0))

    print_node(root, level=0)


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
    # 5. [1:]: in order to prevent negative numbers we remove the first character which might be a "-"
    _id = prefix + "-" + str(hash(str(id(object))))[1:]
    n = 0
    nid = _id
    while nid in html_id_cache:
        nid = f"{_id}-{n}"
        n += 1
    html_id_cache.add(nid)
    return nid
