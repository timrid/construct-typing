# construct-typing
[![PyPI](https://img.shields.io/pypi/v/construct-typing)](https://pypi.org/project/construct-typing/)
![PyPI - Implementation](https://img.shields.io/pypi/implementation/construct-typing)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/construct-typing)
![GitHub](https://img.shields.io/github/license/timrid/construct-typing)

This project is an extension of the python package [*construct*](https://pypi.org/project/construct/), which is a powerful **declarative** and **symmetrical** parser and builder for binary data. This Repository consists of two packages:

- **construct-stubs**: Adding .pyi for the whole *construct 2.10* package (according to  [PEP 561 stub-only packages](https://www.python.org/dev/peps/pep-0561/#stub-only-packages))
- **construct_typed**: Adding additional classes that help with autocompletion and additional type hints.

## Installation
This package comply to [PEP 561](https://www.python.org/dev/peps/pep-0561/). So most of the static code analysers will recognise the stubs automatically. The installation only requires:
```
pip install construct-typing
```

## Tests
The stubs are tested against the pytests of the *construct* package in a slightly modified form. Since the tests are relatively detailed I think most cases are covered.

The new typed constructs have new written pytests, which also passes all pytests and the static type checkers.

The following static type checkers are fully supported:
- [x] mypy
- [x] pyright

## Explanation
### Stubs
The **construct-stubs** package is used for creating type hints for the orignial *construct* package. In particular the `build` and `parse` methods get type hints. So the core of the stubs  are the `TypeVar`'s `ParsedType` and `BuildTypes`:
- `Construct.build`: converts an object of one of the types defined by `BuildTypes` to a `bytes` object.
- `Construct.parse`: converts a `bytes` object to an object of type `ParsedType`.

For each `Construct` the stub file defines to which type it parses to and from which it can be build. For example:

| Construct            | parses to (ParsedType)         | builds from (BuildTypes)                 |
| -------------------- | ------------------------------ | ---------------------------------------- |
| `Int16ub`            | `int`                          | `int`                                    |
| `Bytes`              | `bytes`                        | `bytes`, `bytearray` or `memoryview`     |
| `Array(5, Int16ub)`  | `ListContainer[int]`           | `typing.List[int]`                       |
| `Struct("i" / Byte)` | `Container[typing.Any]`        | `typing.Dict[str, typing.Any]` or `None` |

The problem is to describe the more complex constructs like:
 - `Sequence`, `FocusedSeq` which has heterogenous subcons in comparison to an `Array` with only homogenous subcons. 
 - `Struct`, `BitStruct`, `LazyStruct`, `Union` which has heterogenous and named subcons.

Currently only the very unspecific type `typing.Any` can be used as type hint (maybe in the future it can be optimised a little, when [variadic generics](https://mail.python.org/archives/list/typing-sig@python.org/thread/SQVTQYWIOI4TIO7NNBTFFWFMSMS2TA4J/) become available). But the biggest disadvantage is that autocompletion for the named subcons is not available.

Note: The stubs are based on *construct* in Version 2.10.


### Typed
**!!! EXPERIMENTAL VERSION !!!**

To include autocompletion and further enhance the type hints for these complex constructs the **construct_typed** package is used as an extension to the original *construct* package. It is mainly a few Adapters with the focus on type hints.

It implements the following new constructs:
- `DataclassStruct`: similar to `construct.Struct` but strictly tied to `DataclassMixin` and `@dataclasses.dataclass`
- `DataclassBitStruct`: similar to `construct.BitStruct` but strictly tied to `DataclassMixin` and `@dataclasses.dataclass`
- `TEnum`: similar to `construct.Enum` but strictly tied to a `TEnumBase` class
- `TFlagsEnum`: similar to `construct.FlagsEnum` but strictly tied to a `TFlagsEnumBase` class

These types are strongly typed, which means that there is no difference between the `ParsedType` and the `BuildTypes`. So to build one of the constructs the correct type is enforced. The disadvantage is that the code will be a little bit longer, because you can not for example use a normal `dict` to build an `DataclassStruct`. But the big advantage is, that if you use the correct container type instead of a `dict`, the static code analyses can do its magic and find potential type errors and missing values without running the code itself.


A short example:

```python
import dataclasses
import typing as t
from construct import Array, Byte, Const, Int8ub, this
from construct_typed import DataclassMixin, DataclassStruct, EnumBase, TEnum, csfield

class Orientation(EnumBase):
    HORIZONTAL = 0
    VERTICAL = 1

@dataclasses.dataclass
class Image(DataclassMixin):
    signature: bytes = csfield(Const(b"BMP"))
    orientation: Orientation = csfield(TEnum(Int8ub, Orientation))
    width: int = csfield(Int8ub)
    height: int = csfield(Int8ub)
    pixels: t.List[int] = csfield(Array(this.width * this.height, Byte))

format = DataclassStruct(Image)
obj = Image(
    orientation=Orientation.VERTICAL,
    width=3,
    height=2,
    pixels=[7, 8, 9, 11, 12, 13],
)
print(format.build(obj))
print(format.parse(b"BMP\x01\x03\x02\x07\x08\t\x0b\x0c\r"))
```
Output:
```
b'BMP\x01\x03\x02\x07\x08\t\x0b\x0c\r'
Image: 
    signature = b'BMP' (total 3)
    orientation = Orientation.VERTICAL
    width = 3
    height = 2
    pixels = ListContainer:
        7
        8
        9
        11
        12
        13
```


