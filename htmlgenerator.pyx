import copy
import html
import inspect
import string
import sys
import traceback

# copied from django/utils/safestring.py in order to avoid a dependency
# only for the escaping-functionality
# this is condensed and doc-strings are removed, please read
# https://github.com/django/django/blob/master/django/utils/safestring.py
# for proper documentation

__version__ = "1.1.10"


cdef class SafeString(str):
    def __add__(self, rhs):
        t = super(SafeString, self).__add__(rhs)
        if isinstance(rhs, SafeString):
            return SafeString(t)
        return t

    def __html__(self):
        return self

    def __str__(self):
        return self


def mark_safe(s):
    if hasattr(
        s, "__html__"
    ):  # instead of using isinstance we use __html__ because that
        # is what some other frameworks use too
        return s
    return SafeString(s)


cdef class Lazy:
    """Lazy values will be evaluated at render time via the resolve method."""

    cpdef object resolve(self, dict context):
        raise NotImplementedError("Lazy needs to be subclassed")


cdef class ContextValue(Lazy):
    cdef readonly object value

    def __init__(self, value):
        self.value = value

    cpdef object resolve(self, dict context):
        if isinstance(self.value, str):
            return resolve_lookup(context, self.value)
        return self.value


cdef class ContextFunction(Lazy):
    """Call a function a render time, usefull for calculation of more complex"""

    cdef object func

    def __init__(self, func):
        assert callable(func), "ContextFunction needs to be callable"
        self.func = func

    cpdef object resolve(self, dict context):
        return self.func(context)


C = ContextValue
F = ContextFunction

cdef class BaseElement(list):
    """The base render element
    All nodes used in a render tree should have this class as a base.
    Leaves in the tree may be strings or Lazy objects.
    """

    def __init__(self, *children):
        """
        Uses the given arguments to initialize the list which
        represents the child objects
        """
        super(BaseElement, self).__init__(children)

    cdef str _try_render(self, element, dict context):
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
                return str(element.render(context))
            elif element is not None:
                if hasattr(element, "__html__"):
                    return str(element.__html__())
                else:
                    return html.escape(str(element))
            return ""
        except (Exception, RuntimeError) as e:
            return _handle_exception(e, context)

    cpdef str render_children(self, dict context):
        """
        Renders all elements inside the list.
        Can be used by subclassing elements if they need to controll
        where child elements are rendered.
        """
        return "".join([self._try_render(element, context) for element in self])

    cpdef str render(self, dict context):
        """
        Renders this element and its children.
        Can be overwritten by subclassing elements.
        """
        return self.render_children(context)

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

    def filter(self, filter_func):
        """
        Walks through the tree (including self) and yields each
        element for which a call to filter_func evaluates to True.
        filter_func expects an element and a tuple of all ancestors as arguments.
        returns: A generater which yields the matching elements
        """

        return treewalk(BaseElement(self), (), filter_func=filter_func)

    def wrap(self, filter_func, wrapperelement):
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

    def delete(self, filter_func):
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

    def copy(self):
        return copy.deepcopy(self)


cdef class If(BaseElement):
    cdef object condition

    def __init__(self, object condition, object true_child, object false_child=None):
        """
        condition: Value which determines which child to render
                   (true_child or false_child. Can also be ContextValue or
                   ContextFunction
        """
        super(If, self).__init__(true_child, false_child)
        self.condition = condition

    cpdef str render(self, dict context):
        """The stringy argument can be set to False in order to get a python object
        instead of a rendered string returned. This is usefull when evaluating"""
        if resolve_lazy(self.condition, context):
            return self._try_render(self[0], context)
        elif len(self) > 1:
            return self._try_render(self[1], context)
        return ""


cdef class Iterator(BaseElement):
    cdef readonly object iterator
    cdef readonly str loopvariable

    def __init__(self, object iterator, str loopvariable, object content):
        self.iterator = iterator
        self.loopvariable = loopvariable
        super(Iterator, self).__init__(content)

    cpdef str render(self, dict context):
        context = dict(context)
        ret = []
        for i, value in enumerate(resolve_lazy(self.iterator, context)):
            context[self.loopvariable] = value
            context[self.loopvariable + "_index"] = i
            ret.append(self.render_children(context))
        return "".join(ret)


cdef class WithContext(BaseElement):
    """
    Pass additional names into the context.
    The additional context names are namespaced to the current element
    and its child elements.
    It can be helpfull for shadowing or aliasing names in the context.
    This element is required because context is otherwise only set by the
    render function and the loop-variable of Iterator which can be limiting.
    """

    cdef dict additional_context

    def __init__(self, *children, **kwargs):
        self.additional_context = kwargs
        super(WithContext, self).__init__(*children)

    cpdef str render(self, dict context):
        return super(WithContext, self).render({**context, **self.additional_context})


