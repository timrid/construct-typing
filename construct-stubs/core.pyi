from typing import (
    Callable,
    Generic,
    NoReturn,
    TypeVar,
    Union,
    List,
    Any,
    Literal,
    overload,
    Dict,
    Optional,
    BinaryIO,
    type_check_only
)
import enum
from construct.lib import *
from construct.expr import *
from construct.version import *

StreamType = BinaryIO
BufferType = Union[bytes, memoryview, bytearray]
PathType = str
ContextKWType = Any

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
ParsedType = TypeVar("ParsedType")
BuildTypes = TypeVar("BuildTypes")

class Construct(Generic[ParsedType, BuildTypes]):
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
    def __rtruediv__(self, name: str) -> Construct[ParsedType, BuildTypes]: ...
    __rdiv__: Callable[[str], Construct[ParsedType, BuildTypes]]
    def __mul__(
        self,
        other: Union[str, bytes, Callable[[ParsedType, Context], NoReturn]],
    ) -> Construct[ParsedType, BuildTypes]: ...
    def __rmul__(
        self,
        other: Union[str, bytes, Callable[[ParsedType, Context], NoReturn]],
    ) -> Construct[ParsedType, BuildTypes]: ...
    def __add__(self, other: Construct[Any, Any]) -> Struct: ...
    def __rshift__(self, other: Construct[Any, Any]) -> Sequence[Any, Any]: ...
    def __getitem__(
        self, count: Union[int, Callable[[Context], int]]
    ) -> Array[ParsedType, BuildTypes]: ...

@type_check_only
class Context(Container[Any]):
    _: Optional[Context]
    _params: Optional[Context]
    _root: Optional[Context]
    _parsing: bool
    _building: bool
    _sizing: bool
    _subcons: Container[Construct[Any, Any]]
    _io: Optional[StreamType]
    _index: Optional[int]

ValueType = TypeVar("ValueType")
ConstantOrContextCallable = Union[ValueType, Callable[[Context], Any]]

class Subconstruct(Construct[ParsedType, BuildTypes]):
    def __init__(self, subcon: Construct[Any, Any]) -> None: ...

AdaptedParsedType = TypeVar("AdaptedParsedType")  # new parsed type that the adapter creates from the original parsed type
AdaptedBuildTypes = TypeVar("AdaptedBuildTypes")

class Adapter(Generic[AdaptedParsedType, AdaptedBuildTypes, ParsedType, BuildTypes], Subconstruct[AdaptedParsedType, AdaptedBuildTypes]):
    def __init__(self, subcon: Construct[ParsedType, BuildTypes]) -> None: ...
    def _decode(self, obj: ParsedType, context: Context, path: PathType) -> AdaptedParsedType: ...
    def _encode(self, obj: AdaptedBuildTypes, context: Context, path: PathType) -> BuildTypes: ...

class SymmetricAdapter(Adapter[AdaptedParsedType, AdaptedBuildTypes, ParsedType, BuildTypes]): ...

class Validator(SymmetricAdapter[Any, Any, ParsedType, Any]):
    def _validate(self, obj: ParsedType, context: Context, path: PathType) -> bool: ...

# TODO: Tunnel

# TODO: Compiled

# ===============================================================================
# bytes and bits
# ===============================================================================
class Bytes(Construct[bytes, Union[bytes, bytearray, int]]):
    def __init__(self, length: ConstantOrContextCallable[int]) -> None: ...

GreedyBytes: Construct[bytes, Union[bytes, bytearray, int]]

def Bitwise(
    subcon: Construct[ParsedType, BuildTypes]
) -> Construct[ParsedType, BuildTypes]: ...
def Bytewise(
    subcon: Construct[ParsedType, BuildTypes]
) -> Construct[ParsedType, BuildTypes]: ...


# ===============================================================================
# integers and floats
# ===============================================================================
class FormatField(Construct[ParsedType, BuildTypes]):
    ENDIANITY = Union[Literal["=", "<", ">"], str]
    FORMAT_INT = Literal["B", "H", "L", "Q", "b", "h", "l", "q"]
    FORMAT_FLOAT = Literal["f", "d", "e"]
    @overload
    def __init__(self: FormatField[int, int], endianity: str, format: FORMAT_INT) -> None: ...
    @overload
    def __init__(self: FormatField[float, float], endianity: str, format: FORMAT_FLOAT) -> None: ...
    @overload
    def __init__(self: FormatField[Any, Any], endianity: str, format: str) -> None: ...

