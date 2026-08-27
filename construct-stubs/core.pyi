import enum
import io
import os
import typing as t

import arrow
from construct.lib import (
    Container,
    HexDisplayedBytes,
    HexDisplayedDict,
    HexDisplayedInteger,
    HexDumpDisplayedBytes,
    HexDumpDisplayedDict,
    ListContainer,
    RebufferedBytesIO,
)
from construct.lib.containers import ContainerType, ListType
from cryptography.hazmat.primitives.ciphers import Cipher
from cryptography.hazmat.primitives.ciphers.aead import AESCCM, AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives.ciphers.modes import Mode
from typing_extensions import Buffer, TypeAlias

# unfortunately, there are a few duplications with "typing", e.g. Union and Optional, which is why the t. prefix must be used everywhere

# Some of the Constructs can be optimised when the following typing optimisations are available:
#   - Variadic Generics: https://mail.python.org/archives/list/typing-sig@python.org/thread/SQVTQYWIOI4TIO7NNBTFFWFMSMS2TA4J/
#   - Higher Kinded Types: https://github.com/python/typing/issues/548
#   - Higher Kinded Types: https://sobolevn.me/2020/10/higher-kinded-types-in-python

ReadableBuffer: TypeAlias = Buffer
StreamType = t.IO[bytes]
FilenameType = str | bytes | os.PathLike[str] | os.PathLike[bytes]
PathType = str
ContextKWType = t.Any

# ===============================================================================
# exceptions
# ===============================================================================
class ConstructError(Exception):
    path: PathType | None
    def __init__(
        self, message: str = ..., path: PathType | None = ...
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
class CipherError(ConstructError): ...

# ===============================================================================
# used internally
# ===============================================================================
def stream_read(
    stream: StreamType, length: int, path: PathType | None
) -> bytes: ...
def stream_read_entire(stream: StreamType, path: PathType | None) -> bytes: ...
def stream_write(
    stream: StreamType, data: bytes, length: int, path: PathType | None
) -> None: ...
def stream_seek(
    stream: StreamType, offset: int, whence: int, path: PathType | None
) -> int: ...
def stream_tell(stream: StreamType, path: PathType | None) -> int: ...
def stream_size(stream: StreamType) -> int: ...
def stream_iseof(stream: StreamType) -> bool: ...
def evaluate(param: ConstantOrContextLambda2[T], context: Context) -> T: ...

class BytesIOWithOffsets(io.BytesIO):
    @staticmethod
    def from_reading(
        stream: StreamType, length: int, path: PathType
    ) -> BytesIOWithOffsets: ...
    def __init__(
        self, contents: bytes, parent_stream: StreamType, offset: int
    ) -> None: ...
    def tell(self) -> int: ...
    def seek(self, offset: int, whence: int = ...) -> int: ...

# ===============================================================================
# abstract constructs
# ===============================================================================
ParsedType = t.TypeVar("ParsedType", covariant=True)
BuildTypes = t.TypeVar("BuildTypes", contravariant=True)

class Construct(t.Generic[ParsedType, BuildTypes]):
    name: str | None
    docs: str
    flagbuildnone: bool
    parsed: t.Callable[[ParsedType, Context], None] | None
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
        self, name: t.AnyStr | None
    ) -> Renamed[ParsedType, BuildTypes]: ...
    __rdiv__: t.Callable[[str], Construct[ParsedType, BuildTypes]]
    def __mul__(
        self,
        other: str | bytes | t.Callable[[ParsedType, Context], None],
    ) -> Renamed[ParsedType, BuildTypes]: ...
    def __rmul__(
        self,
        other: str | bytes | t.Callable[[ParsedType, Context], None],
    ) -> Renamed[ParsedType, BuildTypes]: ...
    def __add__(self, other: Construct[t.Any, t.Any]) -> Struct: ...
    def __rshift__(self, other: Construct[t.Any, t.Any]) -> Sequence: ...
    def __getitem__(
        self, count: int | t.Callable[[Context], int]
    ) -> Array[
        ParsedType,
        BuildTypes,
    ]: ...
    def _parse(
        self, stream: StreamType, context: Context, path: PathType
    ) -> ParsedType: ...
    def _parsereport(
        self, stream: StreamType, context: Context, path: PathType
    ) -> ParsedType: ...
    # In most implementations, `_build()` actually returns `ParsedType`, in some others it
    # returns `BuildTypes` or something else entirely. `t.Any` seems a good compromise.
    def _build(
        self, obj: BuildTypes, stream: StreamType, context: Context, path: PathType
    ) -> t.Any: ...
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
ConstantOrContextLambda = ValueType | t.Callable[[Context], t.Any]
ConstantOrContextLambda2 = ValueType | t.Callable[[Context], ValueType]