def treewalk(element, ancestors, filter_func, apply=None):
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




html_id_cache = set()


cpdef str html_id(object object, str prefix="id"):
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
    def __init__(self, context):
        super(ContextFormatter, self).__init__()
        self.context = context

    def get_value(self, key, args, kwds):
        return render(BaseElement(super(ContextFormatter, self).get_value(key, args, kwds)), self.context)


cdef class FormatString(BaseElement):
    cdef tuple args
    cdef dict kwargs

    def __init__(self, *args, **kwargs):
        super(FormatString, self).__init__()
        self.args = args
        self.kwargs = kwargs

    cpdef str render(self, dict context):
        return ContextFormatter(context).format(*self.args, **self.kwargs)


def format(*args, **kwargs):
    return FormatString(*args, **kwargs)


def _handle_exception(exception, context):
    def default_handler(context, message):
        traceback.print_exc()
        print(message, file=sys.stderr)

    last_obj = None
    indent = 0
    message = []
    for i in traceback.StackSummary.extract(
        traceback.walk_tb(sys.exc_info()[2]), capture_locals=True
    ):
        if i.locals is not None and "self" in i.locals and i.locals["self"] != last_obj:
            message.append(" " * indent + str(i.locals["self"]))
            last_obj = i.locals["self"]
            indent += 2
    message.append(" " * indent + str(exception))
    message = "\n".join(message)

    default_handler(context, message)

    return (
        '<pre style="border: solid 1px red; color: red; padding: 1rem; '
        'background-color: #ffdddd">'
        f"    <code>~~~ Exception: {html.escape(str(exception))} ~~~</code>"
        "</pre>"
        f'<script>alert("Error: {html.escape(str(exception))}")</script>'
    )


cdef class HTMLElement(BaseElement):
    """The base for all HTML tags."""

    cdef readonly str tag
    cdef readonly dict attributes
    cdef object lazy_attributes

    def __init__(
        self, *children, lazy_attributes=None, **attributes
    ):
        self.attributes = attributes
        super(HTMLElement, self).__init__(*children)
        self.lazy_attributes = lazy_attributes

    cpdef str render(self, dict context):
        attr_str = flatattrs(
            {
                **self.attributes,
                **(resolve_lazy(self.lazy_attributes, context) or {}),
            },
            context,
        )
        # quirk to prevent tags having a single space if there are no attributes
        attr_str = (" " + attr_str) if attr_str else attr_str
        return f"<{self.tag}{attr_str}>" + super(HTMLElement, self).render_children(context) + f"</{self.tag}>"

    # mostly for debugging purposes
    def __repr__(self):
        return (
            f"<{self.tag} "
            + " ".join(f"{k.lstrip('_')}=\"{v}\"" for k, v in self.attributes.items())
            + f"> ({self.__class__})"
        )


cdef class VoidElement(HTMLElement):
    """Wrapper for elements without a closing tag, cannot have children"""

    # does not accept children
    def __init__(self, **kwargs):
        super(VoidElement, self).__init__(**kwargs)

    cpdef str render(self, dict context):
        return f"<{self.tag} {flatattrs(self.attributes, context)} />"


