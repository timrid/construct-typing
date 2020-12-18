import typing as t
import enum
import io
import arrow  # type: ignore
from construct.lib import Container, ListContainer, HexDisplayedBytes, HexDisplayedDict, HexDisplayedInteger, HexDumpDisplayedBytes, HexDumpDisplayedDict
# unfortunately, there are a few duplications with "typing", e.g. Union and Optional, which is why the t. prefix must be used everywhere

# Some of the Constructs can be optimised when the following typing optimisations are available:
#   - Variadic Generics: https://mail.python.org/archives/list/typing-sig@python.org/thread/SQVTQYWIOI4TIO7NNBTFFWFMSMS2TA4J/
#   - Higher Kinded Types: https://github.com/python/typing/issues/548
#   - Higher Kinded Types: https://sobolevn.me/2020/10/higher-kinded-types-in-python


StreamType = t.BinaryIO
BufferType = t.Union[bytes, memoryview, bytearray]
PathType = str
ContextKWType = t.Any

# ===============================================================================
# exceptions
# ===============================================================================
class ConstructError(Exception):
    path: PathType

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
# abstract constructs
# ===============================================================================
ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")

class Construct(t.Generic[ParsedType, BuildTypes]):
    def parse(self, data: BufferType, **contextkw: ContextKWType) -> ParsedType: ...
    def parse_stream(
        self, stream: StreamType, **contextkw: ContextKWType
    ) -> ParsedType: ...
    def parse_file(
        self, filename: str, **contextkw: ContextKWType
    ) -> ParsedType: ...
    def build(self, obj: BuildTypes, **contextkw: ContextKWType) -> bytes: ...
    def build_stream(
        self, obj: BuildTypes, stream: StreamType, **contextkw: ContextKWType
    ) -> bytes: ...
    def build_file(
        self, obj: BuildTypes, filename: str, **contextkw: ContextKWType
    ) -> bytes: ...
    def sizeof(self, **contextkw: ContextKWType) -> int: ...
    def compile(
        self, filename: str = ...
    ) -> Construct[ParsedType, BuildTypes]: ...
    def benchmark(self, sampledata: BufferType, filename: str = ...) -> str: ...
    def export_ksy(self, schemaname: str = ..., filename: str = ...) -> str: ...
    def __rtruediv__(self, name: str) -> Renamed[ParsedType, BuildTypes]: ...
    __rdiv__: t.Callable[[str], Construct[ParsedType, BuildTypes]]
    def __mul__(
        self,
        other: t.Union[str, bytes, t.Callable[[ParsedType, Context], t.NoReturn]],
    ) -> Renamed[ParsedType, BuildTypes]: ...
    def __rmul__(
        self,
        other: t.Union[str, bytes, t.Callable[[ParsedType, Context], t.NoReturn]],
    ) -> Renamed[ParsedType, BuildTypes]: ...
    def __add__(self, other: Construct[t.Any, t.Any]) -> Struct: ...
    def __rshift__(self, other: Construct[t.Any, t.Any]) -> Sequence[t.Any, t.Any]: ...
    def __getitem__(
        self, count: t.Union[int, t.Callable[[Context], int]]
    ) -> Array[ParsedType, BuildTypes]: ...

@t.type_check_only
class Context(Container[t.Any]):
    _: t.Optional[Context]
    _params: t.Optional[Context]
    _root: t.Optional[Context]
    _parsing: bool
    _building: bool
    _sizing: bool
    _subcons: Container[Construct[t.Any, t.Any]]
    _io: t.Optional[StreamType]
    _index: t.Optional[int]

ValueType = t.TypeVar("ValueType")
ConstantOrContextLambda = t.Union[ValueType, t.Callable[[Context], t.Any]]

SubconParsedType = t.TypeVar("SubconParsedType")
SubconBuildTypes = t.TypeVar("SubconBuildTypes")

class Subconstruct(t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes], Construct[ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls,
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]: ...
    @t.overload
    def __new__(
        cls,
        *args: t.Any,
        **kwargs: t.Any
    ) -> Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]: ...


class Adapter(t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes], Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __init__(self, subcon: Construct[SubconParsedType, SubconBuildTypes]) -> None: ...
    def _decode(self, obj: SubconParsedType, context: Context, path: PathType) -> ParsedType: ...
    def _encode(self, obj: BuildTypes, context: Context, path: PathType) -> SubconBuildTypes: ...

class SymmetricAdapter(Adapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]): ...

