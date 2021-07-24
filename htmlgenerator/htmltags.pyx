import warnings
import cython

from htmlgenerator.base cimport BaseElement, If
from htmlgenerator.lazy cimport Lazy, resolve_lazy


cdef class HTMLElement(BaseElement):
    """The base for all HTML tags."""

    cdef public str tag
    cdef public dict attributes
    cdef public object lazy_attributes

    def __init__(self, *children, lazy_attributes=None, **attributes):
        self.tag = self.__class__.__name__
        if any(attr == "class" for attr in attributes.keys()):
            warnings.warn(
                'You should use "_class" instead of "class" when specifiying HTML classes in htmlgenerator ("class" is a python keyword).'
            )
        self.attributes = attributes
        super().__init__(*children)
        if lazy_attributes and not isinstance(lazy_attributes, Lazy):
            raise ValueError(
                f"Argument 'lazy_attributes' must have type 'Lazy' but has type {type(lazy_attributes)}"
            )
        self.lazy_attributes = lazy_attributes

    cpdef render(self, context, stringify=True):
        attr_str = flatattrs(
            {
                **self.attributes,
                **(resolve_lazy(self.lazy_attributes, context, self) or {}),
            },
            context,
            self,
        )
        # quirk to prevent tags having a single space if there are no attributes
        attr_str = (" " + attr_str) if attr_str else attr_str
        return f"<{self.tag}{attr_str}>" + super().render_children(context) + f"</{self.tag}>"

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
        super().__init__(**kwargs)

    cpdef render(self, context, stringify=True):
        return f"<{self.tag} {flatattrs(self.attributes, context, self)} />"


cdef class A(HTMLElement):
    def __init__(self, *args, newtab=False, **kwargs):
        if newtab:
            kwargs["target"] = "_blank"
            kwargs["rel"] = "noopener noreferrer"
        super().__init__(*args, **kwargs)


cdef class ABBR(HTMLElement):
    pass


cdef class ACRONYM(HTMLElement):
    pass


cdef class ADDRESS(HTMLElement):
    pass


cdef class APPLET(HTMLElement):
    pass


cdef class AREA(VoidElement):
    pass


cdef class ARTICLE(HTMLElement):
    pass


cdef class ASIDE(HTMLElement):
    pass


cdef class AUDIO(HTMLElement):
    pass


cdef class B(HTMLElement):
    pass


cdef class BASE(VoidElement):
    pass


cdef class BASEFONT(HTMLElement):
    pass


cdef class BDI(HTMLElement):
    pass


cdef class BDO(HTMLElement):
    pass


cdef class BGSOUND(HTMLElement):
    pass


cdef class BIG(HTMLElement):
    pass


cdef class BLINK(HTMLElement):
    pass


cdef class BLOCKQUOTE(HTMLElement):
    pass


cdef class BODY(HTMLElement):
    pass


cdef class BR(VoidElement):
    pass


cdef class BUTTON(HTMLElement):
    pass


cdef class CANVAS(HTMLElement):
    pass


cdef class CAPTION(HTMLElement):
    pass


cdef class CENTER(HTMLElement):
    pass


cdef class CITE(HTMLElement):
    pass


cdef class CODE(HTMLElement):
    pass


cdef class COL(VoidElement):
    pass


cdef class COLGROUP(HTMLElement):
    pass


cdef class COMMAND(VoidElement):
    pass


cdef class CONTENT(HTMLElement):
    pass


cdef class DATA(HTMLElement):
    pass


cdef class DATALIST(HTMLElement):
    pass


cdef class DD(HTMLElement):
    pass


cdef class DEL(HTMLElement):
    pass


cdef class DETAILS(HTMLElement):
    pass


cdef class DFN(HTMLElement):
    pass


cdef class DIALOG(HTMLElement):
    pass


cdef class DIR(HTMLElement):
    pass


cdef class DIV(HTMLElement):
    pass


cdef class DL(HTMLElement):
    pass


cdef class DT(HTMLElement):
    pass


cdef class EDIASTREA(HTMLElement):
    pass


cdef class ELEMENT(HTMLElement):
    pass


cdef class EM(HTMLElement):
    pass


cdef class EMBED(VoidElement):
    pass


cdef class FIELDSET(HTMLElement):
    pass


cdef class FIGCAPTION(HTMLElement):
    pass


cdef class FIGURE(HTMLElement):
    pass


cdef class FONT(HTMLElement):
    pass


cdef class FOOTER(HTMLElement):
    pass


cdef class FORM(HTMLElement):
    pass


cdef class FRAME(HTMLElement):
    pass


cdef class FRAMESET(HTMLElement):
    pass


cdef class H1(HTMLElement):
    pass


cdef class H2(HTMLElement):
    pass


cdef class H3(HTMLElement):
    pass


cdef class H4(HTMLElement):
    pass


cdef class H5(HTMLElement):
    pass


cdef class H6(HTMLElement):
    pass


cdef class HEAD(HTMLElement):
    def __init__(self, *children):
        super().__init__(
            META(charset="utf-8"),
            META(name="viewport", content="width=device-width, initial-scale=1.0"),
            *children,
        )


cdef class HEADER(HTMLElement):
    pass


