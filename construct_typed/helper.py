import typing as t

from .generic_wrapper import ListContainer

OptType = t.TypeVar("OptType")
ListType = t.TypeVar("ListType")

Opt = t.Optional[OptType]
List = t.Union[ListContainer[ListType], t.List[ListType]]