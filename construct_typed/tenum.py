import enum
import typing as t
import construct as cs
from .generic_wrapper import *

EnumType = t.TypeVar("EnumType", bound=enum.IntEnum)


class TEnum(Adapter[int, int, EnumType, t.Union[int, str, EnumType]]):
    def __new__(
        cls, subcon: Construct[int, int], enum_type: t.Type[EnumType]
    ) -> "TEnum[EnumType]":
        return super(TEnum, cls).__new__(cls, subcon, enum_type)  # type: ignore

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[EnumType]):
        if not issubclass(enum_type, enum.IntEnum):
            raise TypeError(
                'The class "{}" is not an "enum.IntEnum"'.format(enum_type.__name__)
            )

        @classmethod  # type: ignore
        def _missing_(
            cls: t.Type[EnumType], value: t.Union[int, EnumType]
        ) -> t.Optional[EnumType]:
            if isinstance(value, int):
                return cls._create_pseudo_member_(value)  # type: ignore
            return None  # will raise the ValueError in Enum.__new__

        @classmethod  # type: ignore
        def _create_pseudo_member_(cls: t.Type[EnumType], value: int) -> EnumType:
            pseudo_member = cls._value2member_map_.get(value, None)  # type: ignore
            if pseudo_member is None:
                new_member = int.__new__(cls, value)  # type: ignore
                # I expect a name attribute to hold a string, hence str(value)
                # However, new_member._name_ = value works, too
                new_member._name_ = str(value)
                new_member._value_ = value
                pseudo_member = cls._value2member_map_.setdefault(value, new_member)  # type: ignore
            return pseudo_member  # type: ignore

        # Monkey-patch the enum type with __missing__ method. So if a enum value
        # not found in the enum a new pseudo member is created.
        # The idea is taken from: https://stackoverflow.com/a/57179436
        enum_type._missing_ = _missing_  # type: ignore
        enum_type._create_pseudo_member_ = _create_pseudo_member_  # type: ignore

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