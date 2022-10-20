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

#ifndef __PJ_SIGN_H
#define __PJ_SIGN_H

#include "pj.h"



// ---------------------------------------------------------------------------------------------------------------------
// SigN
// ---------------------------------------------------------------------------------------------------------------------

typedef struct {
    PyObject_HEAD
    SigHeader h;
    TypeNum types[];
} SigN;


static void SigN_dealloc(SigN *self) {
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject * SigN_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    SigN *self;
    self = (SigN *) type->tp_alloc(type, 0);
    if (self != NULL) {

    }
    return (PyObject *) self;
}


static int SigN_init(SigN *self, PyObject *args, PyObject *kwds) {
    return 0;
}


static PyMemberDef SigN_members[] = {
//    {"first", T_OBJECT_EX, offsetof(SigN, first), 0, "first name"},
//    {"last", T_OBJECT_EX, offsetof(SigN, last), 0, "last name"},
//    {"number", T_INT, offsetof(Toy, number), 0, "custom number"},
    {NULL}
};


static PyMethodDef SigN_methods[] = {
//    {"has", (PyCFunction) Toy_has, METH_FASTCALL, "has(key)\n\nanswer if has key"},
//    {"atPut", (PyCFunction) Toy_atPut, METH_FASTCALL, "atPut(key, value)\n\nat key put value, answer self"},
//    {"atIfNone", (PyCFunction) Toy_atIfNone, METH_FASTCALL, "atIfNone(key, value, alt)\n\nanswer the value at key or alt if the key is absent"},
//    {"drop", (PyCFunction) Toy_drop, METH_FASTCALL, "drop(key)\n\ndrop value at key, answer self"},
//    {"count", (PyCFunction) Toy_count, METH_FASTCALL, "count()\n\nanswer the number of elements"},
//    {"numBuckets", (PyCFunction) Toy_numBuckets, METH_FASTCALL, "numBuckets()\n\nanswer the number of buckets"},
//    {"name", (PyCFunction) Toy_name, METH_NOARGS, "Return the name, combining the first and last name"},
    {NULL}
};


static PyTypeObject SigNCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "jones.SigN",
    .tp_doc = PyDoc_STR("Type signature of a 1 arg function"),
    .tp_basicsize = sizeof(SigN),
    .tp_itemsize = sizeof(TypeNum),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = SigN_new,
    .tp_init = (initproc) SigN_init,
    .tp_dealloc = (destructor) SigN_dealloc,
    .tp_members = SigN_members,
    .tp_methods = SigN_methods,
};



#endif