SubconParsedType = t.TypeVar("SubconParsedType")
SubconBuildTypes = t.TypeVar("SubconBuildTypes")

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
    source: str | None
    defersubcon: Construct[t.Any, t.Any] | None
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
class Bytes(Construct[bytes, bytes | bytearray | int]):
    length: ConstantOrContextLambda[int]
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
    ) -> None: ...

GreedyBytes: Construct[bytes, bytes | bytearray]

def Bitwise(
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Transformed[SubconParsedType, SubconBuildTypes] | Restreamed[SubconParsedType, SubconBuildTypes]: ...
def Bytewise(
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Transformed[SubconParsedType, SubconBuildTypes] | Restreamed[SubconParsedType, SubconBuildTypes]: ...

# ===============================================================================
# integers and floats
# ===============================================================================
class FormatField(Construct[ParsedType, BuildTypes]):
    fmtstr: str
    length: int
    ENDIANITY = t.Literal["=", "<", ">"] | str
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
    ENCODING_1 = t.Literal["ascii", "utf8", "utf_8", "u8"]
    ENCODING_2 = t.Literal["utf16", "utf_16", "u16", "utf_16_be", "utf_16_le"]
    ENCODING_4 = t.Literal["utf32", "utf_32", "u32", "utf_32_be", "utf_32_le"]
    ENCODING = str | ENCODING_1 | ENCODING_2 | ENCODING_4
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
    Adapter[int, int, EnumInteger | EnumIntegerString, int | str]
):
    encmapping: t.Dict[str, int]
    decmapping: t.Dict[int, EnumIntegerString]
    ksymapping: t.Dict[int, str]
    def __init__(
        self,
        subcon: Construct[int, int],
        *merge: t.Type[enum.IntEnum] | t.Type[enum.IntFlag],
        **mapping: int,
    ) -> None: ...
    def __getattr__(self, name: str) -> EnumIntegerString: ...

class BitwisableString(str):
    def __or__(self, other: BitwisableString) -> BitwisableString: ...

class FlagsEnum(
    Adapter[int, int, Container[bool], int | str | t.Dict[str, bool]]
):
    flags: t.Dict[str, int]
    reverseflags: t.Dict[int, str]
    def __init__(
        self,
        subcon: Construct[int, int],
        *merge: t.Type[enum.IntEnum] | t.Type[enum.IntFlag],
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
class Struct(Construct[Container[t.Any], t.Dict[str, t.Any] | None]):
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any],
    ) -> None: ...
    def __getattr__(self, name: str) -> t.Any: ...

# this can maybe made better when variadic generics are available
class Sequence(Construct[ListContainer[t.Any], t.List[t.Any] | None]):
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
        ListContainer[SubconParsedType],
        t.List[SubconBuildTypes],
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
        ListContainer[SubconParsedType],
        t.List[SubconBuildTypes],
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
        ListContainer[SubconParsedType],
        t.List[SubconBuildTypes],
    ]
):
    predicate: bool | t.Callable[[SubconParsedType, ListContainer[SubconParsedType], Context], bool]
    discard: bool
    def __init__(
        self,
        predicate: bool | t.Callable[[SubconParsedType, ListContainer[SubconParsedType], Context], bool],
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
        newname: str | None = ...,
        newdocs: str | None = ...,
        newparsed: t.Callable[[t.Any, Context], None] | None = ...,
    ) -> None: ...

# ===============================================================================
# miscellaneous
# ===============================================================================
class Const(Subconstruct[t.Any, t.Any, ParsedType, BuildTypes]):
    value: BuildTypes
    @t.overload
    def __new__(
        cls: "type[Const[bytes, bytes | None]]",
        value: bytes,
    ) -> Const[bytes, bytes | None]: ...
    @t.overload
    def __new__(
        cls: "type[Const[SubconParsedType, SubconBuildTypes | None]]",
        value: SubconBuildTypes,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> Const[SubconParsedType, SubconBuildTypes | None]: ...

class Computed(Construct[ParsedType, None]):
    func: ConstantOrContextLambda2[ParsedType]
    @t.overload
    def __init__(
        self,
        func: t.Callable[[Context], ParsedType],
    ) -> None: ...
    @t.overload
    def __init__(
        self,
        func: ParsedType,
    ) -> None: ...

Index: Construct[int, t.Any]

class Rebuild(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, None]):
    func: ConstantOrContextLambda2[SubconBuildTypes]
    @t.overload
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        func: SubconBuildTypes,
    ) -> None: ...
    @t.overload
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        func: t.Callable[[Context], SubconBuildTypes],
    ) -> None: ...

