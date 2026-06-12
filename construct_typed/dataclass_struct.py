# -*- coding: utf-8 -*-
import typing_extensions
import dataclasses
import textwrap
import typing as t

import construct as cs
from construct.lib.containers import (
    globalPrintFullStrings,
    globalPrintPrivateEntries,
    recursion_lock,
)
from construct.lib.py3compat import bytestringtype, reprstring, unicodestringtype

from construct_typed.generic_wrapper import Adapter, Construct, Context, ParsedType, PathType


# Overload 1: Const → init=False (no __init__ parameter, has internal default)
@t.overload
def csfield(
    subcon: "cs.Const[ParsedType, t.Any]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    init: t.Literal[False] = ...,
) -> ParsedType: ...


# Overload 2: Rebuild → init=False (variable ParsedType, no default)
@t.overload
def csfield(
    subcon: "cs.Rebuild[ParsedType, t.Any]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    init: t.Literal[False] = ...,
) -> ParsedType: ...


# Overload 3: Computed → init=False (variable ParsedType, no default)
@t.overload
def csfield(
    subcon: "cs.Computed[ParsedType]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    init: t.Literal[False] = ...,
) -> ParsedType: ...


# Overload 4: Padded[None,None] = Padding() → init=False, returns None
@t.overload
def csfield(
    subcon: "cs.Padded[None, None]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    init: t.Literal[False] = ...,
) -> None: ...


# Overload 5: cs.Tell → init=False, returns int
@t.overload
def csfield(
    subcon: "cs.TellType",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    init: t.Literal[False] = ...,
) -> int: ...


# Overload 6: cs.Pass, cs.Terminated → init=False, returns None
@t.overload
def csfield(
    subcon: "cs.PassType | cs.TerminatedType",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    init: t.Literal[False] = ...,
) -> None: ...


# Overload 7: Default → optional field but CALLER MUST SPECIFY default= explicitly!
# For example:
# ```
#     default_int: int = csfield(cs.Default(cs.Int8ub, 8), default=0)
# ```
# The "second" `default=` value is used only for the typing system so that Pyright can match with this overload.
# The actual value doesn't matter but should match the `ParsedType`.
@t.overload
def csfield(
    subcon: "cs.Default[ParsedType, t.Any]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    *,
    default: ParsedType = ...,
) -> ParsedType: ...


# Overload 8: all other ctors → mandatory field (no default)
@t.overload
def csfield(
    subcon: Construct[ParsedType, t.Any],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
) -> ParsedType: ...


def csfield(
    subcon: Construct[ParsedType, t.Any],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    **_kwargs: t.Any,  # absorbs `init=` and `default=` from overloads (only for type checkers)
) -> ParsedType:
    """
    Helper method for "DataclassStruct" and "DataclassBitStruct" to create the dataclass fields.

    This method also processes Const and Default, to pass these values als default values to the dataclass.
    """
    orig_subcon = subcon

    # Rename subcon, if doc or parsed are available
    if (doc is not None) or (parsed is not None):
        if doc is not None:
            doc = textwrap.dedent(doc).strip("\n")
        subcon = cs.Renamed(subcon, newdocs=doc, newparsed=parsed)

    if orig_subcon.flagbuildnone is True:
        init = False
        default = None
    else:
        init = True
        default = dataclasses.MISSING

    # Set default values in case of special sucons
    if isinstance(orig_subcon, cs.Const):
        const_subcon = orig_subcon
        default = const_subcon.value
    elif isinstance(orig_subcon, cs.Default):
        default_subcon = orig_subcon
        # Default-Felder sind immer im __init__ (als optionaler Parameter mit Default), unabhängig von flagbuildnone.
        init = True
        if callable(default_subcon.value):
            default = None  # context lambda is only defined at parsing/building
        else:
            default = default_subcon.value

    return t.cast(
        ParsedType,
        dataclasses.field(
            default=default,
            init=init,
            metadata={"subcon": subcon},
        ),
    )


@typing_extensions.dataclass_transform(field_specifiers=(csfield,))
class DataclassMixin:
    """
    Mixin for the dataclasses which are passed to "DataclassStruct" and "DataclassBitStruct".

    Note: This implementation is different to the 'cs.Container' of the original 'construct'
    library. In the original 'cs.Container' some names like "update", "keys", "items", ... can
    only accessed via key access (square brackets) and not via attribute access (dot operator),
    because they are also method names. This implementation is based on "dataclasses.dataclass"
    which only uses modul-level instead of instance-level helper methods.So no instance-level
    methods exists and every name can be used.
    """

    __dataclass_fields__: "t.ClassVar[t.Dict[str, dataclasses.Field[t.Any]]]"

    def __getitem__(self, key: str) -> t.Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: t.Any) -> None:
        setattr(self, key, value)

    @recursion_lock()
    def __str__(self) -> str:
        indentation = "\n    "
        text = [f"{self.__class__.__name__}: "]

        for field in dataclasses.fields(self):
            k = field.name
            v = getattr(self, field.name)
            if k.startswith("_") and not globalPrintPrivateEntries:
                continue
            text.extend([indentation, str(k), " = "])
            if v.__class__.__name__ == "EnumInteger":
                text.append("(enum) (unknown) %s" % (v,))
            elif v.__class__.__name__ == "EnumIntegerString":
                text.append("(enum) %s %s" % (v, v.intvalue))
            elif v.__class__.__name__ in ["HexDisplayedBytes", "HexDumpDisplayedBytes"]:
                text.append(indentation.join(str(v).split("\n")))
            elif isinstance(v, bytestringtype):
                printingcap = 16
                if len(v) <= printingcap or globalPrintFullStrings:
                    text.append("%s (total %d)" % (reprstring(v), len(v)))
                else:
                    text.append(
                        "%s... (truncated, total %d)"
                        % (reprstring(v[:printingcap]), len(v))
                    )
            elif isinstance(v, unicodestringtype):
                printingcap = 32
                if len(v) <= printingcap or globalPrintFullStrings:
                    text.append("%s (total %d)" % (reprstring(v), len(v)))
                else:
                    text.append(
                        "%s... (truncated, total %d)"
                        % (reprstring(v[:printingcap]), len(v))
                    )
            else:
                text.append(indentation.join(str(v).split("\n")))
        return "".join(text)