class BytesInteger(Construct[int, int]):
    def __init__(self, length: ConstantOrContextCallable[int], signed: bool = ..., swapped: bool = ...) -> None: ...

class BitsInteger(Construct[int, int]):
    def __init__(self, length: ConstantOrContextCallable[int], signed: bool = ..., swapped: bool = ...) -> None: ...


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
    ENCODING_1 = Literal["ascii", "utf8", "utf_8", "u8"]
    ENCODING_2 = Literal["utf16", "utf_16", "u16", "utf_16_be", "utf_16_le"]
    ENCODING_4 = Literal["utf32", "utf_32", "u32", "utf_32_be", "utf_32_le"]
    ENCODING = Union[str, ENCODING_1, ENCODING_2, ENCODING_4]
    def __init__(
        self, subcon: Construct[ParsedType, BuildTypes], encoding: ENCODING
    ) -> None: ...

def PaddedString(length: ConstantOrContextCallable[int], encoding: StringEncoded.ENCODING) -> StringEncoded: ...
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

class Enum(Adapter[Union[EnumInteger, EnumIntegerString], Union[int, str], int, int]):
    def __init__(self, subcon: Construct[int, int], *merge: Union[enum.IntEnum, enum.IntFlag], **mapping: int) -> None: ...
    def __getattr__(self, name: str) -> EnumIntegerString: ...


class BitwisableString(str):
    def __or__(self, other: BitwisableString) -> BitwisableString: ...

class FlagsEnum(Adapter[Container[bool], Union[int, str, Dict[str, bool]], int, int]):
    def __init__(self, subcon: Construct[int, int], *merge: Union[enum.IntEnum, enum.IntFlag], **flags: int) -> None: ...
    def __getattr__(self, name: str) -> BitwisableString: ...


# ===============================================================================
# structures and sequences
# ===============================================================================
class Struct(Construct[Container[Any], Dict[str, Any]]):
    def __init__(
        self,
        *subcons: Construct[Any, Any],
        **subconskw: Construct[Any, Any]
    ) -> None: ...

# There are two possible alternatives for the "Struct" stub, so that a "Struct" automatically knows, which
# types it contains. But they both work only, if all struct entries have the same ParsedType / BuildTypes.
# Maybe these alternatives work in the future... Maybe one of the following links help:
#   - https://github.com/python/typing/issues/548
#   - https://sobolevn.me/2020/10/higher-kinded-types-in-python

# Alternative 1:
# --------------
# class StructAlternative1(Construct[Container[ParsedType], Dict[str, BuildTypes]]):
#     def __init__(
#         self, *subcons: Construct[ParsedType, BuildTypes], **subconskw: Construct[ParsedType, BuildTypes]
#     ) -> None: ...

# s_alt1 = StructAlternative1(a=CString("utf8"), b=BytesInteger(2))

# this one complains about 
# - s_alt1:          Type of "s_alt1" is partially unknown
#                    Type of "s_alt1" is "StructAlternative1[Unknown, Unknown]" Pylance (reportUnknownVariableType)
# - CString("utf8"): Argument of type "StringEncoded" cannot be assigned to parameter "a" of type "Construct[ParsedType, BuildTypes]" in function "__init__"
#                    TypeVar "ParsedType" is invariant
#                    Type "str | int" cannot be assigned to type "str" Pylance (reportGeneralTypeIssues)
# - BytesInteger(2): Argument of type "BytesInteger" cannot be assigned to parameter "b" of type "Construct[ParsedType, BuildTypes]" in function "__init__"
#                    TypeVar "ParsedType" is invariant
#                    Type "str | int" cannot be assigned to type "int" Pylance (reportGeneralTypeIssues)

# Alternative 2:
# --------------
# def StructAlternative2(*subcons: Construct[ParsedType, BuildTypes], **subconskw: Construct[ParsedType, BuildTypes]) -> Construct[Container[ParsedType], Dict[str, BuildTypes]]: ...

