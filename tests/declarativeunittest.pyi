import typing as t
from construct import *
from construct.lib import *
import construct_typed as cst

Buffer = t.Union[bytes, memoryview, bytearray]
ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")
T = t.TypeVar("T")

IdentType = t.TypeVar("IdentType")

def ident(p1: IdentType) -> IdentType: ...

devzero: t.BinaryIO

def raises(
    func: t.Callable[..., t.Any], *args: t.Any, **kw: t.Any
) -> t.Union[t.Any, Exception]: ...
@t.overload
def common(
    format: cst.TStruct[ParsedType],
    datasample: Buffer,
    objsample: t.Union[ParsedType, t.Dict[str, t.Any]],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[ParsedType, BuildTypes],
    datasample: Buffer,
    objsample: ParsedType,
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
def setattrs(obj: T, **kwargs: t.Any) -> T: ...
def commonhex(format: Construct[ParsedType, BuildTypes], hexdata: str) -> None: ...
def commondumpdeprecated(
    format: Construct[ParsedType, BuildTypes], filename: str
) -> None: ...
def commondump(format: Construct[ParsedType, BuildTypes], filename: str) -> None: ...
def commonbytes(
    format: Construct[ParsedType, BuildTypes], data: ParsedType
) -> None: ...
