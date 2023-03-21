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

#ifndef __COMMON_PY_H
#define __COMMON_PY_H

#include "Python.h"
#include "structmember.h"       // https://github.com/python/cpython/blob/main/Include/structmember.h
#include "_common.h"

typedef Py_ssize_t pyssize;


// PyExc_ValueError, PyExc_TypeError
#define PY_ASSERT_INT_WITHIN_CLOSED(variable, accessorDesc, lb, ub) \
    if (!((lb) <= (variable) && (variable) <= (ub))) { \
        char *s1, *s2, *s3; \
        asprintf (&s1, "%li", (ji64)(lb)); \
        asprintf (&s2, "%li", (ji64)(ub)); \
        asprintf (&s3, "%li", (ji64)(variable)); \
        char *msg = join_txts(12, __FUNCTION__, ": ", accessorDesc, " = ", s3, " but {", s1, " <= ", accessorDesc, " <= ", s2, "}"); \
        PyObject *answer =  PyErr_Format(JonesError, msg); \
        free(s1); \
        free(s2); \
        free(s3); \
        free(msg); \
        return answer; \
    }


#define TRAP_PY(src) \
    { \
        txt *retval = (src); \
        if (retval != NULL) { \
            PyObject *answer = PyErr_Format(JonesError, (const char *) retval); \
            free(retval); \
            return answer; \
        } \
    }


static PyObject * _raiseWrongNumberOfArgs(const char * fName, int numExpected, Py_ssize_t numGiven) {
    // https://pythonextensionpatterns.readthedocs.io/en/latest/exceptions.html
    // https://docs.python.org/3/library/stdtypes.html#old-string-formatting
    // https://docs.python.org/3/c-api/exceptions.html#c.PyErr_Format
    if (numExpected == 1) {
        return PyErr_Format(
            PyExc_TypeError,
             "%s takes 1 positional argument but %i were given",
             fName,
             numGiven
        );
    }
    else {
        if (numGiven == 1) {
            return PyErr_Format(
                PyExc_TypeError,
                 "%s takes %i positional arguments but 1 was given",
                 fName,
                 numExpected
            );
        }
        else {
            return PyErr_Format(
                PyExc_TypeError,
                 "%s takes %i positional arguments but %i were given",
                 fName,
                 numExpected,
                 numGiven
            );
        }
    }
}



#endif