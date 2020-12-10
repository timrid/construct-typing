from construct.core import *
from construct_typed import *

a = Const(b"asd")

class Image(TypedContainer):
    signature: Subcon(Const(b"asd"))
    width: Subcon(Int8ub)
    height: Subcon(Int8ub)
    pixels: Subcon(Array(cs.this.width * cs.this.height, Byte()))

format = TypedStruct(Image)
obj = Image(width=3, height=2, pixels=[7, 8, 9, 11, 12, 13])
print(format.build(obj))
print(format.parse(b"BMP\x03\x02\x07\x08\t\x0b\x0c\r"))