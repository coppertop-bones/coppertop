## coppertop - multiple-dispatch, partial functions and pipeline style for Python

Coppertop provides an alternative programming experience in Python via the following:

* multiple-dispatch
* partial functions
* piping syntax
* an embryonic [core library](https://github.com/coppertop-bones/coppertop-libs/tree/main/src/dm) of common functions

<br>


### Installation

`pip install coppertop-bones-libs` for the dm core library and the @coppertop decorator.\
`pip install coppertop` just for the @coppertop decorator.

At the moment needs to be git cloned and the setup.py manually run.

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
from coppertop.pipe import *

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
from dm.core import collect, inject

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
from dm.core import both
from dm.testing immport check, equals

actual = [1,2] >> both >> (lambda x, y: x + y) >> [3,4]
assert (1 >> equal >> 1) == True
actual >> check >> equal >> [4, 6]
```

<br> 


### Examples

#### Bag of M&Ms problem 

In [Why coppertop - MM problem from Think Bayes.ipynb](
https://github.com/coppertop-bones/coppertop-libs/blob/main/jupyter/Why%20coppertop%20-%20MM%20problem%20from%20Think%20Bayes.ipynb
) we implement a coppertop solution to the problem and silently introduce intersection types.

#### Cluedo notepad

See [algos.py](
https://github.com/coppertop-bones/coppertop-libs/blob/main/examples/dm/examples/cluedo/algos.py
), where we track a game of Cluedo and infer who did it. See [ex_games.py](
https://github.com/coppertop-bones/coppertop-libs/blob/main/examples/dm/examples/cluedo/ex_games.py
) and [cluedo-pad.ipynb](
https://github.com/coppertop-bones/coppertop-libs/blob/main/jupyter/cluedo-pad.ipynb
) for example game input and notepad output.

<br>


### a whimsical exercise for the ambitious

(both, collect, inject, addOne, appendStr, check, equals are all illustrated above)

```
from dm.core import to
[1,2] >> both >> (lambda x, y: x + y) >> [3,4] 
   >> collect >> (lambda x: x * 2)
   >> inject(_,1,_) >> (lambda x,y: x * y)
   >> addOne >> addOne >> addOne
   >> to >> str >> appendStr(_," red balloons go by")
   >> check >> equal >> ???
```

<br>


### Other
* [Hadley Wickham on pipes](https://r4ds.had.co.nz/pipes.html)
* [Comparison of coppertop style with other piped languages](https://github.com/coppertop-bones/docs/blob/main/docs/compare-with-other-piped-languages.md)

<br>

### Thanks

#### Inspired by
* [Magrittr](
https://magrittr.tidyverse.org/
) - a piping library for R
* [Arthur Whitney's](
https://en.wikipedia.org/wiki/Arthur_Whitney_(computer_scientist)
) ideas especially [kdb/q](https://code.kx.com/q/) and C style e.g. a [tiny k interpreter for educational purposes](
https://github.com/kparc/ksimple
)
* Smalltalk - especially the ideas of [Alan Kay](
https://en.wikipedia.org/wiki/Alan_Kay
) & [Rebecca Wirfs-Brock](
https://en.wikipedia.org/wiki/Rebecca_Wirfs-Brock
) and the [VisualWorks](
https://www.cincomsmalltalk.com/main/products/visualworks/
) and [Cuis](
https://cuis.st/
) implementations
* [Alexander A. Stepanov's](
http://stepanovpapers.com/
) ideas on templating and generics

#### Built using

<p><a href="https://www.jetbrains.com/pycharm/">
<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm.svg" width="200" height="100">
</a></p>

<p><a href="https://www.jetbrains.com/clion/">
<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/CLion.svg" width="160" height="80">
</a></p>
