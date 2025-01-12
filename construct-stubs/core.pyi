import enum
import io
import os
import sys
import typing as t

import arrow
from construct.lib import (
    Container,
    ContainerType,
    HexDisplayedBytes,
    HexDisplayedDict,
    HexDisplayedInteger,
    HexDumpDisplayedBytes,
    HexDumpDisplayedDict,
    ListContainer,
    ListType,
    RebufferedBytesIO,
)
from typing_extensions import Buffer

# unfortunately, there are a few duplications with "typing", e.g. Union and Optional, which is why the t. prefix must be used everywhere

# Some of the Constructs can be optimised when the following typing optimisations are available:
#   - Variadic Generics: https://mail.python.org/archives/list/typing-sig@python.org/thread/SQVTQYWIOI4TIO7NNBTFFWFMSMS2TA4J/
#   - Higher Kinded Types: https://github.com/python/typing/issues/548
#   - Higher Kinded Types: https://sobolevn.me/2020/10/higher-kinded-types-in-python

ReadableBuffer: t.TypeAlias = Buffer
StreamType = t.IO[bytes]
FilenameType = t.Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]
PathType = str
ContextKWType = t.Any

# ===============================================================================
# exceptions
# ===============================================================================
class ConstructError(Exception):
    path: t.Optional[PathType]
    def __init__(
        self, message: str = ..., path: t.Optional[PathType] = ...
    ) -> None: ...

class SizeofError(ConstructError): ...
class AdaptationError(ConstructError): ...
class ValidationError(ConstructError): ...
class StreamError(ConstructError): ...
class FormatFieldError(ConstructError): ...
class IntegerError(ConstructError): ...
class StringError(ConstructError): ...
class MappingError(ConstructError): ...
class RangeError(ConstructError): ...
class RepeatError(ConstructError): ...
class ConstError(ConstructError): ...
class IndexFieldError(ConstructError): ...
class CheckError(ConstructError): ...
class ExplicitError(ConstructError): ...
class NamedTupleError(ConstructError): ...
class TimestampError(ConstructError): ...
class UnionError(ConstructError): ...
class SelectError(ConstructError): ...
class SwitchError(ConstructError): ...
class StopFieldError(ConstructError): ...
class PaddingError(ConstructError): ...
class TerminatedError(ConstructError): ...
class RawCopyError(ConstructError): ...
class RotationError(ConstructError): ...
class ChecksumError(ConstructError): ...
class CancelParsing(ConstructError): ...

# ===============================================================================
# used internally
# ===============================================================================
def stream_read(
    stream: StreamType, length: int, path: t.Optional[PathType]
) -> bytes: ...
def stream_read_entire(stream: StreamType, path: t.Optional[PathType]) -> bytes: ...
def stream_write(
    stream: StreamType, data: bytes, length: int, path: t.Optional[PathType]
) -> None: ...
def stream_seek(
    stream: StreamType, offset: int, whence: int, path: t.Optional[PathType]
) -> int: ...
def stream_tell(stream: StreamType, path: t.Optional[PathType]) -> int: ...
def stream_size(stream: StreamType) -> int: ...
def stream_iseof(stream: StreamType) -> bool: ...
def evaluate(param: ConstantOrContextLambda2[T], context: Context) -> T: ...

# ===============================================================================
# abstract constructs
# ===============================================================================
ParsedType = t.TypeVar("ParsedType", covariant=True)
BuildTypes = t.TypeVar("BuildTypes", contravariant=True)