class Validator(SymmetricAdapter[t.Any, t.Any, SubconParsedType, t.Any]):
    def _validate(self, obj: SubconParsedType, context: Context, path: PathType) -> bool: ...

# TODO: Tunnel

# TODO: Compiled

# ===============================================================================
# bytes and bits
# ===============================================================================
class Bytes(Construct[bytes, t.Union[bytes, bytearray, int]]):
    def __init__(self, length: ConstantOrContextLambda[int]) -> None: ...

GreedyBytes: Construct[bytes, t.Union[bytes, bytearray, int]]

def Bitwise(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> t.Union[Transformed[SubconParsedType, SubconBuildTypes], Restreamed[SubconParsedType, SubconBuildTypes]]: ...
def Bytewise(
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> t.Union[Transformed[SubconParsedType, SubconBuildTypes], Restreamed[SubconParsedType, SubconBuildTypes]]: ...


# ===============================================================================
# integers and floats
# ===============================================================================
class FormatField(Construct[ParsedType, BuildTypes]):
    ENDIANITY = t.Union[t.Literal["=", "<", ">"], str]
    FORMAT_INT = t.Literal["B", "H", "L", "Q", "b", "h", "l", "q"]
    FORMAT_FLOAT = t.Literal["f", "d", "e"]
    @t.overload
    def __init__(self: FormatField[int, int], endianity: str, format: FORMAT_INT) -> None: ...
    @t.overload
    def __init__(self: FormatField[float, float], endianity: str, format: FORMAT_FLOAT) -> None: ...
    @t.overload
    def __init__(self: FormatField[t.Any, t.Any], endianity: str, format: str) -> None: ...

class BytesInteger(Construct[int, int]):
    def __init__(self, length: ConstantOrContextLambda[int], signed: bool = ..., swapped: bool = ...) -> None: ...

class BitsInteger(Construct[int, int]):
    def __init__(self, length: ConstantOrContextLambda[int], signed: bool = ..., swapped: bool = ...) -> None: ...


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

# ===============================================================================
# strings
# ===============================================================================
class StringEncoded(Construct[str, str]):
    ENCODING_1 = t.Literal["ascii", "utf8", "utf_8", "u8"]
    ENCODING_2 = t.Literal["utf16", "utf_16", "u16", "utf_16_be", "utf_16_le"]
    ENCODING_4 = t.Literal["utf32", "utf_32", "u32", "utf_32_be", "utf_32_le"]
    ENCODING = t.Union[str, ENCODING_1, ENCODING_2, ENCODING_4]
    def __init__(
        self, subcon: Construct[ParsedType, BuildTypes], encoding: ENCODING
    ) -> None: ...

def PaddedString(length: ConstantOrContextLambda[int], encoding: StringEncoded.ENCODING) -> StringEncoded: ...
def PascalString(
    lengthfield: Construct[ParsedType, BuildTypes], encoding: StringEncoded.ENCODING
) -> StringEncoded: ...
def CString(encoding: StringEncoded.ENCODING) -> StringEncoded: ...
def GreedyString(encoding: StringEncoded.ENCODING) -> StringEncoded: ...

#===============================================================================
# mappings
#===============================================================================
Flag: Construct[bool, bool]

class EnumInteger(int): ...

class EnumIntegerString(str):
    @staticmethod
    def new(intvalue: int, stringvalue: str) -> EnumIntegerString: ...

class Enum(Adapter[int, int, t.Union[EnumInteger, EnumIntegerString], t.Union[int, str]]):
    def __init__(
        self, 
        subcon: Construct[int, int],
        *merge: t.Union[t.Type[enum.IntEnum], t.Type[enum.IntFlag]],
        **mapping: int
    ) -> None: ...
    def __getattr__(self, name: str) -> EnumIntegerString: ...


class BitwisableString(str):
    def __or__(self, other: BitwisableString) -> BitwisableString: ...

class FlagsEnum(Adapter[int, int, Container[bool], t.Union[int, str, t.Dict[str, bool]]]):
    def __init__(
        self,
        subcon: Construct[int, int],
        *merge: t.Union[t.Type[enum.IntEnum], t.Type[enum.IntFlag]],
        **flags: int
    ) -> None: ...
    def __getattr__(self, name: str) -> BitwisableString: ...

class Mapping(Adapter[SubconParsedType, SubconBuildTypes, t.Any, t.Any]):
    def __init__(self, subcon: Construct[SubconParsedType, SubconBuildTypes], mapping: t.Dict[t.Any, t.Any]) -> None: ...

# ===============================================================================
# structures and sequences
# ===============================================================================
# this can maybe made better when variadic generics are available 
class Struct(Construct[Container[t.Any], t.Optional[t.Dict[str, t.Any]]]):
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any]
    ) -> None: ...

