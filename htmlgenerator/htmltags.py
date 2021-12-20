import typing
import warnings

from .base import BaseElement, If
from .lazy import Lazy, resolve_lazy


class HTMLElement(BaseElement):
    """The base for all HTML tags."""

    tag: str = ""

    def __init__(
        self, *children, lazy_attributes: typing.Optional[Lazy] = None, **attributes
    ):
        assert self.tag != ""
        if any(attr == "class" for attr in attributes.keys()):
            warnings.warn(
                'You should use "_class" instead of "class" when specifiying HTML'
                'classes in htmlgenerator ("class" is a python keyword).'
            )
        self.attributes: dict = attributes
        super().__init__(*children)
        self.lazy_attributes = lazy_attributes

    def render(self, context: dict) -> typing.Generator[str, None, None]:
        attr_str = flatattrs(
            {
                **self.attributes,
                **(resolve_lazy(self.lazy_attributes, context) or {}),
            },
            context,
        )
        # quirk to prevent tags having a single space if there are no attributes
        attr_str = (" " + attr_str) if attr_str else attr_str
        yield f"<{self.tag}{attr_str}>"
        yield from super().render_children(context)
        yield f"</{self.tag}>"

    # mostly for debugging purposes
    def __repr__(self) -> str:
        return (
            f"<{self.tag} "
            + " ".join(f"{k.lstrip('_')}=\"{v}\"" for k, v in self.attributes.items())
            + f"> ({self.__class__})"
        )


class VoidElement(HTMLElement):
    """Wrapper for elements without a closing tag, cannot have children"""

    # does not accept children
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self, context) -> typing.Generator[str, None, None]:
        attr_str = flatattrs(
            {
                **self.attributes,
                **(resolve_lazy(self.lazy_attributes, context) or {}),
            },
            context,
        )
        # quirk to prevent tags having a single space if there are no attributes
        attr_str = (" " + attr_str) if attr_str else attr_str
        yield f"<{self.tag} {attr_str} />"


class A(HTMLElement):
    tag = "a"

    def __init__(self, *args, newtab=False, **kwargs):
        if newtab:
            kwargs["target"] = "_blank"
            kwargs["rel"] = "noopener noreferrer"
        super().__init__(*args, **kwargs)


class ABBR(HTMLElement):
    tag = "abbr"


class ACRONYM(HTMLElement):
    tag = "acronym"


class ADDRESS(HTMLElement):
    tag = "address"


class APPLET(HTMLElement):
    tag = "applet"


class AREA(VoidElement):
    tag = "area"


class ARTICLE(HTMLElement):
    tag = "article"


class ASIDE(HTMLElement):
    tag = "aside"


class AUDIO(HTMLElement):
    tag = "audio"


class B(HTMLElement):
    tag = "b"


class BASE(VoidElement):
    tag = "base"


class BASEFONT(HTMLElement):
    tag = "basefont"


class BDI(HTMLElement):
    tag = "bdi"


class BDO(HTMLElement):
    tag = "bdo"


class BGSOUND(HTMLElement):
    tag = "bgsound"


class BIG(HTMLElement):
    tag = "big"


class BLINK(HTMLElement):
    tag = "blink"


class BLOCKQUOTE(HTMLElement):
    tag = "blockquote"


class BODY(HTMLElement):
    tag = "body"


class BR(VoidElement):
    tag = "br"


class BUTTON(HTMLElement):
    tag = "button"


class CANVAS(HTMLElement):
    tag = "canvas"


class CAPTION(HTMLElement):
    tag = "caption"


class CENTER(HTMLElement):
    tag = "center"


class CITE(HTMLElement):
    tag = "cite"


class CODE(HTMLElement):
    tag = "code"


class COL(VoidElement):
    tag = "col"


class COLGROUP(HTMLElement):
    tag = "colgroup"


class COMMAND(VoidElement):
    tag = "command"


class CONTENT(HTMLElement):
    tag = "content"


class DATA(HTMLElement):
    tag = "data"


class DATALIST(HTMLElement):
    tag = "datalist"


