import dataclasses
import enum
import textwrap
import typing as t

ParsedType = t.TypeVar("ParsedType")
BuildTypes = t.TypeVar("BuildTypes")
SubconParsedType = t.TypeVar("SubconParsedType")
SubconBuildTypes = t.TypeVar("SubconBuildTypes")
ListType = t.TypeVar("ListType")
ValueType = t.TypeVar("ValueType")


if t.TYPE_CHECKING:
    # while type checking, the original classes are already generics, because they are defined like this in the stubs.
    from construct import Adapter as Adapter
    from construct import ConstantOrContextLambda as ConstantOrContextLambda
    from construct import Construct as Construct
    from construct import Context as Context
    from construct import ListContainer as ListContainer
    from construct import PathType as PathType


else:
    import construct as cs

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
