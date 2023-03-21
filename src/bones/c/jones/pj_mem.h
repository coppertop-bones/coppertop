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

#ifndef __PJ_MEM_H
#define __PJ_MEM_H

#include "pj.h"


// ---------------------------------------------------------------------------------------------------------------------
// free fns
// ---------------------------------------------------------------------------------------------------------------------

static PyObject * _toAddress(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 1) return _raiseWrongNumberOfArgs(__FUNCTION__, 1, nargs);
    return PyTuple_Pack(2, PyLong_FromVoidPtr(args[0]), PyLong_FromSize_t(args[0] -> ob_refcnt));
}

static PyObject * _toPtr(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 1) return _raiseWrongNumberOfArgs(__FUNCTION__, 1, nargs);
    return PyLong_FromVoidPtr(args[0]);
}

static PyObject * _pageSize(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 0) return _raiseWrongNumberOfArgs(__FUNCTION__, 0, nargs);
    return PyLong_FromLong(os_page_size());
}

static PyObject * _getCacheLineSize(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 0) return _raiseWrongNumberOfArgs(__FUNCTION__, 0, nargs);
    return PyLong_FromLong((long) os_cache_line_size());
}

static PyObject * _toObj(PyObject *mod, PyObject *args) {
    // could check that address is PyObject aligned
    PyObject *object;
    if (!PyArg_ParseTuple(args, "K", &object)) return NULL;
    Py_INCREF(object);
    return PyTuple_Pack(2, object, PyLong_FromSize_t(object -> ob_refcnt));
}

static PyObject * _ob_refcnt(PyObject *mod, PyObject *args) {
    PyObject *object;  jsize address;
    if (!PyArg_ParseTuple(args, "K", &address)) return NULL;
    object = (PyObject*) address;
    return PyLong_FromSize_t(object -> ob_refcnt);
}

static PyObject * _malloc(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 1) return _raiseWrongNumberOfArgs(__FUNCTION__, 1, nargs);
    // TODO raise a type error
    if (!PyLong_Check(args[0])) return NULL;        // jsize
    jsize size = (jsize) PyLong_AsSize_t(args[0]);
    void *p = malloc(size);
    return PyLong_FromVoidPtr(p);
}

static PyObject * _atU16(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    // for the given pointer to an array of u16 and the index get a u16

    if (nargs != 2) return _raiseWrongNumberOfArgs(__FUNCTION__, 2, nargs);
    // TODO raise a type error & check within bounds of u16
    if (!PyLong_Check(args[0])) return NULL;        // ptr
    if (!PyLong_Check(args[1])) return NULL;        // size_t index

    jsize index = PyLong_AsSize_t(args[1]);
    ju16 *pItem = ((ju16*) (PyLong_AsSize_t(args[0]) & B_PTR_MASK)) + index - 1;

    return PyLong_FromLong(*pItem);
}

static PyObject * _atU16Put(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    // for the given pointer to an array of u16, the index, set the bits given by the mask and value

    if (nargs != 4) return _raiseWrongNumberOfArgs(__FUNCTION__, 4, nargs);
    // TODO raise a type error & check within bounds of u16
    if (!PyLong_Check(args[0])) return NULL;        // ptr
    if (!PyLong_Check(args[1])) return NULL;        // jsize index
    if (!PyLong_Check(args[2])) return NULL;        // u16 bit mask
    if (!PyLong_Check(args[3])) return NULL;        // u16

    jsize index = PyLong_AsSize_t(args[1]);
    ju16 *pItem = ((ju16*) (PyLong_AsSize_t(args[0]) & B_PTR_MASK)) + index - 1;
    ju16 mask = (ju16) PyLong_AsLong(args[2]);           // OPEN check range before converting
    ju16 v = (ju16) PyLong_AsLong(args[3]);

    *pItem = (*pItem & (mask ^ 0xFFFF)) | (v & mask);
    return PyBool_FromLong(*pItem);
}

static PyObject * _atU8(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    // for the given pointer to an array of u8 and the index get a U8

    if (nargs != 2) return _raiseWrongNumberOfArgs(__FUNCTION__, 2, nargs);
    // TODO raise a type error & check within bounds of u16
    if (!PyLong_Check(args[0])) return NULL;        // ptr
    if (!PyLong_Check(args[1])) return NULL;        // jsize index

    jsize index = PyLong_AsSize_t(args[1]);
    ju8 *pItem = ((ju8*) (PyLong_AsSize_t(args[0]) & B_PTR_MASK)) + index - 1;

    return PyLong_FromLong(*pItem);
}

static PyObject * _atU8Put(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    // for the given pointer to an array of u8 and the index, set the bits given by the mask and value

    if (nargs != 4) return _raiseWrongNumberOfArgs(__FUNCTION__, 4, nargs);
    // TODO raise a type error & check within bounds of u8
    if (!PyLong_Check(args[0])) return NULL;        // ptr
    if (!PyLong_Check(args[1])) return NULL;        // jsize index
    if (!PyLong_Check(args[2])) return NULL;        // u8 bit mask
    if (!PyLong_Check(args[3])) return NULL;        // u8

    jsize index = (jsize) PyLong_AsSize_t(args[1]);
    ju8 *pItem = ((ju8*) (PyLong_AsSize_t(args[0]) & B_PTR_MASK)) + index - 1;
    ju8 mask = (ju8) PyLong_AsLong(args[2]);
    ju8 v = (ju8) PyLong_AsLong(args[3]);

    *pItem = (*pItem & (mask ^ 0xFF)) | (v & mask);
    return PyBool_FromLong(*pItem);
}



#endif