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
    class ConstDefaultTest(DataclassStruct):
        const_bytes: bytes = csfield(cs.Bytes(3), const=b"BMP")
        const_int: int = csfield(cs.Int8ub, const=5)
        default_int: int = csfield(cs.Int8ub, default=26)
        default_lambda: t.Optional[bytes] = csfield(
            cs.Default(cs.Bytes(cs.this.const_int), lambda ctx: bytes(ctx.const_int))
        )

    a = ConstDefaultTest()
    assert a.const_bytes == b"BMP"
    assert a.const_int == 5
    assert a.default_int == 26
    assert a.default_lambda == None
    a = ConstDefaultTest(default_int=1)
    assert a.default_int == 1

    format = ConstDefaultTest.__constr__()
    assert isinstance(format.const_bytes.subcon, cs.Const)
    assert isinstance(format.const_int.subcon, cs.Const)
    assert isinstance(format.default_int.subcon, cs.Default)
    assert isinstance(format.default_lambda.subcon, cs.Default)


def test_dataclass_access() -> None:
    class TestTContainer(DataclassStruct):
        a: int = csfield(cs.Byte, const=1)
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
    assert raises(lambda: TestTContainer(a=0, b=1)) == TypeError  # type: ignore


def test_dataclass_str_repr() -> None:
    class Image(DataclassStruct):
        signature: bytes = csfield(cs.Bytes(3), const=b"BMP")
        width: int = csfield(cs.Int8ub)
        height: int = csfield(cs.Int8ub)

    format = constr(Image)
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
    c = Image.__constr__()
    assert c.width.name == "width"
    assert c.height.name == "height"
    assert c.width.subcon is cs.Int8ub
    assert c.height.subcon is cs.Int8ub


def test_dataclass_struct_reverse() -> None:
    class TestContainer(DataclassStruct, reverse_fields=True):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    common(
        constr(TestContainer),
        b"\x02\x00\x01",
        TestContainer(a=1, b=2),
        3,
    )


