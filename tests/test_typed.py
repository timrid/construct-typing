# -*- coding: utf-8 -*-
import dataclasses
import enum
import hashlib
import textwrap
import typing as t

import construct as cs

import construct_typed as cst
from construct_typed import (
    DataclassBitStruct,
    DataclassMixin,
    DataclassStruct,
    csfield,
    csfield_const,
    csfield_default,
    csfield_noinit,
)
from construct_typed.dataclass_struct import DataclassFieldError

from .declarativeunittest import common, raises, setattrs


def test_dataclass_const_default_noinit() -> None:
    @dataclasses.dataclass
    class ConstDefaultTest(DataclassMixin):
        const_bytes: bytes = csfield_const(cs.Bytes(3), b"BMP")
        const_int: int = csfield_const(cs.Int8ub, 5)
        default_int: int = csfield_default(cs.Int8ub, default=8)
        default_lambda: bytes | None = csfield_noinit(
            cs.Default(
                cs.Bytes(cs.this.default_int), lambda ctx: bytes(ctx.default_int)
            )
        )
        computed: bytes | None = csfield_noinit(
            cs.Computed(lambda ctx: bytes(i + 49 for i in range(ctx.default_int)))
        )
        # Construct allows to put non-default values after Default. Dataclass and Pyright don't like that too much. It is necessary to
        # specify the field `kw_only` and pass it "by keyword".
        normal_int: int = csfield(cs.Int8ub, kw_only=True)
        const_int2: int = csfield_const(cs.Int8ub, 5)

    format = DataclassStruct(ConstDefaultTest)

    a = ConstDefaultTest(
        normal_int=7,
    )
    assert a.const_bytes == b"BMP"
    assert a.const_int == 5
    assert a.default_int == 8
    assert a.default_lambda is None
    assert a.computed is None
    assert format.build(a) == b"BMP\x05\x08\x00\x00\x00\x00\x00\x00\x00\x00\x07\x05"
    a = format.parse(format.build(a))
    assert a.default_int == 8
    assert a.default_lambda == bytes(8)
    assert a.computed == b"12345678"

    # Overriding Default-Values should be OK and modify the `computed` value.
    b = ConstDefaultTest(
        default_int=4,
        normal_int=1,
    )
    b.default_lambda = b"TEST"
    b = format.parse(format.build(b))
    assert b.default_int == 4
    assert b.default_lambda == b"TEST"
    assert b.computed == b"1234"


def test_csfield_validation_errors() -> None:
    # `csfield` must reject subcons that can build from None.
    assert (
        raises(lambda: csfield(cs.Const(b"BMP"))) is DataclassFieldError  # type: ignore
    )

    # `csfield_noinit` must reject subcons that cannot build from None.
    assert raises(lambda: csfield_noinit(cs.Int8ub)) is DataclassFieldError  # type: ignore

    # `csfield_const`/`csfield_default` must reject subcons that already can build
    # from None (e.g. double-wrapping another `Const`/`Default`/`Computed`).
    assert (
        raises(lambda: csfield_const(cs.Const(b"BMP"), b"BMP")) is DataclassFieldError  # type: ignore
    )
    assert (
        raises(lambda: csfield_default(cs.Computed(1), default=1))
        is DataclassFieldError  # type: ignore
    )

    # `csfield_const`/`csfield_default` must reject context lambdas.
    assert (
        raises(lambda: csfield_const(cs.Int8ub, lambda ctx: 1)) is DataclassFieldError  # type: ignore
    )
    assert (
        raises(lambda: csfield_default(cs.Int8ub, default=lambda ctx: 1))  # type: ignore
        is DataclassFieldError
    )

    # `csfield_const`/`csfield_default` must reject subcons that are already a `Const`/`Default`.
    assert (
        raises(lambda: csfield_const(cs.Const(b"BMP"), b"BMP"))  # type: ignore
        is DataclassFieldError
    )
    assert (
        raises(lambda: csfield_default(cs.Default(cs.Int8ub, 1), default=1))  # type: ignore
        is DataclassFieldError
    )


