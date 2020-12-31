import enum
import typing as t
import textwrap
import construct as cs
import dataclasses
import .generic_construct as gcs

ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")
SubconParsedType = t.TypeVar("SubconParsedType")
SubconBuildTypes = t.TypeVar("SubconBuildTypes")
EnumType = t.TypeVar("EnumType", bound=enum.IntEnum)
DataclassType = t.TypeVar("DataclassType")
ListType = t.TypeVar("ListType")


# if t.TYPE_CHECKING:
#     # while type checking, the original classes are generics, because they are defined in the stubs.
#     from construct import Construct, Adapter
#     from construct import ListContainer as List
# else:
#     # at runtime, the original classes are no generics, so whe have to make new classes with generics support
#     class Construct(t.Generic[ParsedType, BuildTypes], cs.Construct):
#         pass

#     class Adapter(
#         t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
#         cs.Adapter,
#     ):
#         pass

#     class List(t.Generic[ListType], cs.ListContainer):
#         pass



# ===============================================================================
# mappings
# ===============================================================================
class TEnum(gcs.Adapter[int, int, EnumType, t.Union[int, str, EnumType]]):
    def __new__(
        cls, subcon: gcs.Construct[int, int], enum_type: t.Type[EnumType]
    ) -> "TEnum[EnumType]":
        return super(TEnum, cls).__new__(cls, subcon, enum_type)  # type: ignore

    def __init__(self, subcon: gcs.Construct[int, int], enum_type: t.Type[EnumType]):
        if not issubclass(enum_type, enum.IntEnum):
            raise TypeError(
                'The class "{}" is not an "enum.IntEnum"'.format(
                    enum_type.__name__
                )
            )
        
        @classmethod
        def _missing_(
            cls: t.Type[EnumType], value: t.Union[int, EnumType]
        ) -> t.Optional[EnumType]:
            if isinstance(value, int):
                return cls._create_pseudo_member_(value)
            return None  # will raise the ValueError in Enum.__new__

        @classmethod
        def _create_pseudo_member_(cls: t.Type[EnumType], value: int) -> EnumType:
            pseudo_member = cls._value2member_map_.get(value, None)
            if pseudo_member is None:
                new_member = int.__new__(cls, value)
                # I expect a name attribute to hold a string, hence str(value)
                # However, new_member._name_ = value works, too
                new_member._name_ = str(value)
                new_member._value_ = value
                pseudo_member = cls._value2member_map_.setdefault(value, new_member)
            return pseudo_member

        # Monkey-patch the enum type with __missing__ method. So if a enum value
        # not found in the enum a new pseudo member is created.
        # The idea is taken from: https://stackoverflow.com/a/57179436
        enum_type._missing_ = _missing_
        enum_type._create_pseudo_member_ = _create_pseudo_member_

        # save enum type
        self.enum_type = enum_type

        # init adatper
        super(TEnum, self).__init__(subcon)  # type: ignore

    def _decode(self, obj: int, context: "cs.Context", path: "cs.PathType") -> EnumType:
        return self.enum_type(obj)

    def _encode(
        self,
        obj: t.Union[int, str, EnumType],
        context: "cs.Context",
        path: "cs.PathType",
    ) -> int:
        try:
            if isinstance(obj, str):
                return int(self.enum_type[obj])
            else:
                return int(self.enum_type(obj))
        except:
            raise cs.MappingError(
                "building failed, no mapping for %r" % (obj,), path=path
            )


# ===============================================================================
# structures and sequences
# ===============================================================================
def StructField(
    subcon: gcs.Construct[ParsedType, BuildTypes],
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
        # some subcons have a predefined default value. all other have "None"
        default: t.Any = None
        if isinstance(subcon, (cs.Const, cs.Default)):
            if callable(subcon.value):
                raise ValueError("lamda as default is not supported")
            default = subcon.value

        # if subcon builds from "None", set default to "None"
        field = dataclasses.field(
            default=default,
            init=False,
            metadata={"subcon": cs.Renamed(subcon, newdocs=doc)},
        )
    else:
        field = dataclasses.field(metadata={"subcon": subcon})

    return field  # type: ignore


class _TStruct(
    gcs.Adapter["cs.Container[t.Any]", t.Dict[str, t.Any], DataclassType, DataclassType]
):
    """
    Base class for a typed struct, based on standard dataclasses.
    """

    def __new__(
        cls, dataclass_type: t.Type[DataclassType], swapped: bool = False
    ) -> "_TStruct[DataclassType]":
        return super(_TStruct, cls).__new__(cls, dataclass_type, swapped)  # type: ignore

    def __init__(
        self, dataclass_type: t.Type[DataclassType], swapped: bool = False
    ) -> None:
        if not dataclasses.is_dataclass(dataclass_type):
            raise TypeError(
                'The class "{}" is not a "dataclasses.dataclass"'.format(
                    dataclass_type.__name__
                )
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
        super(_TStruct, self).__init__(self._create_subcon(subcon_fields))  # type: ignore

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> gcs.Construct[t.Any, t.Any]:
        raise NotImplementedError

    def _decode(
        self, obj: "cs.Container[t.Any]", context: "cs.Context", path: "cs.PathType"
    ) -> DataclassType:
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
        self, obj: DataclassType, context: "cs.Context", path: "cs.PathType"
    ) -> t.Dict[str, t.Any]:
        # get all fields from the dataclass
        fields = dataclasses.fields(self.dataclass_type)

        # extract all fields from the container, that are used for create the dataclass object
        ret_dict = {}
        for field in fields:
            value = getattr(obj, field.name)
            ret_dict[field.name] = value

        return ret_dict


class TStruct(_TStruct[DataclassType]):
    """
    Typed struct, based on standard dataclasses.
    """

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> gcs.Construct[t.Any, t.Any]:
        return cs.Struct(**subcon_fields)


class TBitStruct(_TStruct[DataclassType]):
    """
    Typed bit struct, based on standard dataclasses.
    """

    def _create_subcon(
        self, subcon_fields: t.Dict[str, t.Any]
    ) -> gcs.Construct[t.Any, t.Any]:
        return cs.BitStruct(**subcon_fields)



#===============================================================================
# conditional
#===============================================================================
def UnionField(
    subcon: gcs.Construct[ParsedType, BuildTypes],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, "cs.Context"], None]] = None,
) -> ParsedType:
    """
    Create a dataclass field for a "TUnion" from a subcon.
    """
    # Rename subcon, if doc or parsed are available
    if (doc is not None) or (parsed is not None):
        if doc is not None:
            doc = textwrap.dedent(doc)
        subcon = cs.Renamed(subcon, newdocs=doc, newparsed=parsed)

    if subcon.flagbuildnone is True:
        # some subcons have a predefined default value. all other have "None"
        default: t.Any = None
        if isinstance(subcon, (cs.Const, cs.Default)):
            if callable(subcon.value):
                raise ValueError("lamda as default is not supported")
            default = subcon.value

        # if subcon builds from "None", set default to "None"
        field = dataclasses.field(
            default=default,
            init=False,
            metadata={"subcon": cs.Renamed(subcon, newdocs=doc)},
        )
    else:
        field = dataclasses.field(metadata={"subcon": subcon})

    return field  # type: ignore



# TODO: TypedUnion
# TODO: TypedLazyStruct
# TODO: TypedSequence: Based on typing.namedtuple
# TODO: FocusedSeq: Based on typing.namedtuple