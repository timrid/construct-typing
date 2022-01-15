import enum
import typing as t

import construct as cs

from .generics import *

T = t.TypeVar("T")


class ConstructEnumMeta(enum.EnumMeta):
    @classmethod
    def __prepare__(
        metacls,  # type: ignore
        name: str,
        bases: t.Tuple[type, ...],
        **kwargs: t.Any,
    ) -> t.Mapping[str, object]:
        # This method is needed, because the original __prepare__ method does not accept kwargs.
        return super().__prepare__(name, bases)

    def __new__(
        metacls: t.Type[T],  # type: ignore
        name: str,
        bases: t.Tuple[type, ...],
        namespace: t.Dict[str, t.Any],
        **kwargs: t.Any,
    ) -> T:
        # create new enum object
        cls = super().__new__(metacls, name, bases, namespace)  # type: ignore

        # if the `EnumBase` class is created, there are no parameters
        if len(kwargs) == 0:
            return cls

        # extract parameters from kwargs
        subcon: "cs.Construct[t.Any, t.Any]" = kwargs.pop("subcon", None)
        if not isinstance(subcon, cs.Construct):  # type: ignore
            raise ValueError(
                f"`subcon` parameter has to be an `Construct` object but is {type(subcon)}"
            )
        if len(kwargs) > 0:  # check remaining parameters
            unsupp_parm = ", ".join([f"'{k}'" for k in kwargs.keys()])
            raise ValueError(f"unsupported parameter(s) detected: {unsupp_parm}")

        # create construct format
        if EnumBase in bases:
            enum_constr = EnumConstruct(subcon, cls)  # type: ignore
        elif FlagsEnumBase in bases:
            enum_constr = FlagsEnumConstruct(subcon, cls)  # type: ignore
        else:
            enum_constr = None

        # save construct format and make the class compatible to `Constructable` protocol
        setattr(cls, "__construct__", lambda: enum_constr)  # type: ignore

        return cls


# ## EnumConstruct ############################################################################################################
class EnumBase(enum.IntEnum, metaclass=ConstructEnumMeta):
    """
    Base class for an Enum used in `construct_typed.EnumConstruct`.

    This class extends the standard `enum.IntEnum`, so that missing values are automatically generated.
    """

    # Extend the enum type with __missing__ method. So if a enum value
    # not found in the enum, a new pseudo member is created.
    # The idea is taken from: https://stackoverflow.com/a/57179436
    @classmethod
    def _missing_(cls, value: t.Any) -> t.Optional["EnumBase"]:
        if isinstance(value, int):
            return cls._create_pseudo_member_(value)
        return None  # will raise the ValueError in Enum.__new__

    @classmethod
    def _create_pseudo_member_(cls, value: int) -> "EnumBase":
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
        def __construct__(cls: "t.Type[EnumType]") -> "EnumConstruct[EnumType]":
            ...


EnumType = t.TypeVar("EnumType", bound=EnumBase)


class EnumConstruct(Adapter[int, int, EnumType, EnumType]):
    """
    Typed enum.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls, subcon: Construct[int, int], enum_type: t.Type[EnumType]
        ) -> "EnumConstruct[EnumType]":
            ...

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[EnumType]):
        if not issubclass(enum_type, EnumBase):
            raise TypeError(
                "'{}' has to be a '{}'".format(repr(enum_type), repr(EnumBase))
            )

        # save enum type
        self.enum_type = t.cast(t.Type[EnumType], enum_type)  # type: ignore

        # init adatper
        super(EnumConstruct, self).__init__(subcon)  # type: ignore

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


# ## FlagsEnumConstruct #######################################################################################################
class FlagsEnumBase(enum.IntFlag, metaclass=ConstructEnumMeta):
    if t.TYPE_CHECKING:

        @classmethod
        def __construct__(
            cls: "t.Type[FlagsEnumType]",
        ) -> "FlagsEnumConstruct[FlagsEnumType]":
            ...


FlagsEnumType = t.TypeVar("FlagsEnumType", bound=FlagsEnumBase)


class FlagsEnumConstruct(Adapter[int, int, FlagsEnumType, FlagsEnumType]):
    """
    Typed enum.
    """

    if t.TYPE_CHECKING:

        def __new__(
            cls, subcon: Construct[int, int], enum_type: t.Type[FlagsEnumType]
        ) -> "FlagsEnumConstruct[FlagsEnumType]":
            ...

    def __init__(self, subcon: Construct[int, int], enum_type: t.Type[FlagsEnumType]):
        if not issubclass(enum_type, FlagsEnumBase):
            raise TypeError(
                "'{}' has to be a '{}'".format(repr(enum_type), repr(FlagsEnumBase))
            )

        # save enum type
        self.enum_type = t.cast(t.Type[FlagsEnumType], enum_type)  # type: ignore

        # init adatper
        super(FlagsEnumConstruct, self).__init__(subcon)  # type: ignore

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
