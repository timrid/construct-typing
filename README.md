# construct-typing

## 
This project is an extension of the python package `construct`. This Repository consitst of two packages:

- **construct-stubs**: Adding .pyi for the whole `construct` package (according to  [PEP 561 stub-only packages](https://www.python.org/dev/peps/pep-0561/#stub-only-packages))
- **construct-typed**: Adding the additional classes `TypedStruct` and `TypedEnum` that help with autocompletion in cooperation with the stubs.

## Motivation


## Examples

An example of the added `TypedStruct` class:

```python
from construct import *
from construct_typed import *

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