def test_csfield_default_kw_only_ordering() -> None:
    # If a field with a default (created via `csfield_default()`) is followed by a plain `csfield()`
    # without `kw_only=True`, Python's own dataclass machinery must reject the class definition.
    # `dataclasses.make_dataclass()` is used here (instead of a `class` statement) so that static type
    # checkers - which also correctly flag this as an error - don't fail the type-check of this test file.
    def build_bad_class() -> None:
        dataclasses.make_dataclass(
            "BadOrdering",
            [
                ("a", int, csfield_default(cs.Int8ub, default=1)),
                ("b", int, csfield(cs.Int8ub)),  # missing kw_only=True
            ],
            bases=(DataclassMixin,),
        )

    assert raises(build_bad_class) is TypeError

    # Marking the following field as `kw_only=True` fixes the ordering issue.
    @dataclasses.dataclass
    class GoodOrdering(DataclassMixin):
        a: int = csfield_default(cs.Int8ub, default=1)
        b: int = csfield(cs.Int8ub, kw_only=True)

    obj = GoodOrdering(b=2)
    assert obj.a == 1
    assert obj.b == 2


def test_dataclass_padded() -> None:
    @dataclasses.dataclass
    class PaddingTest(DataclassMixin):
        padding: bytes | None = csfield_noinit(cs.Padding(1))
        padded_pass: bytes | None = csfield_noinit(cs.Padded(2, cs.Pass))
        padded_bytes: bytes = csfield(cs.Padded(7, cs.Bytes(5)))
        padded_string: str = csfield(cs.PaddedString(4, "utf-8"))

    format = DataclassStruct(PaddingTest)

    a = PaddingTest(padded_bytes=b"12345", padded_string="abc")
    assert a.padding is None
    assert a.padded_pass is None
    assert a.padded_bytes == b"12345"
    assert a.padded_string == "abc"
    assert format.build(a) == b"\x00\x00\x0012345\x00\x00abc\x00"


def test_dataclass_access() -> None:
    @dataclasses.dataclass
    class TestTContainer(DataclassMixin):
        a: int = csfield_const(cs.Byte, 1)
        b: int = csfield(cs.Int8ub)

    tcontainer = TestTContainer(b=2)

    # tcontainer
    assert tcontainer.a == 1
    assert tcontainer["a"] == 1
    assert tcontainer.b == 2
    assert tcontainer["b"] == 2

    tcontainer.a = 5
    assert tcontainer.a == 5
    assert tcontainer["a"] == 5
    tcontainer["a"] = 6
    assert tcontainer.a == 6
    assert tcontainer["a"] == 6

    # wrong creation
    assert raises(lambda: TestTContainer(a=0, b=1)) is TypeError  # type: ignore


