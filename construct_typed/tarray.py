import typing as t
import construct as cs
from .generic_wrapper import *


class TArray(
    Adapter[
        t.Any,
        t.Any,
        ParsedType,
        BuildTypes,
    ]
):
    """
    Adapter for an Array, that transforms the "ListContainer" to an standard "list" while parsing
    """

    # this is unfortunately needed because the stubs are using __new__ instead of __init__
    if t.TYPE_CHECKING:

        def __new__(
            cls,
            count: ConstantOrContextLambda[int],
            subcon: Construct[SubconParsedType, SubconBuildTypes],
            discard: bool = False,
        ) -> "TArray[t.List[SubconParsedType], t.List[SubconParsedType]]":
            ...

    def __init__(
        self,
        count: ConstantOrContextLambda[int],
        subcon: Construct[ParsedType, BuildTypes],
        discard: bool = False,
    ) -> None:
        # init adatper
        super(TArray, self).__init__(cs.Array(count, subcon, discard))  # type: ignore

    def _decode(
        self, obj: ListContainer[ParsedType], context: Context, path: PathType
    ) -> ParsedType:
        return list(obj)  # type: ignore

    def _encode(
        self,
        obj: BuildTypes,
        context: Context,
        path: PathType,
    ) -> t.List[BuildTypes]:
        return obj  # type: ignore
