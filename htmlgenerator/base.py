import copy

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


def print_logical_tree(root):
    from .htmltags import HTMLElement

    def print_node(node, level):
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

    def filter(self, filter_func):
        """Walks through the tree (self not including) and yields each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        returns: A generater which yields the matching elements
        """

        return treewalk(self, (self,), filter_func=filter_func)

    def wrap(self, filter_func, wrapperelement):
        """Walks through the tree (self not including) and wraps each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        wrapper: the element which will wrap the
        """

        def wrappingfunc(container, i, e):
            wrapper = wrapperelement.copy()
            wrapper.append(container[i])
            container[i] = wrapper

        return list(
            treewalk(self, (self,), filter_func=filter_func, apply=wrappingfunc)
        )

    def delete(self, filter_func):
        """Walks through the tree (self not including) and removes each element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        """

        def delfunc(container, i, e):
            container.remove(e)

        return list(treewalk(self, (self,), filter_func=filter_func, apply=delfunc))

    # TODO: test this function
    def _replace(self, select_func, replacement, all=False):
        """Replaces an element which matches a certain condition with another element"""

        class ReachFirstException(Exception):
            pass

        def walk(element, ancestors):
            replacment_indices = []
            for i, e in enumerate(element):
                if isinstance(e, BaseElement):
                    if select_func(e, ancestors):
                        replacment_indices.append(i)
                    if hasattr(e, "attributes"):
                        walk(e.attributes.values(), ancestors=ancestors + (e,))
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


class If(BaseElement):
    def __init__(self, condition, true_child, false_child=None):
        """condition: Value which determines which child to render (true_child or false_child. Can also be ContextValue or ContextFunction"""
        super().__init__(true_child, false_child)
        self.condition = condition

    def render(self, context):
        if resolve_lazy(self.condition, context, self):
            yield from self._try_render(self[0], context)
        else:
            yield from self._try_render(self[1], context)


class Iterator(BaseElement):
    def __init__(self, iterator, loopvariable, content):
        self.iterator = iterator
        self.loopvariable = loopvariable
        super().__init__(content)

    def render(self, context):
        context = dict(context)
        for i, value in enumerate(resolve_lazy(self.iterator, context, self)):
            context[self.loopvariable] = value
            context[self.loopvariable + "_index"] = i
            yield from self.render_children(context)


def treewalk(
    element,
    ancestors,
    filter_func=None,
    apply=None,
):
    matchelements = []

    for i, e in enumerate(list(element)):
        if isinstance(e, BaseElement):
            if filter_func is None or filter_func(e, ancestors):
                yield e
                matchelements.append((i, e))
            if hasattr(e, "attributes"):
                yield from treewalk(
                    e.attributes.values(),
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
    while nid in html_id.cache:
        nid = f"{_id}-{n}"
        n += 1
    html_id.cache.add(nid)
    return nid


html_id.cache = set()
