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

from .generic_wrapper import Adapter, Construct, Context, ParsedType, PathType


class TContainerMixin:
    """
    Base class for a Container of a TStruct and a TBitStruct. This class has always to be mixed
    with "dataclasses.dataclass".

    Note: This implementation is different to the 'cs.Container' of the original 'construct'
    library. In the original 'cs.Container' some names like "update", "keys", "items", ... can
    only accessed via key access (square brackets) and not via attribute access (dot operator),
    because they are also method names. This implementation is based on "dataclasses.dataclass"
    which only uses modul-level instead of instance-level helper methods.So no instance-level
    methods exists and every name can be used.
    """

    def __getitem__(self, key: str) -> t.Any:
        return getattr(self, key)

    def __setitem__(self, key: str, value: t.Any) -> None:
        setattr(self, key, value)

    @recursion_lock()
    def __str__(self):
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


def sfield(
    subcon: Construct[ParsedType, t.Any],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
) -> ParsedType:
    """
    Create a dataclass field for a "TStruct" and "TBitStruct" from a subcon.
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
        const_subcon: "cs.Const[t.Any, t.Any, t.Any, t.Any]" = orig_subcon
        default = const_subcon.value
    elif isinstance(orig_subcon, cs.Default):
        default_subcon: "cs.Default[t.Any, t.Any, t.Any, t.Any]" = orig_subcon
        if callable(default_subcon.value):
            default = None  # context lambda is only defined at parsing/building
        else:
            default = default_subcon.value

    return dataclasses.field(
        default=default,
        init=init,
        metadata={"subcon": subcon},
    )  # type: ignore


ContainerType = t.TypeVar("ContainerType", bound=TContainerMixin)


class TStruct(Adapter[t.Any, t.Any, ContainerType, ContainerType]):
    """
    Typed struct, based on standard dataclasses.
    """

    subcon: "cs.Struct[t.Any, t.Any]"
    if t.TYPE_CHECKING:

        def __new__(
            cls,
            container_type: t.Type[ContainerType],
            reverse: bool = False,
        ) -> "TStruct[ContainerType]":
            ...

    def __init__(
        self,
        container_type: t.Type[ContainerType],
        reverse: bool = False,
    ) -> None:
        if not issubclass(container_type, TContainerMixin):
            raise TypeError(
                f"'{repr(container_type)}' has to be a '{repr(TContainerMixin)}'"
            )
        if not dataclasses.is_dataclass(container_type):
            raise TypeError(
                f"'{repr(container_type)}' has to be a 'dataclasses.dataclass'"
            )
        self.container_type = container_type
        self.reverse = reverse

        # get all fields from the dataclass
        fields = dataclasses.fields(self.container_type)
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
    ) -> ContainerType:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.container_type)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = obj[field.name]
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.container_type(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = obj[field.name]
                setattr(dc, field.name, value)

        return dc

    def _encode(
        self, obj: ContainerType, context: Context, path: PathType
    ) -> t.Dict[str, t.Any]:
        if isinstance(obj, self.container_type):
            # get all fields from the dataclass
            fields = dataclasses.fields(self.container_type)

            # extract all fields from the container, that are used for create the dataclass object
            ret_dict: t.Dict[str, t.Any] = {}
            for field in fields:
                value = getattr(obj, field.name)
                ret_dict[field.name] = value

            return ret_dict
        raise TypeError(
            "'{}' has to be of type {}".format(repr(obj), repr(self.container_type))
        )


def TBitStruct(container_type: t.Type[ContainerType], reverse: bool = False):
    return cs.Bitwise(TStruct(container_type, reverse))


TContainerBase = TContainerMixin  # also support legacy name
TStructField = sfield  # also support legacy name
