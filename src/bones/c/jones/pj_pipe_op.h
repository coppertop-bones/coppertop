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

#ifndef __PJ_PIPE_OP_H
#define __PJ_PIPE_OP_H

#include "pj.h"



// we could use NULL as a sentinel instead of _? - nice idea but we still need to detect if an object represents the missing object
// bmod should be a dispatcher attribute? we would use it in error messages and repr, the python module is really
// about where the function came from, but the

// tp_alloc inits refcnt to 1

// https://tenthousandmeters.com/blog/python-behind-the-scenes-6-how-python-object-system-works/

// https://peps.python.org/pep-3123/ on making PyObject C standard compliant

//call maps to tp_call
// https://docs.python.org/3/c-api/call.html
// http://etutorials.org/Programming/Python+tutorial/Part+V+Extending+and+Embedding/Chapter+24.+Extending+and+Embedding+Classic+Python/24.1+Extending+Python+with+Pythons+C+API/

// https://docs.python.org/3/c-api/unicode.html#c.PyUnicode_FromFormat
// https://github.com/codie3611/Python-C-API-Advanced-Examples/tree/master/example1_single-inheritance

// https://docs.python.org/3/c-api/typeobj.html#type-objects
// https://docs.python.org/3/c-api/call.html
// https://docs.python.org/3/c-api/tuple.html
// https://docs.python.org/3/c-api/typeobj.html#number-object-structures


// https://docs.python.org/3/c-api/call.html - describes the call protocols
// PyObject_CallMethodNoArgs
// PyObject_CallMethodOneArg
// PyObject_CallFunctionObjArgs()

//define Py_REFCNT(ob)           (((PyObject*)(ob))->ob_refcnt)
//#define Py_TYPE(ob)             (((PyObject*)(ob))->ob_type)
//#define Py_SIZE(ob)             (((PyVarObject*)(ob)

//    if (PyErr_Occurred()) { return -1;}

// PERFORMANCE NOTE - should be able to borrow a tuple when piping, mutate it (!!!) and catch the syntax error - should
// not mutate clients but only tuples owned in this module, PyObject_CallObject - for moment temporarily mutate partial




// https://stackoverflow.com/questions/1104823/python-c-extension-method-signatures-for-documentation
// https://github.com/MSeifert04/iteration_utilities/tree/master/src/iteration_utilities/_iteration_utilities



#define MAX_ARGS 16

#define IS_FN(p) ((p) == &NullaryCls || (p) == &UnaryCls || (p) == &BinaryCls || (p) == &TernaryCls || (p) == &RauCls)
#define IS_PARTIAL(p) ((p) == &PNullaryCls || (p) == &PUnaryCls || (p) == &PBinaryCls || (p) == &PTernaryCls || (p) == &PRauCls)
#define NotYetImplemented PyExc_NotImplementedError
#define ProgrammerError PyExc_Exception


static PyTypeObject NullaryCls;
static PyTypeObject UnaryCls;
static PyTypeObject BinaryCls;
static PyTypeObject TernaryCls;
static PyTypeObject RauCls;

static PyTypeObject PNullaryCls;
static PyTypeObject PUnaryCls;
static PyTypeObject PBinaryCls;
static PyTypeObject PTernaryCls;
static PyTypeObject PRauCls;

static int Partial_initFromFn(
    Partial *self, PyObject *name, PyObject *bmod, PyObject *d, PyObject *TBCSentinel, ju8 num_tbc,
    PyObject *pipe1, PyObject *args[]
);




static PyObject * _nullary_nb_rshift(PyObject *, PyObject *);
static PyObject * _pnullary_nb_rshift(PyObject *, PyObject *);
static PyObject * _unary_nb_rshift(PyObject *, PyObject *);
static PyObject * _punary_nb_rshift(PyObject *, PyObject *);
static PyObject * _binary_nb_rshift(PyObject *, PyObject *);
static PyObject * _pbinary_nb_rshift(PyObject *, PyObject *);
static PyObject * _ternary_nb_rshift(PyObject *, PyObject *);
static PyObject * _pternary_nb_rshift(PyObject *, PyObject *);
static PyObject * _rau_nb_rshift(PyObject *, PyObject *);
static PyObject * _prau_nb_rshift(PyObject *, PyObject *);



// nullary pipe dispatch


