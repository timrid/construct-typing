# -*- coding: utf-8 -*-
# pyright: strict
import dataclasses
import sys
import textwrap
import typing as t

import construct as cs
from construct.lib.containers import (
    globalPrintFullStrings,
    globalPrintPrivateEntries,
    recursion_lock,
)
from construct.lib.py3compat import bytestringtype, reprstring, unicodestringtype

from construct_typed.generic import Adapter, Construct, Context, ParsedType, PathType

# The `key_only` keyword is possible since python 3.10. To support it in python 3.8 & 3.9
# the dataclasses module from python 3.10 is copied to this package.
if sys.version_info >= (3, 10) or t.TYPE_CHECKING:
    import dataclasses
else:
    import construct_typed.dataclasses_py310 as dataclasses

T = t.TypeVar("T")


# Static type inference support via __dataclass_transform__ implemented as per:
# https://github.com/microsoft/pyright/blob/1.1.135/specs/dataclass_transforms.md
def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: t.Tuple[t.Union[type, t.Callable[..., t.Any]], ...] = (()),
) -> t.Callable[[T], T]:
    return lambda a: a


DATACLASS_METADATA_KEY = "__construct_typed_subcon"

# specialisation for constructs, that builds from none and dont have to be declared in the __init__ method
@t.overload
def csfield(
    subcon: "cs.Construct[ParsedType, None]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    init: t.Literal[False] = False,
) -> ParsedType:
    ...


@t.overload
def csfield(
    subcon: "Construct[ParsedType, t.Any]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    init: bool = True,
) -> ParsedType:
    ...