cdef class A(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "a"

    def __init__(self, *args, newtab=False, **kwargs):
        if newtab:
            kwargs["target"] = "_blank"
            kwargs["rel"] = "noopener noreferrer"
        super(A, self).__init__(*args, **kwargs)


cdef class ABBR(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "abbr"


cdef class ACRONYM(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "acronym"


cdef class ADDRESS(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "address"


cdef class APPLET(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "applet"


cdef class AREA(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "area"


cdef class ARTICLE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "article"


cdef class ASIDE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "aside"


cdef class AUDIO(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "audio"


cdef class B(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "b"


cdef class BASE(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "base"


cdef class BASEFONT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "basefont"


cdef class BDI(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "bdi"


cdef class BDO(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "bdo"


cdef class BGSOUND(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "bgsound"


cdef class BIG(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "big"


cdef class BLINK(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "blink"


cdef class BLOCKQUOTE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "blockquote"


cdef class BODY(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "body"


cdef class BR(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "br"


cdef class BUTTON(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "button"


cdef class CANVAS(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "canvas"


cdef class CAPTION(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "caption"


cdef class CENTER(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "center"


cdef class CITE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "cite"


cdef class CODE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "code"


cdef class COL(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "col"


cdef class COLGROUP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "colgroup"


cdef class COMMAND(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "command"


cdef class CONTENT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "content"


cdef class DATA(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "data"


cdef class DATALIST(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "datalist"


cdef class DD(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "dd"


cdef class DEL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "del"


cdef class DETAILS(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "details"


cdef class DFN(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "dfn"


cdef class DIALOG(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "dialog"


cdef class DIR(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "dir"


cdef class DIV(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "div"


cdef class DL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "dl"


cdef class DT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "dt"


cdef class EDIASTREA(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "ediastrea"


cdef class ELEMENT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "element"


cdef class EM(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "em"


cdef class EMBED(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "embed"


cdef class FIELDSET(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "fieldset"


cdef class FIGCAPTION(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "figcaption"


cdef class FIGURE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "figure"


cdef class FONT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "font"


cdef class FOOTER(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "footer"


cdef class FORM(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "form"


cdef class FRAME(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "frame"


cdef class FRAMESET(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "frameset"


cdef class H1(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "h1"


cdef class H2(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "h2"


cdef class H3(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "h3"


cdef class H4(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "h4"


cdef class H5(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "h5"


cdef class H6(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "h6"


cdef class HEAD(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "head"

    def __init__(self, *children):
        super(HEAD, self).__init__(
            META(charset="utf-8"),
            META(name="viewport", content="width=device-width, initial-scale=1.0"),
            *children,
        )


cdef class HEADER(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "header"


cdef class HGROUP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "hgroup"


cdef class HR(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "hr"


cdef class HTML(HTMLElement):
    cdef bint doctype

    def __cinit__(self, *args, **kwargs):
        self.tag = "html"

    def __init__(self, *args, bint doctype=False, **kwargs):
        self.doctype = doctype
        super(HTML, self).__init__(*args, **kwargs)

    cpdef str render(self, dict context):
        if self.doctype:
            return mark_safe("<!DOCTYPE html>") + super(HTML, self).render(context)
        return super(HTML, self).render(context)


cdef class I(HTMLElement):  # noqa
    def __cinit__(self, *args, **kwargs):
        self.tag = "i"


cdef class IFRAME(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "iframe"


cdef class IMAGE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "image"


cdef class IMG(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "img"


cdef class INPUT(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "input"


cdef class INS(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "ins"


cdef class ISINDEX(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "isindex"


cdef class KBD(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "kbd"


cdef class KEYGEN(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "keygen"


cdef class LABEL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "label"


cdef class LEGEND(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "legend"


cdef class LI(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "li"


cdef class LINK(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "link"


cdef class LISTING(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "listing"


cdef class MAIN(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "main"


cdef class MAP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "map"


cdef class MARK(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "mark"


cdef class MARQUEE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "marquee"


cdef class MENU(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "menu"


cdef class MENUITEM(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "menuitem"


cdef class META(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "meta"


cdef class METER(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "meter"


cdef class MULTICOL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "multicol"


cdef class NAV(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "nav"


cdef class NEXTID(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "nextid"


cdef class NOBR(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "nobr"


cdef class NOEMBED(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "noembed"


cdef class NOFRAMES(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "noframes"


cdef class NOSCRIPT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "noscript"


cdef class OBJECT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "object"


cdef class OL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "ol"


cdef class OPTGROUP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "optgroup"


cdef class OPTION(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "option"


cdef class OUTPUT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "output"


cdef class P(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "p"


cdef class PARAM(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "param"


cdef class PICTURE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "picture"


cdef class PLAINTEXT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "plaintext"


cdef class PRE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "pre"


cdef class PROGRESS(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "progress"


cdef class Q(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "q"


cdef class RB(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "rb"


cdef class RE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "re"


cdef class RP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "rp"


cdef class RT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "rt"


cdef class RTC(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "rtc"


cdef class RUBY(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "ruby"


cdef class S(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "s"


cdef class SAMP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "samp"


cdef class SCRIPT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "script"


cdef class SECTION(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "section"


cdef class SELECT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "select"


cdef class SHADOW(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "shadow"


cdef class SLOT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "slot"


cdef class SMALL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "small"


cdef class SOURCE(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "source"


cdef class SPACER(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "spacer"


cdef class SPAN(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "span"


cdef class STRIKE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "strike"


cdef class STRONG(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "strong"


cdef class STYLE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "style"


cdef class SUB(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "sub"


cdef class SUMMARY(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "summary"


cdef class SUP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "sup"


cdef class SVG(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "svg"


cdef class TABLE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "table"


cdef class TBODY(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "tbody"


cdef class TD(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "td"


cdef class TEMPLATE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "template"


cdef class TEXTAREA(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "textarea"


cdef class TFOOT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "tfoot"


cdef class TH(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "th"


cdef class THEAD(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "thead"


cdef class TIME(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "time"


cdef class TITLE(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "title"


cdef class TR(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "tr"


cdef class TRACK(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "track"


cdef class TT(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "tt"


cdef class U(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "u"


cdef class UL(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "ul"


cdef class VAR(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "var"


cdef class VIDEO(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "video"


cdef class WBR(VoidElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "wbr"


cdef class XMP(HTMLElement):
    def __cinit__(self, *args, **kwargs):
        self.tag = "xmp"


cdef str flatattrs(dict attributes, dict context):
    """Converts a dictionary to a string of HTML-attributes.
    Leading underscores are removed and other underscores are replaced with dashes."""

    attlist = []
    for key, value in attributes.items():
        value = resolve_lazy(value, context)
        if isinstance(value, If):
            rendered = list(value.render(context))
            if len(rendered) == 1 and isinstance(rendered[0], bool):
                value = rendered[0]
            else:
                rendered = list(value.render(context))
                value = "".join(rendered) if rendered else None
        elif isinstance(value, BaseElement):
            rendered = list(value.render(context))
            value = "".join(rendered) if rendered else None
        if value is None:
            continue

        if key[0] == "_":
            key = key[1:]
        key = key.replace("_", "-")
        if isinstance(value, bool) and key != "value":
            if value is True:
                attlist.append(f"{key}")
        else:
            attlist.append(f'{key}="{value}"')
    return " ".join(attlist)


def append_attribute(attrs, key, value, separator=None):
    """
    In many cases we want a component to add e.g. something to the
    _class attribute of an HTML element but still allow the caller to
    pass his own _class attribute to the component. In these cases
    we can use ``append_attribute`` which will make sure that existing
    attributes will not simply be overwritten.
    Multiple items of attribute will in general require to be separated
    by a separator. If the ``separator`` is not set, a best guess will be
    done automatically.

    Usage:

        class MyDiv(hg.DIV):
            def __init__(self, *args, **kwargs):
                hg.append_attribute(kwargs, "_class", "mydiv")
                super().__init__(*args, **kwargs)

        a = MyDiv(_class="special-class")

        assert a.attributes["_class"].split(" ") == ["special-class", mydiv]

    """

    def guess_separator(key):
        default_separators = {
            "_class": " ",
            "style": ";",
        }
        if key in default_separators:
            return default_separators[key]
        # onclick and similar event handlers are javascript
        if key.startswith("on") and key.islower() and key.isalpha():
            return ";"
        return " "

    if key in attrs:
        attrs[key] = BaseElement(attrs[key], separator or guess_separator(key), value)
    else:
        attrs[key] = value


cpdef object resolve_lazy(object value, dict context):
    """Shortcut to resolve a value in case it is a Lazy value"""

    while isinstance(value, Lazy):
        value = value.resolve(context)
    return value


def getattr_lazy(lazyobject, attr):
    """
    Takes a lazy object and returns a new lazy object which will
    resolve the attribute on the object
    """

    def wrapper(c):
        ret = getattr(resolve_lazy(lazyobject, c), attr)
        return ret() if callable(ret) else ret

    return F(wrapper)


cpdef object resolve_lookup(object context, str lookup, bint call_functions=True):
    """
    Helper function to extract a value out of a context-dict.
    A lookup string can access attributes, dict-keys, methods without
    parameters and indexes by using the dot-accessor (e.g. ``person.name``)
    This is based on the implementation of the variable lookup of the django
    template system:
    https://github.com/django/django/blob/master/django/template/base.py
    """
    current = context
    for bit in lookup.split("."):
        try:
            current = current[bit]
        except (TypeError, AttributeError, KeyError, ValueError, IndexError):
            try:
                current = getattr(current, bit)
            except (TypeError, AttributeError):
                # Reraise if the exception was raised by a @property
                if not isinstance(current, dict) and bit in dir(current):
                    raise
                try:  # list-index lookup
                    current = current[int(bit)]
                except (
                    IndexError,  # list index out of range
                    ValueError,  # invalid literal for int()
                    KeyError,  # current is a dict without `int(bit)` key
                    TypeError,
                ):  # unsubscriptable object
                    return None
                    # raise LookupError(
                    # "Failed lookup for key " "[%s] in %r", (bit, current)
                    # )  # missing attribute
        if callable(current) and call_functions:
            try:  # method call (assuming no args required)
                current = current()
            except TypeError:
                signature = inspect.signature(current)  # type: ignore
                try:
                    signature.bind()
                except TypeError:  # arguments *were* required
                    # but we continue because we might use an attribute on the
                    # object instead of calling it
                    pass
                else:
                    raise

    return current

# only for API compatability
def render(root, basecontext):
    """Shortcut to serialize an object tree into a string"""
    return root.render(basecontext)
