SEQUENCE

v0.2
- interpreter working for the two failing tests - which implies the list based stack is working?
- solicit feedback and code review

v0.3
- error types and sentinels in C
- building and testing in linux (Github's cheapest) on commit and deploying via pypi on demand - e.g. 0.2.1.wip1
- import bones functions into python and call
- all tests working and all old tests added to test suite
- improved constructors and coercions - so can write types and constructors, e.g. for Cluedo, and use the types easily


OTHER FEATURES
- type namespaces
- tvtuple, tvstruct, tvseq, tvmap, etc in C
- fitsWithin in C (with ability to add Python helpers)
- tc structs in C
- object allocation with bones metadata and boehm gc and Python proxies
- inference
- tc to bytecode
- bonetype enabled C99 to tc compiler
- implementations with CoW updates
