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

#ifndef __PY_VMEM_ARENA_H
#define __PY_VMEM_ARENA_H

#include "pj.h"


static VA *g_va;

static PyObject * _reserve(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    VA *va; jsize numpages, pChunk;

    if (nargs != 2) return _raiseWrongNumberOfArgs(__FUNCTION__, 2, nargs);
    // TODO raise a type error & check within bounds of u16
    if (!PyLong_Check(args[0])) return NULL;        // ptr
    if (!PyLong_Check(args[1])) return NULL;        // u16 index

    va = (VA*) PyLong_AsLong(args[0]);
    numpages = (jsize) PyLong_AsLong(args[1]);
    pChunk = (jsize) reserve(va, numpages);
    return PyLong_FromLong(pChunk);
}

static PyObject * _getVaPtr(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 0) return _raiseWrongNumberOfArgs(__FUNCTION__, 0, nargs);
    return PyLong_FromLong((long) g_va);
}



#endif