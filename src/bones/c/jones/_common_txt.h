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

#ifndef __COMMON_TXT_H
#define __COMMON_TXT_H



// code for handling txt - to start off it'll just be a char* to a null terminate utf8 encoded buffer but
// conceivable could change

typedef char txt;                   // advice is to keep to char

#define txtlen strlen
#define txtcpy strcpy
#define newtxtbuf(numbytes) (malloc((numbytes)+1))
#define droptxt(ptr) (free(ptr))


static txt *join_txts(int num_args, ...) {
    jsize size = 0;
    va_list ap;
    va_start(ap, num_args);
    for (int i = 0; i < num_args; i++) size += txtlen(va_arg(ap, txt*));
    txt *res = newtxtbuf(size);
    size = 0;
    va_start(ap, num_args);
    for (int i = 0; i < num_args; i++) {
        txt *s = va_arg(ap, char*);
        txtcpy(res + size, s);
        size += txtlen(s);
    }
    va_end(ap);
    res[size] = '\0';
    return res;
}




#endif
