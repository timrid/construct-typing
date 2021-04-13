import dataclasses
import textwrap
import typing as t

import construct as cs

from .generic_wrapper import (
    Adapter,
    BuildTypes,
    Construct,
    Context,
    ParsedType,
    PathType,
)

if t.TYPE_CHECKING:

    class _TContainerMixin(cs.Container[t.Any]):
        ...


else:

    class _TContainerMixin(cs.Container):
        pass


class TContainerMixin(_TContainerMixin):
    """
    Base class for a Container of a TStruct and a TBitStruct.

    Note: this always has to be mixed with "dataclasses.dataclass".
    """

    def __getattribute__(self, name: str) -> t.Any:
        # if accessing via an field via dot access, return the object from the dict
        if name in self:
            return self[name]
        else:
            return super().__getattribute__(name)

    def __post_init__(self) -> None:
        # 1. append fields with init=False to the dict of the cs.Container
        # 2. fix the order of the OrderedDict
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if field.init is False:
                self[field.name] = value
            else:
                self.move_to_end(field.name)


TContainerBase = TContainerMixin  # also support legacy name


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

    if isinstance(orig_subcon, (cs.Const, cs.Default)) and not callable(
        orig_subcon.value
    ):
        # Set simple values if cs.Const or cs.Default.
        # If the value is a callable (or context lambda), then we cant set it because it
        # is only defined at parsing/building
        field = dataclasses.field(
            default=orig_subcon.value,
            init=False,
            metadata={"subcon": subcon},
        )
    elif orig_subcon.flagbuildnone is True:
        # If subcon builds from "None", set default to "None"
        field = dataclasses.field(
            default=None,
            init=False,
            metadata={"subcon": subcon},
        )
    else:
        field = dataclasses.field(metadata={"subcon": subcon})

    return field  # type: ignore


TStructField = sfield  # also support legacy name

ContainerType = t.TypeVar("ContainerType", bound=TContainerMixin)


class _TStruct(Adapter[t.Any, t.Any, ContainerType, BuildTypes]):
    """
    Base class for a typed struct, based on standard dataclasses.
    """

    def __init__(
        self,
        container_type: t.Type[ContainerType],
        reverse: bool = False,
        add_offsets: bool = False,
    ) -> None:
        if not issubclass(container_type, TContainerMixin):
            raise TypeError(
                "'{}' has to be a '{}'".format(
                    repr(container_type), repr(TContainerMixin)
                )
            )
        if not dataclasses.is_dataclass(container_type):
            raise TypeError(
                "'{}' has to be a 'dataclasses.dataclass'".format(repr(container_type))
            )
        self.container_type = container_type
        self.reverse = reverse
        self.add_offsets = add_offsets

        # get all fields from the dataclass
        fields = dataclasses.fields(self.container_type)
        if self.reverse:
            fields = tuple(reversed(fields))

        # extract the construct formats from the struct_type
        subcon_fields = {}
        for field in fields:
            if add_offsets:
                subcon_fields[f"@<{field.name}"] = cs.Tell
            subcon_fields[field.name] = field.metadata["subcon"]
            if add_offsets:
                subcon_fields[f"@>{field.name}"] = cs.Tell

        # init adatper
        super(_TStruct, self).__init__(self._create_subcon(subcon_fields))  # type: ignore

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        raise NotImplementedError

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
                value = getattr(obj, field.name)
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.container_type(**dc_init)

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = getattr(obj, field.name)
                setattr(dc, field.name, value)

        # also transfer values that are not part of the dataclass
        dc.update(obj)

        return dc

    def _encode(
        self, obj: BuildTypes, context: Context, path: PathType
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


class TStruct(_TStruct[ContainerType, ContainerType]):
    """
    Typed struct, based on standard dataclasses.
    """

    subcon: "cs.Struct[t.Any, t.Any]"
    if t.TYPE_CHECKING:

        def __new__(
            cls,
            container_type: t.Type[ContainerType],
            reverse: bool = False,
            add_offsets: bool = False,
        ) -> "TStruct[ContainerType]":
            ...

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.Struct(**subcon_fields)


class TBitStruct(_TStruct[ContainerType, ContainerType]):
    """
    Typed bit struct, based on standard dataclasses.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls,
            container_type: t.Type[ContainerType],
            reverse: bool = False,
            add_offsets: bool = False,
        ) -> "TBitStruct[ContainerType]":
            ...

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.BitStruct(**subcon_fields)
