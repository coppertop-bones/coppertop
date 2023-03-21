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

#ifndef __PY_JONES_H
#define __PY_JONES_H

#define PY_SSIZE_T_CLEAN

#include "_common_python.h"
#include "j_all.h"


typedef struct {
    PyObject_VAR_HEAD
} Base;

typedef struct {
    Base Base;
    PyObject *name;
    PyObject *bmod;
    PyObject *d;            // dispatcher
    PyObject *TBCSentinel;
} Fn;

typedef struct {
    Fn Fn;
    ju8 num_tbc;            // the number of arguments missing in the args array
                            // pad48
    PyObject *pipe1;        // 1st piped arg for binaries and ternaries
    PyObject *pipe2;        // 2nd piped arg for ternaries
    PyObject *args[];
} Partial;




static PyObject *JonesError;
static PyObject *JonesSyntaxError;


#endif
