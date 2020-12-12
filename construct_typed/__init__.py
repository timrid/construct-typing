from enum import IntEnum
from typing import Any, Type, Dict, TYPE_CHECKING, TypeVar, Union
import typing
from construct.core import Construct, Adapter, Struct
from construct.lib.containers import Container


#===============================================================================
# mappings
#===============================================================================
if TYPE_CHECKING:
    EnumType = TypeVar("EnumType", bound=IntEnum)

    class TypedEnum(Adapter[EnumType, Union[int, str, IntEnum], int, int]):
        def __init__(self, subcon: Construct[int, int], enum_type: Type[EnumType]): ...

# def wrap_enum(enum_type: Type[EnumType]) -> 
else:
    class TypedEnum(Adapter):
        def __init__(self, subcon, enum_type):
            super(TypedEnum, self).__init__(subcon)

            @classmethod
            def _missing_(cls, value):
                if isinstance(value, int):
                    return cls._create_pseudo_member_(value)
                return None  # will raise the ValueError in Enum.__new__

            @classmethod
            def _create_pseudo_member_(cls, value):
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
           
            self.enum_type = enum_type

        def _decode(self, obj, context, path):
            if isinstance(obj, str):
                return int(self.enum_type[obj])
            else:
                return self.enum_type(obj)

        def _encode(self, obj, context, path):
            try:
                if isinstance(obj, str):
                    return int(self.enum_type[obj])
                else:
                    return int(self.enum_type(obj))
            except:
                raise MappingError("building failed, no mapping for %r" % (obj,), path=path)




# ===============================================================================
# structures and sequences
# ===============================================================================
ParsedType = TypeVar("ParsedType")
BuildTypes = TypeVar("BuildTypes")

# In an optimal way the code look like this (with python 3.9):
#
# def Subcon(subcon: Construct[ParsedType, BuildTypes]) -> Type[ParsedType]:
#     return Annotated[ParsedType, subcon]
#
# But this only works if the type annotations are directly in the source
# code. However, in this case the type annotations are stored in a separate
# stub (.pyi) file, which is not available at runtime.
#
# Therefore a small hack is used here. During the type checking, the type
# of the subcon is determined with the help of the stub files and returned. 
# At runtime the actual subcon and not its type is returned, so that the
# "TypedStruct" can use this for creating the struct.
#
# This has the disadvantage that it can cause problems if the type is evaluated
# at runtime...
if TYPE_CHECKING:
    def Subcon(subcon: Construct[ParsedType, BuildTypes]) -> Type[ParsedType]: ...
else:
    def Subcon(subcon: Construct) -> Construct:
        return subcon

if TYPE_CHECKING:
    class TypedContainer(Container[Any]):
        ...
else:
    class TypedContainer(Container):
        pass

if TYPE_CHECKING:
    ContainerType = TypeVar("ContainerType", bound=TypedContainer)
    class TypedStruct(Adapter[Container[Any], Dict[str, Any], ContainerType, Dict[str, Any]]):
        def __init__(self, container_type: Type[ContainerType], swapped: bool = False) -> None: ...
else:
    class TypedStruct(Adapter):
        def __init__(self, container_type, swapped = False):
            if not issubclass(container_type, TypedContainer):
                raise TypeError("the subcon has to be a TypedContainer")
            self.container_type = container_type

            # extract the construct formats from the struct_type
            subcons = {}
            subcon_formats = typing.get_type_hints(container_type)
            subcon_items = subcon_formats.items()
            if swapped:
                subcon_items = reversed(subcon_items)
            for subcon_name, subcon_format in subcon_items:
                subcons[subcon_name] = subcon_format

            # init Adatper with a Struct as subcon
            super(TypedStruct, self).__init__(Struct(**subcons))

        def _decode(self, obj, context, path):
            return self.container_type(obj)

        def _encode(self, obj, context, path):
            return obj



# TODO: TypedUnion