class Construct(t.Generic[ParsedType, BuildTypes]):
    name: t.Optional[str]
    docs: str
    flagbuildnone: bool
    parsed: t.Optional[t.Callable[[ParsedType, Context], None]]
    def parse(self, data: ReadableBuffer, **contextkw: ContextKWType) -> ParsedType: ...
    def parse_stream(
        self, stream: StreamType, **contextkw: ContextKWType
    ) -> ParsedType: ...
    def parse_file(
        self, filename: FilenameType, **contextkw: ContextKWType
    ) -> ParsedType: ...
    def build(self, obj: BuildTypes, **contextkw: ContextKWType) -> bytes: ...
    def build_stream(
        self, obj: BuildTypes, stream: StreamType, **contextkw: ContextKWType
    ) -> None: ...
    def build_file(
        self, obj: BuildTypes, filename: FilenameType, **contextkw: ContextKWType
    ) -> None: ...
    def sizeof(self, **contextkw: ContextKWType) -> int: ...
    def compile(
        self, filename: FilenameType = ...
    ) -> Construct[ParsedType, BuildTypes]: ...
    def benchmark(
        self, sampledata: ReadableBuffer, filename: FilenameType = ...
    ) -> str: ...
    def export_ksy(
        self, schemaname: str = ..., filename: FilenameType = ...
    ) -> str: ...
    def __rtruediv__(
        self, name: t.Optional[t.AnyStr]
    ) -> Renamed[ParsedType, BuildTypes]: ...
    __rdiv__: t.Callable[[str], Construct[ParsedType, BuildTypes]]
    def __mul__(
        self,
        other: t.Union[str, bytes, t.Callable[[ParsedType, Context], None]],
    ) -> Renamed[ParsedType, BuildTypes]: ...
    def __rmul__(
        self,
        other: t.Union[str, bytes, t.Callable[[ParsedType, Context], None]],
    ) -> Renamed[ParsedType, BuildTypes]: ...
    def __add__(self, other: Construct[t.Any, t.Any]) -> Struct: ...
    def __rshift__(self, other: Construct[t.Any, t.Any]) -> Sequence: ...
    def __getitem__(
        self, count: t.Union[int, t.Callable[[Context], int]]
    ) -> Array[ParsedType, BuildTypes,]: ...
    def _parse(self, stream: StreamType, context: Context, path: PathType) -> ParsedType: ...
    def _parsereport(self, stream: StreamType, context: Context, path: PathType) -> ParsedType: ...
    def _build(self, obj: BuildTypes, stream: StreamType, context: Context, path: PathType) -> int: ...
    def _sizeof(self, context: Context, path: PathType) -> int: ...

@t.type_check_only
class Context(Container[t.Any]):
    _: Context  # optional field
    _params: Context  # optional field
    _root: Context  # optional field
    _parsing: bool
    _building: bool
    _sizing: bool
    _subcons: Container[Construct[t.Any, t.Any]]
    _io: StreamType  # optional field
    _index: int  # optional field

ValueType = t.TypeVar("ValueType")
ConstantOrContextLambda = t.Union[ValueType, t.Callable[[Context], t.Any]]
ConstantOrContextLambda2 = t.Union[ValueType, t.Callable[[Context], ValueType]]

SubconParsedType = t.TypeVar("SubconParsedType", covariant=True)
SubconBuildTypes = t.TypeVar("SubconBuildTypes", contravariant=True)

class Subconstruct(
    t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
    Construct[ParsedType, BuildTypes],
):
    subcon: Construct[SubconParsedType, SubconBuildTypes]
    @t.overload
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...
    @t.overload
    def __init__(  # type: ignore
        self,
        *args: t.Any,
        **kwargs: t.Any,
    ) -> None: ...

class Adapter(
    Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
):
    def __init__(
        self, subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> None: ...
    def _decode(
        self, obj: SubconBuildTypes, context: Context, path: PathType
    ) -> ParsedType: ...
    def _encode(
        self, obj: BuildTypes, context: Context, path: PathType
    ) -> SubconBuildTypes: ...

class SymmetricAdapter(
    Adapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]
): ...

class Validator(
    SymmetricAdapter[
        SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes
    ]
):
    def _validate(
        self, obj: SubconBuildTypes, context: Context, path: PathType
    ) -> bool: ...

class Tunnel(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    def _decode(self, data: bytes, context: Context, path: PathType) -> bytes: ...
    def _encode(self, data: bytes, context: Context, path: PathType) -> bytes: ...

class Compiled(Construct[t.Any, t.Any]):
    source: t.Optional[str]
    defersubcon: t.Optional[Construct[t.Any, t.Any]]
    parsefunc: t.Callable[[StreamType, Context], t.Any]
    buildfunc: t.Callable[[t.Any, StreamType, Context], t.Any]
    def __init__(
        self,
        parsefunc: t.Callable[[StreamType, Context], t.Any],
        buildfunc: t.Callable[[t.Any, StreamType, Context], t.Any],
    ) -> None: ...

# ===============================================================================
# bytes and bits
# ===============================================================================
class Bytes(Construct[bytes, t.Union[bytes, bytearray, int]]):
    length: ConstantOrContextLambda[int]
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
    ) -> None: ...

GreedyBytes: Construct[bytes, t.Union[bytes, bytearray]]

