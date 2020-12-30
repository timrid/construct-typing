# -*- coding: utf-8 -*-

import enum
import dataclasses
import typing as t
from .declarativeunittest import common, raises
from construct import (
    Int8ub,
    Int16ub,
    Const,
    Pass,
    Terminated,
    Padding,
    SizeofError,
    Byte,
    Bytes,
    Computed,
    this,
)
from construct_typed import TStruct, TBitStruct, TSubcon, TEnum


def test_typed_struct_1():
    @dataclasses.dataclass
    class TestDataclass:
        a: int = TSubcon(Int16ub)
        b: int = TSubcon(Int8ub)

    common(TStruct(TestDataclass), b"\x00\x01\x02", TestDataclass(a=1, b=2), 3)
    common(
        TStruct(TestDataclass, swapped=True),
        b"\x02\x00\x01",
        TestDataclass(a=1, b=2),
        3,
    )
    normal = TStruct(TestDataclass)
    swapped = TStruct(TestDataclass, swapped=True)
    assert str(normal.parse(b"\x00\x01\x02")) == str(swapped.parse(b"\x02\x00\x01"))

def test_typed_struct_2():
    @dataclasses.dataclass
    class TestDataclass:
        @dataclasses.dataclass
        class InnerDataclass:
            b: int = TSubcon(Byte)

        a: InnerDataclass = TSubcon(TStruct(InnerDataclass))

    common(
        TStruct(TestDataclass),
        b"\x01",
        TestDataclass(a=TestDataclass.InnerDataclass(b=1)),
        1,
    )

def test_typed_struct_3():
    @dataclasses.dataclass
    class TestDataclass:
        _1: t.Optional[bytes] = TSubcon(Const(b"\x00"))
        _2: None = TSubcon(Padding(1))
        _3: None = TSubcon(Pass)
        _4: None = TSubcon(Terminated)

    common(
        TStruct(TestDataclass),
        bytes(2),
        TestDataclass(),
        SizeofError,
    )

def test_typed_struct_4():
    @dataclasses.dataclass
    class TestDataclass:
        _1: bytes = TSubcon(Bytes(this.missing))

    assert raises(TStruct(TestDataclass).sizeof) == SizeofError

def test_typed_struct_5():
    @dataclasses.dataclass
    class TestDataclass:
        _1: int = TSubcon(Computed(7))
        _2: t.Optional[bytes] = TSubcon(Const(b"JPEG"))
        _3: None = TSubcon(Pass)
        _4: None = TSubcon(Terminated)

    d = TStruct(TestDataclass)
    assert d.build(TestDataclass()) == d.build(TestDataclass())


def test_typed_bit_struct():
    assert False


def test_enum():
    class E(enum.IntEnum):
        a = 1
        b = 2

    a = TEnum(Byte, E)

    common(TEnum(Byte, E), b"\x01", E.a, 1)
    common(TEnum(Byte, E), b"\x01", 1, 1)
    format = TEnum(Byte, E)
    obj = format.parse(b"\x01")
    assert obj == E.a
    data = format.build("a")
    assert data == b"\x01"

    common(TEnum(Byte, E), b"\x02", E.b, 1)
    common(TEnum(Byte, E), b"\x02", 2, 1)
    format = TEnum(Byte, E)
    obj = format.parse(b"\x02")
    assert obj == E.b
    data = format.build("b")
    assert data == b"\x02"

    common(TEnum(Byte, E), b"\x03", 3, 1)
    format = TEnum(Byte, E)
    obj = format.parse(b"\x03")
    assert int(obj) == 3
    data = format.build(3)
    assert data == b"\x03"


def test_enum_in_struct():
    class TestEnum(enum.IntEnum):
        a = 1
        b = 2

    @dataclasses.dataclass
    class TestDataclass:
        a: TestEnum = TSubcon(TEnum(Int8ub, TestEnum))
        b: int = TSubcon(Int8ub)

    common(TStruct(TestDataclass), b"\x00\x01\x02", TestDataclass(a=TestEnum.a, b=TestEnum.b), 3)
