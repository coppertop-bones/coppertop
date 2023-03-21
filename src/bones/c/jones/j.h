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

#ifndef __JONES_H
#define __JONES_H

#include "b_all.h"
#include "khash.h"


static kh_inline khint_t __ac_X31_hash_fred(const txt *s) {
	khint_t h = (khint_t)*s;
	if (h) for (++s ; *s; ++s) h = (h << 5) - h + (khint_t)*s;
	return h;
}

int fredcmp (const txt *p1, const txt *p2) {
  const txt *s1 = (const txt *) p1;
  const txt *s2 = (const txt *) p2;
  txt c1, c2;
  do {
      c1 = (txt) *s1++;
      c2 = (txt) *s2++;
      if (c1 == '\0') return c1 - c2;
  }
  while (c1 == c2);
  return c1 - c2;
}

#define kh_fred_hash_func(key) __ac_X31_hash_fred(key)
#define kh_fred_hash_equal(a, b) (fredcmp(a, b) == 0)



#define KHASH_MAP_INIT_INT32(name, khval_t)								\
	KHASH_INIT(name, khint32_t, khval_t, 1, kh_int_hash_func, kh_int_hash_equal)

#define KHASH_MAP_INIT_INT64(name, khval_t)								\
	KHASH_INIT(name, khint64_t, khval_t, 1, kh_int64_hash_func, kh_int64_hash_equal)

#define KHASH_MAP_INIT_TXT(name, khval_t)								\
	KHASH_INIT(name, kh_cstr_t, khval_t, 1, kh_str_hash_func, kh_str_hash_equal)

#define KHASH_MAP_INIT_U16_ARRAY(name, khval_t)								\
	KHASH_INIT(name, txt, khval_t, 1, kh_fred_hash_func, kh_fred_hash_equal)


KHASH_MAP_INIT_INT32(hm_u32_u8, ju8)
KHASH_MAP_INIT_TXT(hm_txt_u32, ju32)
KHASH_MAP_INIT_TXT(hm_txt_typenum, ju16)




#endif