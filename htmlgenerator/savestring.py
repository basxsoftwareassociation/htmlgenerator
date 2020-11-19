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
    if hasattr(s, "__html__"):
        return s
    return SafeString(s)
