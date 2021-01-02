import typing as t

from .generic_wrapper import ListContainer

OptionalType = t.TypeVar("OptionalType")
ListType = t.TypeVar("ListType")

Optional = t.Optional[OptionalType]
List = t.Union[ListContainer[ListType], t.List[ListType]]