DataclassType = t.TypeVar("DataclassType", bound=DataclassMixin)


class DataclassStruct(Adapter[t.Any, t.Any, DataclassType, DataclassType]):
    """
    Adapter for a dataclasses for optimised type hints / static autocompletion in comparision to the original Struct.

    Before this construct can be created a dataclasses.dataclass type must be created, which must also derive from DataclassMixin. In this dataclass all fields must be assigned to a construct type using csfield.

    Internally, all fields are converted to a Struct, which does the actual parsing/building.

    Parses to a dataclasses.dataclass instance, and builds from such instance. Size is the sum of all subcon sizes, unless any subcon raises SizeofError.

    :param dc_type: Type of the dataclass, which also inherits from DataclassMixin
    :param reverse: Flag if the fields of the dataclass should be reversed

    Example::

        >>> import dataclasses
        >>> from construct import Bytes, Int8ub, this
        >>> from construct_typed import DataclassMixin, DataclassStruct, csfield
        >>> @dataclasses.dataclass
        ... class Image(DataclassMixin):
        ...     width: int = csfield(Int8ub)
        ...     height: int = csfield(Int8ub)
        ...     pixels: bytes = csfield(Bytes(this.height * this.width))
        >>> d = DataclassStruct(Image)
        >>> d.parse(b"\x01\x0212")
        Image(width=1, height=2, pixels=b'12')
    """

    subcon: "cs.Struct"  # type: ignore

    def __init__(
        self,
        dc_type: t.Type[DataclassType],
        reverse: bool = False,
    ) -> None:
        if not issubclass(dc_type, DataclassMixin):  # type: ignore
            raise TypeError(f"'{repr(dc_type)}' has to be a '{repr(DataclassMixin)}'")
        if not dataclasses.is_dataclass(dc_type):
            raise TypeError(f"'{repr(dc_type)}' has to be a 'dataclasses.dataclass'")
        self.dc_type = dc_type
        self.reverse = reverse

        # get all fields from the dataclass
        fields = dataclasses.fields(self.dc_type)
        if self.reverse:
            fields = tuple(reversed(fields))

        # extract the construct formats from the struct_type
        subcon_fields = {}
        for field in fields:
            subcon_fields[field.name] = field.metadata["subcon"]

        # init adatper
        super().__init__(cs.Struct(**subcon_fields))  # type: ignore

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self.subcon, name)

    def _decode(
        self, obj: "cs.Container[t.Any]", context: Context, path: PathType
    ) -> DataclassType:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dc_type)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = obj[field.name]
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.dc_type(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = obj[field.name]
                setattr(dc, field.name, value)

        return dc  # type: ignore

    def _encode(
        self, obj: DataclassType, context: Context, path: PathType
    ) -> t.Dict[str, t.Any]:
        if not isinstance(obj, self.dc_type):
            raise TypeError(f"'{repr(obj)}' has to be of type {repr(self.dc_type)}")

        # get all fields from the dataclass
        fields = dataclasses.fields(self.dc_type)

        # extract all fields from the container, that are used for create the dataclass object
        ret_dict: t.Dict[str, t.Any] = {}
        for field in fields:
            value = getattr(obj, field.name)
            ret_dict[field.name] = value

        return ret_dict


def DataclassBitStruct(
    dc_type: t.Type[DataclassType], reverse: bool = False
) -> t.Union[
    "cs.Transformed[DataclassType, DataclassType]",
    "cs.Restreamed[DataclassType, DataclassType]",
]:
    r"""
    Makes a DataclassStruct inside a Bitwise.

    See :class:`~construct.core.Bitwise` and :class:`~construct_typed.dataclass_struct.DatclassStruct` for semantics and raisable exceptions.

    :param dc_type: Type of the dataclass, which also inherits from DataclassMixin
    :param reverse: Flag if the fields of the dataclass should be reversed

    Example::

        DataclassBitStruct  <-->  Bitwise(DataclassStruct(...))
        >>> import dataclasses
        >>> from construct import BitsInteger, Flag, Nibble, Padding
        >>> from construct_typed import DataclassBitStruct, DataclassMixin, csfield
        >>> @dataclasses.dataclass
        ... class TestDataclass(DataclassMixin):
        ...     a: int = csfield(Flag)
        ...     b: int = csfield(Nibble)
        ...     c: int = csfield(BitsInteger(10))
        ...     d: None = csfield(Padding(1))
        >>> d = DataclassBitStruct(TestDataclass)
        >>> d.parse(b"\x01\x02")
        TestDataclass(a=False, b=0, c=129, d=None)
    """
    return cs.Bitwise(DataclassStruct(dc_type, reverse))


# support legacy names
TStruct = DataclassStruct
TBitStruct = DataclassBitStruct
TContainerMixin = DataclassMixin
TContainerBase = DataclassMixin
TStructField = csfield
sfield = csfield
