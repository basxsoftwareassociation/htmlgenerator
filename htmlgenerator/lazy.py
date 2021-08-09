from __future__ import annotations

import inspect
import typing

import htmlgenerator


def resolve_lazy(value: typing.Any, context: dict):
    """Shortcut to resolve a value in case it is a Lazy value"""

    while isinstance(value, Lazy):
        value = value.resolve(context)
    return value


def getattr_lazy(lazyobject: Lazy, attr: str) -> F:
    """Takes a lazy object and returns a new lazy object which will resolve the attribute on the object"""

    def wrapper(c, e):
        ret = getattr(resolve_lazy(lazyobject, c, e), attr)
        return ret() if callable(ret) else ret

    return F(wrapper)


def resolve_lookup(
    context: dict, lookup: str, call_functions: bool = True
) -> typing.Any:
    """
    Helper function to extract a value out of a context-dict.
    A lookup string can access attributes, dict-keys, methods without parameters and indexes by using the dot-accessor (e.g. ``person.name``)
    This is based on the implementation of the variable lookup of the django template system:
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
                    pass  # but we continue because we might use an attribute on the object instead of calling it
                else:
                    raise

    return current


class Lazy:
    """Lazy values will be evaluated at render time via the resolve method."""

    def resolve(self, context: dict) -> typing.Any:
        raise NotImplementedError("Lazy needs to be subclassed")


class ContextValue(Lazy):
    def __init__(self, value: str):
        self.value = value

    def resolve(self, context: dict) -> typing.Any:
        return resolve_lookup(context, self.value)


class ContextFunction(Lazy):
    """Call a function a render time, usefull for calculation of more complex"""

    def __init__(
        self, func: typing.Callable[[dict, "htmlgenerator.BaseElement"], typing.Any]
    ):
        assert callable(func), "ContextFunction needs to be callable"
        self.func = func

    def resolve(self, context: dict) -> typing.Any:
        return self.func(context)


C = ContextValue
F = ContextFunction
