cdef class Lazy:
    cpdef resolve(self, context, element)


cdef class ContextValue(Lazy):
    cdef str value


cdef class ContextFunction(Lazy):
    cdef object func

cdef resolve_lazy(value, context, element)
