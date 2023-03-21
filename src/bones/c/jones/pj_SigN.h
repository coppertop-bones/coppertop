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