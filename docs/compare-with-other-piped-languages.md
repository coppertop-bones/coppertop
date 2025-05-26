### Comparison of unary piping with other languages

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

<br>


R with magrittr

```
TBD
```

<br>


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

<br>


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

<br>


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
