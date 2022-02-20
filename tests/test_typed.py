# -*- coding: utf-8 -*-
# pyright: strict
import typing as t

import construct as cs
from construct_typed import (
    DataclassBitStruct,
    DataclassStruct,
    csfield,
    constr,
    TEnum,
    TFlags,
)

from tests.declarativeunittest import common, raises, setattrs


def test_dataclass_const_default() -> None:
    class TestDataclass(DataclassStruct):
        const_bytes: bytes = csfield(cs.Bytes(3), const=b"BMP")
        const_int: int = csfield(cs.Int8ub, const=5)
        default_int: int = csfield(cs.Int8ub, default=26)
        default_lambda: t.Optional[bytes] = csfield(
            cs.Default(cs.Bytes(cs.this.const_int), lambda ctx: bytes(ctx.const_int))
        )

    obj = TestDataclass()
    assert obj.const_bytes == b"BMP"
    assert obj.const_int == 5
    assert obj.default_int == 26
    assert obj.default_lambda == None
    obj = TestDataclass(default_int=1)
    assert obj.default_int == 1

    fmt = TestDataclass.__constr__()
    assert isinstance(fmt.const_bytes.subcon, cs.Const)
    assert isinstance(fmt.const_int.subcon, cs.Const)
    assert isinstance(fmt.default_int.subcon, cs.Default)
    assert isinstance(fmt.default_lambda.subcon, cs.Default)


def test_dataclass_access() -> None:
    class TestDataclass(DataclassStruct):
        a: int = csfield(cs.Byte, const=1)
        b: int = csfield(cs.Int8ub)

    obj = TestDataclass(b=2)

    assert obj.a == 1
    assert obj["a"] == 1
    assert obj.b == 2
    assert obj["b"] == 2

    obj.a = 5
    assert obj.a == 5
    assert obj["a"] == 5
    obj["a"] = 6
    assert obj.a == 6
    assert obj["a"] == 6

    # wrong creation
    assert raises(lambda: TestDataclass(a=0, b=1)) == TypeError  # type: ignore