# this can maybe made better when variadic generics are available
class Sequence(Construct[ListContainer[t.Any], t.Optional[t.List[t.Any]]]):
    def __init__(
        self,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any]
    ) -> None: ...

# ===============================================================================
# arrays ranges and repeaters
# ===============================================================================
class Array(Subconstruct[SubconParsedType, SubconBuildTypes, ListContainer[SubconParsedType], t.List[SubconBuildTypes]]):
    def __init__(
        self,
        count: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        discard: bool = ...,
    ) -> None: ...

class GreedyRange(Subconstruct[SubconParsedType, SubconBuildTypes, ListContainer[SubconParsedType], t.List[SubconBuildTypes]]):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        discard: bool = ...
    ) -> None: ...

class RepeatUntil(Subconstruct[SubconParsedType, SubconBuildTypes, ListContainer[SubconParsedType], t.List[SubconBuildTypes]]):
    def __init__(
        self,
        predicate: t.Union[bool, t.Callable[[SubconParsedType, ListContainer[SubconParsedType], Context], bool]], 
        subcon: Construct[SubconParsedType, SubconBuildTypes], 
        discard: bool = ...
    ) -> None: ...

#===============================================================================
# specials
#===============================================================================
class Renamed(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self, 
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        newname: t.Optional[str] = ..., 
        newdocs: t.Optional[str] = ..., 
        newparsed: t.Optional[t.Callable[[t.Any, Context], None]] = ...
    ) -> None: ...