def csfield(
    subcon: "Construct[ParsedType, t.Any]",
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
    init: bool = True,
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

    # Set default values in case of special subcons
    if isinstance(orig_subcon, cs.Const):
        const_subcon: "cs.Const[t.Any, t.Any, t.Any, t.Any]" = orig_subcon
        default = const_subcon.value
    elif isinstance(orig_subcon, cs.Default):
        default_subcon: "cs.Default[t.Any, t.Any, t.Any, t.Any]" = orig_subcon
        if callable(default_subcon.value):
            default = None  # context lambda is only defined at parsing/building
        else:
            default = default_subcon.value

    return t.cast(
        ParsedType,
        dataclasses.field(
            default=default,
            init=init,
            metadata={DATACLASS_METADATA_KEY: subcon},
        ),
    )


class DataclassConstruct(Adapter[t.Any, t.Any, T, T]):
    r"""
    TODO: Add Documentation
    """
    subcon: "cs.Struct[t.Any, t.Any]"
    if t.TYPE_CHECKING:

        def __new__(
            cls,
            dc_type: t.Type[T],
            reverse: bool = False,
        ) -> "DataclassConstruct[T]":
            ...

    def __init__(
        self,
        dc_type: t.Type[T],
        reverse: bool = False,
    ) -> None:
        if not issubclass(dc_type, DataclassStruct):
            raise TypeError(
                f"'{repr(dc_type)}' has to be a subclass of 'DataclassStruct'"
            )
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
            subcon_fields[field.name] = field.metadata[DATACLASS_METADATA_KEY]

        # init adatper
        super().__init__(cs.Struct(**subcon_fields))  # type: ignore

    def __getattr__(self, name: str) -> t.Any:
        return getattr(self.subcon, name)

    def _decode(
        self, obj: "cs.Container[t.Any]", context: Context, path: PathType
    ) -> T:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dc_type)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = obj[field.name]
                dc_init[field.name] = value

        # create object of dataclass
        dc: T = self.dc_type(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = obj[field.name]
                setattr(dc, field.name, value)

        return dc

    def _encode(self, obj: T, context: Context, path: PathType) -> t.Dict[str, t.Any]:
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


# Helper object for defining the `constr` of a `struct`. Will be replaced with the proper construct, when class is created.
this_struct: Construct[t.Any, t.Any] = Construct()


def _replace_this_struct(constr: "Construct[t.Any, t.Any]", replacement: t.Any) -> None:
    """Recursive search for `this_struct` in all SubConstructs and replace it with AttrsStruct"""
    subcon = getattr(constr, "subcon", None)
    if subcon is this_struct:
        setattr(constr, "subcon", replacement)
    elif subcon is not None:
        _replace_this_struct(subcon, replacement)
    else:
        raise ValueError(
            "Could not find `this_struct`. Only SubConstructs are supported"
        )


@__dataclass_transform__(field_descriptors=(csfield,), kw_only_default=True)
class DataclassStruct:
    """
    Adapter for a dataclasses for optimised type hints / static autocompletion in comparision to the original Struct.


    Before this construct can be created a dataclasses.dataclass type must be created, which must also derive from DataclassMixin. In this dataclass all fields must be assigned to a construct type using csfield.

    Internally, all fields are converted to a normal Struct, which does the actual parsing/building.

    Parses to a dataclasses.dataclass instance, and builds from such instance. Size is the sum of all subcon sizes, unless any subcon raises SizeofError.

    :param constr: This can be used if the structure is nested inside a Subconstruct. To represent this struct use the constant `this_struct`.
    :param reverse: Flag if the fields of the dataclass should be reversed

    Example::

        >>> from construct import Bytes, Int8ub, this
        >>> from construct_typed import DataclassMixin, DataclassStruct, csfield, construct
        ... class Image(DataclassStruct):
        ...     width: int = csfield(Int8ub)
        ...     height: int = csfield(Int8ub)
        ...     pixels: bytes = csfield(Bytes(this.height * this.width))
        >>> d = construct(Image)
        >>> d.parse(b"\x01\x0212")
        Image(width=1, height=2, pixels=b'12')
    """

    @classmethod
    def __init_subclass__(
        cls,
        constr: "cs.Construct[t.Any, t.Any]" = this_struct,
        reverse_fields: bool = False,
    ) -> None:
        # validate types
        if not isinstance(constr, cs.Construct):  # type: ignore
            raise ValueError("`constr` parameter has to be an `Construct` object")
        if not isinstance(reverse_fields, bool):  # type: ignore
            raise ValueError("`reverse_fields` parameter has to be an `bool` object")

        # create dataclass
        dataclasses.dataclass(cls, kw_only=True)  # type: ignore

        # create construct format
        dc_constr = DataclassConstruct(cls, reverse_fields)
        if constr is this_struct:
            constr = dc_constr
        else:
            _replace_this_struct(constr, dc_constr)

        # save construct format and make the class compatible to `Constructable` protocol
        setattr(cls, "__constr__", lambda: constr)

    # the `construct` library is using the [] access internally, so struct objects
    # should also make this possible and not only via the dot access.
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

    if t.TYPE_CHECKING:

        @classmethod
        def __constr__(cls: t.Type[T]) -> "DataclassConstruct[T]":
            ...


class DataclassBitStruct(DataclassStruct):
    r"""
    Makes a DataclassStruct inside a Bitwise.

    See :class:`~construct.core.Bitwise` and :class:`~construct_typed.dataclass_struct.DatclassStruct` for semantics and raisable exceptions.

    :param constr: TODO
    :param reverse_fields: Flag if the fields of the dataclass should be reversed

    Example::

        TODO:
        >>> from construct import BitsInteger, Flag, Nibble, Padding
        >>> from construct_typed import DataclassBitStruct, csfield, construct
        ... class TestDataclass(DataclassBitStruct):
        ...     a: int = csfield(Flag)
        ...     b: int = csfield(Nibble)
        ...     c: int = csfield(BitsInteger(10))
        ...     d: None = csfield(Padding(1))
        >>> d = construct(TestDataclass)
        >>> d.parse(b"\x01\x02")
        TestDataclass(a=False, b=0, c=129, d=None)
    """

    @classmethod
    def __init_subclass__(
        cls,
        constr: "cs.Construct[t.Any, t.Any]" = this_struct,
        reverse_fields: bool = False,
    ) -> None:
        cls = DataclassStruct.__init_subclass__.__func__(cls, cs.Bitwise(constr), reverse_fields)  # type: ignore