def test_dataclass_str_repr() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        signature: bytes = csfield_const(cs.Bytes(3), b"BMP")
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)

    format = DataclassStruct(Image)
    obj = Image(width=3, height=2)
    assert (
        str(obj)
        == "Image: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )
    obj = format.parse(format.build(obj))
    assert (
        str(obj)
        == "Image: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )


def test_dataclass_ifthenelse() -> None:
    @dataclasses.dataclass
    class IfThenElseTest(DataclassMixin):
        test_if: int | None = csfield(cs.If(False, cs.Int8ub))
        test_ifthenelse: int | None = csfield(cs.IfThenElse(True, cs.Int8ub, cs.Pass))

    a = IfThenElseTest(test_if=None, test_ifthenelse=None)
    assert a.test_if is None
    assert a.test_ifthenelse is None


def test_dataclass_struct() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        pixels: bytes = csfield(cs.Bytes(cs.this.height * cs.this.width))

    common(
        cst.DataclassStruct(Image),
        b"\x01\x0212",
        Image(width=1, height=2, pixels=b"12"),
    )

    # check __getattr__
    c = cst.DataclassStruct(Image)
    assert c.width.name == "width"
    assert c.height.name == "height"
    assert c.width.subcon is cs.Int8ub
    assert c.height.subcon is cs.Int8ub


def test_dataclass_struct_reverse() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    common(
        DataclassStruct(TestContainer, reverse=True),
        b"\x02\x00\x01",
        TestContainer(a=1, b=2),
        3,
    )
    normal = DataclassStruct(TestContainer)
    reverse = DataclassStruct(TestContainer, reverse=True)
    assert str(normal.parse(b"\x00\x01\x02")) == str(reverse.parse(b"\x02\x00\x01"))


def test_dataclass_struct_nested() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        @dataclasses.dataclass
        class InnerDataclass(DataclassMixin):
            b: int = csfield(cs.Byte)
            c: bytes = csfield(cs.Bytes(cs.this._.length))

        length: int = csfield(cs.Byte)
        a: InnerDataclass = csfield(DataclassStruct(InnerDataclass))

    common(
        DataclassStruct(TestContainer),
        b"\x02\x01\xf1\xf2",
        TestContainer(length=2, a=TestContainer.InnerDataclass(b=1, c=b"\xf1\xf2")),
    )


def test_dataclass_struct_default_field() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        pixels: bytes | None = csfield_noinit(
            cs.Default(
                cs.Bytes(cs.this.width * cs.this.height),
                lambda ctx: bytes(ctx.width * ctx.height),
            )
        )

    common(
        DataclassStruct(Image),
        b"\x02\x03\x00\x00\x00\x00\x00\x00",
        setattrs(Image(2, 3), pixels=bytes(6)),
        sample_building=Image(2, 3),
    )


def test_dataclass_struct_computed_field() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        size: int | None = csfield_noinit(
            cs.Computed(lambda ctx: ctx.width * ctx.height)
        )

    common(
        DataclassStruct(Image),
        b"\x02\x03",
        setattrs(Image(2, 3), size=6),
        2,
    )


def test_dataclass_struct_rebuild_field() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        size: int | None = csfield_noinit(
            cs.Rebuild(cs.Int8ub, cs.this.width * cs.this.height)
        )

    common(
        DataclassStruct(Image),
        b"\x02\x03\x06",
        setattrs(Image(2, 3), size=6),
        3,
    )


def test_dataclass_struct_checksum_field() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        checksum: bytes | None = csfield_noinit(
            cs.Checksum(
                cs.Bytes(4),
                lambda data: hashlib.sha256(data).digest()[:4],
                lambda ctx: bytes([ctx.width, ctx.height]),
            )
        )

    common(
        DataclassStruct(Image),
        b"\x02\x03\xee\x90\x40\xf6",
        setattrs(Image(2, 3), checksum=b"\xee\x90\x40\xf6"),
        6,
    )


def test_dataclass_struct_const_field() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        const_field: bytes | None = csfield_noinit(cs.Const(b"\x00"))

    common(
        DataclassStruct(TestContainer),
        bytes(1),
        setattrs(TestContainer(), const_field=b"\x00"),
        1,
    )

    assert (
        raises(
            DataclassStruct(TestContainer).build,
            setattrs(TestContainer(), const_field=b"\x01"),
        )
        == cs.ConstError
    )


def test_dataclass_struct_array_field() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        array_field: t.List[int] = csfield(cs.Array(5, cs.Int8ub))

    common(
        DataclassStruct(TestContainer),
        bytes(5),
        TestContainer(array_field=[0, 0, 0, 0, 0]),
        5,
    )


def test_dataclass_struct_anonymus_fields_1() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        _1: bytes = csfield_const(cs.Bytes(1), b"\x00")
        _2: None = csfield_noinit(cs.Padding(1))
        _3: None = csfield_noinit(cs.Pass)
        _4: None = csfield_noinit(cs.Terminated)

    common(
        DataclassStruct(TestContainer),
        b"\x00\x00",
        setattrs(TestContainer(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_dataclass_struct_anonymus_fields_2() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        _1: int | None = csfield_noinit(cs.Computed(7))
        _2: bytes = csfield_const(cs.Bytes(4), b"JPEG")
        _3: None = csfield_noinit(cs.Pass)
        _4: None = csfield_noinit(cs.Terminated)

    d = DataclassStruct(TestContainer)
    assert d.build(TestContainer()) == d.build(TestContainer())


def test_dataclass_struct_overloaded_method() -> None:
    # Test dot access to some names that are not accessable via dot
    # in the original 'cs.Container'.
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        clear: int = csfield(cs.Int8ul)
        copy: int = csfield(cs.Int8ul)
        fromkeys: int = csfield(cs.Int8ul)
        get: int = csfield(cs.Int8ul)
        items: int = csfield(cs.Int8ul)
        keys: int = csfield(cs.Int8ul)
        move_to_end: int = csfield(cs.Int8ul)
        pop: int = csfield(cs.Int8ul)
        popitem: int = csfield(cs.Int8ul)
        search: int = csfield(cs.Int8ul)
        search_all: int = csfield(cs.Int8ul)
        setdefault: int = csfield(cs.Int8ul)
        update: int = csfield(cs.Int8ul)
        values: int = csfield(cs.Int8ul)

    d = DataclassStruct(TestContainer)
    obj = d.parse(
        d.build(
            TestContainer(
                clear=1,
                copy=2,
                fromkeys=3,
                get=4,
                items=5,
                keys=6,
                move_to_end=7,
                pop=8,
                popitem=9,
                search=10,
                search_all=11,
                setdefault=12,
                update=13,
                values=14,
            )
        )
    )
    assert obj.clear == 1
    assert obj.copy == 2
    assert obj.fromkeys == 3
    assert obj.get == 4
    assert obj.items == 5
    assert obj.keys == 6
    assert obj.move_to_end == 7
    assert obj.pop == 8
    assert obj.popitem == 9
    assert obj.search == 10
    assert obj.search_all == 11
    assert obj.setdefault == 12
    assert obj.update == 13
    assert obj.values == 14


def test_dataclass_struct_no_dataclass() -> None:
    class TestContainer(DataclassMixin):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    assert raises(lambda: DataclassStruct(TestContainer)) is TypeError


def test_dataclass_struct_no_DataclassMixin() -> None:
    @dataclasses.dataclass
    class TestContainer:
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    cls = t.cast(t.Type[DataclassMixin], TestContainer)
    assert raises(lambda: DataclassStruct(cls)) is TypeError


def test_dataclass_struct_wrong_container() -> None:
    @dataclasses.dataclass
    class TestContainer1(DataclassMixin):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    @dataclasses.dataclass
    class TestContainer2(DataclassMixin):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    assert (
        raises(DataclassStruct(TestContainer1).build, TestContainer2(a=1, b=2))
        is TypeError
    )


def test_dataclass_struct_doc() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        a: int = csfield(cs.Int16ub, "This is the documentation of a")
        b: int = csfield(
            cs.Int8ub, doc="This is the documentation of b\nwhich is multiline"
        )
        c: int = csfield(
            cs.Int8ub,
            """
            This is the documentation of c
            which is also multiline
            """,
        )

    format = DataclassStruct(TestContainer)
    common(format, b"\x00\x01\x02\x03", TestContainer(a=1, b=2, c=3), 4)

    assert format.subcon.a.docs == "This is the documentation of a"
    assert format.subcon.b.docs == "This is the documentation of b\nwhich is multiline"
    assert (
        format.subcon.c.docs
        == "This is the documentation of c\nwhich is also multiline"
    )


def test_dataclass_bitstruct() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        a: int = csfield(cs.BitsInteger(7))
        b: int = csfield(cs.Bit)
        c: int = csfield(cs.BitsInteger(8))

    print("")

    common(
        DataclassBitStruct(TestContainer),
        b"\xfd\x12",
        TestContainer(a=0x7E, b=1, c=0x12),
        2,
    )

    # check __getattr__
    c = DataclassStruct(TestContainer)
    assert c.a.name == "a"
    assert c.b.name == "b"
    assert c.c.name == "c"
    assert isinstance(c.a.subcon, cs.BitsInteger)
    assert c.b.subcon is cs.Bit
    assert isinstance(c.c.subcon, cs.BitsInteger)


def test_tenum() -> None:
    class TestEnum(cst.EnumBase):
        one = 1
        two = 2
        four = 4
        eight = 8

    d = cst.TEnum(cs.Byte, TestEnum)

    common(d, b"\x01", TestEnum.one, 1)
    common(d, b"\xff", TestEnum(255), 1)
    assert d.parse(b"\x01") == TestEnum.one
    assert d.parse(b"\x01") == 1
    assert int(d.parse(b"\x01")) == 1
    assert d.parse(b"\xff") == TestEnum(255)
    assert d.parse(b"\xff") == 255
    assert int(d.parse(b"\xff")) == 255
    assert raises(d.build, 8) is TypeError


def test_tenum_no_enumbase() -> None:
    class E(enum.Enum):
        a = 1
        b = 2

    cls = t.cast(t.Type[cst.EnumBase], E)
    assert raises(lambda: cst.TEnum(cs.Byte, cls)) is TypeError


def test_tenum_asdict() -> None:
    # see: https://github.com/timrid/construct-typing/issues/21
    class TestEnum(cst.EnumBase):
        one = 1
        two = 2
        four = 4
        eight = 8

    @dataclasses.dataclass
    class SomeDataclass:
        a: TestEnum

    dc = SomeDataclass(TestEnum.one)
    dc_dict = dataclasses.asdict(dc)
    assert dc_dict["a"] == dc.a
    assert dc_dict["a"] is dc.a

    dc = SomeDataclass(TestEnum(5))
    dc_dict = dataclasses.asdict(dc)
    assert dc_dict["a"] == dc.a
    assert dc_dict["a"] is dc.a


def test_tenum_docstring() -> None:
    class TestEnum(cst.EnumBase):
        """
        This is an test enum.
        """

        Value_WithDoc = cst.EnumValue(0, doc="an enum with a documentation")
        Value_WithMultilineDoc = cst.EnumValue(
            1,
            """
            An enum with a multiline documentation...
            ...next line...
            """,
        )
        Value_NoDoc = cst.EnumValue(2)
        Value_NoDoc2 = 3

    assert TestEnum.__doc__ is not None
    assert textwrap.dedent(TestEnum.__doc__) == textwrap.dedent(
        """
        This is an test enum.
        """
    )
    assert TestEnum.Value_WithDoc.__doc__ == "an enum with a documentation"
    assert (
        TestEnum.Value_WithMultilineDoc.__doc__
        == """
            An enum with a multiline documentation...
            ...next line...
            """
    )
    assert TestEnum.Value_NoDoc.__doc__ == ""
    assert TestEnum.Value_NoDoc2.__doc__ == ""
    assert TestEnum(5).__doc__ == "missing value"


def test_dataclass_struct_wrong_enumbase() -> None:
    class E1(cst.EnumBase):
        a = 1
        b = 2

    class E2(cst.EnumBase):
        a = 1
        b = 2

    assert raises(cst.TEnum(cs.Byte, E1).build, E2.a) is TypeError


def test_tenum_in_tstruct() -> None:
    class TestEnum(cst.EnumBase):
        a = 1
        b = 2

    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        a: TestEnum = csfield(cst.TEnum(cs.Int8ub, TestEnum))
        b: int = csfield(cs.Int8ub)

    common(
        DataclassStruct(TestContainer),
        b"\x01\x02",
        TestContainer(a=TestEnum.a, b=2),
        2,
    )

    assert (
        raises(cst.TEnum(cs.Byte, TestEnum).build, TestContainer(a=1, b=2)) is TypeError  # type: ignore
    )


def test_tenum_flags() -> None:
    class TestEnum(cst.FlagsEnumBase):
        one = 1
        two = 2
        four = 4
        eight = 8

    d = cst.TFlagsEnum(cs.Byte, TestEnum)
    common(d, b"\x03", TestEnum.one | TestEnum.two, 1)
    assert d.build(TestEnum(0)) == b"\x00"
    assert d.build(TestEnum.one | TestEnum.two) == b"\x03"
    assert d.build(TestEnum(8)) == b"\x08"
    assert d.build(TestEnum(1 | 2)) == b"\x03"
    assert d.build(TestEnum(255)) == b"\xff"
    assert d.build(TestEnum.eight) == b"\x08"
    assert raises(d.build, 2) is TypeError


def test_tenum_flags_asdict() -> None:
    class TestEnum(cst.FlagsEnumBase):
        one = 1
        two = 2
        four = 4
        eight = 8

    @dataclasses.dataclass
    class SomeDataclass:
        a: TestEnum

    dc = SomeDataclass(TestEnum.one)
    dc_dict = dataclasses.asdict(dc)
    assert dc_dict["a"] == dc.a
    assert dc_dict["a"] is dc.a

    dc = SomeDataclass(TestEnum(5))
    dc_dict = dataclasses.asdict(dc)
    assert dc_dict["a"] == dc.a
    assert dc_dict["a"] is dc.a


def test_tenum_flags_docstring() -> None:
    class TestEnum(cst.FlagsEnumBase):
        """
        This is an test flags enum.
        """

        Value_WithDoc = cst.EnumValue(0, doc="an enum with a documentation")
        Value_WithMultilineDoc = cst.EnumValue(
            1,
            """
            An enum with a multiline documentation...
            ...next line...
            """,
        )
        Value_NoDoc = cst.EnumValue(2)
        Value_NoDoc2 = 4

    assert TestEnum.__doc__ is not None
    assert textwrap.dedent(TestEnum.__doc__) == textwrap.dedent(
        """
        This is an test flags enum.
        """
    )
    assert TestEnum.Value_WithDoc.__doc__ == "an enum with a documentation"
    assert (
        TestEnum.Value_WithMultilineDoc.__doc__
        == """
            An enum with a multiline documentation...
            ...next line...
            """
    )
    assert TestEnum.Value_NoDoc.__doc__ == ""
    assert TestEnum.Value_NoDoc2.__doc__ == ""
    assert TestEnum(8).__doc__ == "missing value"


def test_construct_subscriptable() -> None:
    """Construct has to be subscriptable at runtime."""

    class MyByte(cst.Construct[int, int]):
        def _parse(
            self, stream: t.IO[bytes], context: cst.Context, path: cst.PathType
        ) -> int:
            return cs.stream_read(stream, 1, path)[0]

        def _build(
            self,
            obj: int,
            stream: t.IO[bytes],
            context: cst.Context,
            path: cst.PathType,
        ) -> int:
            cs.stream_write(stream, bytes([obj]), 1, path)
            return obj

        def _sizeof(self, context: cst.Context, path: cst.PathType) -> int:
            return 1

    fmt = MyByte()
    assert fmt.parse(b"\x05") == 5
    assert fmt.build(5) == b"\x05"
    assert fmt.sizeof() == 1


def test_subconstruct_subscriptable() -> None:
    """Subconstruct has to be subscriptable at runtime."""

    class MyPaddedBytes(cst.Subconstruct[bytes, bytes, bytes, bytes]):
        def __init__(self) -> None:
            pass

    fmt = MyPaddedBytes()
    assert fmt is not None


def test_adapter_subscriptable() -> None:
    """Adapter has to be subscriptable at runtime."""

    class IpAddressAdapter(cst.Adapter[cst.ListContainer[int], list[int], str, str]):
        def _encode(
            self, obj: str, context: cst.Context, path: cst.PathType
        ) -> list[int]:
            return list(map(int, obj.split(".")))

        def _decode(
            self, obj: list[int], context: cst.Context, path: cst.PathType
        ) -> str:
            return "{0}.{1}.{2}.{3}".format(*obj)

    IpAddress2 = IpAddressAdapter(cs.Byte[4])

    assert IpAddress2.parse(b"\x7f\x80\x81\x82") == "127.128.129.130"
    assert IpAddress2.build("127.1.2.3") == b"\x7f\x01\x02\x03"
    assert IpAddress2.sizeof() == 4


def test_symmetric_adapter_subscriptable() -> None:
    """SymmetricAdapter has to be subscriptable at runtime."""

    T = t.TypeVar("T")

    class ReversedList(cst.SymmetricAdapter[list[T], list[T], list[T], list[T]]):
        def _decode(
            self, obj: list[T], context: cst.Context, path: cst.PathType
        ) -> list[T]:
            return list(reversed(obj))

    assert ReversedList(cs.Array(4, cs.Byte)).build([1, 2, 3, 4]) == b"\x04\x03\x02\x01"
    assert ReversedList(cs.Array(4, cs.Byte)).parse(b"\x01\x02\x03\x04") == [4, 3, 2, 1]


def test_validator_subscriptable() -> None:
    """Validator has to be subscriptable at runtime."""

    class OneOf(cst.Validator[int, int]):
        def _validate(
            self, obj: int, context: cst.Context, path: cst.PathType
        ) -> bool:
            return obj in (1, 2, 3)

    fmt = OneOf(cs.Byte)

    assert fmt.parse(b"\x01") == 1
    assert fmt.build(2) == b"\x02"
    assert raises(fmt.build, 4) is cs.ValidationError
    assert raises(fmt.parse, b"\x04") is cs.ValidationError


def test_tunnel_subscriptable() -> None:
    """Tunnel has to be subscriptable at runtime."""

    class ROT1(cst.Tunnel[bytes, bytes]):
        def _decode(
            self, data: bytes, context: cst.Context, path: cst.PathType
        ) -> bytes:
            return bytes((b - 1) % 256 for b in data)

        def _encode(
            self, data: bytes, context: cst.Context, path: cst.PathType
        ) -> bytes:
            return bytes((b + 1) % 256 for b in data)

    fmt = ROT1(cs.GreedyBytes)

    assert fmt.parse(b"\x02\x03\x04") == b"\x01\x02\x03"
    assert fmt.build(b"\x01\x02\x03") == b"\x02\x03\x04"
