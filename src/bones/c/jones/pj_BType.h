// ---------------------------------------------------------------------------------------------------------------------
//
//                             Copyright (c) 2022 David Briant. All rights reserved.
//
// Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance
// with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software distributed under the License is distributed
// on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for
// the specific language governing permissions and limitations under the License.
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