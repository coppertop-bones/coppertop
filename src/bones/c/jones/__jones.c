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


// ---------------------------------------------------------------------------------------------------------------------
// Writing the Setup Configuration File - https://docs.python.org/3/distutils/configfile.html
// build with > python setup.py build
// ---------------------------------------------------------------------------------------------------------------------

#include "pj_all.h"




//typedef const ju16 *c_u16_array;
//typedef const char *kh_cstr_t;


// to start swith we'll just use null terminated / sized utf8 as our txt format - we shouldn't need to worry very much
// about unicode as we can convert classes and mix types and classes with ease
//
// https://docs.python.org/3/c-api/unicode.html#utf-8-codecs
// PyObject *PyUnicode_DecodeUTF8Stateful(const char *s, Py_ssize_t size, const char *errors, Py_ssize_t *consumed)
// const char *PyUnicode_AsUTF8AndSize(PyObject *unicode, Py_ssize_t *size)

// This decision is backed up by
// https://utf8everywhere.org/
// https://developer.twitter.com/en/docs/counting-characters



// ---------------------------------------------------------------------------------------------------------------------
// init module
// ---------------------------------------------------------------------------------------------------------------------

static PyMethodDef free_fns[] = {
    {"toAddress", (PyCFunction)                 _toAddress, METH_FASTCALL, "toAddress(object)\n\nanswer the address of object and it's refcount"},
    {"toPtr", (PyCFunction)                     _toPtr, METH_FASTCALL, "toPtr(object)\n\nanswer the address of object"},
    {"toObj",                                   _toObj, METH_VARARGS, "toObj(address)\n\nreturn the ptr as an object"},
    {"ob_refcnt",                               _ob_refcnt, METH_VARARGS, "ob_refcnt(address)\n\nreturn the ref count for the object at the address"},
    {"atU16", (PyCFunction)                     _atU16, METH_FASTCALL, "atU16(pBuf, index"},
    {"atU16Put", (PyCFunction)                  _atU16Put, METH_FASTCALL, "atU16Put(pBuf, index, mask, value"},
    {"atU8", (PyCFunction)                      _atU8, METH_FASTCALL, "atU8(pBuf, index"},
    {"atU8Put", (PyCFunction)                   _atU8Put, METH_FASTCALL, "atU8Put(pBuf, index, mask, value"},
    {"malloc", (PyCFunction)                    _malloc, METH_FASTCALL, ""},
    {"getPageSize", (PyCFunction)               _pageSize, METH_FASTCALL, "system page size"},
    {"getCacheLineSize", (PyCFunction)          _getCacheLineSize, METH_FASTCALL, "system cache line size"},
//    {"reserve", (PyCFunction)                   _reserve, METH_FASTCALL, "reserve(pVA, numPages)"},
//    {"getVaPtr", (PyCFunction)                  _getVaPtr, METH_FASTCALL, "getVaPtr()"},

    {"sc_new", (PyCFunction)                    _SC_new, METH_FASTCALL, "sc_init(numArgs, arrayLen) -> pSC"},
    {"sc_drop", (PyCFunction)                   _SC_drop, METH_FASTCALL, "sc_drop(pSC) -> None"},
    {"sc_slotWidth", (PyCFunction)              _SC_slot_width, METH_FASTCALL, "sc_slotWidth(pSC) -> count"},
    {"sc_numSlots", (PyCFunction)               _SC_num_slots, METH_FASTCALL, "sc_numSlots(pSC) -> count"},
    {"sc_drop", (PyCFunction)                   _SC_drop, METH_FASTCALL, "sc_drop(pSC) -> None"},
    {"scNextFreeArrayIndex", (PyCFunction)      _SC_next_free_array_index, METH_FASTCALL, ""},
    {"scAtArrayPut", (PyCFunction)              _SC_atArrayPut, METH_FASTCALL, "puts a fnId in the selection cache"},
    {"scQueryPtr", (PyCFunction)                _SC_pQuery, METH_FASTCALL, "scQueryPtr(pSC)\n\nanswer a pointer to the query buffer"},
    {"scArrayPtr", (PyCFunction)                _SC_pArray, METH_FASTCALL, "scArrayPtr(pSC)\n\nanswer a pointer to the array of sigs"},
    {"sc_getFnId", (PyCFunction)                _SC_get_result, METH_FASTCALL, ""},
    {"sc_fillQuerySlotAndGetFnId", (PyCFunction) _SC_fill_query_slot_and_get_result, METH_FASTCALL, "sc_fillQuerySlotAndGetFnId(pSC, tArgs : pytuple) -> fnId\n\nanswer the resultId for the signature tArgs"},
    {"sc_tArgsFromQuery", (PyCFunction)         _SC_tArgs_from_query, METH_FASTCALL, "sc_tArgsFromQuery(pSC : ptr, allTypes : pylist)\n\nanswers a tuple of tArgs from the slot"},
    {"sc_fillQuerySlotWithBTypesOf", (PyCFunction) _SC_fill_query_slot_with_btypes_of, METH_FASTCALL, "sc_fillQuerySlotWithBTypesOf(pSC : ptr, args : tuple)\n\nanswers a tuple of tArgs from the slot"},

//    {"type_new",                                Shifter_type_new, METH_VARARGS | METH_KEYWORDS, ""},


//    {"unreserve", (PyCFunction)                 _unreserve, METH_FASTCALL, ""},

    // play
    {"execShell",                               _execShell, METH_VARARGS, "Execute a shell command."},
    {"sizeofFredJoe", (PyCFunction)             _sizeofFredJoe, METH_FASTCALL, "tuple with sizeOf Fred and Joe in it"},
    {NULL, NULL, 0, NULL}
};