def test_dataclass_str_repr() -> None:
    class Image(DataclassStruct):
        signature: bytes = csfield(cs.Bytes(3), const=b"BMP")
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)

    fmt = constr(Image)
    obj = Image(width=3, height=2)
    assert (
        str(obj)
        == "Image: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )
    obj = fmt.parse(fmt.build(obj))
    assert (
        str(obj)
        == "Image: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )


def test_dataclass_struct() -> None:
    class Image(DataclassStruct):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        pixels: bytes = csfield(cs.Bytes(cs.this.height * cs.this.width))

    common(
        constr(Image),
        b"\x01\x0212",
        Image(width=1, height=2, pixels=b"12"),
    )

    # check __getattr__
    fmt = Image.__constr__()
    assert fmt.width.name == "width"
    assert fmt.height.name == "height"
    assert fmt.width.subcon is cs.Int8ub
    assert fmt.height.subcon is cs.Int8ub


def test_dataclass_struct_reverse() -> None:
    class TestDataclass(DataclassStruct, reverse_fields=True):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    common(
        constr(TestDataclass),
        b"\x02\x00\x01",
        TestDataclass(a=1, b=2),
        3,
    )


def test_dataclass_struct_nested() -> None:
    class TestDataclass(DataclassStruct):
        class InnerDataclass(DataclassStruct):
            b: int = csfield(cs.Byte)
            c: bytes = csfield(cs.Bytes(cs.this._.length))

        length: int = csfield(cs.Byte)
        a: InnerDataclass = csfield(constr(InnerDataclass))

    common(
        constr(TestDataclass),
        b"\x02\x01\xF1\xF2",
        TestDataclass(length=2, a=TestDataclass.InnerDataclass(b=1, c=b"\xF1\xF2")),
    )


def test_dataclass_struct_default_field() -> None:
    class Image(DataclassStruct):
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)
        pixels: t.Optional[bytes] = csfield(
            cs.Default(
                cs.Bytes(cs.this.width * cs.this.height),
                lambda ctx: bytes(ctx.width * ctx.height),
            )
        )

    common(
        constr(Image),
        b"\x02\x03\x00\x00\x00\x00\x00\x00",
        setattrs(Image(width=2, height=3), pixels=bytes(6)),
        sample_building=Image(width=2, height=3),
    )


def test_dataclass_struct_const_field() -> None:
    class TestDataclass(DataclassStruct):
        const_field: t.Optional[bytes] = csfield(cs.Const(b"\x00"))

    common(
        constr(TestDataclass),
        bytes(1),
        setattrs(TestDataclass(), const_field=b"\x00"),
        1,
    )

    assert (
        raises(
            constr(TestDataclass).build,
            setattrs(TestDataclass(), const_field=b"\x01"),
        )
        == cs.ConstError
    )


def test_dataclass_struct_array_field() -> None:
    class TestDataclass(DataclassStruct):
        array_field: t.List[int] = csfield(cs.Array(5, cs.Int8ub))

    common(
        constr(TestDataclass),
        bytes(5),
        TestDataclass(array_field=[0, 0, 0, 0, 0]),
        5,
    )


def test_dataclass_struct_anonymus_fields_1() -> None:
    class TestDataclass(DataclassStruct):
        _1: t.Optional[bytes] = csfield(cs.Const(b"\x00"))
        _2: None = csfield(cs.Padding(1))
        _3: None = csfield(cs.Pass)
        _4: None = csfield(cs.Terminated)

    common(
        constr(TestDataclass),
        bytes(2),
        setattrs(TestDataclass(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_dataclass_struct_anonymus_fields_2() -> None:
    class TestDataclass(DataclassStruct):
        _1: t.Optional[int] = csfield(cs.Computed(7))
        _2: t.Optional[bytes] = csfield(cs.Const(b"JPEG"))
        _3: None = csfield(cs.Pass)
        _4: None = csfield(cs.Terminated)

    fmt = constr(TestDataclass)
    assert fmt.build(TestDataclass()) == fmt.build(TestDataclass())


def test_dataclass_struct_overloaded_method() -> None:
    # Test dot access to some names that are not accessable via dot
    # in the original 'cs.Container'.
    class TestDataclass(DataclassStruct):
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

    fmt = constr(TestDataclass)
    obj = fmt.parse(
        fmt.build(
            TestDataclass(
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


def test_dataclass_struct_wrong_container() -> None:
    class TestContainer1(DataclassStruct):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    class TestContainer2(DataclassStruct):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    assert raises(constr(TestContainer1).build, TestContainer2(a=1, b=2)) == TypeError


def test_dataclass_struct_doc() -> None:
    class TestDataclass1(DataclassStruct):
        """
        Documentation of TestDataclass1
        """

        a: int = csfield(cs.Int16ub, doc="This is the doc of a")
        b: int = csfield(cs.Int8ub, doc="This is the doc of b\nwhich is multiline")
        c: int = csfield(
            cs.Int8ub,
            doc="""
            This is the doc of c
            which is also multiline
            """,
        )

    fmt1 = TestDataclass1.__constr__()
    common(fmt1, b"\x00\x01\x02\x03", TestDataclass1(a=1, b=2, c=3), 4)

    assert fmt1.docs == "Documentation of TestDataclass1"
    assert fmt1.subcon.a.docs == "This is the doc of a"
    assert fmt1.subcon.b.docs == "This is the doc of b\nwhich is multiline"
    assert fmt1.subcon.c.docs == "This is the doc of c\nwhich is also multiline"

    class TestDataclass2(DataclassStruct):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)
        c: int = csfield(cs.Int8ub)

    fmt2 = TestDataclass2.__constr__()
    assert fmt2.docs == ""
    assert fmt2.subcon.a.docs == ""
    assert fmt2.subcon.b.docs == ""
    assert fmt2.subcon.c.docs == ""


def test_dataclass_bitwise() -> None:
    class TestDataclass(DataclassStruct, constr=lambda cls: cs.Bitwise(cls)):
        a: int = csfield(cs.BitsInteger(7))
        b: int = csfield(cs.Bit)
        c: int = csfield(cs.BitsInteger(8))

    common(
        constr(TestDataclass),
        b"\xFD\x12",
        TestDataclass(a=0x7E, b=1, c=0x12),
        2,
    )

    # check __getattr__
    fmt = TestDataclass.__constr__()
    assert fmt.subcon.a.name == "a"
    assert fmt.subcon.b.name == "b"
    assert fmt.subcon.c.name == "c"
    assert isinstance(fmt.subcon.a.subcon, cs.BitsInteger)
    assert fmt.subcon.b.subcon is cs.Bit
    assert isinstance(fmt.subcon.c.subcon, cs.BitsInteger)


def test_dataclass_bitstruct() -> None:
    class TestDataclass(DataclassBitStruct):
        a: int = csfield(cs.BitsInteger(7))
        b: int = csfield(cs.Bit)
        c: int = csfield(cs.BitsInteger(8))

    common(
        constr(TestDataclass),
        b"\xFD\x12",
        TestDataclass(a=0x7E, b=1, c=0x12),
        2,
    )

    # check __getattr__
    fmt = TestDataclass.__constr__()
    assert fmt.subcon.a.name == "a"
    assert fmt.subcon.b.name == "b"
    assert fmt.subcon.c.name == "c"
    assert isinstance(fmt.subcon.a.subcon, cs.BitsInteger)
    assert fmt.subcon.b.subcon is cs.Bit
    assert isinstance(fmt.subcon.c.subcon, cs.BitsInteger)


def test_tenum() -> None:
    class TestEnum(TEnum, subcon=cs.Byte):
        one = 1
        two = 2
        four = 4
        eight = 8

    fmt = constr(TestEnum)

    common(fmt, b"\x01", TestEnum.one, 1)
    common(fmt, b"\xff", TestEnum(255), 1)
    assert fmt.parse(b"\x01") == TestEnum.one
    assert fmt.parse(b"\x01") == 1
    assert int(fmt.parse(b"\x01")) == 1
    assert fmt.parse(b"\xff") == TestEnum(255)
    assert fmt.parse(b"\xff") == 255
    assert int(fmt.parse(b"\xff")) == 255
    assert raises(fmt.build, 8) == TypeError


def test_tenum_doc() -> None:
    class TestEnum1(TEnum, subcon=cs.Byte):
        """
        TestEnum documentation
        """

        one = 1

    d1 = constr(TestEnum1)
    assert d1.docs == "TestEnum documentation"

    class TestEnum2(TEnum, subcon=cs.Byte):
        two = 2

    d2 = constr(TestEnum2)
    assert d2.docs == ""


def test_tenum_in_dataclass_struct() -> None:
    class TestEnum(TEnum, subcon=cs.Int8ub):
        a = 1
        b = 2

    class TestDataclass(DataclassStruct):
        a: TestEnum = csfield(constr(TestEnum))
        b: int = csfield(cs.Int8ub)

    common(
        constr(TestDataclass),
        b"\x01\x02",
        TestDataclass(a=TestEnum.a, b=2),
        2,
    )

    assert (
        raises(constr(TestEnum).build, TestDataclass(a=1, b=2)) == TypeError  # type: ignore
    )


def test_tflags() -> None:
    class TestFlags(TFlags, subcon=cs.Byte):
        one = 1
        two = 2
        four = 4
        eight = 8

    fmt = constr(TestFlags)
    common(fmt, b"\x03", TestFlags.one | TestFlags.two, 1)
    assert fmt.build(TestFlags(0)) == b"\x00"
    assert fmt.build(TestFlags.one | TestFlags.two) == b"\x03"
    assert fmt.build(TestFlags(8)) == b"\x08"
    assert fmt.build(TestFlags(1 | 2)) == b"\x03"
    assert fmt.build(TestFlags(255)) == b"\xff"
    assert fmt.build(TestFlags.eight) == b"\x08"
    assert raises(fmt.build, 2) == TypeError
