import collections
from inspect import signature


def resolve_lazy(value, context, element):
    """Shortcut to resolve a value in case it is a Lazy value"""

    while isinstance(value, Lazy):
        value = value.resolve(context, element)
    return value


def getattr_lazy(lazyobject, attr):
    """Takes a lazy object and returns a new lazy object which will resolve the attribute of the object"""
    return F(lambda c, e: getattr(resolve_lazy(lazyobject, c, e), attr))


def extractfromcontext(context, accessorstr):
    """Helper function to extract a value out of a context-dict
    An accessorstr can access attributes, dict-keys and methods without paremeters.
    Example: extractfromcontext({"data": {"colors": ("RED", "GREEN", "BLUE")}, "data.colors.__len__") would return 3
    """
    for accessor in accessorstr.split("."):
        if hasattr(context, accessor):
            context = getattr(context, accessor)
            context = (
                context()
                if (callable(context) and len(signature(context).parameters) == 0)
                else context
            )
        elif hasattr(context, "get"):
            context = context.get(accessor)
        else:
            context = None

    return context


class Lazy:
    """Lazy values will be evaluated at render time via the resolve method."""

    def resolve(self, context, element):
        raise NotImplementedError("Lazy needs to be subclassed")


class ContextValue(Lazy):
    def __init__(self, value):
        assert isinstance(
            value, collections.Hashable
        ), "ContextValue needs to be hashable"
        self.value = value

    def resolve(self, context, element):
        if isinstance(self.value, str):
            return extractfromcontext(context, self.value)
        return context[self.value]


class ContextFunction(Lazy):
    """Call a function a render time, usefull for calculation of more complex """

    def __init__(self, func):
        assert callable(func), "ContextFunction needs to be callable"
        self.func = func

    def resolve(self, context, element):
        return self.func(context, element)


C = ContextValue
F = ContextFunction
