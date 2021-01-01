# -*- coding: utf-8 -*-

import enum
import dataclasses
import typing as t
from .declarativeunittest import common, raises, setattrs
import construct as cs
import construct_typed as cst


def test_tstruct() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    common(cst.TStruct(TestDataclass), b"\x00\x01\x02", TestDataclass(a=1, b=2), 3)


def test_tstruct_swapped() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

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
            b: int = cst.TStructField(cs.Byte)

        a: InnerDataclass = cst.TStructField(cst.TStruct(InnerDataclass))

    common(
        cst.TStruct(TestDataclass),
        b"\x01",
        TestDataclass(a=TestDataclass.InnerDataclass(b=1)),
        1,
    )


def test_tstruct_default_field() -> None:
    @dataclasses.dataclass
    class Image:
        width: int = cst.TStructField(cs.Int8ub)
        height: int = cst.TStructField(cs.Int8ub)
        pixels: t.Optional[bytes] = cst.TStructField(
            cs.Default(
                cs.Bytes(cs.this.width * cs.this.height),
                lambda ctx: bytes(ctx.width * ctx.height),
            )
        )

    common(
        cst.TStruct(Image),
        b"\x02\x03\x00\x00\x00\x00\x00\x00",
        setattrs(Image(2, 3), pixels=bytes(6)),
        sample_building=Image(2, 3),
    )


def test_tstruct_const_field() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        const_field: t.Optional[bytes] = cst.TStructField(cs.Const(b"\x00"))

    common(
        cst.TStruct(TestDataclass),
        bytes(1),
        setattrs(TestDataclass(), const_field=b"\x00"),
        1,
    )

    assert (
        raises(
            cst.TStruct(TestDataclass).build,
            setattrs(TestDataclass(), const_field=b"\x01"),
        )
        == cs.ConstError
    )


def test_tstruct_anonymus_fields_1() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        _1: t.Optional[bytes] = cst.TStructField(cs.Const(b"\x00"))
        _2: None = cst.TStructField(cs.Padding(1))
        _3: None = cst.TStructField(cs.Pass)
        _4: None = cst.TStructField(cs.Terminated)

    common(
        cst.TStruct(TestDataclass),
        bytes(2),
        setattrs(TestDataclass(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_tstruct_anonymus_fields_2() -> None:
    @dataclasses.dataclass
    class TestDataclass:
        _1: int = cst.TStructField(cs.Computed(7))
        _2: t.Optional[bytes] = cst.TStructField(cs.Const(b"JPEG"))
        _3: None = cst.TStructField(cs.Pass)
        _4: None = cst.TStructField(cs.Terminated)

    d = cst.TStruct(TestDataclass)
    assert d.build(TestDataclass()) == d.build(TestDataclass())


def test_tstruct_missing_dataclass() -> None:
    class TestDataclass:
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    assert raises(lambda: cst.TStruct(TestDataclass)) == TypeError


def test_tstruct_wrong_dataclass() -> None:
    @dataclasses.dataclass
    class TestDataclass1:
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    @dataclasses.dataclass
    class TestDataclass2:
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    assert (
        raises(cst.TStruct(TestDataclass1).build, TestDataclass2(a=1, b=2)) == TypeError
    )


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

    assert raises(lambda: cst.TEnum(cs.Byte, E)) == TypeError


def test_tenum_in_tstruct() -> None:
    class TestEnum(enum.IntEnum):
        a = 1
        b = 2

    @dataclasses.dataclass
    class TestDataclass:
        a: TestEnum = cst.TStructField(cst.TEnum(cs.Int8ub, TestEnum))
        b: int = cst.TStructField(cs.Int8ub)

    common(
        cst.TStruct(TestDataclass),
        b"\x00\x01\x02",
        TestDataclass(a=TestEnum.a, b=TestEnum.b),
        3,
    )
