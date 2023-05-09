# -*- coding: utf-8 -*-
# pyright: strict
import dataclasses
import enum
import typing as t

import construct as cs
import construct_typed as cst
from construct_typed import DataclassBitStruct, DataclassMixin, DataclassStruct, csfield

from .declarativeunittest import common, raises, setattrs


def test_dataclass_const_default() -> None:
    @dataclasses.dataclass
    class ConstDefaultTest(DataclassMixin):
        const_bytes: bytes = csfield(cs.Const(b"BMP"))
        const_int: int = csfield(cs.Const(5, cs.Int8ub))
        default_int: int = csfield(cs.Default(cs.Int8ub, 28))
        default_lambda: bytes = csfield(
            cs.Default(cs.Bytes(cs.this.const_int), lambda ctx: bytes(ctx.const_int))
        )

    a = ConstDefaultTest()
    assert a.const_bytes == b"BMP"
    assert a.const_int == 5
    assert a.default_int == 28
    assert a.default_lambda == None


def test_dataclass_access() -> None:
    @dataclasses.dataclass
    class TestTContainer(DataclassMixin):
        a: t.Optional[int] = csfield(cs.Const(1, cs.Byte))
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
    assert raises(lambda: TestTContainer(a=0, b=1)) == TypeError


def test_dataclass_str_repr() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        signature: t.Optional[bytes] = csfield(cs.Const(b"BMP"))
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
        b"\x02\x01\xF1\xF2",
        TestContainer(length=2, a=TestContainer.InnerDataclass(b=1, c=b"\xF1\xF2")),
    )


def test_dataclass_struct_default_field() -> None:
    @dataclasses.dataclass
    class Image(DataclassMixin):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        pixels: t.Optional[bytes] = csfield(
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


def test_dataclass_struct_const_field() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        const_field: t.Optional[bytes] = csfield(cs.Const(b"\x00"))

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
        _1: t.Optional[bytes] = csfield(cs.Const(b"\x00"))
        _2: None = csfield(cs.Padding(1))
        _3: None = csfield(cs.Pass)
        _4: None = csfield(cs.Terminated)

    common(
        DataclassStruct(TestContainer),
        bytes(2),
        setattrs(TestContainer(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_dataclass_struct_anonymus_fields_2() -> None:
    @dataclasses.dataclass
    class TestContainer(DataclassMixin):
        _1: int = csfield(cs.Computed(7))
        _2: t.Optional[bytes] = csfield(cs.Const(b"JPEG"))
        _3: None = csfield(cs.Pass)
        _4: None = csfield(cs.Terminated)

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

    assert raises(lambda: DataclassStruct(TestContainer)) == TypeError


def test_dataclass_struct_no_DataclassMixin() -> None:
    @dataclasses.dataclass
    class TestContainer:
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    cls = t.cast(t.Type[DataclassMixin], TestContainer)
    assert raises(lambda: DataclassStruct(cls)) == TypeError


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
        == TypeError
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
        b"\xFD\x12",
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
    assert raises(d.build, 8) == TypeError


def test_tenum_no_enumbase() -> None:
    class E(enum.Enum):
        a = 1
        b = 2

    cls = t.cast(t.Type[cst.EnumBase], E)
    assert raises(lambda: cst.TEnum(cs.Byte, cls)) == TypeError


def test_tenum_asdict():
    # see: https://github.com/timrid/construct-typing/issues/21
    import construct_typed as cst
    import dataclasses

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

    assert (
        TestEnum.__doc__
        == """
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

    assert raises(cst.TEnum(cs.Byte, E1).build, E2.a) == TypeError


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
        raises(cst.TEnum(cs.Byte, TestEnum).build, TestContainer(a=1, b=2)) == TypeError  # type: ignore
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
    assert raises(d.build, 2) == TypeError


def test_tenum_flags_asdict():
    import construct_typed as cst
    import dataclasses

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

    assert (
        TestEnum.__doc__
        == """
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
