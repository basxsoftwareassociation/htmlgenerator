from __future__ import annotations

import inspect
import typing
import warnings


def resolve_lazy(value: typing.Any, context: dict):
    """Shortcut to resolve a value in case it is a Lazy value"""

    while isinstance(value, Lazy):
        value = value.resolve(context)
    return value


def resolve_lookup(
    context: dict, lookup: str, call_functions: bool = True
) -> typing.Any:
    """
    Helper function to extract a value out of a context-dict.
    A lookup string can access attributes, dict-keys, methods without
    parameters and indexes by using the dot-accessor (e.g. ``person.name``)
    This is based on the implementation of the variable lookup of the django
    template system:
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
                    # but we continue because we might use an attribute on the
                    # object instead of calling it
                    pass
                else:
                    raise

    return current


class Lazy:
    """Lazy values will be evaluated at render time via the resolve method."""

    def __getattr__(self, name):
        return ContextFunction(lambda c: getattr(self.resolve(c), name))

    def __call__(self, *args, **kwargs):
        def resolve_call(context):
            value = self.resolve(context)
            # value should in theory always be callable
            # however, older versions of htmlgenerator
            # use resolve_lookup which will try to call
            # any attributes it encounters
            # __callable__ marks this object as callable
            # and will therefore be called inside resolve_lookup
            # even though the resolved value is not callable
            if callable(value):
                return value(*args, **kwargs)
            return value

        return ContextFunction(resolve_call)

    def __getitem__(self, name):
        return ContextFunction(lambda c: self.resolve(c)[name])

    def resolve(self, context: dict) -> typing.Any:
        raise NotImplementedError("Lazy needs to be subclassed")


class ContextValue(Lazy):
    def __init__(self, value: str):
        self.value = value

    def resolve(self, context: dict) -> typing.Any:
        if isinstance(self.value, str):
            return resolve_lookup(context, self.value)
        return self.value


class ContextFunction(Lazy):
    """Call a function a render time, usefull for calculation of more complex"""

    def __init__(self, func: typing.Callable[[dict], typing.Any]):
        assert callable(func), "ContextFunction needs to be callable"
        self.func = func

    def resolve(self, context: dict) -> typing.Any:
        return self.func(context)


C = ContextValue
F = ContextFunction


def getattr_lazy(lazyobject: Lazy, attr: str) -> F:
    """
    Takes a lazy object and returns a new lazy object which will
    resolve the attribute on the object
    """
    warnings.warn(
        "getattr_lazy should no longer be used. Lazy objects support "
        "now direct access to attributes of lazy objects"
    )

    def wrapper(c):
        ret = getattr(resolve_lazy(lazyobject, c), attr)
        return ret() if callable(ret) else ret

    return F(wrapper)
