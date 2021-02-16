import collections


def resolve_lazy(value, context, element):
    """Shortcut to resolve a value in case it is a Lazy value"""

    while isinstance(value, Lazy):
        value = value.resolve(context, element)
    return value


def getattr_lazy(lazyobject, attr):
    """Takes a lazy object and returns a new lazy object which will resolve the attribute of the object"""
    return F(lambda c, e: getattr(resolve_lazy(lazyobject, c, e), attr))


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
            for accessor in self.value.split("."):
                if hasattr(context, accessor):
                    context = getattr(context, accessor)
                    context = context() if callable(context) else context
                elif hasattr(context, "get"):
                    context = context.get(accessor)
                else:
                    context = None

            return context
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