def test_dataclass_struct_nested() -> None:
    class TestContainer(DataclassStruct):
        class InnerDataclass(DataclassStruct):
            b: int = csfield(cs.Byte)
            c: bytes = csfield(cs.Bytes(cs.this._.length))

        length: int = csfield(cs.Byte)
        a: InnerDataclass = csfield(constr(InnerDataclass))

    common(
        constr(TestContainer),
        b"\x02\x01\xF1\xF2",
        TestContainer(length=2, a=TestContainer.InnerDataclass(b=1, c=b"\xF1\xF2")),
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
    class TestContainer(DataclassStruct):
        const_field: t.Optional[bytes] = csfield(cs.Const(b"\x00"))

    common(
        constr(TestContainer),
        bytes(1),
        setattrs(TestContainer(), const_field=b"\x00"),
        1,
    )

    assert (
        raises(
            constr(TestContainer).build,
            setattrs(TestContainer(), const_field=b"\x01"),
        )
        == cs.ConstError
    )


def test_dataclass_struct_array_field() -> None:
    class TestContainer(DataclassStruct):
        array_field: t.List[int] = csfield(cs.Array(5, cs.Int8ub))

    common(
        constr(TestContainer),
        bytes(5),
        TestContainer(array_field=[0, 0, 0, 0, 0]),
        5,
    )


def test_dataclass_struct_anonymus_fields_1() -> None:
    class TestContainer(DataclassStruct):
        _1: t.Optional[bytes] = csfield(cs.Const(b"\x00"))
        _2: None = csfield(cs.Padding(1))
        _3: None = csfield(cs.Pass)
        _4: None = csfield(cs.Terminated)

    common(
        constr(TestContainer),
        bytes(2),
        setattrs(TestContainer(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_dataclass_struct_anonymus_fields_2() -> None:
    class TestContainer(DataclassStruct):
        _1: t.Optional[int] = csfield(cs.Computed(7))
        _2: t.Optional[bytes] = csfield(cs.Const(b"JPEG"))
        _3: None = csfield(cs.Pass)
        _4: None = csfield(cs.Terminated)

    d = constr(TestContainer)
    assert d.build(TestContainer()) == d.build(TestContainer())


def test_dataclass_struct_overloaded_method() -> None:
    # Test dot access to some names that are not accessable via dot
    # in the original 'cs.Container'.
    class TestContainer(DataclassStruct):
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

    d = constr(TestContainer)
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


def test_dataclass_struct_wrong_container() -> None:
    class TestContainer1(DataclassStruct):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    class TestContainer2(DataclassStruct):
        a: int = csfield(cs.Int16ub)
        b: int = csfield(cs.Int8ub)

    assert raises(constr(TestContainer1).build, TestContainer2(a=1, b=2)) == TypeError


def test_dataclass_struct_doc() -> None:
    class TestContainer(DataclassStruct):
        a: int = csfield(cs.Int16ub, doc="This is the documentation of a")
        b: int = csfield(
            cs.Int8ub, doc="This is the documentation of b\nwhich is multiline"
        )
        c: int = csfield(
            cs.Int8ub,
            doc="""
            This is the documentation of c
            which is also multiline
            """,
        )

    format = TestContainer.__constr__()
    common(format, b"\x00\x01\x02\x03", TestContainer(a=1, b=2, c=3), 4)

    assert format.subcon.a.docs == "This is the documentation of a"
    assert format.subcon.b.docs == "This is the documentation of b\nwhich is multiline"
    assert (
        format.subcon.c.docs
        == "This is the documentation of c\nwhich is also multiline"
    )


def test_dataclass_bitstruct() -> None:
    class TestContainer(DataclassBitStruct):
        a: int = csfield(cs.BitsInteger(7))
        b: int = csfield(cs.Bit)
        c: int = csfield(cs.BitsInteger(8))

    common(
        constr(TestContainer),
        b"\xFD\x12",
        TestContainer(a=0x7E, b=1, c=0x12),
        2,
    )

    # check __getattr__
    c = TestContainer.__constr__()
    assert c.subcon.a.name == "a"
    assert c.subcon.b.name == "b"
    assert c.subcon.c.name == "c"
    assert isinstance(c.subcon.a.subcon, cs.BitsInteger)
    assert c.subcon.b.subcon is cs.Bit
    assert isinstance(c.subcon.c.subcon, cs.BitsInteger)


def test_tenum() -> None:
    class TestEnum(TEnum, subcon=cs.Byte):
        one = 1
        two = 2
        four = 4
        eight = 8

    d = constr(TestEnum)

    common(d, b"\x01", TestEnum.one, 1)
    common(d, b"\xff", TestEnum(255), 1)
    assert d.parse(b"\x01") == TestEnum.one
    assert d.parse(b"\x01") == 1
    assert int(d.parse(b"\x01")) == 1
    assert d.parse(b"\xff") == TestEnum(255)
    assert d.parse(b"\xff") == 255
    assert int(d.parse(b"\xff")) == 255
    assert raises(d.build, 8) == TypeError


def test_tenum_in_dataclass_struct() -> None:
    class TestEnum(TEnum, subcon=cs.Int8ub):
        a = 1
        b = 2

    class TestContainer(DataclassStruct):
        a: TestEnum = csfield(constr(TestEnum))
        b: int = csfield(cs.Int8ub)

    common(
        constr(TestContainer),
        b"\x01\x02",
        TestContainer(a=TestEnum.a, b=2),
        2,
    )

    assert (
        raises(constr(TestEnum).build, TestContainer(a=1, b=2)) == TypeError  # type: ignore
    )


def test_tflags() -> None:
    class TestFlags(TFlags, subcon=cs.Byte):
        one = 1
        two = 2
        four = 4
        eight = 8

    d = constr(TestFlags)
    common(d, b"\x03", TestFlags.one | TestFlags.two, 1)
    assert d.build(TestFlags(0)) == b"\x00"
    assert d.build(TestFlags.one | TestFlags.two) == b"\x03"
    assert d.build(TestFlags(8)) == b"\x08"
    assert d.build(TestFlags(1 | 2)) == b"\x03"
    assert d.build(TestFlags(255)) == b"\xff"
    assert d.build(TestFlags.eight) == b"\x08"
    assert raises(d.build, 2) == TypeError
