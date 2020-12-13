# construct-typing
This project is an extension of the python package *construct*. This Repository consitst of two packages:

- **construct-stubs**: Adding .pyi for the whole *construct* package (according to  [PEP 561 stub-only packages](https://www.python.org/dev/peps/pep-0561/#stub-only-packages))
- **construct_typed**: Adding the additional classes that help with autocompletion and additional type hints.

## Installation
This package comply to PEP 561. So most of the static code analysers will recognise the stubs automatically.

You just have to type:
```
pip install construct-typing
```

## Usage
I'm mostly working with VSCode and Pylance (which works really great) ??? But i have also tested the stubs with mypy. ????


## Explanation
### Stubs
The **construct-stubs** package is used for creating type hints for the orignial *construct* package. In particular the `build` and `parse` methods get type hints. So the core of the stubs  are the `TypeVar`'s `ParsedType` and `BuildTypes`:
- The `build` method of a `Construct` converts an object of one of the types defined by `BuildTypes` to a `bytes` object.
- The `parse` method of a `Construct` converts a `bytes` object to an object of type `ParsedType`.

For each of the `Construct`s it is defined which type it is parsed to and from which it can be build. 
For example:
 - an `Int16ub` construct parses to an `int` and can be build from an `int`.
 - an `Bytes` construct parsed to a `bytes` and can be build from an `bytes`, `bytearray` or `memoryview`.
 - an `Array(5, Int16ub)` construct parses to a `ListContainer[int]` and can be build from an `List[int]`. 

The problem is to describe the more complex constructs like:
 - `Sequence` which has heterogenous subcons in comparison to an `Array` with only homogenous subcons. 
 - `Struct`, `BitStruct`, `Union` which has heterogenous and named subcons.

Currently only the very unspecific type `typing.Any` can be used as type hint (maybe in the future it can be optimised a little, when variadic generics become available). But the biggest disadvantage is that autocompletion for the named subcons is not available.


### Typed
To include autocompletion and further enhance the type hints for these complex constructs the **construct_typed** package is used as an extension to the original *construct* package.

It implements the following new types:
- TypedEnum
- TypedStruct
- TypedBitStruct
- TypedUnion


An example of the added `TypedStruct` class:

```python
from construct import Const, Int8ub, Array, this, Byte
from construct_typed import TypedContainer, Subcon, TypedStruct

class Image(TypedContainer):
    signature: Subcon(Const(b"BMP"))
    width: Subcon(Int8ub())
    height: Subcon(Int8ub())
    pixels: Subcon(Array(cs.this.width * cs.this.height, Byte()))

format = TypedStruct(Image)
obj = Image(width=3, height=2, pixels=[7, 8, 9, 11, 12, 13])
print(format.build(obj))
print(format.parse(b"BMP\x03\x02\x07\x08\t\x0b\x0c\r"))
```

An example of the added `TypedEnum` class:

