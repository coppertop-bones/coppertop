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

#ifndef __J_VMEM_ARENA_H
#define __J_VMEM_ARENA_H

#include "j.h"


// https://github.com/dlang/phobos/blob/master/std/experimental/allocator/mmap_allocator.d
// https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/mmap.2.html
// https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/madvise.2.html#//apple_ref/doc/man/2/madvise

// https://stackoverflow.com/questions/55768549/in-malloc-why-use-brk-at-all-why-not-just-use-mmap

// overcommit - https://www.etalabs.net/overcommit.html - mmap - readonly, then mmap read-write what you need


#include <unistd.h>
#include <sys/mman.h>

#include "cache_line_size.h"


#define CACHE_LINE_SIZE_M1_COMPATIBLE 128
#define PAGE_SIZE_M1_COMPATIBLE _16K



// int munmap(void *addr, jsize len);
// int madvise(void *addr, jsize len, int advice);
// MADV_SEQUENTIAL
// MADV_FREE pages may be reused right away



// VA (standing for virtual arena) is an arena style allocator that tracks in units of whole number of pages
// it informs the os whenever a whole page is no longer needed from physical memory
// it is fixed size
// it forces us to be aware of alignment and cache lines
// we use it to store types, symbols (interned subset of strings) and enums (small groups of interned strings)
// we want dispatch caches to be compact - but we don't know the size of the args yet
// inference types can be done in a large scratch pad -

// need space for hash maps which may need resizing, growable arrays to hold utfs strings, object pointers



typedef struct VA {
    // new line
    jsize cachelinesize;
    jsize pagesize;
    void *next_free_page;       // if we need to realloc we just drop the page(s) back to OS rather than reusing ourself
    void *ceiling;              // points to the byte after my last byte
    ju32 num_reserved;         // can count up to 16TB at 4096k per page
    ju32 num_unreserved;
} VA;


typedef struct Chunk {
    void *ceiling;              // points to the byte after my last byte
} Chunk;


static VA * init_va(jsize numpages) {
    jsize pagesize = db_os_page_size();
    jsize cachelinesize = db_os_cache_line_size();

    // for the mo just code for my M1
    if (pagesize != PAGE_SIZE_M1_COMPATIBLE) return NULL;
    if (cachelinesize != CACHE_LINE_SIZE_M1_COMPATIBLE) return NULL;

    jsize totalsize = numpages * pagesize;
    if (totalsize > _1TB) return NULL;
    VA *va = (VA*) mmap((void*) 0, totalsize, PROT_READ, MAP_ANON | MAP_PRIVATE, -1, 0);
    if ((ji64) -1 == (ji64) va) return NULL;
    int protect_res = mprotect((void*) va, pagesize, PROT_READ | PROT_WRITE);
    if (protect_res == -1) return NULL;
    va->cachelinesize = db_os_cache_line_size();
    va->pagesize = pagesize;
    va->next_free_page = (void*)((jsize) va + pagesize);
    va->ceiling = (void*)((jsize) va + totalsize);
    va->num_reserved = 1;
    va->num_unreserved = 0;
    return va;
}


static void * reserve(VA *va, jsize numpages) {
    Chunk *chunk = (Chunk *) va->next_free_page;        // we allocate the new chunk at the  what was the next free page
    void *chunk_ceiling = (void*)((jsize)va->next_free_page + numpages * va->pagesize);
    if (chunk_ceiling > va->ceiling) return NULL;       // there's not enough vm left to satisfy the request
    int protect_res = mprotect((void*) chunk, numpages * va->pagesize, PROT_READ | PROT_WRITE);
    if (protect_res == -1) return NULL;
    // TODO to verify os can give us the memory - if not return NULL  // will MADV_WILLNEED work?
    chunk->ceiling = chunk_ceiling;
    va->next_free_page = chunk_ceiling;
    va->num_reserved += numpages;
    return (void *) chunk;
}

static int unreserve(VA *va, Chunk *chunk) {
    jsize size = (jsize) chunk->ceiling - (jsize) chunk;
    int protect_res = mprotect((void*) chunk, size, 0);
    if (protect_res == -1) return 0;
    va->num_unreserved += (ju32)(size / va->pagesize);
    madvise((void*) chunk, size, MADV_FREE);            // tell os can reclaim the physical memory
    return 1;
}



#endif /* __J_ALLOC_H */