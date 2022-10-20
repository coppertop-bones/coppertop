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

#ifndef __COMMON_H
#define __COMMON_H

#include <stdlib.h>
#include <stdarg.h>
#include <stddef.h>
#include <stdbool.h>

#define _4K 4096
#define _16K 16384
#define _64K 65536
#define _1M 1048576
#define _1GB 1073741824
#define _2GB 2147483648
#define _4GB 4294967296
#define _1TB 1099511627776


// Quote Originally Posted by C99 Section 6.2.5 Paragraph 15 and note 35
// The three types char, signed char, and unsigned char are collectively called the character types. The
// implementation shall define char to have the same range, representation, and behavior as either signed
// char or unsigned char.
//
// CHAR_MIN, defined in <limits.h>, will have one of the values 0 or SCHAR_MIN, and this can be used to
// distinguish the two options. Irrespective of the choice made, char is a separate type from the other
// two and is not compatible with either.
//
// consider:
// strcmp - e.g. https://codebrowser.dev/glibc/glibc/string/strcmp.c.html


// size_t
//   - the type which is used to represent the size of objects in bytes, and returned from sizeof
//   - for example https://www.embedded.com/further-insights-into-size_t/


typedef unsigned char       ju8;
typedef unsigned short int  ju16;
typedef unsigned int        ju32;
typedef unsigned long int   ju64;

typedef signed char         ji8;
typedef signed short int    ji16;
typedef signed int          ji32;
typedef signed long int     ji64;

typedef size_t              jsize;


// https://embeddedgurus.com/stack-overflow/2008/06/efficient-c-tips-1-choosing-the-correct-integer-size/
typedef uint_fast8_t fu8;
typedef uint_fast16_t fu16;
typedef uint_fast32_t fu32;
typedef uint_fast64_t fu64;

typedef uint_least8_t lu8;
typedef uint_least16_t lu16;
typedef uint_least32_t lu32;
typedef uint_least64_t lu64;




//
//char* concatMsg(const char* str1, const char* str2){
//    char* result;
//    asprintf(&result, "%s%s", str1, str2);
//    return result;
//}









// # - single hash in macro puts the argument in quotes, ## creates a new symbol
// https://gcc.gnu.org/onlinedocs/cpp/Concatenation.html#Concatenation

// X macro - https://www.digitalmars.com/articles/b51.html, https://en.wikipedia.org/wiki/X_Macro

//#define IFNDEF \#ifndef
//#define DEFINE \#define
//#define INCLUDE \#include
//#define ENDIF \#endif
//
//
//#define J_INCLUDE(file_locator, guard_symbol) \
//    IFNDEF guard_symbol \
//    INCLUDE file_locator \
//    DEFINE guard_symbol \
//    ENDIF





#if defined _WIN64 || defined _WIN32
  #include "cache_line_size_win64.h"
#elif defined _APPLE_ || defined __MACH__
  #include "cache_line_size_macos.h"
#elif defined __linux__
  #include "cache_line_size_linux.h"
#endif



#endif
