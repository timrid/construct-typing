import dataclasses
import textwrap
import typing as t

from .generic_wrapper import *


if t.TYPE_CHECKING:

    class TContainerBase(cs.Container[t.Any]):
        def __init__(self, *args: t.Any, **kwargs: t.Any):
            ...


else:

    class TContainerBase(cs.Container):
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "this should never be called, because it shoult be overwritten by 'dataclasses.dataclass'"
            )

        # if accessing via an field via dot access, return the object from the dict
        def __getattribute__(self, name):
            if name in self:
                return self[name]
            else:
                return super().__getattribute__(name)

        def __post_init__(self):
            # 1. fix the __keys_order__ of the cs.Container
            # 2. append fields with init=False to the dict of the cs.Container
            self.__keys_order__ = []
            for field in dataclasses.fields(self):
                value = getattr(self, field.name)
                if field.init is True:
                    self.__keys_order__.append(field.name)                        
                else:
                    self[field.name] = value


def TStructField(
    subcon: Construct[ParsedType, BuildTypes],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
) -> ParsedType:
    """
    Create a dataclass field for a "TStruct" and "TBitStruct" from a subcon.
    """
    # Rename subcon, if doc or parsed are available
    if (doc is not None) or (parsed is not None):
        if doc is not None:
            doc = textwrap.dedent(doc)
        subcon = cs.Renamed(subcon, newdocs=doc, newparsed=parsed)

    if subcon.flagbuildnone is True:
        # if subcon builds from "None", set default to "None"
        field = dataclasses.field(
            default=None,
            init=False,
            metadata={"subcon": cs.Renamed(subcon, newdocs=doc)},
        )
    else:
        field = dataclasses.field(metadata={"subcon": subcon})

    return field  # type: ignore


ContainerType = t.TypeVar("ContainerType", bound=TContainerBase)


class _TStruct(Adapter[t.Any, t.Any, ContainerType, BuildTypes]):
    """
    Base class for a typed struct, based on standard dataclasses.
    """

    def __init__(
        self, container_type: t.Type[ContainerType], swapped: bool = False
    ) -> None:
        if not issubclass(container_type, TContainerBase):
            raise TypeError(
                "'{}' has to be a '{}'".format(
                    repr(container_type), repr(TContainerBase)
                )
            )
        if not dataclasses.is_dataclass(container_type):
            raise TypeError(
                "'{}' has to be a 'dataclasses.dataclass'".format(repr(container_type))
            )
        self.container_type = container_type
        self.swapped = swapped

        # get all fields from the dataclass
        fields = dataclasses.fields(self.container_type)
        if self.swapped:
            fields = tuple(reversed(fields))

        # extract the construct formats from the struct_type
        subcon_fields = {}
        for field in fields:
            subcon_fields[field.name] = field.metadata["subcon"]

        # init adatper
        super(_TStruct, self).__init__(self._create_subcon(subcon_fields))

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        raise NotImplementedError

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

        return dc

    def _encode(
        self, obj: BuildTypes, context: Context, path: PathType
    ) -> t.Dict[str, t.Any]:
        if isinstance(obj, self.container_type):
            # get all fields from the dataclass
            fields = dataclasses.fields(self.container_type)

            # extract all fields from the container, that are used for create the dataclass object
            ret_dict = {}
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

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.Struct(**subcon_fields)


class TBitStruct(_TStruct[ContainerType, ContainerType]):
    """
    Typed bit struct, based on standard dataclasses.
    """

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.BitStruct(**subcon_fields)
