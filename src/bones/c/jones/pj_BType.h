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

#ifndef __PJ_BTYPE_H
#define __PJ_BTYPE_H

#include "pj.h"


typedef struct {
    PyObject_HEAD
    TypeNum TN1;
    TypeNum TN2;
} BType;


static void BType_dealloc(BType *self) {
    Py_TYPE(self)->tp_free((PyObject *) self);
}


static PyObject * BType_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    BType *self = (BType *) type->tp_alloc(type, 0);
    if (self != NULL) {
        self->TN1 = 0;
        self->TN2 = 0;
    }
    return (PyObject *) self;
}


static int BType_init(BType *self, PyObject *args, PyObject *kwds) {
    static char *kwlist[] = {"id", NULL};
    ji32 id;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|i", kwlist, &id)) return -1;
    self->TN1 = id & 0xFFFF;
    self->TN2 = (id & 0xFFFF0000) >> 16;
    return 0;
}


static PyMemberDef BType_members[] = {
    {"TN1", T_USHORT, offsetof(BType, TN1), 0, "custom number"},
    {"TN2", T_USHORT, offsetof(BType, TN2), 0, "custom number"},
    {NULL}
};


static PyMethodDef BType_methods[] = {
    {NULL}
};


static PyTypeObject BTypeCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "jones.BType",
    .tp_doc = PyDoc_STR("a BType to play with"),
    .tp_basicsize = sizeof(BType),
    .tp_itemsize = 0,
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    .tp_new = BType_new,
    .tp_init = (initproc) BType_init,
    .tp_dealloc = (destructor) BType_dealloc,
    .tp_members = BType_members,
    .tp_methods = BType_methods,
};


#endif