static PyModuleDef jones_module = {
    PyModuleDef_HEAD_INIT,
    .m_name = "jones",
    .m_doc = "as in archibald",
    .m_size = -1,
    free_fns
};


//    {"bmodule", T_OBJECT, offsetof(Fn, bmodule), READONLY, "bones module name"},

PyMODINIT_FUNC PyInit_jones(void) {
    PyObject *m;

// TODO make cross platform
//    ju32 num_pages = _1GB / db_os_page_size();
//    VA *va = init_va(num_pages);
//    if (va == NULL) return NULL;
//    g_va = va;


    m = PyModule_Create(&jones_module);
    if (m == NULL) return NULL;

//    PyObject *tbc = Py_None;
//    Py_XINCREF(tbc);
//    if (PyModule_AddObject(m, "_", tbc) < 0) {
//        Py_XDECREF(tbc);
//        return NULL;
//    }
    // PyModule_AddObject() stole a reference to obj:
    // Py_DECREF(obj) is not needed here


    // JonesError
    JonesError = PyErr_NewException("jones.JonesError", NULL, NULL);
    if (PyModule_AddObject(m, "error", JonesError) < 0) {
        Py_XDECREF(JonesError);
        Py_CLEAR(JonesError);
        Py_DECREF(m);
        return NULL;
    }

    // JonesSyntaxError
    JonesSyntaxError = PyErr_NewException("jones.JonesSyntaxError", NULL, NULL);
    if (PyModule_AddObject(m, "error", JonesSyntaxError) < 0) {
        Py_XDECREF(JonesSyntaxError);
        Py_CLEAR(JonesSyntaxError);
        Py_DECREF(m);
        return NULL;
    }

    // add BTypeCls
    if (PyType_Ready(&BTypeCls) < 0) return NULL;
    if (PyModule_AddObject(m, "BType", (PyObject *) &BTypeCls) < 0) {
        Py_DECREF(&BTypeCls);
        Py_DECREF(m);
        return NULL;
    }


    // add function classes
    if (PyType_Ready(&FnCls) < 0) return NULL;
    if (PyModule_AddObject(m, "_fn", (PyObject *) &FnCls) < 0) {
        Py_DECREF(&FnCls);
        Py_DECREF(m);
        return NULL;
    }

    if (PyType_Ready(&NullaryCls) < 0) return NULL;
    if (PyModule_AddObject(m, "_nullary", (PyObject *) &NullaryCls) < 0) {
        Py_DECREF(&NullaryCls);
        Py_DECREF(m);
        return NULL;
    }

    if (PyType_Ready(&UnaryCls) < 0) return NULL;
    if (PyModule_AddObject(m, "_unary", (PyObject *) &UnaryCls) < 0) {
        Py_DECREF(&UnaryCls);
        Py_DECREF(m);
        return NULL;
    }

    if (PyType_Ready(&BinaryCls) < 0) return NULL;
    if (PyModule_AddObject(m, "_binary", (PyObject *) &BinaryCls) < 0) {
        Py_DECREF(&BinaryCls);
        Py_DECREF(m);
        return NULL;
    }

    if (PyType_Ready(&TernaryCls) < 0) return NULL;
    if (PyModule_AddObject(m, "_ternary", (PyObject *) &TernaryCls) < 0) {
        Py_DECREF(&TernaryCls);
        Py_DECREF(m);
        return NULL;
    }

    if (PyType_Ready(&RauCls) < 0) return NULL;
    if (PyModule_AddObject(m, "_rau", (PyObject *) &RauCls) < 0) {
        Py_DECREF(&RauCls);
        Py_DECREF(m);
        return NULL;
    }


    // init the partial classes
    if (PyType_Ready(&PNullaryCls) < 0) return NULL;
    if (PyType_Ready(&PUnaryCls) < 0) return NULL;
    if (PyType_Ready(&PBinaryCls) < 0) return NULL;
    if (PyType_Ready(&PTernaryCls) < 0) return NULL;
    if (PyType_Ready(&PRauCls) < 0) return NULL;


    // add ToyCls
    if (PyType_Ready(&ToyCls) < 0) return NULL;
    if (PyModule_AddObject(m, "Toy", (PyObject *) &ToyCls) < 0) {
        Py_DECREF(&ToyCls);
        Py_DECREF(m);
        return NULL;
    }

    return m;
}