cdef class HGROUP(HTMLElement):
    pass


cdef class HR(VoidElement):
    pass


cdef class HTML(HTMLElement):
    def __init__(self, *args, doctype=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctype = doctype

    cpdef render(self, context, stringify=True):
        if self.doctype:
            return "<!DOCTYPE html>" + super().render(context)
        else:
            super().render(context)


cdef class I(HTMLElement):  # noqa
    pass


cdef class IFRAME(HTMLElement):
    pass


cdef class IMAGE(HTMLElement):
    pass


cdef class IMG(VoidElement):
    pass


cdef class INPUT(VoidElement):
    pass


cdef class INS(HTMLElement):
    pass


cdef class ISINDEX(HTMLElement):
    pass


cdef class KBD(HTMLElement):
    pass


cdef class KEYGEN(VoidElement):
    pass


cdef class LABEL(HTMLElement):
    pass


cdef class LEGEND(HTMLElement):
    pass


cdef class LI(HTMLElement):
    pass


cdef class LINK(VoidElement):
    pass


cdef class LISTING(HTMLElement):
    pass


cdef class MAIN(HTMLElement):
    pass


cdef class MAP(HTMLElement):
    pass


cdef class MARK(HTMLElement):
    pass


cdef class MARQUEE(HTMLElement):
    pass


cdef class MENU(HTMLElement):
    pass


cdef class MENUITEM(HTMLElement):
    pass


cdef class META(VoidElement):
    pass


cdef class METER(HTMLElement):
    pass


cdef class MULTICOL(HTMLElement):
    pass


cdef class NAV(HTMLElement):
    pass


cdef class NEXTID(HTMLElement):
    pass


cdef class NOBR(HTMLElement):
    pass


cdef class NOEMBED(HTMLElement):
    pass


cdef class NOFRAMES(HTMLElement):
    pass


cdef class NOSCRIPT(HTMLElement):
    pass


cdef class OBJECT(HTMLElement):
    pass


cdef class OL(HTMLElement):
    pass


cdef class OPTGROUP(HTMLElement):
    pass


cdef class OPTION(HTMLElement):
    pass


cdef class OUTPUT(HTMLElement):
    pass


cdef class P(HTMLElement):
    pass


cdef class PARAM(VoidElement):
    pass


cdef class PICTURE(HTMLElement):
    pass


cdef class PLAINTEXT(HTMLElement):
    pass


cdef class PRE(HTMLElement):
    pass


cdef class PROGRESS(HTMLElement):
    pass


cdef class Q(HTMLElement):
    pass


cdef class RB(HTMLElement):
    pass


cdef class RE(HTMLElement):
    pass


cdef class RP(HTMLElement):
    pass


cdef class RT(HTMLElement):
    pass


cdef class RTC(HTMLElement):
    pass


cdef class RUBY(HTMLElement):
    pass


cdef class S(HTMLElement):
    pass


cdef class SAMP(HTMLElement):
    pass


cdef class SCRIPT(HTMLElement):
    pass


cdef class SECTION(HTMLElement):
    pass


cdef class SELECT(HTMLElement):
    pass


cdef class SHADOW(HTMLElement):
    pass


cdef class SLOT(HTMLElement):
    pass


cdef class SMALL(HTMLElement):
    pass


cdef class SOURCE(VoidElement):
    pass


cdef class SPACER(HTMLElement):
    pass


cdef class SPAN(HTMLElement):
    pass


cdef class STRIKE(HTMLElement):
    pass


cdef class STRONG(HTMLElement):
    pass


cdef class STYLE(HTMLElement):
    pass


cdef class SUB(HTMLElement):
    pass


cdef class SUMMARY(HTMLElement):
    pass


cdef class SUP(HTMLElement):
    pass


cdef class SVG(HTMLElement):
    pass


cdef class TABLE(HTMLElement):
    pass


cdef class TBODY(HTMLElement):
    pass


cdef class TD(HTMLElement):
    pass


cdef class TEMPLATE(HTMLElement):
    pass


cdef class TEXTAREA(HTMLElement):
    pass


cdef class TFOOT(HTMLElement):
    pass


cdef class TH(HTMLElement):
    pass


cdef class THEAD(HTMLElement):
    pass


cdef class TIME(HTMLElement):
    pass


cdef class TITLE(HTMLElement):
    pass


cdef class TR(HTMLElement):
    pass


cdef class TRACK(VoidElement):
    pass


cdef class TT(HTMLElement):
    pass


cdef class U(HTMLElement):
    pass


cdef class UL(HTMLElement):
    pass


cdef class VAR(HTMLElement):
    pass


cdef class VIDEO(HTMLElement):
    pass


cdef class WBR(VoidElement):
    pass


cdef class XMP(HTMLElement):
    pass


cdef flatattrs(attributes, context, element):
    """Converts a dictionary to a string of HTML-attributes.
    Leading underscores are removed and other underscores are replaced with dashes."""

    attlist = []
    for key, value in attributes.items():
        value = resolve_lazy(value, context, element)
        if isinstance(value, If):
            rendered = list(value.render(context, stringify=False))
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


cdef append_attribute(attrs, key, value, separator=None):
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
