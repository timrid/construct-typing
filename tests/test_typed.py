# -*- coding: utf-8 -*-

import dataclasses
import enum
import typing as t

import construct as cs
import construct_typed as cst

from .declarativeunittest import common, raises, setattrs


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


def test_tstruct_no_dataclass() -> None:
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

    assert raises(lambda: cst.TEnum(cs.Byte, E)) == TypeError


def test_tstruct_wrong_enumbase() -> None:
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
    class TestDataclass:
        a: TestEnum = cst.TStructField(cst.TEnum(cs.Int8ub, TestEnum))
        b: int = cst.TStructField(cs.Int8ub)

    common(
        cst.TStruct(TestDataclass),
        b"\x01\x02",
        TestDataclass(a=TestEnum.a, b=2),
        2,
    )

    assert (
        raises(cst.TEnum(cs.Byte, TestEnum).build, TestDataclass(a=1, b=2)) == TypeError  # type: ignore
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
