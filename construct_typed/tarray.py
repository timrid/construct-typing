import typing as t
import construct as cs
from .generic_wrapper import *


class TArray(
    Adapter[
        SubconParsedType,
        SubconBuildTypes,
        t.List[SubconParsedType],
        t.List[SubconParsedType],
    ]
):
    """
    Adapter for an Array, that transforms the "ListContainer" to an standard "list" while parsing
    """

    def __init__(
        self,
        count: ConstantOrContextLambda[int],
        subcon: Construct[SubconParsedType, SubconBuildTypes],
        discard: bool = False,
    ) -> None:
        # init adatper
        super(TArray, self).__init__(cs.Array(count, subcon, discard))  # type: ignore

    def _decode(
        self, obj: SubconParsedType, context: Context, path: PathType
    ) -> ParsedType:
        return list(obj)  # type: ignore

    def _encode(
        self,
        obj: t.List[SubconParsedType],
        context: Context,
        path: PathType,
    ) -> SubconBuildTypes:
        return obj  # type: ignore
