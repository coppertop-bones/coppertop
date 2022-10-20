## coppertop-bones - partial functions, multi-dispatch and pipeline style for Python

Coppertop provides a bones-style aggregation manipulation experience in Python via the following:

* partial (application of) functions
* multiple-dispatch
* piping syntax
* data focussed type system with atoms, intersections, unions, products, exponentials, overloads and type schemas thus 
  allowing Python to be a library implementation language for bones
* an embryonic [core library](https://github.com/DangerMouseB/coppertop-bones/tree/main/src/dm) of common functions 


<br>

### Partial (application of) functions

By decorating a function with @coppertop (and importing _) we can easily create partial functions, for example:

syntax: `f(_, a)` -> `f(_)`  \
where `_` is used as a sentinel place-holder for arguments yet to be confirmed (TBC)

```
from coppertop.pipe import *

@coppertop
def appendStr(x, y):
    assert isinstance(x, str) and isinstance(y, str)
    return x + y

appendWorld = appendStr(_, " world!")

assert appendWorld("hello") == "hello world!"
```

<br>


### Multiple-dispatch

Just redefine functions with different type annotations. Missing annotations are taken as 
fallback wildcards. Class inheritance is ignored when matching caller and function signatures.

```
@coppertop
def addOne(x:int) -> int:
    return x + 1
    
@coppertop
def addOne(x:str) -> str:
    return x + 'One'
    
@coppertop
def addOne(x):                 # fallback
    if isinstance(x, list):
        return x + [1]
    else:
        raise NotYetImplemented()

assert addOne(1) == 2
assert addOne('Three Two ') == 'Three Two One'
assert addOne([0]) == [0, 1]
```

<br>


### Piping syntax

The @coppertop function decorator also extends functions with the `>>` operator
and so allows code to be written in a more essay style format - i.e. left-to-right and 
top-to-bottom. The idea is to make it easy to express the syntax (aka sequence) of a solution.


<br>

#### unary style - takes 1 piped argument and 0+ called arguments

syntax: `A >> f(args)` -> `f(args)(A)`

```
from coppertop.pipe import *

@coppertop(style=unary)
def addOne(x):
    return x + 1

1 >> addOne
"hello" >> appendStr(_," ") >> appendStr(_, "world!")

1 >> partial(lambda x: x +1)
```

<br>

#### binary style - takes 2 piped argument and 0+ called arguments

syntax: `A >> f(args) >> B` -> `f(args)(A, B)`

```
from bones.core.errors import NotYetImplemented
import dm.core
from coppertop import collect, inject

@coppertop(style=binary)
def add(x, y):
    return x + y

@coppertop(style=binary)
def op(x, action, y):
    if action == "+":
        return x + y
    else:
        raise NotYetImplemented()

1 >> add >> 1
1 >> op(_,"+",_) >> 1
[1,2] >> collect >> (lambda x: x + 1)
[1,2,3] >> inject(_,0,_) >> (lambda x,y: x + y)
```

<br>

#### ternary style - takes 3 piped argument and 0+ called arguments

syntax: `A >> f(args) >> B >> C` -> `f(args)(A, B, C)`

```
from coppertop import both, check, equal

actual = [1,2] >> both >> (lambda x, y: x + y) >> [3,4]
assert (1 >> equal >> 1) == True
actual >> check >> equal >> [4, 6]
```

<br> 

#### as an exercise for the reader
```
from coppertop import to
[1,2] >> both >> (lambda x, y: x + y) >> [3,4] 
   >> collect >> (lambda x: x * 2)
   >> inject(_,1,_) >> (lambda x,y: x * y)
   >> addOne >> addOne >> addOne
   >> to >> str >> appendStr(_," red balloons go by")
   >> check >> equal >> ???
```

<br>


### Bones type system

As an introduction, consider:

```
from bones.lang.metatypes import BTAtom, S
from dm.core.types import num, index, txt, N
num = BTAtom.ensure('num')      # nominal
_ccy = BTAtom.ensure('_ccy')    # nominal
ccy = num & _ccy                # intersection
ccy + null                      # union
ccy * index * txt               # tuple (sequence of types)
S(name=txt, age=num)            # struct
N ** ccy                        # collection of ccy accessed by an ordinal (N)
txt ** ccy                      # collection of ccy accessed by a python string
(num*num) ^ num                 # (num, num) -> num - a function
T, T1, T2, ...                  # type variable - to be inferred at build time
```

<br>


### Example - Cluedo notepad

See [algos.py](https://github.com/DangerMouseB/coppertop-bones-demo/blob/main/src/dm/examples/cluedo/algos.py), where 
we track a game of Cluedo and infer who did it. See [games.py](https://github.com/DangerMouseB/coppertop-bones-demo/blob/main/src/dm/examples/cluedo/games.py) 
for example game input.
