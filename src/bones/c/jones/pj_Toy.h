// ---------------------------------------------------------------------------------------------------------------------
//
//                             Copyright (c) 2022 David Briant. All rights reserved.
//
// Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
// following conditions are met:
//
// 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the
//    following disclaimer.
//
// 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
//    following disclaimer in the documentation and/or other materials provided with the distribution.
//
// 3. All advertising materials mentioning features or use of this software must display the following
//    acknowledgement:
//          This product includes software developed by <the copyright holders>.
//
// 4. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
//    products derived from this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
// INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
// SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
// SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
// OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
// ---------------------------------------------------------------------------------------------------------------------

#ifndef __PJ_TOY_H
#define __PJ_TOY_H

#include "pj.h"





// https://llllllllll.github.io/c-extension-tutorial/fancy-argument-parsing.html
// http://web.mit.edu/people/amliu/vrut/python/ext/parseTuple.html
// https://docs.activestate.com/activepython/3.8/python/c-api/structures.html#c._PyCFunctionFast



typedef struct {
    PyObject_HEAD                   // ob_refcnt:Py_ssize_t, *ob_type:PyTypeObject
    PyObject *first;                // first name
    PyObject *last;                 // last name
    ji32 number;
    khash_t(hm_u32_u8) *h;          // (u32**u8)&hashmap
} Toy;


static void Toy_dealloc(Toy *self) {
    kh_destroy(hm_u32_u8, self->h);       // deallocate the hash table
    Py_XDECREF(self->first);
    Py_XDECREF(self->last);
    Py_TYPE(self)->tp_free((PyObject *) self);
}


static PyObject * Toy_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    Toy *self;
    self = (Toy *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->first = PyUnicode_FromString("");         // ref count will be 1
        if (self->first == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->last = PyUnicode_FromString("");
        if (self->last == NULL) {
            Py_DECREF(self);
            return NULL;
        }
        self->number = 0;
        self->h = kh_init(hm_u32_u8);     // allocate the hash table
    }
    return (PyObject *) self;
}


static int Toy_init(Toy *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {"first", "last", "number", NULL};
    PyObject *first = NULL, *last = NULL, *old;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOi", kwlist, &first, &last, &self->number)) return -1;

    if (first) {
        old = self->first;
        Py_INCREF(first);               // we also own a ref to first
        self->first = first;
        Py_XDECREF(old);
    }
    if (last) {
        old = self->last;
        Py_INCREF(last);
        self->last = last;
        Py_XDECREF(old);
    }
    return 0;
}


static PyMemberDef Toy_members[] = {
    {"first", T_OBJECT_EX, offsetof(Toy, first), 0, "first name"},
    {"last", T_OBJECT_EX, offsetof(Toy, last), 0, "last name"},
    {"number", T_INT, offsetof(Toy, number), 0, "custom number"},
    {NULL}
};


static PyObject * Toy_name(Toy *self, PyObject *Py_UNUSED(ignored)) {
    if (self->first == NULL) {
        PyErr_SetString(PyExc_AttributeError, "first");
        return NULL;
    }
    if (self->last == NULL) {
        PyErr_SetString(PyExc_AttributeError, "last");
        return NULL;
    }
    return PyUnicode_FromFormat("%S %S", self->first, self->last);
}


static PyObject * Toy_has(Toy *self, PyObject *const *args, Py_ssize_t nargs) {
    khint_t it;  int exists;  int k;
    if (nargs != 1) return _raiseWrongNumberOfArgs(__FUNCTION__, 1, nargs);
    if (!PyLong_Check(args[0])) return NULL;        // TODO raise a type error
    k = (int) PyLong_AsLong(args[0]);
//    if (!PyArg_ParseTuple(args, "I", &key)) return NULL;
    it = kh_get(hm_u32_u8, self->h, k);                 // find key or end
    exists = (it != kh_end(self->h));
    return PyBool_FromLong(exists);
}


