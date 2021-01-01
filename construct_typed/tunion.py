import enum
import typing as t
import textwrap
import construct as cs
import dataclasses
from .generic_wrapper import *

DataclassType = t.TypeVar("DataclassType")


def TUnionField(
    subcon: Construct[ParsedType, BuildTypes],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, "cs.Context"], None]] = None,
) -> ParsedType:
    """
    Create a dataclass field for a "TUnion" from a subcon.
    """
    # Rename subcon, if doc or parsed are available
    if (doc is not None) or (parsed is not None):
        if doc is not None:
            doc = textwrap.dedent(doc)
        subcon = cs.Renamed(subcon, newdocs=doc, newparsed=parsed)

    if subcon.flagbuildnone is True:
        # some subcons have a predefined default value. all other have "None"
        default: t.Any = None
        if isinstance(subcon, (cs.Const, cs.Default)):
            if callable(subcon.value):  # type: ignore
                raise ValueError("lamda as default is not supported")
            default = subcon.value  # type: ignore

        # if subcon builds from "None", set default to "None"
        field = dataclasses.field(
            default=default,
            init=False,
            metadata={"subcon": cs.Renamed(subcon, newdocs=doc)},
        )
    else:
        field = dataclasses.field(metadata={"subcon": subcon})

    return field  # type: ignore


class TUnion(Adapter[t.Any, t.Any, DataclassType, DataclassType]):
    pass  # TODO