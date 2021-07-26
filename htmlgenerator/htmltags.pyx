import warnings

import cython

from htmlgenerator.base cimport BaseElement, If
from htmlgenerator.lazy cimport Lazy, _resolve_lazy_internal


cdef class HTMLElement(BaseElement):
    """The base for all HTML tags."""

    cdef str tag
    cdef public dict attributes
    cdef public object lazy_attributes

    def __init__(self, *children, lazy_attributes=None, **attributes):
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

    cpdef str render(self, dict context):
        attrs = dict(self.attributes)
        attrs.update(_resolve_lazy_internal(self.lazy_attributes, context, self) or {})
        return f"<{self.tag}{flatattrs(attrs, context, self)}>" + self.render_children(context) + f"</{self.tag}>"

    # mostly for debugging purposes
    def __repr__(self):
        return (
            f"<{self.tag} "
            + " ".join(f"{k.lstrip('_')}=\"{v}\"" for k, v in self.attributes.items())
            + f"> ({self.__class__})"
        )

    def __reduce__(self):
        return (self.__class__, (*self,))


cdef class VoidElement(HTMLElement):
    """Wrapper for elements without a closing tag, cannot have children"""

    # does not accept children
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    cpdef str render(self, dict context):
        attrs = dict(self.attributes)
        attrs.update(_resolve_lazy_internal(self.lazy_attributes, context, self) or {})
        return f"<{self.tag}{flatattrs(self.attributes, context, self)} />"


cdef class A(HTMLElement):
    def __cinit__(self):
        self.tag = "a"

    def __init__(self, *args, newtab=False, **kwargs):
        if newtab:
            kwargs["target"] = "_blank"
            kwargs["rel"] = "noopener noreferrer"
        super().__init__(*args, **kwargs)


cdef class ABBR(HTMLElement):
    def __cinit__(self):
        self.tag = "ABBR"


cdef class ACRONYM(HTMLElement):
    def __cinit__(self):
        self.tag = "ACRONYM"


cdef class ADDRESS(HTMLElement):
    def __cinit__(self):
        self.tag = "ADDRESS"


cdef class APPLET(HTMLElement):
    def __cinit__(self):
        self.tag = "APPLET"


cdef class AREA(VoidElement):
    def __cinit__(self):
        self.tag = "AREA"


cdef class ARTICLE(HTMLElement):
    def __cinit__(self):
        self.tag = "ARTICLE"


cdef class ASIDE(HTMLElement):
    def __cinit__(self):
        self.tag = "ASIDE"


cdef class AUDIO(HTMLElement):
    def __cinit__(self):
        self.tag = "AUDIO"


cdef class B(HTMLElement):
    def __cinit__(self):
        self.tag = "B"


cdef class BASE(VoidElement):
    def __cinit__(self):
        self.tag = "BASE"


cdef class BASEFONT(HTMLElement):
    def __cinit__(self):
        self.tag = "BASEFONT"


cdef class BDI(HTMLElement):
    def __cinit__(self):
        self.tag = "BDI"


cdef class BDO(HTMLElement):
    def __cinit__(self):
        self.tag = "BDO"


cdef class BGSOUND(HTMLElement):
    def __cinit__(self):
        self.tag = "BGSOUND"


cdef class BIG(HTMLElement):
    def __cinit__(self):
        self.tag = "BIG"


cdef class BLINK(HTMLElement):
    def __cinit__(self):
        self.tag = "BLINK"


cdef class BLOCKQUOTE(HTMLElement):
    def __cinit__(self):
        self.tag = "BLOCKQUOTE"


cdef class BODY(HTMLElement):
    def __cinit__(self):
        self.tag = "BODY"


cdef class BR(VoidElement):
    def __cinit__(self):
        self.tag = "BR"


cdef class BUTTON(HTMLElement):
    def __cinit__(self):
        self.tag = "BUTTON"


cdef class CANVAS(HTMLElement):
    def __cinit__(self):
        self.tag = "CANVAS"


cdef class CAPTION(HTMLElement):
    def __cinit__(self):
        self.tag = "CAPTION"


cdef class CENTER(HTMLElement):
    def __cinit__(self):
        self.tag = "CENTER"


cdef class CITE(HTMLElement):
    def __cinit__(self):
        self.tag = "CITE"


cdef class CODE(HTMLElement):
    def __cinit__(self):
        self.tag = "CODE"


cdef class COL(VoidElement):
    def __cinit__(self):
        self.tag = "COL"


