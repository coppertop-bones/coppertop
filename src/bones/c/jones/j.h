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