def Bitwise(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> t.Union[
    Transformed[SubconParsedType, SubconBuildTypes],
    Restreamed[SubconParsedType, SubconBuildTypes],
]: ...
def Bytewise(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> t.Union[
    Transformed[SubconParsedType, SubconBuildTypes],
    Restreamed[SubconParsedType, SubconBuildTypes],
]: ...

# ===============================================================================
# integers and floats
# ===============================================================================
class FormatField(Construct[ParsedType, BuildTypes]):
    fmtstr: str
    length: int
    if sys.version_info >= (3, 8):
        ENDIANITY = t.Union[t.Literal["=", "<", ">"], str]
        FORMAT_INT = t.Literal["B", "H", "L", "Q", "b", "h", "l", "q"]
        FORMAT_FLOAT = t.Literal["f", "d", "e"]
        FORMAT_BOOL = t.Literal["?"]
        @t.overload
        def __new__(
            cls: "type[FormatField[int, int]]",
            endianity: str,
            format: FORMAT_INT,
        ) -> FormatField[int, int]: ...
        @t.overload
        def __new__(
            cls: "type[FormatField[float, float]]",
            endianity: str,
            format: FORMAT_FLOAT,
        ) -> FormatField[float, float]: ...
        @t.overload
        def __new__(
            cls: "type[FormatField[bool, bool]]",
            endianity: str,
            format: FORMAT_BOOL,
        ) -> FormatField[bool, bool]: ...
        @t.overload
        def __new__(
            cls: "type[FormatField[t.Any, t.Any]]",
            endianity: str,
            format: str,
        ) -> FormatField[t.Any, t.Any]: ...

    else:
        def __new__(
            cls: "type[FormatField[t.Any, t.Any]]",
            endianity: str,
            format: str,
        ) -> FormatField[t.Any, t.Any]: ...

class BytesInteger(Construct[int, int]):
    length: ConstantOrContextLambda[int]
    signed: bool
    swapped: ConstantOrContextLambda[bool]
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
        signed: bool = ...,
        swapped: ConstantOrContextLambda[bool] = ...,
    ) -> None: ...

class BitsInteger(Construct[int, int]):
    length: ConstantOrContextLambda[int]
    signed: bool
    swapped: ConstantOrContextLambda[bool]
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
        signed: bool = ...,
        swapped: ConstantOrContextLambda[bool] = ...,
    ) -> None: ...

Bit: BitsInteger
Nibble: BitsInteger
Octet: BitsInteger

Int8ub: FormatField[int, int]
Int16ub: FormatField[int, int]
Int32ub: FormatField[int, int]
Int64ub: FormatField[int, int]
Int8sb: FormatField[int, int]
Int16sb: FormatField[int, int]
Int32sb: FormatField[int, int]
Int64sb: FormatField[int, int]
Int8ul: FormatField[int, int]
Int16ul: FormatField[int, int]
Int32ul: FormatField[int, int]
Int64ul: FormatField[int, int]
Int8sl: FormatField[int, int]
Int16sl: FormatField[int, int]
Int32sl: FormatField[int, int]
Int64sl: FormatField[int, int]
Int8un: FormatField[int, int]
Int16un: FormatField[int, int]
Int32un: FormatField[int, int]
Int64un: FormatField[int, int]
Int8sn: FormatField[int, int]
Int16sn: FormatField[int, int]
Int32sn: FormatField[int, int]
Int64sn: FormatField[int, int]

Byte: FormatField[int, int]
Short: FormatField[int, int]
Int: FormatField[int, int]
Long: FormatField[int, int]

Float16b: FormatField[float, float]
Float16l: FormatField[float, float]
Float16n: FormatField[float, float]
Float32b: FormatField[float, float]
Float32l: FormatField[float, float]
Float32n: FormatField[float, float]
Float64b: FormatField[float, float]
Float64l: FormatField[float, float]
Float64n: FormatField[float, float]

Half: FormatField[float, float]
Single: FormatField[float, float]
Double: FormatField[float, float]

Int24ub: BytesInteger
Int24ul: BytesInteger
Int24un: BytesInteger
Int24sb: BytesInteger
Int24sl: BytesInteger
Int24sn: BytesInteger

VarInt: Construct[int, int]
ZigZag: Construct[int, int]

# ===============================================================================
# strings
# ===============================================================================
possiblestringencodings: t.Dict[str, int]

class StringEncoded(Construct[str, str]):
    if sys.version_info >= (3, 8):
        ENCODING_1 = t.Literal["ascii", "utf8", "utf_8", "u8"]
        ENCODING_2 = t.Literal["utf16", "utf_16", "u16", "utf_16_be", "utf_16_le"]
        ENCODING_4 = t.Literal["utf32", "utf_32", "u32", "utf_32_be", "utf_32_le"]
        ENCODING = t.Union[str, ENCODING_1, ENCODING_2, ENCODING_4]
    else:
        ENCODING = str
    encoding: ENCODING
    def __init__(
        self,
        subcon: Construct[bytes, bytes],
        encoding: ENCODING,
    ) -> None: ...