cdef class COLGROUP(HTMLElement):
    def __cinit__(self):
        self.tag = "COLGROUP"


cdef class COMMAND(VoidElement):
    def __cinit__(self):
        self.tag = "COMMAND"


cdef class CONTENT(HTMLElement):
    def __cinit__(self):
        self.tag = "CONTENT"


cdef class DATA(HTMLElement):
    def __cinit__(self):
        self.tag = "DATA"


cdef class DATALIST(HTMLElement):
    def __cinit__(self):
        self.tag = "DATALIST"


cdef class DD(HTMLElement):
    def __cinit__(self):
        self.tag = "DD"


cdef class DEL(HTMLElement):
    def __cinit__(self):
        self.tag = "DEL"


cdef class DETAILS(HTMLElement):
    def __cinit__(self):
        self.tag = "DETAILS"


cdef class DFN(HTMLElement):
    def __cinit__(self):
        self.tag = "DFN"


cdef class DIALOG(HTMLElement):
    def __cinit__(self):
        self.tag = "DIALOG"


cdef class DIR(HTMLElement):
    def __cinit__(self):
        self.tag = "DIR"


cdef class DIV(HTMLElement):
    def __cinit__(self):
        self.tag = "DIV"


cdef class DL(HTMLElement):
    def __cinit__(self):
        self.tag = "DL"


cdef class DT(HTMLElement):
    def __cinit__(self):
        self.tag = "DT"


cdef class EDIASTREA(HTMLElement):
    def __cinit__(self):
        self.tag = "EDIASTREA"


cdef class ELEMENT(HTMLElement):
    def __cinit__(self):
        self.tag = "ELEMENT"


cdef class EM(HTMLElement):
    def __cinit__(self):
        self.tag = "EM"


cdef class EMBED(VoidElement):
    def __cinit__(self):
        self.tag = "EMBED"


cdef class FIELDSET(HTMLElement):
    def __cinit__(self):
        self.tag = "FIELDSET"


cdef class FIGCAPTION(HTMLElement):
    def __cinit__(self):
        self.tag = "FIGCAPTION"


cdef class FIGURE(HTMLElement):
    def __cinit__(self):
        self.tag = "FIGURE"


cdef class FONT(HTMLElement):
    def __cinit__(self):
        self.tag = "FONT"


cdef class FOOTER(HTMLElement):
    def __cinit__(self):
        self.tag = "FOOTER"


cdef class FORM(HTMLElement):
    def __cinit__(self):
        self.tag = "FORM"


cdef class FRAME(HTMLElement):
    def __cinit__(self):
        self.tag = "FRAME"


cdef class FRAMESET(HTMLElement):
    def __cinit__(self):
        self.tag = "FRAMESET"


cdef class H1(HTMLElement):
    def __cinit__(self):
        self.tag = "H1"


cdef class H2(HTMLElement):
    def __cinit__(self):
        self.tag = "H2"


cdef class H3(HTMLElement):
    def __cinit__(self):
        self.tag = "H3"


cdef class H4(HTMLElement):
    def __cinit__(self):
        self.tag = "H4"


cdef class H5(HTMLElement):
    def __cinit__(self):
        self.tag = "H5"


cdef class H6(HTMLElement):
    def __cinit__(self):
        self.tag = "H6"


cdef class HEAD(HTMLElement):
    def __cinit__(self):
        self.tag = "head"

    def __init__(self, *children):
        super().__init__(
            META(charset="utf-8"),
            META(name="viewport", content="width=device-width, initial-scale=1.0"),
            *children,
        )


cdef class HEADER(HTMLElement):
    def __cinit__(self):
        self.tag = "HEADER"


cdef class HGROUP(HTMLElement):
    def __cinit__(self):
        self.tag = "HGROUP"


cdef class HR(VoidElement):
    def __cinit__(self):
        self.tag = "HR"


