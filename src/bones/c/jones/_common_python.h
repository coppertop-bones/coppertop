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