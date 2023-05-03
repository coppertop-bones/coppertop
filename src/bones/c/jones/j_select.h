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

#ifndef __J_FN_SELECTION_H
#define __J_FN_SELECTION_H

#include "j.h"


// we only keep hits in the cache as cache misses mean "not found" which initiates a fitsWithin search, and then either
// a type error is raised or the new hit is added to the cache
// we want to count the number of hits so we can sort according to hits -> which hopefully will be faster overall

// assuming that L1 & L2 cache misses are important for the dispatch we compact the signatures
// a type can be TN1 or TN2 so the number of slots is 1 byte for header + 2 * num_args - TN1 is 1 short, TN2 is 2 shorts
// we have 48 bits in a 1 arg signature however we only can rely on there being space in the first and last short
// so we have 32 bits to play with


// SHORT (16-bit) ALIGNED
// |         TN2          |           TN1            |      Sig Header     |
// | PPPPP HHH HHHH H TTT | TN2 Po TT TTTT TTTT TTTT | PPPP PPPP PPP NNNNN |
//
// N -> max size of sig in multiples of SHORT -> 5 bits up to 32 shorts (16 args without winging it)
// P -> payload (i.e. the function slot for this overload)
// T -> type (17 bits -> 128k types)
// Po -> is pointer (1 bit)
// TN2 -> is TN2 type
// H -> hit count (8 bits -> 256 hot hits before incrementing cold hit)


//pointers
//| ---- ---- PPPP PPPP | PPPP PPPP PPPP P--- |
//
//11 spare bits
//
//IEEE Doubles - NaN boxing - 52 spare bits
//
//S[Exponent-][Mantissa------------------------------------------]
//| SEEE EEEE EEEE MMMM | MMMM MMMM MMMM MMMM | MMMM MMMM MMMM MMMM | MMMM MMMM MMMM MMMM |
//| S111 1111 1111 0000 | 0000 0000 0000 0000 | 0000 0000 0000 0000 | 0000 0000 0000 0000 |   +- infinity
//| -111 1111 1111 1--- | ---- ---- ---- ---- | ---- ---- ---- ---- | ---- ---- ---- ---- |   non-signalling NaN
//| -111 1111 1111 0--- | ---- ---- ---- ---- | ---- ---- ---- ---- | ---- ---- ---- ---- |   signalling NaN but mantissa > 0
//
//if double + pStr - 7 spare bits
//
//any struct > 2 things is going to be a pointer - so no real overhead in a 64bit box?
//symbols
//unboxed types
//symbols (length prefixed utf8), strings (utf8), numbers u8, i8, u64, i64, f64, bool, small structs
//
//stack
//scratch
//heap objects - prefix with a 32 bit meta field (which includes the type) - this  might get padded to 64bits for
//    doubles? or we can align the payload?, e.g. to cache lines or possibly set lines?



#define MAX_NUM_T1_TYPES _16K
#define MAX_NUM_T2_TYPES _128K

// masks for for embedding the code
#define V_LMASK 0x001F                      // 0000 0000 0001 1111
#define V_UMASK 0xFFE0
#define LAST_TN_PAYLOAD_SHIFT 3
#define LAST_TN_HITS_SHIFT 8
#define LAST_TN_HITS_MASK 0xFF00
#define HAS_TN2_MASK 0x8000                 // 1000 0000 0000 0000
#define IS_PTR_MASK 0x4000                  // 0100 0000 0000 0000
#define TN2_SHIFT 16

// pSig vs replicating sig
// pSig is 8bytes - sig1 is 4 to 6 bytes, sig2 is 6 to 10 bytes, sig3 is 8 to 14 bytes
// fnId can be encoded in pSig and sig - fnId = 2 ^ 11 (2048 fns per overload), pSig could encode more
// *pSig may be a cache miss (+200 cycles), but sig[] is less likely to be a miss
// functions with many args are not likely to have lots of overloads so the space saved by pSig in real terms may be
// minimal compared to the locality gained

// encode function number in sigheader - in bits 15 to 5 - allowing a max of 2048 overloads, with 16 arguments

typedef struct {
    ju8 slot_width;                         // in count of TypeNum
    ju8 num_slots;                          // number of slots in the array (we also have a scratch slot for the query)
    ju16 hash_n_slots;                      // at 50% this can hold 32k functions (should be enough!!!???)
//    ju16 count_buf_size
//    ju16 count_buf_next
//    TypeNum *count_buf
//    func *call_back
    TypeNum type_nums[];
//    TypeNum query[1][slot_width];      // a buffer of the right size to copy the TypeNums from the call site
                                            // OPEN: is this needed in bones or just Python
//    TypeNum sig_array[num_slots][slot_width];
//    TypeNum sig_hash[hash_n_slots][slot_width];// a hash table of signatures - we'll borrow techniques from else where to organise
} SelectorCache;

// OPEN: maybe add query count so can sort by it - for mo just track in Python

