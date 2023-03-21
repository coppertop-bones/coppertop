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

#ifndef __COMMON_OS_SHIM_H
#define __COMMON_OS_SHIM_H



#if defined _WIN64 || defined _WIN32
  #include "_common_os_win64.h"
#elif defined _APPLE_ || defined __MACH__
  #include "_common_os_macos.h"
#elif defined __linux__
  #include "_common_os_linux.h"
#endif



#endif