# s_alt2 = StructAlternative2(a=CString("utf8"), b=BytesInteger(2))

# This one is a little bit better than the "StructAlternative1", because "s_alt2" is correctly recognised
# as "Construct[Container[str | int], Dict[str, str | int]]". But it does not reflect the real implementation,
# because "Struct" is implemented as a class.

# this one complains about:
# - CString("utf8"): Argument of type "StringEncoded" cannot be assigned to parameter "a" of type "Construct[ParsedType, BuildTypes]" in function "StructAlternative2"
#                    TypeVar "ParsedType" is invariant
#                    Type "str | int" cannot be assigned to type "str"Pylance (reportGeneralTypeIssues)
# - BytesInteger(2): Argument of type "BytesInteger" cannot be assigned to parameter "b" of type "Construct[ParsedType, BuildTypes]" in function "StructAlternative2"
#                    TypeVar "ParsedType" is invariant
#                    Type "str | int" cannot be assigned to type "int"Pylance (reportGeneralTypeIssues)


class Sequence(Construct[ListContainer[ParsedType], List[BuildTypes]]):
    @overload
    def __init__(
        self: Sequence[ParsedType, BuildTypes],
        *subcons: Construct[ParsedType, BuildTypes],
        **subconskw: Construct[ParsedType, BuildTypes]
    ) -> None: ...
    @overload
    def __init__(
        self: Sequence[Any, Any],
        *subcons: Construct[Any, Any],
        **subconskw: Construct[Any, Any]
    ) -> None: ...

# There are two possible alternatives for the "Sequence" stub. These work the same way as with "Struct".

# ===============================================================================
# arrays ranges and repeaters
# ===============================================================================
class Array(Subconstruct[ListContainer[ParsedType], List[BuildTypes]]):
    def __init__(
        self,
        count: ConstantOrContextCallable[int],
        subcon: Construct[ParsedType, BuildTypes],
        discard: bool = ...,
    ) -> None: ...

class GreedyRange(Subconstruct[ListContainer[ParsedType], List[BuildTypes]]):
    def __init__(
        self,
        subcon: Construct[ParsedType, BuildTypes],
        discard: bool = ...
    ) -> None: ...

class RepeatUntil(Subconstruct[ListContainer[ParsedType], List[BuildTypes]]):
    def __init__(
        self,
        predicate: Union[bool, Callable[[Construct[ParsedType, BuildTypes], ListContainer[ParsedType], Context], bool]], 
        subcon: Construct[ParsedType, BuildTypes], 
        discard: bool = ...
    ) -> None: ...

# ===============================================================================
# miscellaneous
# ===============================================================================

# class Const(Subconstruct[ParsedType, BuildTypes]):
#     @overload
#     def __init__(
#         self: Const[bytes, Union[bytes, bytearray, int]],
#         value: bytes,
#     ) -> None: ...
#     @overload
#     def __init__(
#         self,
#         value: BuildTypes,
#         subcon: Construct[ParsedType, BuildTypes]
#     ) -> None: ...

# Problem: The above implementation work in most cases, but unfortunately not in all.
#          This for Example gives an error:
#          class Container3(TypedContainer):
#              d: Subcon(Const(b"\x00"))
#
# Workaround: We pretend that this class it is a method so that we can use @overload. 

@overload
def Const(value: bytes) -> Subconstruct[bytes, Union[bytes, bytearray, int]]: ...
@overload
def Const(value: bytes, subcon: Construct[ParsedType, BuildTypes]) -> Subconstruct[ParsedType, BuildTypes]: ...


class Computed(Construct[ValueType, Any]):
    def __init__(self, func: ConstantOrContextCallable[ValueType]) -> None: ...

Index: Construct[int, Any]

class Rebuild(Subconstruct[ValueType, BuildTypes]):
    def __init__(self, subcon: Construct[ParsedType, BuildTypes], func: ConstantOrContextCallable[ValueType]) -> None: ...

class Default(Subconstruct[ValueType, Union[None, Any]]):
    def __init__(self, subcon: Construct[ParsedType, Any], value: ConstantOrContextCallable[ValueType]) -> None: ...

class Check(Construct[None, None]):
    def __init__(self, func: ConstantOrContextCallable[bool]) -> None: ...

Error: Construct[None, None]

