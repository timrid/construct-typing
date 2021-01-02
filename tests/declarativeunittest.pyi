import typing as t
from construct import *
from construct.lib import *
import construct_typed as cst

Buffer = t.Union[bytes, memoryview, bytearray]
ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")
ContainerType = t.TypeVar("ContainerType", bound=cst.TContainerBase)
T = t.TypeVar("T")

IdentType = t.TypeVar("IdentType")

def ident(p1: IdentType) -> IdentType: ...

devzero: t.BinaryIO

def raises(
    func: t.Callable[..., t.Any], *args: t.Any, **kw: t.Any
) -> t.Union[t.Any, Exception]: ...
@t.overload
def common(
    format: cst.TStruct[ContainerType],
    datasample: Buffer,
    objsample: t.Union[ContainerType, t.Dict[str, t.Any]],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[ListContainer[ParsedType], t.Any],
    datasample: Buffer,
    objsample: t.List[ParsedType],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[Container[t.Any], t.Any],
    datasample: Buffer,
    objsample: t.Dict[str, t.Any],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[t.Union[EnumInteger, EnumIntegerString], t.Any],
    datasample: Buffer,
    objsample: t.Union[int, str],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[HexDisplayedInteger, t.Any],
    datasample: Buffer,
    objsample: t.Union[HexDisplayedInteger, int],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[HexDisplayedBytes, t.Any],
    datasample: Buffer,
    objsample: t.Union[HexDisplayedBytes, bytes],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[HexDisplayedDict[str, t.Any], t.Any],
    datasample: Buffer,
    objsample: t.Dict[str, t.Any],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[HexDumpDisplayedBytes, t.Any],
    datasample: Buffer,
    objsample: t.Union[HexDumpDisplayedBytes, bytes],
    sizesample: t.Union[int, t.Type[Exception]] = ...,
    **kw: t.Any
) -> None: ...
@t.overload
def common(
    format: Construct[HexDumpDisplayedDict[str, t.Any], t.Any],
    datasample: Buffer,
    objsample: t.Dict[str, t.Any],
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
