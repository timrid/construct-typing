# -*- coding: utf-8 -*-

import enum
import dataclasses
import typing as t
from .declarativeunittest import common, raises
import construct as cs
import construct_typed as cst


def test_tstruct_1() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        a: int = cst.StructField(cs.Int16ub)
        b: int = cst.StructField(cs.Int8ub)

    common(cst.TStruct(TestDataclass), b"\x00\x01\x02", TestDataclass(a=1, b=2), 3)


def test_tstruct_swapped() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        a: int = cst.StructField(cs.Int16ub)
        b: int = cst.StructField(cs.Int8ub)

    common(
        cst.TStruct(TestDataclass, swapped=True),
        b"\x02\x00\x01",
        TestDataclass(a=1, b=2),
        3,
    )
    normal = cst.TStruct(TestDataclass)
    swapped = cst.TStruct(TestDataclass, swapped=True)
    assert str(normal.parse(b"\x00\x01\x02")) == str(swapped.parse(b"\x02\x00\x01"))


def test_tstruct_nested() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        @dataclasses.dataclass
        class InnerDataclass:
            b: int = cst.StructField(cs.Byte)

        a: InnerDataclass = cst.StructField(cst.TStruct(InnerDataclass))

    common(
        cst.TStruct(TestDataclass),
        b"\x01",
        TestDataclass(a=TestDataclass.InnerDataclass(b=1)),
        1,
    )


def test_tstruct_anonymus_fields_1() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        _1: t.Optional[bytes] = cst.StructField(cs.Const(b"\x00"))
        _2: None = cst.StructField(cs.Padding(1))
        _3: None = cst.StructField(cs.Pass)
        _4: None = cst.StructField(cs.Terminated)

    common(
        cst.TStruct(TestDataclass),
        bytes(2),
        TestDataclass(),
        cs.SizeofError,
    )


def test_tstruct_anonymus_fields_2() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        _1: int = cst.StructField(cs.Computed(7))
        _2: t.Optional[bytes] = cst.StructField(cs.Const(b"JPEG"))
        _3: None = cst.StructField(cs.Pass)
        _4: None = cst.StructField(cs.Terminated)

    d = cst.TStruct(TestDataclass)
    assert d.build(TestDataclass()) == d.build(TestDataclass())


def test_tstruct_missing_dataclass() -> None:
    class TestDataclass:
        a: int = cst.StructField(cs.Int16ub)
        b: int = cst.StructField(cs.Int8ub)

    assert raises(cst.TStruct, TestDataclass) == TypeError


def test_tbitstruct() -> None:
    assert False


def test_tenum() -> None:
    class E(enum.IntEnum):
        a = 1
        b = 2

    common(cst.TEnum(cs.Byte, E), b"\x01", E.a, 1)
    common(cst.TEnum(cs.Byte, E), b"\x01", 1, 1)
    format = cst.TEnum(cs.Byte, E)
    obj = format.parse(b"\x01")
    assert obj == E.a
    assert obj == 1
    data = format.build("a")
    assert data == b"\x01"

    common(cst.TEnum(cs.Byte, E), b"\x02", E.b, 1)
    common(cst.TEnum(cs.Byte, E), b"\x02", 2, 1)
    format = cst.TEnum(cs.Byte, E)
    obj = format.parse(b"\x02")
    assert obj == E.b
    assert obj == 2
    data = format.build("b")
    assert data == b"\x02"


def test_tenum_missing_value() -> None:
    class E(enum.IntEnum):
        a = 1
        b = 2

    common(cst.TEnum(cs.Byte, E), b"\x03", 3, 1)
    format = cst.TEnum(cs.Byte, E)
    obj = format.parse(b"\x03")
    assert int(obj) == 3
    data = format.build(3)
    assert data == b"\x03"


def test_tenum_no_int_enum() -> None:
    class E(enum.Enum):
        a = 1
        b = 2

    assert raises(cst.TEnum, cs.Byte, E) == TypeError


def test_tenum_in_tstruct() -> None:
    class TestEnum(enum.IntEnum):
        a = 1
        b = 2

    @dataclasses.dataclass
    class TestDataclass:
        a: TestEnum = cst.StructField(cst.TEnum(cs.Int8ub, TestEnum))
        b: int = cst.StructField(cs.Int8ub)

    common(
        cst.TStruct(TestDataclass),
        b"\x00\x01\x02",
        TestDataclass(a=TestEnum.a, b=TestEnum.b),
        3,
    )
