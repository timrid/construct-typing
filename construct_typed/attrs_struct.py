# -*- coding: utf-8 -*-
# pyright: strict
import textwrap
import typing as t

import attr
import construct as cs
from .generics import Adapter, Construct, Context, ParsedType, PathType

T = t.TypeVar("T")

# Static type inference support via __dataclass_transform__ implemented as per:
# https://github.com/microsoft/pyright/blob/1.1.135/specs/dataclass_transforms.md
def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: t.Tuple[t.Union[type, t.Callable[..., t.Any]], ...] = (()),
) -> t.Callable[[T], T]:
    return lambda a: a


ATTRS_METADATA_KEY = "__construct_typed_subcon"


def attrs_field(
    subcon: Construct[ParsedType, t.Any],
    doc: t.Optional[str] = None,
    parsed: t.Optional[t.Callable[[t.Any, Context], None]] = None,
) -> ParsedType:
    """
    Helper method for `AttrsStruct` and `AttrsBitStruct` to create the attrs fields.

    This method also processes `Const` and `Default`, to pass these values als default values to the dataclass.

    # TODO: Implement `default` parameter for `attrs_field`
    """
    orig_subcon = subcon

    # Rename subcon, if doc or parsed are available
    if (doc is not None) or (parsed is not None):
        if doc is not None:
            doc = textwrap.dedent(doc).strip("\n")
        subcon = cs.Renamed(subcon, newdocs=doc, newparsed=parsed)

    if orig_subcon.flagbuildnone is True:
        init = False
        default = None
    else:
        init = True
        default = attr.NOTHING

    # Set default values in case of special sucons
    if isinstance(orig_subcon, cs.Const):
        const_subcon: "cs.Const[t.Any, t.Any, t.Any, t.Any]" = orig_subcon
        default = const_subcon.value
    elif isinstance(orig_subcon, cs.Default):
        default_subcon: "cs.Default[t.Any, t.Any, t.Any, t.Any]" = orig_subcon
        if callable(default_subcon.value):
            default = None  # context lambda is only defined at parsing/building
        else:
            default = default_subcon.value

    return t.cast(
        ParsedType,
        attr.field(
            default=default,
            init=init,
            metadata={ATTRS_METADATA_KEY: subcon},
        ),
    )


class AttrsConstruct(Adapter[t.Any, t.Any, T, T]):
    if t.TYPE_CHECKING:

        def __new__(
            cls,
            attrs_cls: t.Type[T],
            reverse_fields: bool = False,
        ) -> "AttrsConstruct[T]":
            ...

    def __init__(
        self,
        attrs_cls: t.Type[T],
        reverse_fields: bool = False,
    ) -> None:
        if not attr.has(attrs_cls):
            raise TypeError(f"'{attrs_cls}' has to be a 'attrs' object")

        self.attrs_cls = attrs_cls
        self.reverse_fields = reverse_fields

        # get all fields from the dataclass
        fields = attr.fields(attrs_cls)
        if reverse_fields:
            fields = tuple(reversed(fields))

        # extract the construct formats from the struct_type
        subcon_fields = {}
        for field in fields:
            subcon_fields[field.name] = field.metadata[ATTRS_METADATA_KEY]

        # init adatper
        super().__init__(cs.Struct(**subcon_fields))  # type: ignore

    def _decode(
        self,
        obj: "cs.Container[t.Any]",
        context: Context,
        path: PathType,
    ) -> T:
        # get all fields from the dataclass
        fields = attr.fields(self.attrs_cls)

        # extract all fields from the container, that are used for create the dataclass object
        dc_init = {}
        for field in fields:
            if field.init:
                value = obj[field.name]
                dc_init[field.name] = value

        # create object of dataclass
        dc = self.attrs_cls(**dc_init)  # type: ignore

        # extract all other values from the container, an pass it to the dataclass
        for field in fields:
            if not field.init:
                value = obj[field.name]
                setattr(dc, field.name, value)

        return dc

    def _encode(self, obj: T, context: Context, path: PathType) -> t.Dict[str, t.Any]:
        if not isinstance(obj, self.attrs_cls):
            raise TypeError(f"'{repr(obj)}' has to be of type {repr(self.attrs_cls)}")

        # get all fields from the dataclass
        fields = attr.fields(self.attrs_cls)

        # extract all fields from the container, that are used for create the dataclass object
        ret_dict: t.Dict[str, t.Any] = {}
        for field in fields:
            value = getattr(obj, field.name)
            ret_dict[field.name] = value

        return ret_dict


