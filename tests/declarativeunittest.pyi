from typing import Callable, TypeVar, Union, Any, Type, BinaryIO
from construct import *
from construct.lib import *

Buffer = Union[bytes, memoryview, bytearray]
ParsedType = TypeVar("ParsedType")
BuildTypes = TypeVar("BuildTypes")

devzero: BinaryIO

def raises(
    func: Callable[..., Any], *args: Any, **kw: Any
) -> Union[Any, Exception]: ...
def common(
    format: Construct[ParsedType, BuildTypes],
    datasample: Buffer,
    objsample: BuildTypes,
    sizesample: Union[int, Type[Exception]] = ...,
    **kw: Any
) -> None: ...
def commonhex(
    format: Construct[ParsedType, BuildTypes], hexdata: str
) -> None: ...
def commondumpdeprecated(
    format: Construct[ParsedType, BuildTypes], filename: str
) -> None: ...
def commondump(
    format: Construct[ParsedType, BuildTypes], filename: str
) -> None: ...
def commonbytes(
    format: Construct[ParsedType, BuildTypes], data: ParsedType
) -> None: ...