def PaddedString(
    length: ConstantOrContextLambda[int], encoding: StringEncoded.ENCODING
) -> StringEncoded: ...
def PascalString(
    lengthfield: Construct[int, int], encoding: StringEncoded.ENCODING
) -> StringEncoded: ...
def CString(encoding: StringEncoded.ENCODING) -> StringEncoded: ...
def GreedyString(encoding: StringEncoded.ENCODING) -> StringEncoded: ...

# ===============================================================================
# mappings
# ===============================================================================
Flag: Construct[bool, bool]

class EnumInteger(int): ...

class EnumIntegerString(str):
    @staticmethod
    def new(intvalue: int, stringvalue: str) -> EnumIntegerString: ...

class Enum(
    Adapter[int, int, t.Union[EnumInteger, EnumIntegerString], t.Union[int, str]]
):
    encmapping: t.Dict[str, int]
    decmapping: t.Dict[int, EnumIntegerString]
    ksymapping: t.Dict[int, str]
    def __init__(
        self,
        subcon: Construct[int, int],
        *merge: t.Union[t.Type[enum.IntEnum], t.Type[enum.IntFlag]],
        **mapping: int,
    ) -> None: ...
    def __getattr__(self, name: str) -> EnumIntegerString: ...

class BitwisableString(str):
    def __or__(self, other: BitwisableString) -> BitwisableString: ...

class FlagsEnum(
    Adapter[int, int, Container[bool], t.Union[int, str, t.Dict[str, bool]]]
):
    flags: t.Dict[str, int]
    reverseflags: t.Dict[int, str]
    def __init__(
        self,
        subcon: Construct[int, int],
        *merge: t.Union[t.Type[enum.IntEnum], t.Type[enum.IntFlag]],
        **flags: int,
    ) -> None: ...
    def __getattr__(self, name: str) -> BitwisableString: ...

class Mapping(Adapter[SubconParsedType, SubconBuildTypes, t.Any, t.Any]):
    decmapping: t.Dict[int, str]
    encmapping: t.Dict[str, int]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        mapping: t.Dict[t.Any, t.Any],
    ) -> None: ...

# ===============================================================================
# structures and sequences
# ===============================================================================
# this can maybe made better when variadic generics are available
class Struct(Construct[Container[t.Any], t.Optional[t.Dict[str, t.Any]]]):
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...
    def __getattr__(self, name: str) -> t.Any: ...

# this can maybe made better when variadic generics are available
class Sequence(Construct[ListContainer[t.Any], t.Optional[t.List[t.Any]]]):
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...
    def __getattr__(self, name: str) -> t.Any: ...

# ===============================================================================
# arrays ranges and repeaters
# ===============================================================================
class Array(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        ListContainer[SubconParsedType],  # type: ignore
        t.List[SubconBuildTypes],  # type: ignore
    ]
):
    count: ConstantOrContextLambda[int]
    discard: bool
    def __init__(
        self,
        count: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        discard: bool = ...,
    ) -> None: ...

class GreedyRange(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        ListContainer[SubconParsedType],  # type: ignore
        t.List[SubconBuildTypes],  # type: ignore
    ]
):
    discard: bool
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        discard: bool = ...,
    ) -> None: ...

class RepeatUntil(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        ListContainer[SubconParsedType],  # type: ignore
        t.List[SubconBuildTypes],  # type: ignore
    ]
):
    predicate: t.Union[
        bool,
        t.Callable[[SubconParsedType, ListContainer[SubconParsedType], Context], bool],
    ]
    discard: bool
    def __init__(
        self,
        predicate: t.Union[
            bool,
            t.Callable[
                [SubconParsedType, ListContainer[SubconParsedType], Context], bool
            ],
        ],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        discard: bool = ...,
    ) -> None: ...

# ===============================================================================
# specials
# ===============================================================================
class Renamed(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        newname: t.Optional[str] = ...,
        newdocs: t.Optional[str] = ...,
        newparsed: t.Optional[t.Callable[[t.Any, Context], None]] = ...,
    ) -> None: ...

# ===============================================================================
# miscellaneous
# ===============================================================================
class Const(Subconstruct[t.Any, t.Any, ParsedType, BuildTypes]):
    value: BuildTypes
    @t.overload
    def __new__(
        cls: "type[Const[bytes, t.Optional[bytes]]]",
        value: bytes,
    ) -> Const[bytes, t.Optional[bytes]]: ...
    @t.overload
    def __new__(
        cls: "type[Const[SubconParsedType, t.Optional[SubconBuildTypes]]]",
        value: SubconBuildTypes,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> Const[SubconParsedType, t.Optional[SubconBuildTypes]]: ...

class Computed(Construct[ParsedType, None]):
    func: ConstantOrContextLambda2[ParsedType]
    def __init__(
        self,
        func: ConstantOrContextLambda2[ParsedType],
    ) -> None: ...

Index: Construct[int, t.Any]

class Rebuild(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, None]):
    func: ConstantOrContextLambda[SubconBuildTypes]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        func: ConstantOrContextLambda[SubconBuildTypes],
    ) -> None: ...

