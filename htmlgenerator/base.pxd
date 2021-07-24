
cdef class BaseElement(list):
    cdef str _try_render(self, object element, dict context)
    cpdef str render_children(self, dict context)
    cpdef str render(self, dict context)
    cpdef filter(self, filter_func)
    cpdef delete(self, filter_func)
    cpdef replace(self, select_func, replacement, all=*)
    cpdef copy(self)

cdef class If(BaseElement):
    cdef object condition

cdef class Iterator(BaseElement):
    cdef public object iterator
    cdef public str loopvariable