class FocusedSeq(Construct[Any, Any]):
    def __init__(
        self,
        parsebuildfrom: ConstantOrContextCallable[str],
        *subcons: Construct[Any, Any],
        **subconskw: Construct[Any, Any]
    ) -> None: ...



K = TypeVar("K")
V = TypeVar("V")
# class Hex(Adapter[ParsedType, BuildTypes, ParsedType, BuildTypes]):
#     @overload
#     def __init__(
#         self: Adapter[HexDisplayedInteger, BuildTypes, int, BuildTypes],
#         subcon: Construct[int, BuildTypes]
#     ) -> None: ...
#     @overload
#     def __init__(
#         self: Adapter[HexDisplayedBytes, BuildTypes, bytes, BuildTypes],
#         subcon: Construct[bytes, BuildTypes]
#     ) -> None: ...
#     @overload
#     def __init__(
#         self: Adapter[HexDisplayedDict[K, V], BuildTypes, Dict[K, V], BuildTypes],
#         subcon: Construct[Dict[K, V], BuildTypes]
#     ) -> None: ...
#     @overload
#     def __init__(
#         self,
#         subcon: Construct[ParsedType, BuildTypes]
#     ) -> None: ...

# Problem: The above works just with a weird declaration like this:
#     d: Hex[HexDisplayedInteger, Union[bytes, bytearray, int]] = Hex(Bytes(5))
# Maybe its a bug in Pylance?
#
# Workaround: We pretend that this class it is a method so that we can use @overload. Now
# the declaration looks like this:
#     d = Hex(Bytes(5))
@overload
def Hex(
    subcon: Construct[int, BuildTypes]
) -> Construct[HexDisplayedInteger, BuildTypes]: ...
@overload
def Hex(
    subcon: Construct[bytes, BuildTypes]
) -> Construct[HexDisplayedBytes, BuildTypes]: ...
@overload
def Hex(
    subcon: Construct[Dict[K, V], BuildTypes]
) -> Construct[HexDisplayedDict[K, V], BuildTypes]: ...
@overload
def Hex(
    subcon: Construct[ParsedType, BuildTypes]
) -> Construct[ParsedType, BuildTypes]: ...


#===============================================================================
# alignment and padding
#===============================================================================
def Padding(length: ConstantOrContextCallable[int], pattern: bytes = ...) -> Padded[None, None]: ...

class Padded(Subconstruct[ParsedType, BuildTypes]):
    def __init__(self, length: ConstantOrContextCallable[int], subcon: Construct[ParsedType, BuildTypes], pattern: bytes = ...) -> None: ...


class Aligned(Subconstruct[ParsedType, BuildTypes]):
    def __init__(self, modulus: ConstantOrContextCallable[int], subcon: Construct[ParsedType, BuildTypes], pattern: bytes = ...) -> None: ...

def AlignedStruct(modulus: ConstantOrContextCallable[int], *subcons: Construct[Any, Any], **subconskw: Construct[Any, Any]) -> Struct: ...

def BitStruct(*subcons: Construct[Any, Any], **subconskw: Construct[Any, Any]) -> Struct: ...


#===============================================================================
# stream manipulation
#===============================================================================

Tell: Construct[int, None]
Pass: Construct[None, None]
Terminated: Construct[None, None]

#===============================================================================
# adapters and validators
#===============================================================================
class ExprAdapter(Adapter[AdaptedParsedType, AdaptedBuildTypes, ParsedType, BuildTypes]):
    def __init__(
        self, 
        subcon: Construct[ParsedType, BuildTypes], 
        decoder: Callable[[ParsedType, Context], AdaptedParsedType], 
        encoder: Callable[[AdaptedBuildTypes, Context], BuildTypes]
    ) -> None: ...

class ExprSymmetricAdapter(ExprAdapter[AdaptedParsedType, AdaptedBuildTypes, ParsedType, BuildTypes]):
    def __init__(self, subcon: Construct[ParsedType, BuildTypes], encoder: Callable[[AdaptedBuildTypes, Context], BuildTypes]) -> None: ...


class ExprValidator(Validator[ParsedType]):
    def __init__(self, subcon: Construct[ParsedType, Any], validator: Callable[[ParsedType, Context], bool]) -> None: ...

