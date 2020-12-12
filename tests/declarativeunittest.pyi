import typing as t
from construct.core import Construct

Buffer = t.Union[bytes, memoryview, bytearray]
ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")

devzero: t.BinaryIO

def raises(
    func: t.Callable[..., t.Any], *args: t.Any, **kw: t.Any
) -> t.Union[t.Any, Exception]: ...
def common(
    format: Construct[ParsedType, BuildTypes],
    datasample: Buffer,
    objsample: BuildTypes,
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
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