static PyObject * _nullary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);
    if (tLhs == &NullaryCls) {
        Fn *fn = (Fn*) lhs;
        return PyErr_Format(PyExc_SyntaxError, "Arguments cannot by piped into nullary style fn %s.%s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    }
    else if (tRhs == &NullaryCls) {
        Fn *fn = (Fn*) rhs;
        return PyErr_Format(PyExc_SyntaxError, "Arguments cannot by piped into nullary style fn %s.%s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    }
    else
        return PyErr_Format(ProgrammerError, "_nullary_nb_rshift - unhandled case");
}


static PyObject * _pnullary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);
    if (tLhs == &PNullaryCls) {
        Fn *fn = (Fn*) lhs;
        return PyErr_Format(PyExc_SyntaxError, "Arguments cannot by piped into nullary style fn %s.%s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    }
    else if (tRhs == &PNullaryCls) {
        Fn *fn = (Fn*) rhs;
        return PyErr_Format(PyExc_SyntaxError, "Arguments cannot by piped into nullary style fn %s.%s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    }
    else
        return PyErr_Format(ProgrammerError, "_pnullary_nb_rshift - unhandled case");
}



// important check lhs first to catch errors

// unary pipe dispatch
//
// 1) _unary >> argN        - syntax error
// 2) _punary >> argN       - syntax error
// 3) pipe1 >> _unary       - dispatch, arg1 cannot be a class from this module as it would already have been piped
// 4) pipe1 >> _punary      - dispatch, arg1 cannot be a class from this module as it would already have been piped


static PyObject * _unary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);

    if (tLhs == &UnaryCls) {
        if (tRhs == &UnaryCls);             // falls through to the below
        else if (tRhs == &PUnaryCls) return _punary_nb_rshift(lhs, rhs);
        else if (tRhs == &BinaryCls) return _binary_nb_rshift(lhs, rhs);
        else if (tRhs == &PBinaryCls) return _pbinary_nb_rshift(lhs, rhs);
        else if (tRhs == &TernaryCls) return _ternary_nb_rshift(lhs, rhs);
        else if (tRhs == &PTernaryCls) return _pternary_nb_rshift(lhs, rhs);
        else {
            // 1. _unary >> argN - syntax error
            Fn *fn = (Fn*) lhs;
            return PyErr_Format(PyExc_SyntaxError, "First arg to unary style fn %s.%s must be piped from the left", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
        }
    }
    if (tRhs == &UnaryCls) {
        // 3. arg1 >> _unary - dispatch, arg1 cannot be a class from this module as it would already have been piped
        Fn *fn = (Fn*) rhs;
        return PyObject_CallOneArg(fn->d, lhs);
    }
    else
        return PyErr_Format(ProgrammerError, "_unary_nb_rshift - unhandled case");
}


static PyObject * _punary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);

    if (tLhs == &PUnaryCls) {
        if (tRhs == &UnaryCls) return _unary_nb_rshift(lhs, rhs);
        else if (tRhs == &PUnaryCls);       // falls through to the below
        else if (tRhs == &BinaryCls) return _binary_nb_rshift(lhs, rhs);
        else if (tRhs == &PBinaryCls) return _pbinary_nb_rshift(lhs, rhs);
        else if (tRhs == &TernaryCls) return _ternary_nb_rshift(lhs, rhs);
        else if (tRhs == &PTernaryCls) return _pternary_nb_rshift(lhs, rhs);
        else {
            // 2. _punary >> argN - syntax error
            Partial *partial = (Partial *) lhs;
            return PyErr_Format(PyExc_SyntaxError, "First arg to unary style partial fn %s.%s must be piped from the left", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
        }
    }
    if (tRhs == &PUnaryCls) {
        // 4. pipe1 >> _punary - dispatch, arg1 cannot be a class from this module as it would already have been piped
        // PyObject_CallObject
        Partial * partial = (Partial *) rhs;
        if (partial->num_tbc > 1)
            return PyErr_Format(PyExc_SyntaxError, "Trying to pipe an argument into unary style partial fn %s.%s that needs a total of %u more arguments", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name), partial->num_tbc);
        // this should not be called re-entrantly but we can't stop it - so detect and throw as it would be hard to debug
        int iPipe1 = 32;
        Py_ssize_t num_args = Py_SIZE(partial);
        for (Py_ssize_t o=0; o < num_args; o++) {
            if (partial->args[o] == partial->Fn.TBCSentinel) {
                iPipe1 = o;
                break;
            }
        }
        if (iPipe1 == 32) return PyErr_Format(PyExc_SyntaxError, "Can't find the slot for the piped argument - check that unary style partial fn %s.%s has not been reentrantly called", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
        partial->args[iPipe1] = lhs;
        PyObject * result = PyObject_Vectorcall(partial->Fn.d, partial->args, num_args, NULL);
        partial->args[iPipe1] = partial->Fn.TBCSentinel;
        return result;
    }
    else
        return PyErr_Format(ProgrammerError, "_punary_nb_rshift - unhandled case");
}



// binary pipe dispatch
//
// 1. _binary >> arg2      - syntax error
// 2. _pbinary >> arg2     - dispatch
// 3. arg1 >> _binary      - create a partial that can pipe one more argument
// 4. arg1 >> _pbinary     - check this is the first arg, then create a partial that can pipe one more argument


static PyObject * _binary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);

    if (tLhs == &BinaryCls) {
        if (tRhs == &UnaryCls) return _unary_nb_rshift(lhs, rhs);
        else if (tRhs == &PUnaryCls) return _punary_nb_rshift(lhs, rhs);
        else if (tRhs == &BinaryCls);       // falls through to the below
        else if (tRhs == &PBinaryCls) return _pbinary_nb_rshift(lhs, rhs);
        else if (tRhs == &TernaryCls) return _ternary_nb_rshift(lhs, rhs);
        else if (tRhs == &PTernaryCls) return _pternary_nb_rshift(lhs, rhs);
        else {
            // 1. _binary >> argN
            Fn *fn = (Fn *) lhs;
            return PyErr_Format(PyExc_SyntaxError, "First arg to binary style fn %s.%s must be piped from the left", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
        }
    }
    if (tRhs == &BinaryCls) {
        // 3. arg1 >> _binary - create a partial that can pipe one more argument
        Partial *partial = (Partial *) ((&PBinaryCls)->tp_alloc(&PBinaryCls, 0));       // 0 as don't need to catch any args
        if (partial == NULL) Py_RETURN_NOTIMPLEMENTED;
        Fn *fn = (Fn *) rhs;
        Partial_initFromFn(
            partial,
            (PyObject *) fn->name,
            (PyObject *) fn->bmod,
            (PyObject *) fn->d,
            (PyObject *) fn->TBCSentinel,
            (ju8) 2,
            lhs,
            NULL
        );
        return (PyObject *) partial;
    }
    else
        return PyErr_Format(ProgrammerError, "_binary_nb_rshift - unhandled case");
}


static PyObject * _pbinary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);

    if (tLhs == &PBinaryCls) {
        // 2. _pbinary >> arg2 - dispatch (unless the is the first argument and the rhs is a function)
        Partial *partial = (Partial *) lhs;
        if (partial->pipe1 == NULL && (tRhs == &UnaryCls || tRhs == &BinaryCls || tRhs == &TernaryCls || tRhs == &PUnaryCls || tRhs == &PBinaryCls || tRhs == &PTernaryCls)) Py_RETURN_NOTIMPLEMENTED;
        if (partial->pipe1 == NULL) return PyErr_Format(PyExc_SyntaxError, "Trying to pipe the 2nd argument into binary style partial fn %s.%s but the first argument hasn't been piped yet", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
        if (Py_SIZE(partial) == 0)
            return PyObject_CallFunctionObjArgs((PyObject *)partial->Fn.d, partial->pipe1, rhs, NULL);
        else {
            // this should not be called re-entrantly (and probably won't) but we can't stop it - so detect and throw as it would be hard to debug
            int iPipe1 = 32;  int iPipe2 = 32;
            Py_ssize_t num_args = Py_SIZE(partial);
            for (Py_ssize_t o=0; o < num_args; o++)
                if (partial->args[o] == partial->Fn.TBCSentinel) {
                    if (iPipe1 == 32)
                        iPipe1 = o;
                    else {
                        iPipe2 = o;
                        break;
                    }
                }
            if (iPipe1 == 32) return PyErr_Format(PyExc_SyntaxError, "Can't find the slot for the first piped argument - check that binary style partial fn %s.%s has not been reentrantly called", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
            if (iPipe2 == 32) return PyErr_Format(PyExc_SyntaxError, "Can't find the slot for the second piped argument - check that binary style partial fn %s.%s has not been reentrantly called", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
            partial->args[iPipe1] = partial->pipe1;
            partial->args[iPipe2] = rhs;
            PyObject * result = PyObject_Vectorcall(partial->Fn.d, partial->args, num_args, NULL);
            partial->args[iPipe1] = partial->Fn.TBCSentinel;
            partial->args[iPipe2] = partial->Fn.TBCSentinel;
            return result;
        }
    }
    else if (tRhs == &PBinaryCls) {
        // 4. arg1 >> _pbinary - check this is the first arg, then create a partial that can pipe one more argument
        Partial *partial = (Partial *) rhs;
        if (partial->num_tbc != 2)
            return PyErr_Format(PyExc_SyntaxError, "2 arguments will be piped into binary style partial fn %s.%s - but %u required", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name), partial->num_tbc);
        if (partial->pipe1 != NULL)
            return PyErr_Format(PyExc_SyntaxError, "First argument has already been piped into binary style partial fn %s.%s", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
        // we have to copy as
        // fred = add(1, _, _)
        // x = 1 >> fred >> (2 >> fred >> 3)
        // is valid - so the first copy (from partial to piping mode) cannot be finessed
        Py_ssize_t num_args = Py_SIZE(partial);
        Partial *newPartial = (Partial *) ((&PBinaryCls)->tp_alloc(&PBinaryCls, num_args));
        if (newPartial == NULL) return NULL;            // OPEN raise an error
        Partial_initFromFn(
            newPartial,
            (PyObject *) partial->Fn.name,
            (PyObject *) partial->Fn.bmod,
            (PyObject *) partial->Fn.d,
            (PyObject *) partial->Fn.TBCSentinel,
            (ju8) 2,
            lhs,
            partial->args
        );
        return (PyObject *) newPartial;
    }
    else
        return PyErr_Format(ProgrammerError, "_pbinary_nb_rshift - unhandled case");
}



// ternary pipe dispatch
//
// 1. _ternary >> arg       - syntax error
// 2. _pternary >> arg2Or3  - if 2 is missing then keep it else it must be 3 so dispatch
// 3. arg1 >> _ternary      - create a partial that can pipe two more arguments
// 4. arg1 >> _pternary     - check this is the first arg, then create a partial that can pipe two more arguments


static PyObject * _ternary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);

    if (tLhs == &TernaryCls) {
        if (tRhs == &UnaryCls) return _unary_nb_rshift(lhs, rhs);
        else if (tRhs == &PUnaryCls) return _punary_nb_rshift(lhs, rhs);
        else if (tRhs == &BinaryCls) return _binary_nb_rshift(lhs, rhs);
        else if (tRhs == &PBinaryCls) return _pbinary_nb_rshift(lhs, rhs);
        else if (tRhs == &TernaryCls);       // falls through to the below
        else if (tRhs == &PTernaryCls) return _pternary_nb_rshift(lhs, rhs);
        else {
            // 1. _binary >> argN
            Fn *fn = (Fn *) lhs;
            return PyErr_Format(PyExc_SyntaxError, "First arg to binary style fn %s.%s must be piped from the left", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
        }
    }

    if (tLhs == &TernaryCls) {
        // 1. _ternary >> argN
        Fn *fn = (Fn *) lhs;
        return PyErr_Format(PyExc_SyntaxError, "First arg to ternary style fn %s.%s must be piped from the left", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    }
    else if (tRhs == &TernaryCls) {
        // 3. arg1 >> _ternary - create a partial that can pipe two more arguments
        Partial *partial = (Partial *) ((&PTernaryCls)->tp_alloc(&PTernaryCls, 0));     // 0 as don't need to catch any args
        if (partial == NULL) return NULL;
        Fn *fn = (Fn *) rhs;
        Partial_initFromFn(
            partial,
            (PyObject *) fn->name,
            (PyObject *) fn->bmod,
            (PyObject *) fn->d,
            (PyObject *) fn->TBCSentinel,
            (ju8) 3,
            lhs,
            NULL
        );
        return (PyObject *) partial;
    }
    else
        return PyErr_Format(ProgrammerError, "_ternary_nb_rshift - unhandled case");
}


static PyObject * _pternary_nb_rshift(PyObject *lhs, PyObject *rhs) {
    PyTypeObject *tLhs = Py_TYPE(lhs);  PyTypeObject *tRhs = Py_TYPE(rhs);

    if (tLhs == &PTernaryCls) {
        // 2. _pternary >> arg2Or3 - if 2 is missing then keep it else it must be 3 so dispatch
        Partial *partial = (Partial *) lhs;
        if (partial->pipe1 == NULL) return PyErr_Format(PyExc_SyntaxError, "Trying to pipe the 2nd argument into ternary style partial fn %s.%s but the first argument hasn't been piped yet", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
        if (partial->pipe1 != NULL && partial->pipe2 == NULL) {
            // keeping argument 2
            partial->pipe2 = rhs;
            Py_INCREF(rhs);
            Py_INCREF(partial);                 // we're handing out another ref to partial to the caller
            return (PyObject *) partial;
        }
        // dispatch
        if (Py_SIZE(partial) == 0)
            return PyObject_CallFunctionObjArgs((PyObject *) partial->Fn.d, partial->pipe1, partial->pipe2, rhs, NULL);
        else {
            // this should not be called re-entrantly (and probably won't) but we can't stop it - so detect and throw as it would be hard to debug
            int iPipe1 = 32;  int iPipe2 = 32;  int iPipe3 = 32;
            Py_ssize_t num_args = Py_SIZE(partial);
            for (Py_ssize_t o=0; o < num_args; o++)
                if (partial->args[o] == partial->Fn.TBCSentinel) {
                    if (iPipe1 == 32)
                        iPipe1 = o;
                    else if (iPipe2 == 32)
                        iPipe2 = o;
                    else {
                        iPipe3 = o;
                        break;
                    }
                }
            if (iPipe1 == 32) return PyErr_Format(PyExc_SyntaxError, "Can't find the slot for the first piped argument - check that ternary style partial fn %s.%s has not been reentrantly called", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
            if (iPipe2 == 32) return PyErr_Format(PyExc_SyntaxError, "Can't find the slot for the second piped argument - check that ternary style partial fn %s.%s has not been reentrantly called", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
            if (iPipe3 == 32) return PyErr_Format(PyExc_SyntaxError, "Can't find the slot for the third piped argument - check that ternary style partial fn %s.%s has not been reentrantly called", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
            partial->args[iPipe1] = partial->pipe1;
            partial->args[iPipe2] = partial->pipe2;
            partial->args[iPipe3] = rhs;
            PyObject * result = PyObject_Vectorcall(partial->Fn.d, partial->args, num_args, NULL);
            partial->args[iPipe1] = partial->Fn.TBCSentinel;
            partial->args[iPipe2] = partial->Fn.TBCSentinel;
            partial->args[iPipe3] = partial->Fn.TBCSentinel;
            return result;
        }
    }
    else if (tRhs == &PTernaryCls) {
        // 4. arg1 >> _pternary - check this is the first arg, then create a partial that can pipe one more argument
        Partial *partial = (Partial *) rhs;
        if (partial->num_tbc != 3)
            return PyErr_Format(PyExc_SyntaxError, "3 arguments will be piped into ternary style partial fn %s.%s - but %u required", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name), partial->num_tbc);
        if (partial->pipe1 != NULL)
            return PyErr_Format(PyExc_SyntaxError, "First argument has already been piped into ternary style partial fn %s.%s", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
        // we have to copy as
        // fred = add(1, _, _)
        // x = 1 >> fred >> (2 >> fred >> 3)
        // is valid - so the first copy (from partial to piping mode) cannot be finessed
        Py_ssize_t num_args = Py_SIZE(partial);
        Partial *newPartial = (Partial *) ((&PTernaryCls)->tp_alloc(&PTernaryCls, num_args));
        if (newPartial == NULL) return NULL;            // OPEN raise an error
        Partial_initFromFn(
            newPartial,
            (PyObject *) partial->Fn.name,
            (PyObject *) partial->Fn.bmod,
            (PyObject *) partial->Fn.d,
            (PyObject *) partial->Fn.TBCSentinel,
            (ju8) 3,
            lhs,
            partial->args
        );
        return (PyObject *) newPartial;
    }
    else
        return PyErr_Format(ProgrammerError, "_pternary_nb_rshift - unhandled case");
}



// rau pipe dispatch
//

static PyObject * _rau_nb_rshift(PyObject *lhs, PyObject *rhs) {
    return PyErr_Format(NotYetImplemented, "arg >> _rau encountered");
}

static PyObject * _prau_nb_rshift(PyObject *lhs, PyObject *rhs) {
    return PyErr_Format(NotYetImplemented, "arg >> _prau encountered");
}



// Fn(...)

static PyObject * _Fn__call__(Fn *fn, PyObject *args, PyObject *kwds) {
    int num_tbc = 0;  Py_ssize_t num_args = PyTuple_GET_SIZE(args);
    if (kwds != NULL && PyDict_Size(kwds) > 0) return PyErr_Format(PyExc_TypeError, "%s.%s does not take keyword arguments", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    if (num_args > MAX_ARGS) return PyErr_Format(PyExc_SyntaxError, "Maximum number of args for fn %s.%s is %s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name), MAX_ARGS);
    for (Py_ssize_t o=0; o < num_args ; o++)
        num_tbc += PyTuple_GET_ITEM(args, o) == fn->TBCSentinel;
    PyTypeObject *t = Py_TYPE(fn);
    if (num_tbc == 0)
        if (t == &NullaryCls && num_args >= 0) return PyObject_CallObject(fn->d, args);
        else if (t == &UnaryCls && num_args >= 1) return PyObject_CallObject(fn->d, args);
        else if (t == &BinaryCls && num_args >= 2) return PyObject_CallObject(fn->d, args);
        else if (t == &TernaryCls && num_args >= 3) return PyObject_CallObject(fn->d, args);
        else if (t == &RauCls && num_args >= 1) return PyObject_CallObject(fn->d, args);
        else return PyErr_Format(PyExc_SyntaxError, "Not enough args for fn %s.%s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
    else {
        Partial *partial;
        if (t == &NullaryCls && num_args >= 0) partial = (Partial *) ((&PNullaryCls)->tp_alloc(&PNullaryCls, num_args));
        else if (t == &UnaryCls && num_args >= 1) partial = (Partial *) ((&PUnaryCls)->tp_alloc(&PUnaryCls, num_args));
        else if (t == &BinaryCls && num_args >= 2) partial = (Partial *) ((&PBinaryCls)->tp_alloc(&PBinaryCls, num_args));
        else if (t == &TernaryCls && num_args >= 3) partial = (Partial *) ((&PTernaryCls)->tp_alloc(&PTernaryCls, num_args));
        else if (t == &RauCls && num_args >= 1) partial = (Partial *) ((&PRauCls)->tp_alloc(&PRauCls, num_args));
        else return PyErr_Format(PyExc_SyntaxError, "Not enough args for fn %s.%s", PyUnicode_DATA(fn->bmod), PyUnicode_DATA(fn->name));
        if (partial == NULL) return NULL;
        Partial_initFromFn(
            partial,
            (PyObject *) fn->name,
            (PyObject *) fn->bmod,
            (PyObject *) fn->d,
            (PyObject *) fn->TBCSentinel,
            (ju8) num_tbc,
            NULL,
            NULL
        );
        // this loop could be eliminated by taking ownership of the args object by keeping the pointer to it but
        // this maybe less cache friendly. downstream on call completion the tuple could be modified on the strict
        // understanding that the dispatcher doesn't keep it but must copy it - TODO time tp_alloc for different sizes
        for (Py_ssize_t o=0; o < num_args ; o++) {
            partial->args[o] = PyTuple_GET_ITEM(args, o);
            Py_XINCREF(partial->args[o]);
        }
        return (PyObject *) partial;
    }
}



// Partial(...)

static PyObject * _Partial__call__(Partial *partial, PyObject *args, PyObject *kwds) {
    int new_missing = 0;  Py_ssize_t num_args = PyTuple_GET_SIZE(args);  PyObject * TBC = partial->Fn.TBCSentinel;
    if (kwds != NULL && PyDict_Size(kwds) > 0) return PyErr_Format(PyExc_TypeError, "%s.%s does not take keyword arguments", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));
    if (num_args != partial->num_tbc) return PyErr_Format(PyExc_SyntaxError, "Wrong number of args to partial fn %s.%s - %l expected, %l given", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name), partial->num_tbc, num_args);
    if (partial->pipe1 != NULL) return PyErr_Format(PyExc_SyntaxError, "Partial fn %s.%s is now piping - it is no longer callable in fortran style", PyUnicode_DATA(partial->Fn.bmod), PyUnicode_DATA(partial->Fn.name));

    for (Py_ssize_t o=0; o < num_args ; o++) new_missing += PyTuple_GET_ITEM(args, o) == TBC;
    Py_ssize_t full_size = Py_SIZE(partial);
    if (new_missing == 0) {
        // dispatch
        PyObject ** buffer = malloc(sizeof(PyObject*) * full_size);         // we could keep a stack of buffers
        int oNextArg = 0;
        for (Py_ssize_t o=0; o < full_size; o++) {
            PyObject * arg = partial->args[o];
            if (arg == TBC) {
                buffer[o] = PyTuple_GET_ITEM(args, oNextArg);
                oNextArg ++;
            }
            else
                buffer[o] = arg;
        }
        PyObject * result = PyObject_Vectorcall(partial->Fn.d, buffer, full_size, NULL);
        free(buffer);
        return result;
    }
    else {
        // create another partial
        Partial *new_partial = (Partial *) Py_TYPE(partial)->tp_alloc(Py_TYPE(partial), full_size);
        Partial_initFromFn(
            new_partial, partial->Fn.name, partial->Fn.bmod, partial->Fn.d, TBC,
            new_missing, NULL, partial->args
        );
        // replace the TBIs with the new args
        int oNextArg = 0;
        for (Py_ssize_t o=0; o < full_size; o++) {
            PyObject * arg = partial->args[o];
            if (arg == TBC) {
                Py_DECREF(arg);
                PyObject * new_arg = PyTuple_GET_ITEM(args, oNextArg);
                new_partial->args[o] = new_arg;
                Py_INCREF(new_arg);
                oNextArg ++;
            }
        }
        return (PyObject *) new_partial;
    }
}



// Partial misc

static PyObject * Partial_o_tbc(Partial *partial, void* closure) {
    Py_ssize_t full_size = Py_SIZE(partial);  PyObject **args = partial->args;  PyObject * TBC = partial->Fn.TBCSentinel;
    if (partial->pipe1 != NULL || partial->pipe2 != NULL) return NULL;
    int num_tbc = 0;
    for (Py_ssize_t o=0; o < full_size; o++) num_tbc += (args[o] == TBC);
    PyObject *answer = PyTuple_New(num_tbc);
    if (answer == NULL) return NULL;
    int o_next = 0;
    for (Py_ssize_t o=0; o < full_size; o++) {
        if (args[o] == TBC) {
            PyTuple_SET_ITEM(answer, o_next, PyLong_FromLong(o));
            o_next++;
        }
    }
    return answer;
}



// Fn lifecycle

static void Fn_dealloc(Fn *self) {
    Py_DECREF(self->name);
    Py_DECREF(self->bmod);
    Py_DECREF(self->d);
    Py_DECREF(self->TBCSentinel);
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static PyObject * Fn_new(PyTypeObject *type, PyObject *args, PyObject *kwds) {
    if (PyTuple_GET_SIZE(args) != 4) return PyErr_Format(ProgrammerError, "Must be created as Fn(name, bmod, d, TBCSentinel)");
    Fn *instance = (Fn *) type->tp_alloc(type, 0);
    if (instance == NULL) return NULL;
    return (PyObject *) instance;
}

static int Fn_init(Fn *self, PyObject *args, PyObject *kwds) {
    if (!PyArg_ParseTuple(args, "UUOO:", &self->name, &self->bmod, &self->d, &self->TBCSentinel)) return -1;
    Py_INCREF(self->name);
    Py_INCREF(self->bmod);
    Py_INCREF(self->d);
    Py_INCREF(self->TBCSentinel);
    if (!PyCallable_Check(self->d)) {
        PyErr_Format(PyExc_TypeError, "d is not a callable");
        return -1;
    }
    return 0;
}



// Partial lifecycle

static void Partial_dealloc(Partial *self) {
    Py_DECREF(self->Fn.name);
    Py_DECREF(self->Fn.bmod);
    Py_DECREF(self->Fn.d);
    Py_DECREF(self->Fn.TBCSentinel);
    Py_XDECREF(self->pipe1);
    Py_XDECREF(self->pipe2);
    // decref each arg
    Py_ssize_t num_args = Py_SIZE(self);
    if (num_args > 0) {
        for (Py_ssize_t o=0; o < num_args ; o++) {
            Py_XDECREF(self->args[o]);
        }
    }
    Py_TYPE(self)->tp_free((PyObject *) self);
}

static int Partial_initFromFn(
        Partial *self, PyObject *name, PyObject *bmod, PyObject *d, PyObject *TBCSentinel, ju8 num_tbc,
        PyObject *pipe1, PyObject *args[]) {

    self->Fn.name = name;
    self->Fn.bmod = bmod;
    self->Fn.d = d;
    self->Fn.TBCSentinel = TBCSentinel;
    self->num_tbc = num_tbc;
    self->pipe1 = pipe1;
    self->pipe2 = NULL;
    Py_INCREF(name);
    Py_INCREF(bmod);
    Py_INCREF(d);
    Py_INCREF(TBCSentinel);
    Py_XINCREF(pipe1);

    Py_ssize_t num_args = Py_SIZE(self);
    if (args != NULL) {
        for (Py_ssize_t o=0; o < num_args ; o++) {
            self->args[o] = args[o];
            Py_XINCREF(args[o]);
        }
    }

    return 0;
}



// members, get/setter, methods

static PyObject * Fn_get_doc(Fn *self, void *closure) {
    return PyUnicode_FromString("hello");
}

static PyObject * Fn_get_d(Fn *self, void *closure) {
    Py_INCREF(self->d);
    return self->d;
}

static int Fn_set_d(Fn *self, PyObject *d, void* closure) {
    if (!PyCallable_Check(d)) {
        PyErr_Format(PyExc_TypeError, "d is not a callable");
        return -1;
    }
    self->d = d;
    Py_INCREF(d);
    return 0;
}

static PyGetSetDef Fn_getsetters[] = {
    {"d", (getter) Fn_get_d, (setter) Fn_set_d, "dispatcher", NULL},
    {"__doc__", (getter) Fn_get_doc, NULL, NULL, NULL},
    {NULL}
};

static PyMemberDef Fn_members[] = {
    {"name", T_OBJECT, offsetof(Fn, name), READONLY, "function name"},
    {"bmod", T_OBJECT, offsetof(Fn, bmod), READONLY, "bones module name"},
    {NULL}
};

static PyGetSetDef Partial_getsetters[] = {
    {"o_tbc", (getter) Partial_o_tbc, NULL, "offsets of missing arguments", NULL},
    {NULL}
};

static PyMemberDef Partial_members[] = {
    {"name", T_OBJECT, offsetof(Partial, Fn.name), READONLY, "function name"},
    {"bmod", T_OBJECT, offsetof(Partial, Fn.bmod), READONLY, "bones module name"},
    {"d", T_OBJECT, offsetof(Partial, Fn.d), READONLY, "dispatcher"},
    {"num_tbc", T_UBYTE, offsetof(Partial, num_tbc), READONLY, "number of argument to be confirmed"},
    {"num_args", T_UBYTE, offsetof(PyVarObject, ob_size), READONLY, "total number of arguments"},
    {"pipe1", T_OBJECT, offsetof(Partial, pipe1), READONLY, "first piped arg"},
    {"pipe2", T_OBJECT, offsetof(Partial, pipe2), READONLY, "second piped arg"},
    {NULL}
};


static PyNumberMethods _nullary_tp_as_number = {.nb_rshift = (binaryfunc) _nullary_nb_rshift,};
static PyNumberMethods _pnullary_tp_as_number = {.nb_rshift = (binaryfunc) _pnullary_nb_rshift,};

static PyNumberMethods _unary_tp_as_number = {.nb_rshift = (binaryfunc) _unary_nb_rshift,};
static PyNumberMethods _punary_tp_as_number = {.nb_rshift = (binaryfunc) _punary_nb_rshift,};

static PyNumberMethods _binary_tp_as_number = {.nb_rshift = (binaryfunc) _binary_nb_rshift,};
static PyNumberMethods _pbinary_tp_as_number = {.nb_rshift = (binaryfunc) _pbinary_nb_rshift,};

static PyNumberMethods _ternary_tp_as_number = {.nb_rshift = (binaryfunc) _ternary_nb_rshift,};
static PyNumberMethods _pternary_tp_as_number = {.nb_rshift = (binaryfunc) _pternary_nb_rshift,};
static PyNumberMethods _rau_tp_as_number = {.nb_rshift = (binaryfunc) _rau_nb_rshift,};
static PyNumberMethods _prau_tp_as_number = {.nb_rshift = (binaryfunc) _prau_nb_rshift,};



// Python classes

static PyTypeObject FnCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "jones._fn",
    .tp_basicsize = sizeof(Base),
    .tp_itemsize = 0,
    .tp_doc = PyDoc_STR("_fn"),
    .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
};


static PyTypeObject NullaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._nullary",
    .tp_basicsize = sizeof(Fn),
    .tp_itemsize = 0,
    .tp_doc = PyDoc_STR("_nullary() - todo delegate to d"),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Fn_new,
    .tp_init = (initproc) Fn_init,
    .tp_dealloc = (destructor) Fn_dealloc,
    .tp_members = Fn_members,
    .tp_getset = Fn_getsetters,
    .tp_call = (ternaryfunc) _Fn__call__,
    .tp_as_number = (PyNumberMethods*) &_nullary_tp_as_number,
};

static PyTypeObject PNullaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._pnullary",
    .tp_basicsize = sizeof(Partial),
    .tp_itemsize = sizeof(PyObject *),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_dealloc = (destructor) Partial_dealloc,
    .tp_members = Partial_members,
    .tp_getset = Partial_getsetters,
    .tp_call = (ternaryfunc) _Partial__call__,
    .tp_as_number = (PyNumberMethods*) &_pnullary_tp_as_number,
};


static PyTypeObject UnaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._unary",
    .tp_basicsize = sizeof(Fn),
    .tp_itemsize = 0,
    .tp_doc = PyDoc_STR("_unary() - todo delegate to d"),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Fn_new,
    .tp_init = (initproc) Fn_init,
    .tp_dealloc = (destructor) Fn_dealloc,
    .tp_members = Fn_members,
    .tp_getset = Fn_getsetters,
    .tp_call = (ternaryfunc) _Fn__call__,
    .tp_as_number = (PyNumberMethods*) &_unary_tp_as_number,
};

static PyTypeObject PUnaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._punary",
    .tp_basicsize = sizeof(Partial),
    .tp_itemsize = sizeof(PyObject *),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_dealloc = (destructor) Partial_dealloc,
    .tp_members = Partial_members,
    .tp_getset = Partial_getsetters,
    .tp_call = (ternaryfunc) _Partial__call__,
    .tp_as_number = (PyNumberMethods*) &_punary_tp_as_number,
};


static PyTypeObject BinaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._binary",
    .tp_basicsize = sizeof(Fn),
    .tp_itemsize = 0,
    .tp_doc = PyDoc_STR("_binary() - todo delegate to d"),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Fn_new,
    .tp_init = (initproc) Fn_init,
    .tp_dealloc = (destructor) Fn_dealloc,
    .tp_members = Fn_members,
    .tp_getset = Fn_getsetters,
    .tp_call = (ternaryfunc) _Fn__call__,
    .tp_as_number = (PyNumberMethods*) &_binary_tp_as_number,
};

static PyTypeObject PBinaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._pbinary",
    .tp_basicsize = sizeof(Partial),
    .tp_itemsize = sizeof(PyObject *),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_dealloc = (destructor) Partial_dealloc,
    .tp_members = Partial_members,
    .tp_getset = Partial_getsetters,
    .tp_call = (ternaryfunc) _Partial__call__,
    .tp_as_number = (PyNumberMethods*) &_pbinary_tp_as_number,
};


static PyTypeObject TernaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._ternary",
    .tp_basicsize = sizeof(Fn),
    .tp_itemsize = 0,
    .tp_doc = PyDoc_STR("_ternary() - todo delegate to d"),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Fn_new,
    .tp_init = (initproc) Fn_init,
    .tp_dealloc = (destructor) Fn_dealloc,
    .tp_members = Fn_members,
    .tp_getset = Fn_getsetters,
    .tp_call = (ternaryfunc) _Fn__call__,
    .tp_as_number = (PyNumberMethods*) &_ternary_tp_as_number,
};

static PyTypeObject PTernaryCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._pternary",
    .tp_basicsize = sizeof(Partial),
    .tp_itemsize = sizeof(PyObject *),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_dealloc = (destructor) Partial_dealloc,
    .tp_members = Partial_members,
    .tp_getset = Partial_getsetters,
    .tp_call = (ternaryfunc) _Partial__call__,
    .tp_as_number = (PyNumberMethods*) &_pternary_tp_as_number,
};


static PyTypeObject RauCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._rau",
    .tp_basicsize = sizeof(Fn),
    .tp_itemsize = 0,
    .tp_doc = PyDoc_STR("_rau() - todo delegate to d"),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_new = Fn_new,
    .tp_init = (initproc) Fn_init,
    .tp_dealloc = (destructor) Fn_dealloc,
    .tp_members = Fn_members,
    .tp_getset = Fn_getsetters,
    .tp_call = (ternaryfunc) _Fn__call__,
    .tp_as_number = (PyNumberMethods*) &_rau_tp_as_number,
};

static PyTypeObject PRauCls = {
    PyVarObject_HEAD_INIT(NULL, 0)
    .tp_base = &FnCls,
    .tp_name = "jones._prau",
    .tp_basicsize = sizeof(Partial),
    .tp_itemsize = sizeof(PyObject *),
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_dealloc = (destructor) Partial_dealloc,
    .tp_members = Partial_members,
    .tp_getset = Partial_getsetters,
    .tp_call = (ternaryfunc) _Partial__call__,
    .tp_as_number = (PyNumberMethods*) &_prau_tp_as_number,
};



#endif