cdef class HTML(HTMLElement):
    cdef bint doctype

    def __cinit__(self):
        self.tag = "html"
        self.doctype = False

    def __init__(self, *args, doctype=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctype = doctype

    cpdef str render(self, dict context):
        if self.doctype:
            return "<!DOCTYPE html>" + super(HTMLElement, self).render(context)
        return super(HTMLElement, self).render(context)


cdef class I(HTMLElement):  # noqa
    def __cinit__(self):
        self.tag = "I"


cdef class IFRAME(HTMLElement):
    def __cinit__(self):
        self.tag = "IFRAME"


cdef class IMAGE(HTMLElement):
    def __cinit__(self):
        self.tag = "IMAGE"


cdef class IMG(VoidElement):
    def __cinit__(self):
        self.tag = "IMG"


cdef class INPUT(VoidElement):
    def __cinit__(self):
        self.tag = "INPUT"


cdef class INS(HTMLElement):
    def __cinit__(self):
        self.tag = "INS"


cdef class ISINDEX(HTMLElement):
    def __cinit__(self):
        self.tag = "ISINDEX"


cdef class KBD(HTMLElement):
    def __cinit__(self):
        self.tag = "KBD"


cdef class KEYGEN(VoidElement):
    def __cinit__(self):
        self.tag = "KEYGEN"


cdef class LABEL(HTMLElement):
    def __cinit__(self):
        self.tag = "LABEL"


cdef class LEGEND(HTMLElement):
    def __cinit__(self):
        self.tag = "LEGEND"


cdef class LI(HTMLElement):
    def __cinit__(self):
        self.tag = "LI"


cdef class LINK(VoidElement):
    def __cinit__(self):
        self.tag = "LINK"


cdef class LISTING(HTMLElement):
    def __cinit__(self):
        self.tag = "LISTING"


cdef class MAIN(HTMLElement):
    def __cinit__(self):
        self.tag = "MAIN"


cdef class MAP(HTMLElement):
    def __cinit__(self):
        self.tag = "MAP"


cdef class MARK(HTMLElement):
    def __cinit__(self):
        self.tag = "MARK"


cdef class MARQUEE(HTMLElement):
    def __cinit__(self):
        self.tag = "MARQUEE"


cdef class MENU(HTMLElement):
    def __cinit__(self):
        self.tag = "MENU"


cdef class MENUITEM(HTMLElement):
    def __cinit__(self):
        self.tag = "MENUITEM"


cdef class META(VoidElement):
    def __cinit__(self):
        self.tag = "META"


cdef class METER(HTMLElement):
    def __cinit__(self):
        self.tag = "METER"


cdef class MULTICOL(HTMLElement):
    def __cinit__(self):
        self.tag = "MULTICOL"


cdef class NAV(HTMLElement):
    def __cinit__(self):
        self.tag = "NAV"


cdef class NEXTID(HTMLElement):
    def __cinit__(self):
        self.tag = "NEXTID"


cdef class NOBR(HTMLElement):
    def __cinit__(self):
        self.tag = "NOBR"


cdef class NOEMBED(HTMLElement):
    def __cinit__(self):
        self.tag = "NOEMBED"


cdef class NOFRAMES(HTMLElement):
    def __cinit__(self):
        self.tag = "NOFRAMES"


cdef class NOSCRIPT(HTMLElement):
    def __cinit__(self):
        self.tag = "NOSCRIPT"


cdef class OBJECT(HTMLElement):
    def __cinit__(self):
        self.tag = "OBJECT"


cdef class OL(HTMLElement):
    def __cinit__(self):
        self.tag = "OL"


cdef class OPTGROUP(HTMLElement):
    def __cinit__(self):
        self.tag = "OPTGROUP"


cdef class OPTION(HTMLElement):
    def __cinit__(self):
        self.tag = "OPTION"


cdef class OUTPUT(HTMLElement):
    def __cinit__(self):
        self.tag = "OUTPUT"


cdef class P(HTMLElement):
    def __cinit__(self):
        self.tag = "P"


cdef class PARAM(VoidElement):
    def __cinit__(self):
        self.tag = "PARAM"


cdef class PICTURE(HTMLElement):
    def __cinit__(self):
        self.tag = "PICTURE"


cdef class PLAINTEXT(HTMLElement):
    def __cinit__(self):
        self.tag = "PLAINTEXT"


cdef class PRE(HTMLElement):
    def __cinit__(self):
        self.tag = "PRE"


cdef class PROGRESS(HTMLElement):
    def __cinit__(self):
        self.tag = "PROGRESS"


cdef class Q(HTMLElement):
    def __cinit__(self):
        self.tag = "Q"


cdef class RB(HTMLElement):
    def __cinit__(self):
        self.tag = "RB"


cdef class RE(HTMLElement):
    def __cinit__(self):
        self.tag = "RE"


cdef class RP(HTMLElement):
    def __cinit__(self):
        self.tag = "RP"


cdef class RT(HTMLElement):
    def __cinit__(self):
        self.tag = "RT"


cdef class RTC(HTMLElement):
    def __cinit__(self):
        self.tag = "RTC"


cdef class RUBY(HTMLElement):
    def __cinit__(self):
        self.tag = "RUBY"


cdef class S(HTMLElement):
    def __cinit__(self):
        self.tag = "S"


cdef class SAMP(HTMLElement):
    def __cinit__(self):
        self.tag = "SAMP"


cdef class SCRIPT(HTMLElement):
    def __cinit__(self):
        self.tag = "SCRIPT"


cdef class SECTION(HTMLElement):
    def __cinit__(self):
        self.tag = "SECTION"


cdef class SELECT(HTMLElement):
    def __cinit__(self):
        self.tag = "SELECT"


cdef class SHADOW(HTMLElement):
    def __cinit__(self):
        self.tag = "SHADOW"


cdef class SLOT(HTMLElement):
    def __cinit__(self):
        self.tag = "SLOT"


cdef class SMALL(HTMLElement):
    def __cinit__(self):
        self.tag = "SMALL"


cdef class SOURCE(VoidElement):
    def __cinit__(self):
        self.tag = "SOURCE"


cdef class SPACER(HTMLElement):
    def __cinit__(self):
        self.tag = "SPACER"


cdef class SPAN(HTMLElement):
    def __cinit__(self):
        self.tag = "SPAN"


cdef class STRIKE(HTMLElement):
    def __cinit__(self):
        self.tag = "STRIKE"


cdef class STRONG(HTMLElement):
    def __cinit__(self):
        self.tag = "STRONG"


cdef class STYLE(HTMLElement):
    def __cinit__(self):
        self.tag = "STYLE"


cdef class SUB(HTMLElement):
    def __cinit__(self):
        self.tag = "SUB"


cdef class SUMMARY(HTMLElement):
    def __cinit__(self):
        self.tag = "SUMMARY"


cdef class SUP(HTMLElement):
    def __cinit__(self):
        self.tag = "SUP"


cdef class SVG(HTMLElement):
    def __cinit__(self):
        self.tag = "SVG"


cdef class TABLE(HTMLElement):
    def __cinit__(self):
        self.tag = "TABLE"


cdef class TBODY(HTMLElement):
    def __cinit__(self):
        self.tag = "TBODY"


cdef class TD(HTMLElement):
    def __cinit__(self):
        self.tag = "TD"


cdef class TEMPLATE(HTMLElement):
    def __cinit__(self):
        self.tag = "TEMPLATE"


cdef class TEXTAREA(HTMLElement):
    def __cinit__(self):
        self.tag = "TEXTAREA"


cdef class TFOOT(HTMLElement):
    def __cinit__(self):
        self.tag = "TFOOT"


cdef class TH(HTMLElement):
    def __cinit__(self):
        self.tag = "TH"


cdef class THEAD(HTMLElement):
    def __cinit__(self):
        self.tag = "THEAD"


cdef class TIME(HTMLElement):
    def __cinit__(self):
        self.tag = "TIME"


cdef class TITLE(HTMLElement):
    def __cinit__(self):
        self.tag = "TITLE"


cdef class TR(HTMLElement):
    def __cinit__(self):
        self.tag = "TR"


cdef class TRACK(VoidElement):
    def __cinit__(self):
        self.tag = "TRACK"


cdef class TT(HTMLElement):
    def __cinit__(self):
        self.tag = "TT"


cdef class U(HTMLElement):
    def __cinit__(self):
        self.tag = "U"


cdef class UL(HTMLElement):
    def __cinit__(self):
        self.tag = "UL"


cdef class VAR(HTMLElement):
    def __cinit__(self):
        self.tag = "VAR"


cdef class VIDEO(HTMLElement):
    def __cinit__(self):
        self.tag = "VIDEO"


cdef class WBR(VoidElement):
    def __cinit__(self):
        self.tag = "WBR"


cdef class XMP(HTMLElement):
    def __cinit__(self):
        self.tag = "XMP"


# TODO: remove element parameter
cdef str flatattrs(dict attributes, dict context, object element):
    """Converts a dictionary to a string of HTML-attributes.
    Leading underscores are removed and other underscores are replaced with dashes."""

    cdef str attlist = ""
    for key, value in attributes.items():
        value = _resolve_lazy_internal(value, context, element)
        if isinstance(value, BaseElement):
            value = value.render(context)
        value = str(value)
        if value in ("None", "", "False") and key != "value":
            continue
        if key[0] == "_":
            key = key[1:]
        key = key.replace("_", "-")
        attlist += " " + key
        if value != "True" or key == "value":
            attlist += '="' + value + '"'
    return attlist


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
