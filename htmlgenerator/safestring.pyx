import html

import cython

# copied from django/utils/safestring.py in order to avoid a dependency only for the escaping-functionality
# this is condensed and doc-strings are removed, please read https://github.com/django/django/blob/master/django/utils/safestring.py for proper documentation


class SafeData:
    def __html__(self):
        return self


class SafeString(str, SafeData):
    def __add__(self, rhs):
        t = super().__add__(rhs)
        if isinstance(rhs, SafeData):
            return SafeString(t)
        return t

    def __str__(self):
        return self


def mark_safe(s):
    if hasattr(
        s, "__html__"
    ):  # instead of using isinstance we use __html__ because that is what some other frameworks use too
        return s
    return SafeString(s)


def conditional_escape(value):
    if hasattr(value, "__html__"):
        return value.__html__()
    else:
        return mark_safe(html.escape(str(value)))
