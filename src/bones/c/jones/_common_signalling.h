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

#ifndef __COMMON_SIGNALLING_H
#define __COMMON_SIGNALLING_H


#include "_common.h"
#include "_common_txt.h"


typedef txt* err;
#define ok NULL

#define SIGNAL(msg) return (err) join_txts(3, __FUNCTION__, ": ", msg);       // __PRETTY_FUNCTION__, __FILE__, __LINE__, __FUNCTION__, __func__


#endif
