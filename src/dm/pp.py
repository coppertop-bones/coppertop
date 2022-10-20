# **********************************************************************************************************************
#
#                             Copyright (c) 2017-2021 David Briant. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#    disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#    following disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. All advertising materials mentioning features or use of this software must display the following acknowledgement:
#    This product includes software developed by the copyright holders.
#
# 4. Neither the name of the copyright holder nor the names of the  contributors may be used to endorse or promote
#    products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDERS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# **********************************************************************************************************************

BONES_NS = ''

from copy import copy as _copy
import numpy as np

from collections import namedtuple
from coppertop.pipe import *
from dm.core.aggman import collect, interleave
from bones.core.sentinels import Missing, list_iter

__all__ = []


@coppertop
def formatStruct(s, name, keysFormat, valuesFormat, sep):
    def formatKv(kv):
        k,v = kv
        k = k if isinstance(k, str) else format(k, keysFormat)
        v = v if isinstance(v, str) else format(v, valuesFormat)
        return f'{k}={v}'
    return f'{name}({list(s._kvs()) >> collect >> formatKv >> interleave >> sep})'
    # return f'{name}({s >> kvs >> collect >> formatKv >> join >> sep})'


@coppertop
def PPS(lines):
    for line in lines:
        print(line)
    return lines

@coppertop
def PP(x):
    print(x)
    return x

@coppertop
def PP(x, f):
    print(f(x))
    return x

@coppertop
def RR(x):
    print(repr(x))
    return x

@coppertop
def RR(x, f):
    print(repr(f(x)))
    return x

@coppertop
def SS(x):
    print(str(x))
    return x

@coppertop
def SS(x, f):
    print(str(f(x)))
    return x

@coppertop
def DD(x):
    print(dir(x))
    return x

@coppertop
def JJ(x):
    print('                                                                                                                                                                                                                                                                                      ', end='\r')
    print(x, end='\r')
    return x

@coppertop
def HH(x):
    if hasattr(x, '_doc'):
        print(x._doc)
    else:
        help(x)
    return x

@coppertop
def TT(x):
    print(typeOf(x))
    return x

@coppertop
def LL(x):
    if isinstance(x, list_iter):
        x = list(_copy(x)) # if it's an iterator it's state will be changed by len - so make a copy
    if isinstance(x, np.ndarray):
        print(x.shape)
    else:
        print(len(x))
    return x


Titles = namedtuple('Titles', ['title', 'subTitles'])  # aka heading def


@coppertop
def formatAsTable(listOfRows):
    return _formatAsTable(listOfRows)

@coppertop
def formatAsTable(listOfRows, headingDefs):
    return _formatAsTable(listOfRows, headingDefs)

@coppertop
def formatAsTable(listOfRows, headingDefs, title):
    return _formatAsTable(listOfRows, headingDefs, title)

def _formatAsTable(listOfRows, headingDefs=Missing, title=Missing):
    # for moment only handle one level of grouping
    columnTitles = _Collector()
    i = 0
    groupTitles = _Collector()
    hasGroupTitles = False
    for headingDef in headingDefs:
        if isinstance(headingDef, str):
            groupTitles << (i, i, '')
            columnTitles << headingDef
            i += 1
        elif not headingDef:
            groupTitles << (i, i, '')
            columnTitles << ''
            i += 1
        else:
            groupTitles << (i, i + len(headingDef.subTitles) - 1, headingDef.title)
            columnTitles += headingDef.subTitles
            i += len(headingDef.subTitles)
            hasGroupTitles = True
    allRows = ([columnTitles] if headingDefs else []) + [list(row) for row in listOfRows]
    widths = [1] * len(allRows[0])
    for row in allRows:
        for j, cell in enumerate(row):
            row[j] = str(row[j])
            widths[j] = widths[j] if widths[j] >= len(row[j]) else len(row[j])
    cellsWidth = sum(widths) + 2 * len(widths)
    lines = []
    if title is not Missing:
        titleLine = '- ' + title + ' -' if title else ''
        LHWidth = int((cellsWidth - len(titleLine)) / 2)
        RHWidth = (cellsWidth - len(titleLine)) - LHWidth
        titleLine = ('-' * LHWidth) + titleLine + ('-' * RHWidth)
        lines.append(titleLine)
    if groupTitles:
        line = ''
        for i1, i2, groupTitle in groupTitles:
            width = sum([widths[i] for i in range(i1, i2 + 1)])
            width += 2 * (i2 - i1)
            line += (' %' + str(width) + 's|') % groupTitle[:width]
        lines.append(line)
    for i, row in enumerate(allRows):
        line = ''
        for j, cell in enumerate(row):
            line += (' %' + str(widths[j]) + 's|') % cell
        lines.append(line)
        if i == 0 and headingDefs:
            line = ''
            for width in widths:
                line += '-' * (width + 1) + '|'
            lines.append(line)
    return lines

class _Collector(list):
    def __lshift__(self, other):  # self << other
        self.append(other)
        return self