class DD(HTMLElement):
    tag = "dd"


class DEL(HTMLElement):
    tag = "del"


class DETAILS(HTMLElement):
    tag = "details"


class DFN(HTMLElement):
    tag = "dfn"


class DIALOG(HTMLElement):
    tag = "dialog"


class DIR(HTMLElement):
    tag = "dir"


class DIV(HTMLElement):
    tag = "div"


class DL(HTMLElement):
    tag = "dl"


class DT(HTMLElement):
    tag = "dt"


class EDIASTREA(HTMLElement):
    tag = "ediastrea"


class ELEMENT(HTMLElement):
    tag = "element"


class EM(HTMLElement):
    tag = "em"


class EMBED(VoidElement):
    tag = "embed"


class FIELDSET(HTMLElement):
    tag = "fieldset"


class FIGCAPTION(HTMLElement):
    tag = "figcaption"


class FIGURE(HTMLElement):
    tag = "figure"


class FONT(HTMLElement):
    tag = "font"


class FOOTER(HTMLElement):
    tag = "footer"


class FORM(HTMLElement):
    tag = "form"


class FRAME(HTMLElement):
    tag = "frame"


class FRAMESET(HTMLElement):
    tag = "frameset"


class H1(HTMLElement):
    tag = "h1"


class H2(HTMLElement):
    tag = "h2"


class H3(HTMLElement):
    tag = "h3"


class H4(HTMLElement):
    tag = "h4"


class H5(HTMLElement):
    tag = "h5"


class H6(HTMLElement):
    tag = "h6"


class HEAD(HTMLElement):
    tag = "head"

    def __init__(self, *children):
        super().__init__(
            META(charset="utf-8"),
            META(name="viewport", content="width=device-width, initial-scale=1.0"),
            *children,
        )


class HEADER(HTMLElement):
    tag = "header"


class HGROUP(HTMLElement):
    tag = "hgroup"


class HR(VoidElement):
    tag = "hr"


