import enum
import typing as t

from .generic_wrapper import *


# ## TEnum ############################################################################################################
class EnumBase(enum.IntEnum):
    """
    Base class for an Enum used in `construct_typed.TEnum`.

    This class extends the standard `enum.IntEnum`, so that missing values are automatically generated.
    """

    # Extend the enum type with __missing__ method. So if a enum value
    # not found in the enum, a new pseudo member is created.
    # The idea is taken from: https://stackoverflow.com/a/57179436
    @classmethod
    def _missing_(cls, value: t.Any) -> t.Optional["EnumBase"]:
        if isinstance(value, int):
            return cls._create_pseudo_member(value)
        return None  # will raise the ValueError in Enum.__new__

    @classmethod
    def _create_pseudo_member(cls, value: int) -> "EnumBase":
        pseudo_member = cls._value2member_map_.get(value, None)  # type: ignore
        if pseudo_member is None:
            new_member = int.__new__(cls, value)
            # I expect a name attribute to hold a string, hence str(value)
            # However, new_member._name_ = value works, too
            new_member._name_ = str(value)
            new_member._value_ = value
            pseudo_member = cls._value2member_map_.setdefault(value, new_member)  # type: ignore
        return pseudo_member  # type: ignore


EnumType = t.TypeVar("EnumType", bound=EnumBase)


class TEnum(Adapter[int, int, EnumType, EnumType]):
    """
    Typed enum.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls, subcon: Construct[int, int], enum_type: t.Type[EnumType]
        ) -> "TEnum[EnumType]":
            ...

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[EnumType]):
        if not issubclass(enum_type, EnumBase):
            raise TypeError(
                "'{}' has to be a '{}'".format(repr(enum_type), repr(EnumBase))
            )

        # save enum type
        self.enum_type = t.cast(t.Type[EnumType], enum_type)  # type: ignore

        # init adatper
        super(TEnum, self).__init__(subcon)  # type: ignore

    def _decode(self, obj: int, context: Context, path: PathType) -> EnumType:
        return self.enum_type(obj)

    def _encode(
        self,
        obj: EnumType,
        context: Context,
        path: PathType,
    ) -> int:
        if isinstance(obj, self.enum_type):
            return int(obj)
        raise TypeError(
            "'{}' has to be of type {}".format(repr(obj), repr(self.enum_type))
        )


# ## TFlagsEnum #######################################################################################################
class FlagsEnumBase(enum.IntFlag):
    pass


FlagsEnumType = t.TypeVar("FlagsEnumType", bound=FlagsEnumBase)


class TFlagsEnum(Adapter[int, int, FlagsEnumType, FlagsEnumType]):
    """
    Typed enum.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls, subcon: Construct[int, int], enum_type: t.Type[FlagsEnumType]
        ) -> "TFlagsEnum[FlagsEnumType]":
            ...

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[FlagsEnumType]):
        if not issubclass(enum_type, FlagsEnumBase):
            raise TypeError(
                "'{}' has to be a '{}'".format(repr(enum_type), repr(FlagsEnumBase))
            )

        # save enum type
        self.enum_type = t.cast(t.Type[FlagsEnumType], enum_type)  # type: ignore

        # init adatper
        super(TFlagsEnum, self).__init__(subcon)  # type: ignore

    def _decode(self, obj: int, context: Context, path: PathType) -> FlagsEnumType:
        return self.enum_type(obj)

    def _encode(
        self,
        obj: FlagsEnumType,
        context: Context,
        path: PathType,
    ) -> int:
        if isinstance(obj, self.enum_type):
            return int(obj)
        raise TypeError(
            "'{}' has to be of type {}".format(repr(obj), repr(self.enum_type))
        )
