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
    from construct import Array as Array
    from construct import Construct as Construct
    from construct import ListContainer as ListContainer
    from construct import Subconstruct as Subconstruct
    from construct import SymmetricAdapter as SymmetricAdapter
    from construct import Tunnel as Tunnel
    from construct import Validator as Validator
    from construct.core import ConstantOrContextLambda as ConstantOrContextLambda
    from construct.core import Context as Context
    from construct.core import PathType as PathType


else:
    import construct as cs

    # at runtime, the original classes are not generic, so we have to make new classes with generics support
    class Construct(t.Generic[ParsedType, BuildTypes], cs.Construct):
        """Subscriptable version of `construct.Construct` that can be used as a generic type."""

    class Subconstruct(
        t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
        cs.Subconstruct,
    ):
        """Subscriptable version of `construct.Subconstruct` that can be used as a generic type."""

    class Adapter(
        t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
        cs.Adapter,
    ):
        """Subscriptable version of `construct.Adapter` that can be used as a generic type."""

    class Tunnel(
        t.Generic[SubconParsedType, SubconBuildTypes],
        cs.Tunnel,
    ):
        """Subscriptable version of `construct.Tunnel` that can be used as a generic type."""

    class SymmetricAdapter(
        t.Generic[SubconParsedType, SubconBuildTypes, ParsedType, BuildTypes],
        cs.SymmetricAdapter,
    ):
        """Subscriptable version of `construct.SymmetricAdapter` that can be used as a generic type."""

    class Validator(
        t.Generic[SubconParsedType, SubconBuildTypes],
        cs.Validator,
    ):
        """Subscriptable version of `construct.Validator` that can be used as a generic type."""

    class Array(
        t.Generic[SubconParsedType, SubconBuildTypes],
        cs.Array,
    ):
        """Subscriptable version of `construct.Array` that can be used as a generic type."""

    class ListContainer(t.Generic[ListType], cs.ListContainer):
        pass

    class Context:
        pass

    ConstantOrContextLambda = ValueType | t.Callable[[Context], t.Any]
    PathType = str