#define P_QUERY(sc) (&(sc)->type_nums[0])
#define P_SIG_ARRAY(sc) (&(sc)->type_nums[1 * (sc)->slot_width])
#define P_SIG_HASH(sc) (&(sc)->type_nums[(1 + (sc)->num_slots) * (sc)->slot_width])
#define SLOT_WIDTH_FROM_NUM_ARGS(num_args) (1 + 2 * (num_args))
#define NUM_ARGS_FROM_SLOT_WIDTH(slot_width) ((slot_width - 1) / 2)

// sig array has a variable length encoding
// SigHeader header - last 5 bits are length in u16 so 11111 = 31 which is taken as 32 (as it makes no sense to 
// dispatch on 0 args) so in total we can hold between 16 u32 TypeNums and 32 u16 TypeNums

// sig arrays must be stored sparsely in the hash part of the cache but could be stored consecutively in the array
// part of the cache - for the moment only do sparse - only advantage of compact is avoiding cache misses

static void SC_at_array_put(SelectorCache *sc, int index, TypeNum sig[], ju16 v) {
    // index is one based, sig is size prefixed array of T1|T2
    TypeNum *dest = P_SIG_ARRAY(sc) + (index - 1) * sc->slot_width;
    TypeNum size = sig[0] & V_LMASK;
    dest[0] = (v & V_UMASK) | size;
    for (fu8 o=1; o < size + 2; o++) dest[o] = sig[o];
    TypeNum *pad_array = dest + size + 2;
    jsize num_to_pad = sc->slot_width - (size + 1);
    for (fu8 o=0; o < num_to_pad; o++) pad_array[o] = TN_NULL;
    fu8 o_last = sc->slot_width - 1;
    dest[o_last] = dest[o_last] | ((v & V_LMASK) << LAST_TN_PAYLOAD_SHIFT);
}

static ju8 SC_next_free_array_index(SelectorCache *sc) {
    fu16 num_slots = sc->num_slots;
    fu16 slot_width = sc->slot_width;
    TypeNum *array = P_SIG_ARRAY(sc);
    for (fu16 o=0; o < num_slots; o++) if ((array + o * slot_width)[0] == 0x0000) return o + 1;
    return 0;
}

//static void SC_at_hash_put() {}

// printf("query[o]: %#02x, sig[o]: %#02x\n", query[o], sig[o]);

static inline fu16 fast_compare_sig(TypeNum query[], TypeNum sig[], fu8 slot_width) {
    fu16 N = query[0];
    if (N != (sig[0] & V_LMASK)) return 0;                                       // check count
    for (fu8 o = 1; o <= N; o++) {
        if (query[o] != sig[o]) return 0;                                        // check TypeNums
//        if (query[o] == TN_NULL) return (sig[0] & V_UMASK) | ((sig[o_last] >> LAST_TN_PAYLOAD_SHIFT) & V_LMASK);   // check null terminal
    }
//    if (query[o_last] != (sig[o_last] & V_UMASK)) return 0;                             // check last
    return (sig[0] & V_UMASK) | ((sig[slot_width - 1] >> LAST_TN_PAYLOAD_SHIFT) & V_LMASK);
}

// the client will likely probe array first, compute a hash if missing, then probe from hash start
static fu16 fast_probe_sigs(TypeNum query[], TypeNum sigs[], fu8 slot_width, fu16 num_slots) {
    for (fu32 o = 0; o < num_slots; o++) {
        if (*(sigs + o * slot_width) == TN_NULL) return 0;
        fu16 v = fast_compare_sig(query, sigs + o * slot_width, slot_width);
        if (v) return v;
    }
    return 0;
}

static jsize SC_new_size(ju8 num_args, ju8 num_slots) {
    // OPEN check range and return err (like in SC_init)
    ju8 slot_width = SLOT_WIDTH_FROM_NUM_ARGS(num_args);
    return sizeof(SelectorCache) + sizeof(TypeNum) * ((jsize)num_slots + 1) * (jsize)slot_width;
}

static err SC_init(SelectorCache *sc, ju8 num_args, ju8 num_slots) {
    ju8 slot_width = SLOT_WIDTH_FROM_NUM_ARGS(num_args);
    if (!(1 <= num_args && num_args <=16)) SIGNAL("num_args is not within {1, 16}");         // OPEN add num_args value to msg
    if (!(1 <= num_slots && num_slots <=128)) SIGNAL("num_slots is not within {1, 128}");

    sc -> slot_width = slot_width;
    sc -> num_slots = num_slots;
    sc -> hash_n_slots = 0x0000;
    TypeNum *query = P_QUERY(sc);
    for (int i=0; i < (int)slot_width; i++) query[i] = 0x0000;
    TypeNum *array = P_SIG_ARRAY(sc);
    for (int i=0; i < (int)slot_width * (int)num_slots; i++) array[i] = 0x0000;
    return ok;
}

static void SC_drop(SelectorCache *sc) {
}


#endif          // __J_FN_SELECTION_H