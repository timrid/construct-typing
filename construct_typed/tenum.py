import enum
import typing as t

import construct as cs

from .generic import *

T = t.TypeVar("T")


# ## TEnum ############################################################################################################
class TEnum(enum.IntEnum):
    """
    Base class for an Enum used in `construct_typed.TEnumConstruct`.

    This class extends the standard `enum.IntEnum`, so that missing values are automatically generated.
    """

    @classmethod
    def __init_subclass__(
        cls,
        subcon: "cs.Construct[t.Any, t.Any]",
        **kwargs: t.Any,
    ):
        super().__init_subclass__(**kwargs)

        # validate types
        if not isinstance(subcon, cs.Construct):  # type: ignore
            raise ValueError(
                f"`subcon` parameter has to be an `Construct` object but is {type(subcon)}"
            )

        # create construct format
        enum_constr = TEnumConstruct(subcon, cls)

        # save construct format and make the class compatible to `Constructable` protocol
        setattr(cls, "__construct__", lambda: enum_constr)

        return cls

    # Extend the enum type with __missing__ method. So if a enum value
    # not found in the enum, a new pseudo member is created.
    # The idea is taken from: https://stackoverflow.com/a/57179436
    @classmethod
    def _missing_(cls, value: t.Any) -> t.Optional["TEnum"]:
        if isinstance(value, int):
            return cls._create_pseudo_member_(value)
        return None  # will raise the ValueError in Enum.__new__

    @classmethod
    def _create_pseudo_member_(cls, value: int) -> "TEnum":
        pseudo_member = cls._value2member_map_.get(value, None)  # type: ignore
        if pseudo_member is None:
            new_member = int.__new__(cls, value)
            # I expect a name attribute to hold a string, hence str(value)
            # However, new_member._name_ = value works, too
            new_member._name_ = str(value)
            new_member._value_ = value
            pseudo_member = cls._value2member_map_.setdefault(value, new_member)  # type: ignore
        return pseudo_member  # type: ignore

    if t.TYPE_CHECKING:

        @classmethod
        def __construct__(cls: "t.Type[EnumType]") -> "TEnumConstruct[EnumType]":
            ...


EnumType = t.TypeVar("EnumType", bound=TEnum)


class TEnumConstruct(Adapter[int, int, EnumType, EnumType]):
    """
    Typed enum.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls, subcon: Construct[int, int], enum_type: t.Type[EnumType]
        ) -> "TEnumConstruct[EnumType]":
            ...

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[EnumType]):
        if not issubclass(enum_type, TEnum):
            raise TypeError(
                "'{}' has to be a '{}'".format(repr(enum_type), repr(TEnum))
            )

        # save enum type
        self.enum_type = t.cast(t.Type[EnumType], enum_type)  # type: ignore

        # init adatper
        super(TEnumConstruct, self).__init__(subcon)  # type: ignore

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

# ## TFlags #######################################################################################################
class TFlags(enum.IntFlag):
    @classmethod
    def __init_subclass__(
        cls,
        subcon: "cs.Construct[t.Any, t.Any]",
        **kwargs: t.Any,
    ):
        super().__init_subclass__(**kwargs)

        # validate types
        if not isinstance(subcon, cs.Construct):  # type: ignore
            raise ValueError(
                f"`subcon` parameter has to be an `Construct` object but is {type(subcon)}"
            )

        # create construct format
        enum_constr = TFlagsConstruct(subcon, cls)

        # save construct format and make the class compatible to `Constructable` protocol
        setattr(cls, "__construct__", lambda: enum_constr)

        return cls

    if t.TYPE_CHECKING:

        @classmethod
        def __construct__(
            cls: "t.Type[FlagsEnumType]",
        ) -> "TFlagsConstruct[FlagsEnumType]":
            ...


FlagsEnumType = t.TypeVar("FlagsEnumType", bound=TFlags)


class TFlagsConstruct(Adapter[int, int, FlagsEnumType, FlagsEnumType]):
    """
    Typed flags.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls, subcon: Construct[int, int], enum_type: t.Type[FlagsEnumType]
        ) -> "TFlagsConstruct[FlagsEnumType]":
            ...

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[FlagsEnumType]):
        if not issubclass(enum_type, TFlags):
            raise TypeError(
                "'{}' has to be a '{}'".format(repr(enum_type), repr(TFlags))
            )

        # save enum type
        self.enum_type = t.cast(t.Type[FlagsEnumType], enum_type)  # type: ignore

        # init adatper
        super(TFlagsConstruct, self).__init__(subcon)  # type: ignore

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
