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

#ifndef __PJ_PLAY_H
#define __PJ_PLAY_H

#include "pj.h"



// ---------------------------------------------------------------------------------------------------------------------
// free fns
// ---------------------------------------------------------------------------------------------------------------------


typedef struct {
    PyObject_HEAD                   // ob_refcnt:Py_ssize_t, *ob_type:PyTypeObject
} Fred;


typedef struct {
    PyObject_VAR_HEAD                   // ob_refcnt:Py_ssize_t, *ob_type:PyTypeObject
} Joe;


static PyObject * _sizeofFredJoe(PyObject *mod, PyObject *const *args, Py_ssize_t nargs) {
    if (nargs != 0) return _raiseWrongNumberOfArgs(__FUNCTION__, 0, nargs);
    return PyTuple_Pack(2, PyLong_FromLong((long) sizeof(Fred)), PyLong_FromLong((long) sizeof(Joe)));
}


static PyObject * _execShell(PyObject *mod, PyObject *args) {
    const char *command;  int ret;
    if (!PyArg_ParseTuple(args, "s", &command)) return NULL;
    ret = system(command);
    if (ret < 0) {
        PyErr_SetString(JonesError, "System command failed");
        return NULL;
    }
    return PyLong_FromLong(ret);
}



#endif