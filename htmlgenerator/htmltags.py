import typing

from .base import BaseElement
from .lazy import Lazy, resolve_lazy


class HTMLElement(BaseElement):
    """The base for all HTML tags."""

    tag: str = ""

    def __init__(
        self, *children, lazy_attributes: typing.Optional[Lazy] = None, **attributes
    ):
        assert self.tag != ""
        self.attributes: dict = attributes
        super().__init__(*children)
        if lazy_attributes and not isinstance(lazy_attributes, Lazy):
            raise ValueError(
                f"Argument 'lazy_attributes' must have type 'Lazy' but has type {type(lazy_attributes)}"
            )
        self.lazy_attributes = lazy_attributes

    def render(self, context: dict) -> typing.Generator[str, None, None]:
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
        yield f"<{self.tag}{attr_str}>"
        yield from super().render_children(context)
        yield f"</{self.tag}>"

    # mostly for debugging purposes
    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            + ", ".join(
                [str(self.attributes), f"{len(self)} children"],
            )
            + ")"
        )


class VoidElement(HTMLElement):
    """Wrapper for elements without a closing tag, cannot have children"""

    # does not accept children
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def render(self, context) -> typing.Generator[str, None, None]:
        yield f"<{self.tag} {flatattrs(self.attributes, context, self)} />"


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


def flatattrs(attributes: dict, context: dict, element: BaseElement) -> str:
    """Converts a dictionary to a string of HTML-attributes.
    Leading underscores are removed and other underscores are replaced with dashes."""

    attlist = []
    for key, value in attributes.items():
        value = resolve_lazy(value, context, element)
        if isinstance(value, BaseElement):
            # in order to use e.g. an If element to disable the attribute
            # we check whether the render result is empty
            # (e.g. when we have only an If element which returns None in one branch)
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