static PyObject * Toy_atIfNone(Toy *self, PyObject *const *args, Py_ssize_t nargs) {
    khint_t it;  int k;
    if (nargs != 2) return _raiseWrongNumberOfArgs(__FUNCTION__, 2, nargs);
    if (!PyLong_Check(args[0])) return NULL;        // TODO raise a type error
    k = (int) PyLong_AsLong(args[0]);
    it = kh_get(hm_u32_u8, self->h, k);                  // find key or end
    if (it == kh_end(self->h))
        return args[1];
    else
        return PyLong_FromLong(kh_value(self->h, it));
}


static PyObject * Toy_atPut(Toy *self, PyObject *const *args, Py_ssize_t nargs) {
    khint_t it;  int ret;  int k;  int v;
    if (nargs != 2) return _raiseWrongNumberOfArgs(__FUNCTION__, 2, nargs);
    if (!PyLong_Check(args[0])) return NULL;        // TODO raise a type error
    if (!PyLong_Check(args[1])) return NULL;        // TODO raise a type error
    k = (int) PyLong_AsLong(args[0]);
    v = (int) PyLong_AsLong(args[1]);

    it = kh_put(hm_u32_u8, self->h, k, &ret);            // find key or insert
    if (ret == -1) return NULL;
    kh_value(self->h, it) = v;                      // set the value

    Py_INCREF(self);
    return (PyObject *) self;
}


static PyObject * Toy_drop(Toy *self, PyObject *const *args, Py_ssize_t nargs) {
    khint_t it;  int k;
    if (nargs != 1) return _raiseWrongNumberOfArgs(__FUNCTION__, 1, nargs);
    if (!PyLong_Check(args[0])) return NULL;            // TODO raise a type error
    k = (int) PyLong_AsLong(args[0]);

    it = kh_get(hm_u32_u8, self->h, k);                 // find key or end
    if (it != kh_end(self->h))
        kh_del(hm_u32_u8, self->h, it);                 // TODO raise error if absent?

    // https://docs.python.org/3/extending/extending.html#ownership-rules
    // "The object reference returned from a C function that is called from Python must be an owned reference"
    Py_INCREF(self);
    return (PyObject *) self;
}


static PyObject * Toy_count(Toy *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 0) return _raiseWrongNumberOfArgs(__FUNCTION__, 0, nargs);
    return PyLong_FromLong(kh_size(self->h));
}


static PyObject * Toy_numBuckets(Toy *self, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 0) return _raiseWrongNumberOfArgs(__FUNCTION__, 0, nargs);
    return PyLong_FromLong(kh_n_buckets(self->h));
}


static PyMethodDef Toy_methods[] = {
    {"has", (PyCFunction) Toy_has, METH_FASTCALL, "has(key)\n\nanswer if has key"},
    {"atPut", (PyCFunction) Toy_atPut, METH_FASTCALL, "atPut(key, value)\n\nat key put value, answer self"},
    {"atIfNone", (PyCFunction) Toy_atIfNone, METH_FASTCALL, "atIfNone(key, value, alt)\n\nanswer the value at key or alt if the key is absent"},
    {"drop", (PyCFunction) Toy_drop, METH_FASTCALL, "drop(key)\n\ndrop value at key, answer self"},
    {"count", (PyCFunction) Toy_count, METH_FASTCALL, "count()\n\nanswer the number of elements"},
    {"numBuckets", (PyCFunction) Toy_numBuckets, METH_FASTCALL, "numBuckets()\n\nanswer the number of buckets"},
    {"name", (PyCFunction) Toy_name, METH_NOARGS, "Return the name, combining the first and last name"},
    {NULL}
};


static PyTypeObject ToyCls = {
     PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "jones.Toy",
    .tp_doc = PyDoc_STR("a Toy to play with"),
    .tp_basicsize = sizeof(Toy),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = Toy_new,                                      // was PyType_GenericNew
    .tp_init = (initproc) Toy_init,
    .tp_dealloc = (destructor) Toy_dealloc,
    .tp_members = Toy_members,
    .tp_methods = Toy_methods,
};



#endif