# ===============================================================================
# miscellaneous
# ===============================================================================
class Const(Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls,
        value: bytes,
    ) -> Const[None, None, bytes, t.Union[bytes, bytearray, int]]: ...
    @t.overload
    def __new__(
        cls,
        value: SubconBuildTypes,
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> Const[None, None, SubconParsedType, SubconBuildTypes]: ...

class Computed(Construct[ValueType, None]):
    def __init__(self, func: ConstantOrContextLambda[ValueType]) -> None: ...

Index: Construct[int, t.Any]

class Rebuild(Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __new__(
        cls, 
        subcon: Construct[SubconParsedType, SubconBuildTypes], 
        func: ConstantOrContextLambda[SubconBuildTypes]
    ) -> Rebuild[SubconParsedType, SubconBuildTypes, SubconParsedType, None]: ...

class Default(Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __new__(
        cls,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        value: ConstantOrContextLambda[SubconBuildTypes]
    ) -> Default[SubconParsedType, SubconBuildTypes, SubconParsedType, t.Optional[SubconBuildTypes]]: ...

class Check(Construct[None, None]):
    def __init__(self, func: ConstantOrContextLambda[bool]) -> None: ...

Error: Construct[None, None]

class FocusedSeq(Construct[t.Any, t.Any]):
    def __init__(
        self,
        parsebuildfrom: ConstantOrContextLambda[str],
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any]
    ) -> None: ...

Pickled: Construct[t.Any, t.Any]

Numpy: Construct[t.Any, t.Any]

class NamedTuple(Adapter[SubconParsedType, SubconBuildTypes, t.Tuple[t.Any, ...], t.Union[t.Tuple[t.Any, ...], t.List[t.Any], t.Dict[str, t.Any]]]):
    def __init__(
        self,
        tuplename: str,
        tuplefields: str,
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> None: ...


@t.overload
def Timestamp(
    subcon: Construct[int, int],
    unit: t.Literal["msdos"],
    epoch: t.Literal["msdos"]
) -> Adapter[int, int, arrow.Arrow, arrow.Arrow]: ...

@t.overload
def Timestamp(
    subcon: Construct[int, int],
    unit: t.Union[int, float],
    epoch: t.Union[int, arrow.Arrow]
) -> Adapter[int, int, arrow.Arrow, arrow.Arrow]: ...

@t.overload
def Timestamp(
    subcon: Construct[float, float],
    unit: t.Union[int, float],
    epoch: t.Union[int, arrow.Arrow]
) -> Adapter[float, float, arrow.Arrow, arrow.Arrow]: ...


K = t.TypeVar("K")
V = t.TypeVar("V")
class Hex(Adapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls,
        subcon: Construct[int, BuildTypes]
    ) -> Hex[int, BuildTypes, HexDisplayedInteger, BuildTypes]: ...
    @t.overload
    def __new__(
        cls,
        subcon: Construct[bytes, BuildTypes]
    ) -> Hex[bytes, BuildTypes, HexDisplayedBytes, BuildTypes]: ...
    @t.overload
    def __new__(
        cls,
        subcon: Construct[t.Dict[K, V], BuildTypes]
    ) -> Hex[t.Dict[K, V], BuildTypes, HexDisplayedDict[K, V], BuildTypes]: ...
    @t.overload
    def __new__(
        cls,
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> Hex[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]: ...

class HexDump(Adapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls,
        subcon: Construct[bytes, BuildTypes]
    ) -> HexDump[bytes, BuildTypes, HexDumpDisplayedBytes, BuildTypes]: ...
    @t.overload
    def __new__(
        cls,
        subcon: Construct[t.Dict[K, V], BuildTypes]
    ) -> HexDump[t.Dict[K, V], BuildTypes, HexDumpDisplayedDict[K, V], BuildTypes]: ...
    @t.overload
    def __new__(
        cls,
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> HexDump[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]: ...


#===============================================================================
# conditional
#===============================================================================
# this can maybe made better when variadic generics are available 
class Union(Construct[Container[t.Any], t.Dict[str, t.Any]]):
    def __init__(
        self,
        parsefrom: t.Optional[ConstantOrContextLambda[t.Union[int, str]]],
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any]
    ) -> None: ...


# this can maybe made better when variadic generics are available
class Select(Construct[ParsedType, BuildTypes]):
    def __new__(
        cls,
        *subcons: Construct[t.Any, t.Any],
        **subconskw: Construct[t.Any, t.Any]
    ) -> Select[t.Any, t.Any]: ...

def Optional(subcon: Construct[SubconParsedType, SubconBuildTypes]) -> Select[t.Union[SubconParsedType, None], t.Union[SubconBuildTypes, None]]: ...



ThenParsedType = t.TypeVar("ThenParsedType")
ThenBuildTypes = t.TypeVar("ThenBuildTypes")
ElseParsedType = t.TypeVar("ElseParsedType")
ElseBuildTypes = t.TypeVar("ElseBuildTypes")

class IfThenElse(t.Generic[ThenParsedType, ThenBuildTypes, ElseParsedType, ElseBuildTypes], Construct[t.Union[ThenParsedType, ElseParsedType], t.Union[ThenBuildTypes, ElseBuildTypes]]):
    def __init__(
        self, 
        condfunc: ConstantOrContextLambda[bool], 
        thensubcon: Construct[ThenParsedType, ThenBuildTypes], 
        elsesubcon: Construct[ElseParsedType, ElseBuildTypes]
    ) -> None: ...

def If(condfunc: ConstantOrContextLambda[bool], subcon: Construct[ThenParsedType, ThenBuildTypes]) -> IfThenElse[ThenParsedType, ThenBuildTypes, None, None]: ...


SwitchType = t.TypeVar("SwitchType")

class Switch(Construct[ParsedType, BuildTypes]):
    @t.overload
    def __new__(
        cls,
        keyfunc: ConstantOrContextLambda[SwitchType],
        cases: t.Dict[SwitchType, Construct[int, int]],
        default: t.Optional[Construct[int, int]] = ...
    ) -> Switch[int, int]: ...

    @t.overload
    def __new__(
        cls,
        keyfunc: ConstantOrContextLambda[SwitchType],
        cases: t.Dict[SwitchType, Construct[t.Any, t.Any]],
        default: t.Optional[Construct[t.Any, t.Any]] = ...
    ) -> Switch[t.Any, t.Any]: ...


class StopIf(Construct[None, None]):
    def __init__(self, condfunc: ConstantOrContextLambda[bool]) -> None: ...

#===============================================================================
# alignment and padding
#===============================================================================
def Padding(length: ConstantOrContextLambda[int], pattern: bytes = ...) -> Padded[None, None]: ...

class Padded(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        pattern: bytes = ...
    ) -> None: ...


class Aligned(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(self, modulus: ConstantOrContextLambda[int], subcon: Construct[SubconParsedType, SubconBuildTypes], pattern: bytes = ...) -> None: ...

def AlignedStruct(modulus: ConstantOrContextLambda[int], *subcons: Construct[t.Any, t.Any], **subconskw: Construct[t.Any, t.Any]) -> Struct: ...

def BitStruct(*subcons: Construct[t.Any, t.Any], **subconskw: Construct[t.Any, t.Any]) -> t.Union[Transformed[Container[t.Any], t.Dict[str, t.Any]], Restreamed[Container[t.Any], t.Dict[str, t.Any]]]: ...


#===============================================================================
# stream manipulation
#===============================================================================
class Pointer(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self,
        offset: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        stream: t.Optional[t.Callable[[Context], StreamType]] = ...
    ) -> None: ...

class Peek(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, t.Any]): ...


class Seek(Construct[int, None]):
    def __init__(self, at: ConstantOrContextLambda[int], whence: ConstantOrContextLambda[t.Literal[0, 1, 2]] = ...) -> None: ...


Tell: Construct[int, None]
Pass: Construct[None, None]
Terminated: Construct[None, None]

#===============================================================================
# tunneling and byte/bit swapping
#===============================================================================
@t.type_check_only
class RawCopyObj(t.Generic[ParsedType], Container[t.Any]):
    data: bytes
    value: ParsedType
    offset1: int
    offset2: int
    length: int

class RawCopy(Subconstruct[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __new__(
        cls,
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> RawCopy[SubconParsedType, SubconBuildTypes, RawCopyObj[SubconParsedType], t.Optional[t.Dict[str, t.Union[SubconBuildTypes, BufferType]]]]: ...

def ByteSwapped(subcon: Construct[SubconParsedType, SubconBuildTypes]) -> Transformed[SubconParsedType, SubconBuildTypes]: ...
def BitsSwapped(subcon: Construct[SubconParsedType, SubconBuildTypes]) -> t.Union[Transformed[SubconParsedType, SubconBuildTypes], Restreamed[SubconParsedType, SubconBuildTypes]]: ...

class Prefixed(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self, 
        lengthfield: Construct[int, int], 
        subcon: Construct[SubconParsedType, SubconBuildTypes], 
        includelength: t.Optional[bool] = ...
    ) -> None: ...

def PrefixedArray(
    countfield: Construct[int, int],
    subcon: Construct[SubconParsedType, SubconBuildTypes]
) -> Array[SubconParsedType, SubconBuildTypes]: ...

class FixedSized(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self,
        length: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> None: ...

class NullTerminated(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self,
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        term: bytes = ...,
        include: t.Optional[bool] = ...,
        consume: t.Optional[bool] = ...,
        require: t.Optional[bool] = ...
    ) -> None: ...

class NullStripped(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(self, subcon: Construct[SubconParsedType, SubconBuildTypes], pad: bytes = ...) -> None: ...

class RestreamData(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, None]):
    def __init__(
        self,
        datafunc: t.Union[bytes, io.BytesIO, Construct[bytes, t.Any], t.Callable[[Context], bytes]],
        subcon: Construct[SubconParsedType, SubconBuildTypes]
    ) -> None: ...

class Transformed(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self, 
        subcon: Construct[SubconParsedType, SubconBuildTypes], 
        decodefunc: t.Callable[[bytes], bytes],
        decodeamount: t.Optional[int],
        encodefunc: t.Callable[[bytes], bytes],
        encodeamount: t.Optional[int]
    ) -> None: ...

class Restreamed(Subconstruct[SubconParsedType, SubconBuildTypes, SubconParsedType, SubconBuildTypes]):
    def __init__(
        self, 
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        decoder: t.Callable[[bytes], bytes],
        decoderunit: int,
        encoder: t.Callable[[bytes], bytes],
        encoderunit: int,
        sizecomputer: t.Callable[[int], int]
    ) -> None: ...


#===============================================================================
# adapters and validators
#===============================================================================
class ExprAdapter(Adapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __init__(
        self, 
        subcon: Construct[SubconParsedType, SubconBuildTypes], 
        decoder: t.Callable[[SubconParsedType, Context], ParsedType], 
        encoder: t.Callable[[BuildTypes, Context], SubconBuildTypes]
    ) -> None: ...

class ExprSymmetricAdapter(ExprAdapter[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes]):
    def __init__(self, subcon: Construct[SubconParsedType, SubconBuildTypes], encoder: t.Callable[[BuildTypes, Context], SubconBuildTypes]) -> None: ...


class ExprValidator(Validator[ParsedType]):
    def __init__(self, subcon: Construct[ParsedType, t.Any], validator: t.Callable[[ParsedType, Context], bool]) -> None: ...