class Default(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        SubconParsedType,
        SubconBuildTypes | None,
    ]
):
    value: ConstantOrContextLambda2[SubconBuildTypes]
    @t.overload
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        value: SubconBuildTypes,
    ) -> None: ...
    @t.overload
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        value: t.Callable[[Context], SubconBuildTypes],
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
        t.Tuple[t.Any, ...] | t.List[t.Any] | t.Dict[str, t.Any],
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

MSDOS = t.Literal["msdos"]

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
    unit: int | float,
    epoch: int | arrow.Arrow,
) -> TimestampAdapter[int, int]: ...
@t.overload
def Timestamp(
    subcon: Construct[float, float],
    unit: int | float,
    epoch: int | arrow.Arrow,
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
        cls: "type[Hex[HexDisplayedDict[str, int | bytes | SubconParsedType], BuildTypes,]]",
        subcon: Construct[RawCopyObj[SubconParsedType], BuildTypes],
    ) -> Hex[
        HexDisplayedDict[str, int | bytes | SubconParsedType],
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
        cls: "type[HexDump[HexDumpDisplayedDict[str, int | bytes | SubconParsedType],BuildTypes,]]",
        subcon: Construct[RawCopyObj[SubconParsedType], BuildTypes],
    ) -> HexDump[
        HexDumpDisplayedDict[str, int | bytes | SubconParsedType],
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
    parsefrom: ConstantOrContextLambda[int | str] | None
    subcons: t.List[Construct[t.Any, t.Any]]
    _subcons: t.Dict[str, Construct[t.Any, t.Any]]
    def __init__(
        self,
        parsefrom: ConstantOrContextLambda[int | str] | None,
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
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Construct[SubconParsedType | None, SubconBuildTypes | None]: ...

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
        cls: "type[IfThenElse[ThenParsedType | ElseParsedType, ThenBuildTypes | ElseBuildTypes]]",
        condfunc: ConstantOrContextLambda[bool],
        thensubcon: Construct[ThenParsedType, ThenBuildTypes],
        elsesubcon: Construct[ElseParsedType, ElseBuildTypes],
    ) -> "IfThenElse[ThenParsedType | ElseParsedType, ThenBuildTypes | ElseBuildTypes]": ...
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
) -> IfThenElse[ThenParsedType | None, ThenBuildTypes | None]: ...

SwitchType = t.TypeVar("SwitchType")

class Switch(Construct[ParsedType, BuildTypes]):
    keyfunc: ConstantOrContextLambda[t.Any]
    cases: t.Dict[t.Any, Construct[t.Any, t.Any]]
    default: Construct[t.Any, t.Any]
    @t.overload
    def __new__(
        cls: "type[Switch[int, int | None]]",
        keyfunc: ConstantOrContextLambda[SwitchType],
        cases: t.Dict[SwitchType, Construct[int, int]],
        default: Construct[int, int] | None = ...,
    ) -> Switch[int, int | None]: ...
    @t.overload
    def __new__(
        cls: "type[Switch[t.Any, t.Any]]",
        keyfunc: ConstantOrContextLambda[t.Any],
        cases: t.Dict[t.Any, Construct[t.Any, t.Any]],
        default: Construct[t.Any, t.Any] | None = ...,
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
) -> Transformed[Container[t.Any], t.Dict[str, t.Any]] | Restreamed[Container[t.Any], t.Dict[str, t.Any]]: ...

