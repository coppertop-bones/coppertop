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

#ifndef __BONES_H
#define __BONES_H


#include "_common_all.h"


typedef ju16 TypeNum;
#define TN_NULL 0x0000

// signature encoding
typedef ju16 TN1;          // bit 15 - hasUpper, bit 14 - isPointer, bit 13-0 are the first 16k types
typedef ju16 TN2;          // bits 15-4 reserved for sig cache payload, bits 2-0 make total up to 128k types
typedef ju16 SigHeader;    // bits 15-5 reserved, bits 4-0 size in bytes (can handle up to 16 TN2 arguments)



// symbol encoding
// size prefixed, utf8 sequence, from 0 to 255 bytes so 0 is effectively the null symbol - we "waste" one byte for
// null termination so standard c string functions can work - size prefix allows for slightly faster comparison as
// we check size first


// 0x0000_FFFF_FFFF_FFFF
#define B_PTR_MASK 0x0000FFFFFFFFFFFF





#endif