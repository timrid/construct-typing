import enum
import typing as t

from .generic_wrapper import *


# ## TEnum ############################################################################################################
class EnumValue:
    """
    This is a helper class for adding documentation to an enum value.
    """

    def __init__(self, value: int, doc: t.Optional[str] = None) -> None:
        self.value = value
        self.__doc__ = doc if doc else ""


class EnumBase(enum.IntEnum):
    """
    Base class for an Enum used in `construct_typed.TEnum`.

    This class extends the standard `enum.IntEnum` by.
     - missing values are automatically generated
     - possibility to add documentation for each enum value (see `EnumValue`)

    Example::

        >>> class State(EnumBase):
        ...     Idle = 1
        ...     Running = EnumValue(2, "This is the running state.")

        >>> State(1)
        <State.Idle: 1>

        >>> State["Idle"]
        <State.Idle: 1>

        >>> State.Idle
        <State.Idle: 1>

        >>> State(3)  # missing value
        <State.3: 3>

        >>> State.Running.__doc__  # documentation
        'This is the running state.'
    """

    def __new__(cls, val: t.Union[EnumValue, int]) -> "EnumBase":
        if isinstance(val, EnumValue):
            obj = int.__new__(cls, val.value)
            obj._value_ = val.value
            obj.__doc__ = val.__doc__
        else:
            obj = int.__new__(cls, val)
            obj._value_ = val
            obj.__doc__ = ""
        return obj

    # Extend the enum type with _missing_ method. So if a enum value
    # not found in the enum, a new pseudo member is created.
    # The idea is taken from: https://stackoverflow.com/a/57179436
    @classmethod
    def _missing_(cls, value: t.Any) -> t.Optional[enum.Enum]:
        if isinstance(value, int):
            pseudo_member = cls._value2member_map_.get(value, None)
            if pseudo_member is None:
                new_member = int.__new__(cls, value)
                # I expect a name attribute to hold a string, hence str(value)
                # However, new_member._name_ = value works, too
                new_member._name_ = str(value)
                new_member._value_ = value
                new_member.__doc__ = "missing value"
                pseudo_member = cls._value2member_map_.setdefault(value, new_member)
            return pseudo_member
        return None  # will raise the ValueError in Enum.__new__

    def __reduce_ex__(self, proto: t.Any):
        """
        Pickle enums by value instead of name (restores pre-3.11 behavior).
        See https://github.com/python/cpython/pull/26658 for why this exists.
        """
        return self.__class__, (self._value_,)


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
    """
    Base class for an Enum used in `construct_typed.TFlagsEnum`.

    This class extends the standard `enum.IntFlag` by.
     - possibility to add documentation for each enum value (see `EnumValue`)

    Example::

        >>> class Option(FlagsEnumBase):
        ...     OptOne = 1
        ...     OptTwo = EnumValue(2, "This is option two.")

        >>> Option(1)
        <Option.OptOne: 1>

        >>> Option["OptOne"]
        <Option.OptOne: 1>

        >>> Option.OptOne
        <Option.OptOne: 1>

        >>> Option(3)
        <Option.OptTwo|OptOne: 3>

        >>> Option(4)
        <Option.4: 4>

        >>> Option.OptTwo.__doc__  # documentation
        'This is option two.'
    """

    def __new__(cls, val: t.Union[EnumValue, int]) -> "FlagsEnumBase":
        if isinstance(val, EnumValue):
            obj = int.__new__(cls, val.value)
            obj._value_ = val.value
            obj.__doc__ = val.__doc__
        else:
            obj = int.__new__(cls, val)
            obj._value_ = val
            obj.__doc__ = ""
        return obj

    @classmethod
    def _missing_(cls, value: t.Any) -> t.Any:
        """
        Returns member (possibly creating it) if one can be found for value.
        """
        new_member = super()._missing_(value)
        new_member.__doc__ = "missing value"
        return new_member

    def __reduce_ex__(self, proto: t.Any):
        """
        Pickle enums by value instead of name (restores pre-3.11 behavior).
        See https://github.com/python/cpython/pull/26658 for why this exists.
        """
        return self.__class__, (self._value_,)


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
