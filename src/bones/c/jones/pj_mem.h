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