# ===============================================================================
# stream manipulation
# ===============================================================================
class Pointer(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    offset: ConstantOrContextLambda[int]
    stream: t.Callable[[Context], StreamType] | None
    def __init__(
        self,
        offset: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        stream: t.Callable[[Context], StreamType] | None = ...,
    ) -> None: ...

class Peek(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        SubconParsedType,
        SubconBuildTypes | None,
    ]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class OffsettedEnd(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    endoffset: ConstantOrContextLambda[int]
    def __init__(
        self,
        endoffset: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class Seek(Construct[int, None]):
    at: ConstantOrContextLambda[int]
    WHENCE = t.Literal[0, 1, 2]
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
        t.Dict[str, SubconBuildTypes | bytes] | None,
    ]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

def ByteSwapped(
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Transformed[SubconParsedType, SubconBuildTypes]: ...
def BitsSwapped(
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Transformed[SubconParsedType, SubconBuildTypes] | Restreamed[SubconParsedType, SubconBuildTypes]: ...

class Prefixed(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    lengthfield: Construct[SubconParsedType, SubconBuildTypes]
    includelength: bool | None
    def __init__(
        self,
        lengthfield: Construct[int, int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        includelength: bool | None = ...,
    ) -> None: ...

def PrefixedArray(
    countfield: Construct[int, int],
    subcon: Construct[SubconParsedType, SubconBuildTypes],
) -> Array[
    SubconParsedType,
    SubconBuildTypes,
]: ...

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
    include: bool | None
    consume: bool | None
    require: bool | None
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        term: bytes = ...,
        include: bool | None = ...,
        consume: bool | None = ...,
        require: bool | None = ...,
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
    datafunc: bytes | io.BytesIO | Construct[bytes, t.Any] | t.Callable[[Context], bytes]
    def __init__(
        self,
        datafunc: bytes | io.BytesIO | Construct[bytes, t.Any] | t.Callable[[Context], bytes],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class Transformed(
    Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    decodefunc: t.Callable[[bytes], bytes]
    decodeamount: int | None
    encodefunc: t.Callable[[bytes], bytes]
    encodeamount: int | None
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        decodefunc: t.Callable[[bytes], bytes],
        decodeamount: int | None,
        encodefunc: t.Callable[[bytes], bytes],
        encodeamount: int | None,
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
    padfunc: ConstantOrContextLambda2[int | bytes]
    def __init__(
        self,
        padfunc: ConstantOrContextLambda2[int | bytes],
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

class Checksum(t.Generic[T, ParsedType, BuildTypes], Construct[ParsedType, BuildTypes | None]):
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
    level: int | None
    lib: t.Any
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        encoding: str,
        level: int | None = ...,
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
        tailcutoff: int | None = ...,
    ) -> None: ...

class EncryptedSym(Tunnel[SubconParsedType, SubconBuildTypes]):
    cipher: ConstantOrContextLambda2[Cipher[Mode]]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        cipher: ConstantOrContextLambda2[Cipher[Mode]],
    ) -> None: ...

class EncryptedSymAead(Tunnel[SubconParsedType, SubconBuildTypes]):
    cipher: ConstantOrContextLambda2[AESGCM | AESCCM | ChaCha20Poly1305]
    nonce: ConstantOrContextLambda2[bytes]
    associated_data: ConstantOrContextLambda2[bytes]
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        cipher: ConstantOrContextLambda2[AESGCM | AESCCM | ChaCha20Poly1305],
        nonce: ConstantOrContextLambda2[bytes],
        associated_data: ConstantOrContextLambda2[bytes] = ...,
    ) -> None: ...

# ===============================================================================
# lazy equivalents
# ===============================================================================
class Lazy(
    Subconstruct[
        SubconParsedType,
        SubconBuildTypes,
        t.Callable[[], SubconParsedType],
        t.Callable[[], SubconParsedType] | SubconParsedType,
    ]
):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
    ) -> None: ...

class LazyContainer(t.Generic[ContainerType], t.Dict[str, ContainerType]):
    def __getattr__(self, name: str) -> ContainerType: ...
    def __getitem__(self, index: str | int) -> ContainerType: ...
    def keys(self) -> t.Iterator[str]: ...  # type: ignore
    def values(self) -> t.List[ContainerType]: ...  # type: ignore
    def items(self) -> t.List[t.Tuple[str, ContainerType]]: ...  # type: ignore

class LazyStruct(Construct[LazyContainer[t.Any], t.Dict[str, t.Any] | None]):
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
        ListContainer[SubconParsedType],
        t.List[SubconBuildTypes],
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
        ListContainer[SubconParsedType],
        t.List[SubconBuildTypes],
    ]
):
    def __init__(
        self,
        subcon: Array[SubconParsedType, SubconBuildTypes] | GreedyRange[SubconParsedType, SubconBuildTypes],
        count: int,
        start: int | None,
        stop: int | None,
        step: int = ...,
        empty: SubconParsedType | None = ...,
    ) -> None: ...

class Indexing(
    Adapter[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]
):
    def __init__(
        self,
        subcon: Array[SubconParsedType, SubconBuildTypes] | GreedyRange[SubconParsedType, SubconBuildTypes],
        count: int,
        index: int,
        empty: SubconParsedType | None = ...,
    ) -> None: ...
