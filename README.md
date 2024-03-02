## coppertop - multiple-dispatch, partial functions and pipeline style for Python

Coppertop provides an alternative programming experience in Python via the following:

* multiple-dispatch
* partial functions
* piping syntax
* an embryonic [core library](https://github.com/coppertop-bones/dm/tree/main/src/dm) of common functions

<br>


### Installation

`pip install coppertop-bones-dm` for the dm core library and the @coppertop decorator.\
`pip install coppertop` just for the @coppertop decorator.


<br>

### Multiple-dispatch

To use multiple-dispatch decorate functions with @coppertop and use different type annotations. Missing annotations 
are taken as fallback wildcards. Class inheritance is ignored when matching caller and function signatures.

```
from coppertop.pipe import *

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


### Partial (application of) functions

syntax: `f(_, a)` -> `f(_)`  \
where `_` is used as a sentinel place-holder for arguments yet to be confirmed (TBC)

We create partials of @coppertop decorated functions when we use _ indicating deferred arguments. For example:

```
@coppertop
def appendStr(x, y):
    assert isinstance(x, str) and isinstance(y, str)
    return x + y

appendWorld = appendStr(_, " world!")           # first argument is deferred

assert appendWorld("hello") == "hello world!"
```

<br>


### Piping syntax

The @coppertop function decorator also extends functions with the `>>` operator
and so allows code to be written in a more essay style format - i.e. left-to-right and 
top-to-bottom. The idea is to make it easier to express program syntax (aka sequence).


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

#### binary style - takes 2 piped arguments and 0+ called arguments

syntax: `A >> f(args) >> B` -> `f(args)(A, B)`

```
from bones.core.errors import NotYetImplemented
import dm.core
from _ import collect, inject

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


#### ternary style - takes 3 piped arguments and 0+ called arguments

syntax: `A >> f(args) >> B >> C` -> `f(args)(A, B, C)`

```
from _ import both, check, equals

actual = [1,2] >> both >> (lambda x, y: x + y) >> [3,4]
assert (1 >> equal >> 1) == True
actual >> check >> equal >> [4, 6]
```

<br> 


### Example - Cluedo notepad

See [algos.py](https://github.com/coppertop-bones/dm/blob/main/examples/dm/examples/cluedo/algos.py), where 
we track a game of Cluedo and infer who did it. See [ex_games.py](https://github.com/coppertop-bones/dm/blob/main/examples/dm/examples/cluedo/ex_games.py) 
for example game input.

<br>


### a whimsical exercise for the ambitious

(both, collect, inject, addOne, appendStr, check, equals are all illustrated above)

```
from _ import to
[1,2] >> both >> (lambda x, y: x + y) >> [3,4] 
   >> collect >> (lambda x: x * 2)
   >> inject(_,1,_) >> (lambda x,y: x * y)
   >> addOne >> addOne >> addOne
   >> to >> str >> appendStr(_," red balloons go by")
   >> check >> equal >> ???
```

<br>


### Appendix - comparison of unary piping with other languages

Python (using the @coppertop decorator)

```
@coppertop     # default is unary
def unaryAddOne(x):
  return x + 1

@coppertop
def unaryAdd2Args(x, y):
  return x + y

@coppertop
def unaryAdd3Args(x, y, z):
  return x + y + z

unaryAddOne(1)
1 >> unaryAddOne

unaryAdd2Args(1,2)
1 >> unaryAdd2Args(_,2)
2 >> unaryAdd2Args(1,_)

unaryAdd3Args(1,2,3)
1 >> unaryAdd3Args(_,2,3)
2 >> unaryAdd3Args(1,_,3)
3 >> unaryAdd3Args(1,2,_)
```

R - TBD

```
# with magrittr
```

q / kdb (an APL derivative)

```
unaryAddOne: {x + 1}
unaryAdd2args: {x + y}
unaryAdd3Args: {x + y + z}

unaryAddOne[1]
unaryAddOne 1

unaryAdd2Args[1;2]
unaryAdd2Args[;2] 1
unaryAdd2Args[1;] 2

unaryAdd3Args[1;2;3]
unaryAdd3Args[;2;3] 1
unaryAdd3Args[1;;3] 2
unaryAdd3Args[1;2;] 3
```

<br>

F# / OCaml

```
unaryAddOne x = x + 1
unaryAdd2Args x y = x + y
unaryAdd3Args x y z = x + y + z

unaryAddOne 1
1 |> unaryAddOne

unaryAdd2Args 1 2
2 |> unaryAdd2Args 1

unaryAdd3Args 1 2 3
3 |> unaryAdd3Args 1 2
```

Smalltalk

```
unaryAddOne
    ^ self + 1

unaryAdd2Args: y
    ^ self + y

unaryAdd3Args: y with: z
    ^ self + y + z

1 addOne
1 unaryAdd2Args: 2
1 unaryAdd3Args: 2 with: 3
```

bones (influenced by q/kdb and Smalltalk)

```
unaryAddOne: {x + 1}
unaryAdd2Args: {x + y}
unaryAdd3Args: {x + y + z}

unaryAddOne(1)
1 unaryAddOne

unaryAdd2Args(1,2)
1 unaryAdd2Args(,2)
2 unaryAdd2Args(1,)

unaryAdd3Args(1,2,3)
1 unaryAdd2Args(,2,3)
2 unaryAdd2Args(1,,3)
3 unaryAdd2Args(1,2,)
```