# Helper object for defining the `constr` of a `struct`. Will be replaced with the proper construct, when class is created.
this_struct: Construct[t.Any, t.Any] = Construct()


def _replace_this_struct(constr: "Construct[t.Any, t.Any]", replacement: t.Any):
    """Recursive search for `this_struct` in all SubConstructs and replace it with AttrsStruct"""
    subcon = getattr(constr, "subcon", None)
    if subcon is this_struct:
        setattr(constr, "subcon", replacement)
    elif subcon is not None:
        _replace_this_struct(subcon, replacement)
    else:
        raise ValueError(
            "Could not find `this_struct`. Only SubConstructs are supported"
        )


@__dataclass_transform__(kw_only_default=True, field_descriptors=(attrs_field,))
class AttrsStruct:
    """
    Adapter for a attrs-class for optimised type hints / static autocompletion in comparision to the original Struct.

    Before this construct can be created a dataclasses.dataclass type must be created, which must also derive from DataclassMixin. In this dataclass all fields must be assigned to a construct type using csfield.

    Internally, all fields are converted to a Struct, which does the actual parsing/building.

    Parses to a dataclasses.dataclass instance, and builds from such instance. Size is the sum of all subcon sizes, unless any subcon raises SizeofError.

    Metaclass paramters::

    :param constr: Create a more complex construct. `this_struct` can be used for representing this AttrsStruct object.
    :param reverse_fields: Flag if the fields should be reversed parsed/build

    Example::

        >>> from construct import Bytes, Int8ub, this
        >>> from construct_typed import AttrsStruct, attrs_field, construct
        >>> class Image(AttrsStruct):
        ...     width: int = attrs_field(Int8ub)
        ...     height: int = attrs_field(Int8ub)
        ...     pixels: bytes = attrs_field(Bytes(this.height * this.width))
        >>> d = construct(Image)
        >>> d.parse(b"\x01\x0212")
        Image(width=1, height=2, pixels=b'12')
    """

    @classmethod
    def __init_subclass__(
        cls,
        constr: "cs.Construct[t.Any, t.Any]" = this_struct,
        reverse_fields: bool = False,
        **kwargs: t.Any,
    ):
        super().__init_subclass__(**kwargs)

        # validate types
        if not isinstance(constr, cs.Construct):  # type: ignore
            raise ValueError("`constr` parameter has to be an `Construct` object")
        if not isinstance(reverse_fields, bool):  # type: ignore
            raise ValueError("`reverse_fields` parameter has to be an `bool` object")

        # create attrs class
        cls = attr.define(cls, kw_only=True, slots=False)

        # create construct format
        attrs_constr = AttrsConstruct(cls, reverse_fields)
        if constr is this_struct:
            constr = attrs_constr
        else:
            _replace_this_struct(constr, attrs_constr)

        # save construct format and make the class compatible to `Constructable` protocol
        setattr(cls, "__construct__", lambda: constr)

        # the `construct` library is using the [] access internally, so struct objects
        # should also make this possible and not only via the dot access.
        setattr(cls, "__getitem__", lambda self, key: getattr(self, key))  # type: ignore
        setattr(cls, "__setitem__", lambda self, key, value: setattr(self, key, value))  # type: ignore

        return cls

    if t.TYPE_CHECKING:

        @classmethod
        def __construct__(cls: t.Type[T]) -> "AttrsConstruct[T]":
            ...

        def __getitem__(self, key: str) -> t.Any:
            ...

        def __setitem__(self, key: str, value: t.Any) -> None:
            ...
