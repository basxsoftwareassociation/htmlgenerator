
cdef class BaseElement(list):
    cdef _try_render(self, element, context, stringify)
    cdef render_children(self, context, stringify=*)
    cpdef render(self, context, stringify=*)
    cdef filter(self, filter_func)
    cdef wrap(self, filter_func, wrapperelement)
    cdef delete(self, filter_func)
    cdef _replace(self, select_func, replacement, all=*)
    cdef copy(self)

cdef class If(BaseElement):
    cdef object condition

cdef class Iterator(BaseElement):
    cdef public object iterator
    cdef public str loopvariable