class HTML(HTMLElement):
    tag = "html"

    def __init__(self, *args, doctype=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.doctype = doctype

    def render(self, context: dict) -> typing.Generator[str, None, None]:
        if self.doctype:
            yield "<!DOCTYPE html>"
        yield from super().render(context)


class I(HTMLElement):  # noqa
    tag = "i"


class IFRAME(HTMLElement):
    tag = "iframe"


class IMAGE(HTMLElement):
    tag = "image"


class IMG(VoidElement):
    tag = "img"


class INPUT(VoidElement):
    tag = "input"


class INS(HTMLElement):
    tag = "ins"


class ISINDEX(HTMLElement):
    tag = "isindex"


class KBD(HTMLElement):
    tag = "kbd"


class KEYGEN(VoidElement):
    tag = "keygen"


class LABEL(HTMLElement):
    tag = "label"


class LEGEND(HTMLElement):
    tag = "legend"


class LI(HTMLElement):
    tag = "li"


class LINK(VoidElement):
    tag = "link"


class LISTING(HTMLElement):
    tag = "listing"


class MAIN(HTMLElement):
    tag = "main"


class MAP(HTMLElement):
    tag = "map"


class MARK(HTMLElement):
    tag = "mark"


class MARQUEE(HTMLElement):
    tag = "marquee"


class MENU(HTMLElement):
    tag = "menu"


class MENUITEM(HTMLElement):
    tag = "menuitem"


class META(VoidElement):
    tag = "meta"


class METER(HTMLElement):
    tag = "meter"


class MULTICOL(HTMLElement):
    tag = "multicol"


class NAV(HTMLElement):
    tag = "nav"


class NEXTID(HTMLElement):
    tag = "nextid"


class NOBR(HTMLElement):
    tag = "nobr"


class NOEMBED(HTMLElement):
    tag = "noembed"


class NOFRAMES(HTMLElement):
    tag = "noframes"


class NOSCRIPT(HTMLElement):
    tag = "noscript"


class OBJECT(HTMLElement):
    tag = "object"


class OL(HTMLElement):
    tag = "ol"


class OPTGROUP(HTMLElement):
    tag = "optgroup"


class OPTION(HTMLElement):
    tag = "option"


class OUTPUT(HTMLElement):
    tag = "output"


class P(HTMLElement):
    tag = "p"


class PARAM(VoidElement):
    tag = "param"


class PICTURE(HTMLElement):
    tag = "picture"


class PLAINTEXT(HTMLElement):
    tag = "plaintext"


class PRE(HTMLElement):
    tag = "pre"


class PROGRESS(HTMLElement):
    tag = "progress"


class Q(HTMLElement):
    tag = "q"


class RB(HTMLElement):
    tag = "rb"


class RE(HTMLElement):
    tag = "re"


class RP(HTMLElement):
    tag = "rp"


class RT(HTMLElement):
    tag = "rt"


class RTC(HTMLElement):
    tag = "rtc"


class RUBY(HTMLElement):
    tag = "ruby"


class S(HTMLElement):
    tag = "s"


class SAMP(HTMLElement):
    tag = "samp"


class SCRIPT(HTMLElement):
    tag = "script"


class SECTION(HTMLElement):
    tag = "section"


class SELECT(HTMLElement):
    tag = "select"


class SHADOW(HTMLElement):
    tag = "shadow"


class SLOT(HTMLElement):
    tag = "slot"


class SMALL(HTMLElement):
    tag = "small"


class SOURCE(VoidElement):
    tag = "source"


class SPACER(HTMLElement):
    tag = "spacer"


class SPAN(HTMLElement):
    tag = "span"


class STRIKE(HTMLElement):
    tag = "strike"


class STRONG(HTMLElement):
    tag = "strong"


class STYLE(HTMLElement):
    tag = "style"


class SUB(HTMLElement):
    tag = "sub"


class SUMMARY(HTMLElement):
    tag = "summary"


class SUP(HTMLElement):
    tag = "sup"


class SVG(HTMLElement):
    tag = "svg"


class TABLE(HTMLElement):
    tag = "table"


class TBODY(HTMLElement):
    tag = "tbody"


class TD(HTMLElement):
    tag = "td"


class TEMPLATE(HTMLElement):
    tag = "template"


class TEXTAREA(HTMLElement):
    tag = "textarea"


class TFOOT(HTMLElement):
    tag = "tfoot"


class TH(HTMLElement):
    tag = "th"


class THEAD(HTMLElement):
    tag = "thead"


class TIME(HTMLElement):
    tag = "time"


class TITLE(HTMLElement):
    tag = "title"


class TR(HTMLElement):
    tag = "tr"


class TRACK(VoidElement):
    tag = "track"


class TT(HTMLElement):
    tag = "tt"


class U(HTMLElement):
    tag = "u"


class UL(HTMLElement):
    tag = "ul"


class VAR(HTMLElement):
    tag = "var"


class VIDEO(HTMLElement):
    tag = "video"


class WBR(VoidElement):
    tag = "wbr"


class XMP(HTMLElement):
    tag = "xmp"


def flatattrs(attributes: dict, context: dict) -> str:
    """Converts a dictionary to a string of HTML-attributes.
    Leading underscores are removed and other underscores are replaced with dashes."""

    attlist = []
    for key, value in attributes.items():
        value = resolve_lazy(value, context)
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


def merge_html_attrs(
    attrs: typing.Dict[str, typing.Any],
    newattrs: typing.Dict[str, typing.Any],
    separators: typing.Optional[typing.Dict[str, str]] = None,
):
    """
    Will try to merge two dictionaries with html attributes
    while preserving all values by concatenating them with the appropriate
    separators
    """
    if attrs is None:
        return newattrs
    if newattrs is None:
        return attrs
    separators = separators or {}
    ret = attrs
    for key, value in newattrs.items():
        ret = _append_attribute(ret, key, value, separators.get(key))
    return ret


def _append_attribute(
    attrs: dict, key: str, value: typing.Any, separator: typing.Optional[str] = None
):
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
    return attrs