class Default(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        SubconParsedType,
        t.Optional[SubconBuildTypes],
    ]
):
    value: ConstantOrContextLambda[SubconBuildTypes]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        value: ConstantOrContextLambda[SubconBuildTypes],
    ) -> None: ...

class Check(Construct[None, None]):
    func: ConstantOrContextLambda[bool]
    def __init__(
        self,
        func: ConstantOrContextLambda[bool],
    ) -> None: ...

Error: Construct[None, None]

class FocusedSeq(Construct[t.Any, t.Any]):
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    def __init__(
        self,
        parsebuildfrom: ConstantOrContextLambda[str],
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...
    def __getattr__(self, name: str) -> t.Any: ...

Pickled: Construct[t.Any, t.Any]

Numpy: Construct[t.Any, t.Any]

class NamedTuple(
    Adapter[
        SubconParsedType,
        SubconBuildTypes,
        t.Tuple[t.Any, ...],
        t.Union[t.Tuple[t.Any, ...], t.List[t.Any], t.Dict[str, t.Any]],
    ]
):
    tuplename: str
    tuplefields: str
    factory: Construct[SubconParsedType, SubconBuildTypes]
    def __init__(
        self,
        tuplename: str,
        tuplefields: str,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

if sys.version_info >= (3, 8):
    MSDOS = t.Literal["msdos"]
else:
    MSDOS = str

class TimestampAdapter(
    Adapter[SubconParsedType, SubconBuildTypes, arrow.Arrow, arrow.Arrow]
): ...

@t.overload
def Timestamp(
    subcon: Construct[int, int], unit: MSDOS, epoch: MSDOS
) -> TimestampAdapter[int, int]: ...
@t.overload
def Timestamp(
    subcon: Construct[int, int],
    unit: t.Union[int, float],
    epoch: t.Union[int, arrow.Arrow],
) -> TimestampAdapter[int, int]: ...
@t.overload
def Timestamp(
    subcon: Construct[float, float],
    unit: t.Union[int, float],
    epoch: t.Union[int, arrow.Arrow],
) -> TimestampAdapter[float, float]: ...

K = t.TypeVar("K")
V = t.TypeVar("V")

class Hex(Adapter[t.Any, t.Any, ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls: "type[Hex[HexDisplayedInteger, BuildTypes]]",
        subcon: Construct[int, BuildTypes],
    ) -> Hex[HexDisplayedInteger, BuildTypes]: ...
    @t.overload
    def __new__(
        cls: "type[Hex[HexDisplayedBytes, BuildTypes]]",
        subcon: Construct[bytes, BuildTypes],
    ) -> Hex[HexDisplayedBytes, BuildTypes]: ...
    @t.overload
    def __new__(
        cls: "type[Hex[HexDisplayedDict[str, t.Union[int, bytes, SubconParsedType]], BuildTypes,]]",
        subcon: Construct[RawCopyObj[SubconParsedType], BuildTypes],
    ) -> Hex[
        HexDisplayedDict[str, t.Union[int, bytes, SubconParsedType]],
        BuildTypes,
    ]: ...
    @t.overload
    def __new__(
        cls: "type[Hex[HexDisplayedDict[str, t.Any], BuildTypes]]",
        subcon: Construct[Container[t.Any], BuildTypes],
    ) -> Hex[HexDisplayedDict[str, t.Any], BuildTypes]: ...
    @t.overload
    def __new__(
        cls: "type[Hex[SubconParsedType, SubconBuildTypes]]",
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> Hex[SubconParsedType, SubconBuildTypes]: ...

class HexDump(Adapter[t.Any, t.Any, ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls: "type[HexDump[HexDumpDisplayedBytes, BuildTypes]]",
        subcon: Construct[bytes, BuildTypes],
    ) -> HexDump[HexDumpDisplayedBytes, BuildTypes]: ...
    @t.overload
    def __new__(
        cls: "type[HexDump[HexDumpDisplayedDict[str, t.Union[int, bytes, SubconParsedType]],BuildTypes,]]",
        subcon: Construct[RawCopyObj[SubconParsedType], BuildTypes],
    ) -> HexDump[
        HexDumpDisplayedDict[str, t.Union[int, bytes, SubconParsedType]],
        BuildTypes,
    ]: ...
    @t.overload
    def __new__(
        cls: "type[HexDump[HexDumpDisplayedDict[str, t.Any], BuildTypes]]",
        subcon: Construct[Container[t.Any], BuildTypes],
    ) -> HexDump[HexDumpDisplayedDict[str, t.Any], BuildTypes]: ...
    @t.overload
    def __new__(
        cls: "type[HexDump[SubconParsedType, SubconBuildTypes]]",
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> HexDump[SubconParsedType, SubconBuildTypes]: ...

# ===============================================================================
# conditional
# ===============================================================================
# this can maybe made better when variadic generics are available
class Union(Construct[Container[t.Any], t.Dict[str, t.Any]]):
    parsefrom: t.Optional[ConstantOrContextLambda[t.Union[int, str]]]
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    def __init__(
        self,
        parsefrom: t.Optional[ConstantOrContextLambda[t.Union[int, str]]],
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...
    def __getattr__(self, name: str) -> t.Any: ...

# this can maybe made better when variadic generics are available
class Select(Construct[t.Any, t.Any]):
    subcons: t.List[Construct[t.Any, t.Any]]
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...

def Optional(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> Construct[t.Union[SubconParsedType, None], t.Union[SubconBuildTypes, None]]: ...

ThenParsedType = t.TypeVar("ThenParsedType")
ThenBuildTypes = t.TypeVar("ThenBuildTypes")
ElseParsedType = t.TypeVar("ElseParsedType")
ElseBuildTypes = t.TypeVar("ElseBuildTypes")

class IfThenElse(Construct[ParsedType, BuildTypes]):
    condfunc: ConstantOrContextLambda[bool]
    thensubcon: Construct[t.Any, t.Any]
    elsesubcon: Construct[t.Any, t.Any]
    @t.overload
    def __new__(
        cls: "type[IfThenElse[t.Union[ThenParsedType, ElseParsedType], t.Union[ThenBuildTypes, ElseBuildTypes]]]",
        condfunc: ConstantOrContextLambda[bool],
        thensubcon: Construct[ThenParsedType, ThenBuildTypes],
        elsesubcon: Construct[ElseParsedType, ElseBuildTypes],
    ) -> "IfThenElse[t.Union[ThenParsedType, ElseParsedType], t.Union[ThenBuildTypes, ElseBuildTypes]]": ...
    @t.overload
    def __new__(
        cls: "type[IfThenElse[t.Any, t.Any]]",
        condfunc: ConstantOrContextLambda[bool],
        thensubcon: Construct[t.Any, t.Any],
        elsesubcon: Construct[t.Any, t.Any],
    ) -> "IfThenElse[t.Any, t.Any]": ...

def If(
    condfunc: ConstantOrContextLambda[bool],
    subcon: Construct[ThenParsedType, ThenBuildTypes],
) -> IfThenElse[t.Optional[ThenParsedType], t.Optional[ThenBuildTypes]]: ...

SwitchType = t.TypeVar("SwitchType")

class Switch(Construct[ParsedType, BuildTypes]):
    keyfunc: ConstantOrContextLambda[t.Any]
    cases: t.Dict[t.Any, Construct[t.Any, t.Any]]
    default: Construct[t.Any, t.Any]
    @t.overload
    def __new__(
        cls: "type[Switch[int, t.Optional[int]]]",
        keyfunc: ConstantOrContextLambda[SwitchType],
        cases: t.Dict[SwitchType, Construct[int, int]],
        default: t.Optional[Construct[int, int]] = ...,
    ) -> Switch[int, t.Optional[int]]: ...
    @t.overload
    def __new__(
        cls: "type[Switch[t.Any, t.Any]]",
        keyfunc: ConstantOrContextLambda[t.Any],
        cases: t.Dict[t.Any, Construct[t.Any, t.Any]],
        default: t.Optional[Construct[t.Any, t.Any]] = ...,
    ) -> Switch[t.Any, t.Any]: ...

class StopIf(Construct[None, None]):
    condfunc: ConstantOrContextLambda[bool]
    def __init__(
        self,
        condfunc: ConstantOrContextLambda[bool],
    ) -> None: ...

# ===============================================================================
# alignment and padding
# ===============================================================================
def Padding(
    length: ConstantOrContextLambda[int], pattern: bytes = ...
) -> Padded[None, None]: ...

class Padded(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    length: ConstantOrContextLambda[int]
    pattern: bytes
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        pattern: bytes = ...,
    ) -> None: ...

class Aligned(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    modulus: ConstantOrContextLambda[int]
    pattern: bytes
    def __init__(
        self,
        modulus: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        pattern: bytes = ...,
    ) -> None: ...

def AlignedStruct(
    modulus: ConstantOrContextLambda[int],
    *subcons: Construct[t.Any, t.Any],
    **subconskw: Construct[t.Any, t.Any],
) -> Struct: ...
def BitStruct(
    *subcons: Construct[t.Any, t.Any], **subconskw: Construct[t.Any, t.Any]
) -> t.Union[
    Transformed[Container[t.Any], t.Dict[str, t.Any]],
    Restreamed[Container[t.Any], t.Dict[str, t.Any]],
]: ...

# ===============================================================================
# stream manipulation
# ===============================================================================
class Pointer(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    offset: ConstantOrContextLambda[int]
    stream: t.Optional[t.Callable[[Context], StreamType]]
    def __init__(
        self,
        offset: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        stream: t.Optional[t.Callable[[Context], StreamType]] = ...,
    ) -> None: ...

class Peek(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        SubconParsedType,
        t.Union[SubconBuildTypes, None],
    ]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class Seek(Construct[int, None]):
    at: ConstantOrContextLambda[int]
    if sys.version_info >= (3, 8):
        WHENCE = t.Literal[0, 1, 2]
    else:
        WHENCE = int
    whence: ConstantOrContextLambda[WHENCE]
    def __init__(
        self,
        at: ConstantOrContextLambda[int],
        whence: ConstantOrContextLambda[WHENCE] = ...,
    ) -> None: ...

Tell: Construct[int, None]
Pass: Construct[None, None]
Terminated: Construct[None, None]

# ===============================================================================
# tunneling and byte/bit swapping
# ===============================================================================
@t.type_check_only
class RawCopyObj(t.Generic[ParsedType], Container[t.Any]):
    data: bytes
    value: ParsedType
    offset1: int
    offset2: int
    length: int

class RawCopy(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        RawCopyObj[SubconParsedType],
        t.Optional[t.Dict[str, t.Union[SubconBuildTypes, bytes]]],
    ]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

def ByteSwapped(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> Transformed[SubconParsedType, SubconBuildTypes]: ...
def BitsSwapped(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> t.Union[
    Transformed[SubconParsedType, SubconBuildTypes],
    Restreamed[SubconParsedType, SubconBuildTypes],
]: ...

class Prefixed(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    lengthfield: Construct[SubconParsedType, SubconBuildTypes]
    includelength: t.Optional[bool]
    def __init__(
        self,
        lengthfield: Construct[int, int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        includelength: t.Optional[bool] = ...,
    ) -> None: ...

def PrefixedArray(
    countfield: Construct[int, int],
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Array[SubconParsedType, SubconBuildTypes,]: ...

class FixedSized(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    length: ConstantOrContextLambda[int]
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class NullTerminated(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    term: bytes
    include: t.Optional[bool]
    consume: t.Optional[bool]
    require: t.Optional[bool]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        term: bytes = ...,
        include: t.Optional[bool] = ...,
        consume: t.Optional[bool] = ...,
        require: t.Optional[bool] = ...,
    ) -> None: ...

class NullStripped(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    pad: bytes
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        pad: bytes = ...,
    ) -> None: ...

class RestreamData(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, None]
):
    datafunc: t.Union[
        bytes, io.BytesIO, Construct[bytes, t.Any], t.Callable[[Context], bytes]
    ]
    def __init__(
        self,
        datafunc: t.Union[
            bytes, io.BytesIO, Construct[bytes, t.Any], t.Callable[[Context], bytes]
        ],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class Transformed(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    decodefunc: t.Callable[[bytes], bytes]
    decodeamount: t.Optional[int]
    encodefunc: t.Callable[[bytes], bytes]
    encodeamount: t.Optional[int]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        decodefunc: t.Callable[[bytes], bytes],
        decodeamount: t.Optional[int],
        encodefunc: t.Callable[[bytes], bytes],
        encodeamount: t.Optional[int],
    ) -> None: ...

class Restreamed(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    decoder: t.Callable[[bytes], bytes]
    decoderunit: int
    encoder: t.Callable[[bytes], bytes]
    encoderunit: int
    sizecomputer: t.Callable[[int], int]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        decoder: t.Callable[[bytes], bytes],
        decoderunit: int,
        encoder: t.Callable[[bytes], bytes],
        encoderunit: int,
        sizecomputer: t.Callable[[int], int],
    ) -> None: ...

class ProcessXor(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    padfunc: ConstantOrContextLambda2[t.Union[int, bytes]]
    def __init__(
        self,
        padfunc: ConstantOrContextLambda2[t.Union[int, bytes]],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class ProcessRotateLeft(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    amount: ConstantOrContextLambda2[int]
    group: ConstantOrContextLambda2[int]
    def __init__(
        self,
        amount: ConstantOrContextLambda2[int],
        group: ConstantOrContextLambda2[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

T = t.TypeVar("T")

class Checksum(t.Generic[T, ParsedType, BuildTypes], Construct[ParsedType, BuildTypes]):
    checksumfield: Construct[ParsedType, BuildTypes]
    hashfunc: t.Callable[[T], BuildTypes]
    bytesfunc: t.Callable[[Context], T]
    def __init__(
        self,
        checksumfield: Construct[ParsedType, BuildTypes],
        hashfunc: t.Callable[[T], BuildTypes],
        bytesfunc: t.Callable[[Context], T],
    ) -> None: ...

class Compressed(Tunnel[SubconParsedType, SubconBuildTypes]):
    encoding: str
    level: t.Optional[int]
    lib: t.Any
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        encoding: str,
        level: t.Optional[int] = ...,
    ) -> None: ...

class CompressedLZ4(Tunnel[SubconParsedType, SubconBuildTypes]):
    lib: t.Any
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class Rebuffered(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    stream2: RebufferedBytesIO
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        tailcutoff: t.Optional[int] = ...,
    ) -> None: ...

# ===============================================================================
# lazy equivalents
# ===============================================================================
class Lazy(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        t.Callable[[], SubconParsedType],
        t.Union[t.Callable[[], SubconParsedType], SubconParsedType],
    ]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class LazyContainer(t.Generic[ContainerType], t.Dict[str, ContainerType]):
    def __getattr__(self, name: str) -> ContainerType: ...
    def __getitem__(self, index: t.Union[str, int]) -> ContainerType: ...
    def keys(self) -> t.Iterator[str]: ...  # type: ignore
    def values(self) -> t.List[ContainerType]: ...  # type: ignore
    def items(self) -> t.List[t.Tuple[str, ContainerType]]: ...  # type: ignore

class LazyStruct(Construct[LazyContainer[t.Any], t.Optional[t.Dict[str, t.Any]]]):
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    _subconsindexes: t.Dict[str, int]
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...
    def __getattr__(self, name: str) -> t.Any: ...

class LazyListContainer(t.List[ListType]): ...

class LazyArray(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        ListContainer[SubconParsedType],  # type: ignore
        t.List[SubconBuildTypes],  # type: ignore
    ]
):
    count: ConstantOrContextLambda[int]
    def __init__(
        self,
        count: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class LazyBound(Construct[ParsedType, BuildTypes]):
    subconfunc: t.Callable[[], Construct[ParsedType, BuildTypes]]
    def __init__(
        self,
        subconfunc: t.Callable[[], Construct[ParsedType, BuildTypes]],
    ) -> None: ...

# ===============================================================================
# adapters and validators
# ===============================================================================
class ExprAdapter(Adapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        decoder: t.Callable[[SubconParsedType, Context], ParsedType],
        encoder: t.Callable[[BuildTypes, Context], SubconBuildTypes],
    ) -> None: ...

class ExprSymmetricAdapter(
    ExprAdapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        encoder: t.Callable[[BuildTypes, Context], SubconBuildTypes],
    ) -> None: ...

class ExprValidator(Validator[SubconParsedType, SubconBuildTypes]):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        validator: t.Callable[[SubconParsedType, Context], bool],
    ) -> None: ...

def OneOf(
    subcon: Construct[SubconParsedType, SubconBuildTypes],
    valids: t.Container[SubconParsedType],
) -> ExprValidator[SubconParsedType, SubconBuildTypes]: ...
def NoneOf(
    subcon: Construct[SubconParsedType, SubconBuildTypes],
    invalids: t.Container[SubconParsedType],
) -> ExprValidator[SubconParsedType, SubconBuildTypes]: ...
def Filter(
    predicate: t.Callable[[SubconParsedType, Context], bool],
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> ExprSymmetricAdapter[
    SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes
]: ...

class Slicing(
    Adapter[
        SubconParsedType,
        SubconBuildTypes,
        ListContainer[SubconParsedType],  # type: ignore
        t.List[SubconBuildTypes],  # type: ignore
    ]
):
    def __init__(
        self,
        subcon: t.Union[
            Array[
                SubconParsedType,
                SubconBuildTypes,
            ],
            GreedyRange[
                SubconParsedType,
                SubconBuildTypes,
            ],
        ],
        count: int,
        start: t.Optional[int],
        stop: t.Optional[int],
        step: int = ...,
        empty: t.Optional[SubconParsedType] = ...,
    ) -> None: ...

class Indexing(
    Adapter[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    def __init__(
        self,
        subcon: t.Union[
            Array[
                SubconParsedType,
                SubconBuildTypes,
            ],
            GreedyRange[
                SubconParsedType,
                SubconBuildTypes,
            ],
        ],
        count: int,
        index: int,
        empty: t.Optional[SubconParsedType] = ...,
    ) -> None: ...
