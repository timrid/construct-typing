import typing as t

ParsedType = t.TypeVar("ParsedType", covariant=True)
BuildTypes = t.TypeVar("BuildTypes", contravariant=True)
SubconParsedType = t.TypeVar("SubconParsedType", covariant=True)
SubconBuildTypes = t.TypeVar("SubconBuildTypes", contravariant=True)
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


@t.runtime_checkable
class Constructable(t.Protocol[ParsedType, BuildTypes]):
    def __construct__(self) -> "Construct[ParsedType, BuildTypes]":
        raise NotImplementedError


def construct(
    constr: t.Union[
        Constructable[ParsedType, BuildTypes], "Construct[ParsedType, BuildTypes]"
    ],
) -> Construct[ParsedType, BuildTypes]:
    """Get construct instance of `Constructable` or `Construct`"""
    if isinstance(constr, Constructable):
        constr = constr.__construct__()
    return constr
