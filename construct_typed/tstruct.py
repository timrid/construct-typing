import dataclasses
import textwrap
import typing as t

from .generic_wrapper import *

DataclassType = t.TypeVar("DataclassType")


def TStructField(
    subcon: Construct[ParsedType, BuildTypes],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, "cs.Context"], None]] = None,
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


class _TStruct(Adapter[t.Any, t.Any, ParsedType, BuildTypes]):
    """
    Base class for a typed struct, based on standard dataclasses.
    """

    def __init__(
        self, dataclass_type: t.Type[ParsedType], swapped: bool = False
    ) -> None:
        if not dataclasses.is_dataclass(dataclass_type):
            raise TypeError(
                "'{}' has to be a 'dataclasses.dataclass'".format(dataclass_type)
            )
        self.dataclass_type = dataclass_type
        self.swapped = swapped

        # get all fields from the dataclass
        fields = dataclasses.fields(self.dataclass_type)
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
        self, obj: "cs.Container[t.Any]", context: "cs.Context", path: "cs.PathType"
    ) -> ParsedType:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dataclass_type)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = getattr(obj, field.name)
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.dataclass_type(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = getattr(obj, field.name)
                setattr(dc, field.name, value)

        return dc

    def _encode(
        self, obj: BuildTypes, context: "cs.Context", path: "cs.PathType"
    ) -> t.Dict[str, t.Any]:
        if isinstance(obj, self.dataclass_type):
            # get all fields from the dataclass
            fields = dataclasses.fields(self.dataclass_type)

            # extract all fields from the container, that are used for create the dataclass object
            ret_dict = {}
            for field in fields:
                value = getattr(obj, field.name)
                ret_dict[field.name] = value

            return ret_dict
        raise TypeError("'{}' has to be of type {}".format(obj, self.dataclass_type))


class TStruct(_TStruct[ParsedType, ParsedType]):
    """
    Typed struct, based on standard dataclasses.
    """

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.Struct(**subcon_fields)


class TBitStruct(_TStruct[ParsedType, ParsedType]):
    """
    Typed bit struct, based on standard dataclasses.
    """

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> Construct[t.Any, t.Any]:
        return cs.BitStruct(**subcon_fields)
