import enum
import typing as t
import textwrap
import construct as cs
import dataclasses

ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")
SubconParsedType = t.TypeVar("SubconParsedType")
SubconBuildTypes = t.TypeVar("SubconBuildTypes")
ListType = t.TypeVar("ListType")
ValueType = t.TypeVar("ValueType")


if t.TYPE_CHECKING:
    # while type checking, the original classes are generics, because they are defined in the stubs.
    from construct import Construct as Construct
    from construct import Adapter as Adapter
    from construct import ListContainer as ListContainer
    from construct import Context as Context
    from construct import ConstantOrContextLambda as ConstantOrContextLambda
    from construct import PathType as PathType
else:
    # at runtime, the original classes are no generics, so whe have to make new classes with generics support
    class Construct(t.Generic[ParsedType, BuildTypes], cs.Construct):
        pass

    class Adapter(
        t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
        cs.Adapter,
    ):
        pass

    class ListContainer(t.Generic[ListType], cs.ListContainer):
        pass

    class Context:
        pass

    ConstantOrContextLambda = t.Union[ValueType, t.Callable[[Context], t.Any]]
    PathType = str
