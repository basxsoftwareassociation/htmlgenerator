import black
from bs4 import BeautifulSoup, Comment, Doctype, NavigableString, Tag

# be aware: attributes with the empty string as value will be converted
# to empty attributes which is okay since it does not alter behaviour
# (https://html.spec.whatwg.org/multipage/syntax.html#attributes-2)

INDENT = "    "


def multiline(s):
    if '"""' not in s:
        if s.endswith('"'):
            s = s[:-1] + "\\" + s[-1]  # this will likely not work well...
        return f'r"""{s}"""'
    if "'''" not in s:
        if s.endswith('"'):
            s = s[:-1] + "\\" + s[-1]  # this will likely not work well...
        return f"r'''{s}'''"
    raise RuntimeError(
        f"""
The following string could not be escaped.
Please open an issue on https://github.com/basxsoftwareassociation/htmlgenerator/issues
{s}
"""
    )


def marksafestring(func):
    def wrapper(s):
        ret = func(s)
        return f"s({ret})" if ret else ret

    return wrapper


@marksafestring
def escapestring(s):
    s = s.replace("\\", "\\\\")  # escape backslashes
    if not s:
        return ""
    if "\n" in s:
        return multiline(s)
    if '"' not in s:
        return f'r"{s}"'
    if "'" not in s:
        return f"r'{s}'"
    return multiline(s)


def convert(tag, level=0):
    indent = INDENT * level
    if isinstance(tag, Doctype):
        return [indent + f's("<!DOCTYPE {tag}>")']
    if isinstance(tag, Comment):
        if tag.strip():
            ret = []
            for line in tag.splitlines():
                if line.split():
                    ret.append(indent + f"# {line}")
            return ret
        return []
    if isinstance(tag, NavigableString):
        return [indent + escapestring(tag)]
    if isinstance(tag, Tag):
        ret = [indent + f"hg.{tag.name.upper()}("]
        attrs = []
        for key, value in tag.attrs.items():
            if isinstance(
                value, list
            ):  # for multivalued attributes, see beautifullsoup docs
                value = ' + " " + '.join(escapestring(v) for v in value)
            elif value == "":
                value = "True"
            else:
                value = escapestring(value)
            if key in (
                "class",
                "for",
                "async",
            ):  # handling reserved python keywords, see htmlgenerator docs
                key = "_" + key
            key = key.replace("-", "_")
            attrs.append(f"{key}={value}")
        for subtag in tag.children:
            subcontent = convert(subtag, level + 1)
            if subcontent:
                if subcontent[-1].strip():
                    subcontent[-1] += ","
                ret.extend(subcontent)
        ret.append(indent + INDENT + ", ".join(attrs))

        ret.append(indent + ")")
        return ret


def converthtml(html, formatting):
    out = [
        "import htmlgenerator as hg",
        "from htmlgenerator import mark_safe as s",
        "html = hg.BaseElement(",
    ]

    soup = BeautifulSoup(html, "lxml")
    for subtag in soup.contents:
        tags = convert(subtag, 1)
        if tags:
            if tags[-1].strip():
                tags[-1] += ","
            out.extend(tags)
    out.append(")\n")

    htmlstr = "\n".join(filter(lambda line: bool(line.strip()), out))
    if not formatting:
        return htmlstr
    return black.format_file_contents(htmlstr, fast=True, mode=black.FileMode())


def main():
    import sys

    formatflag = "--no-formatting"

    files = sys.argv[1:]
    formatting = formatflag not in files
    if formatflag in files:
        files.remove(formatflag)
    if not files:
        print(converthtml(sys.stdin.read(), formatting), end="")
    for _file in files:
        with open(_file) as rf:
            with open(_file + ".py", "w") as wf:
                wf.write(converthtml(rf.read(), formatting))


if __name__ == "__main__":
    main()
