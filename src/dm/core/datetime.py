# **********************************************************************************************************************
#
#                             Copyright (c) 2017-2020 David Briant. All rights reserved.
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

# SHOULDDO handle locales


import sys
if hasattr(sys, '_TRACE_IMPORTS') and sys._TRACE_IMPORTS: print(__name__)


from _strptime import _strptime
import datetime
from bones.core.sentinels import Missing
from coppertop.pipe import *
from dm.core.types import txt, index, date


@coppertop
def year(x):
    return x.year

@coppertop
def month(x):
    return x.month

@coppertop
def day(x):
    return x.day

@coppertop
def hour(x):
    return x.hour

@coppertop
def minute(x):
    return x.minute

@coppertop
def second(x):
    return x.second

@coppertop
def weekday(x):
    return x.weekday()

@coppertop
def weekdayName(x):
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][x]

@coppertop
def weekdayName(x, locale):
    return ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][x]

@coppertop
def weekdayLongName(x):
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]

@coppertop
def weekdayLongName(x, locale):
    return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][x]

@coppertop
def monthName(month):
    return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month - 1]

@coppertop
def monthName(month, locale):
    return ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][month - 1]

@coppertop
def monthLongName(month):
    return ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][month - 1]

@coppertop
def monthLongName(month, locale):
    return ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'][month - 1]

@coppertop
def parseDate(x:txt, cFormat:txt) -> date:
    # rework to be more efficient in bulk by parsing format separately from x or handle x as an array / range
    dt, micro, _ = _strptime(x, cFormat)
    return datetime.date(dt[0], dt[1], dt[2])

@coppertop
def toCTimeFormat(simpleFormat:txt) -> txt:

    # a little care is needed here to avoid clashes between formats
    answer = simpleFormat
    answer = answer.replace('DDDD', '%A')
    answer = answer.replace('DDD', '%a')
    answer = answer.replace('DD', '%d')
    answer = answer.replace('D', '%e')

    answer = answer.replace('YYYY', '%Y')
    answer = answer.replace('YY', '%y')

    answer = answer.replace('ms', '%f')                             # Microsecond as a decimal number, zero-padded to 6 digits
    answer = answer.replace('us', '%f')

    answer = answer.replace('mm', '%M')
    answer = answer.replace('m', '%-M')

    answer = answer.replace('ms', '%f')                             # Microsecond as a decimal number, zero-padded to 6 digits
    answer = answer.replace('us', '%f')

    answer = answer.replace('ss', '%S')
    answer = answer.replace('s', '%<single-digit-second>')

    answer = answer.replace('MMMM', '%B')                           # Month as locale’s full name
    answer = answer.replace('MMM', '%b')                            # Month as locale’s abbreviated name
    answer = answer.replace('MM', '%m')                             # Month as a zero-padded decimal number
    answer = answer.replace('M', '%<single-digit-month>')
    answer = answer.replace('%%<single-digit-month>', '%M')
    answer = answer.replace('%-%<single-digit-month>', '%-M')

    answer = answer.replace('hh', '%H')                             # 0 padded 12 hour
    answer = answer.replace('h', '%-H')
    answer = answer.replace('HH', '%I')                             # 0 padded 24 hour
    answer = answer.replace('H', '%-I')
    answer = answer.replace('%%-I', '%H')
    answer = answer.replace('%-%-I', '%-H')

    answer = answer.replace('TT', '%p')                             # Locale’s equivalent of either AM or PM

    answer = answer.replace('city', '%<city>')
    answer = answer.replace('z/z', '%<IANA>')
    answer = answer.replace('z', '%Z')                              # Time zone name (empty string if the object is naive)
    return answer

@coppertop
def addDays(d:date, n:index):
    return d + datetime.timedelta(n)
