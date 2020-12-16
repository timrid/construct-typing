# -*- coding: utf-8 -*-

import enum
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
from construct.lib import Container
from construct_typed import TypedContainer, TypedStruct, TypedEnum, Subcon


def test_typed_struct():
    class Container1(TypedContainer):
        a: Subcon(Int16ub)
        b: Subcon(Int8ub)

    common(TypedStruct(Container1), b"\x00\x01\x02", Container1(a=1, b=2), 3)
    common(
        TypedStruct(Container1, swapped=True),
        b"\x02\x00\x01",
        Container(a=1, b=2),
        3,
    )
    normal = TypedStruct(Container1)
    swapped = TypedStruct(Container1, swapped=True)
    assert str(normal.parse(b"\x00\x01\x02")) == str(swapped.parse(b"\x02\x00\x01"))

    class Container2(TypedContainer):
        class InnerContainer(TypedContainer):
            b: Subcon(Byte)

        a: Subcon(TypedStruct(InnerContainer))

    common(TypedStruct(Container2), b"\x01", Container(a=Container(b=1)), 1)

    # TODO: How to get anonymus subcons?
    class Container3(TypedContainer):
        anonymus1: Subcon(Const(b"\x00"))
        anonymus2: Subcon(Padding(1))
        anonymus3: Subcon(Pass)
        anonymus4: Subcon(Terminated)

    common(
        TypedStruct(Container3),
        bytes(2),
        dict(anonymus1=b"\x00", anonymus2=None, anonymus3=None, anonymus4=None),
        SizeofError,
    )

    class Container4(TypedContainer):
        missingkey: Subcon(Byte)

    assert raises(TypedStruct(Container4).build, {}) == KeyError

    # TODO: How to get anonymus subcons?
    class Container5(TypedContainer):
        anonymus1: Subcon(Bytes(this.missing))

    assert raises(TypedStruct(Container5).sizeof) == SizeofError

    # TODO: How to get anonymus subcons?
    class Container6(TypedContainer):
        anonymus1: Subcon(Computed(7))
        anonymus2: Subcon(Const(b"JPEG"))
        anonymus3: Subcon(Pass)
        anonymus4: Subcon(Terminated)

    d = TypedStruct(Container6)
    assert d.build({}) == d.build({})


def test_typed_bit_struct():
    assert False


def test_enum():
    class E(enum.IntEnum):
        a = 1
        b = 2

    common(TypedEnum(Byte, E), b"\x01", E.a, 1)
    common(TypedEnum(Byte, E), b"\x01", 1, 1)
    format = TypedEnum(Byte, E)
    obj = format.parse(b"\x01")
    assert obj == E.a
    data = format.build("a")
    assert data == b"\x01"

    common(TypedEnum(Byte, E), b"\x02", E.b, 1)
    common(TypedEnum(Byte, E), b"\x02", 2, 1)
    format = TypedEnum(Byte, E)
    obj = format.parse(b"\x02")
    assert obj == E.b
    data = format.build("b")
    assert data == b"\x02"

    common(TypedEnum(Byte, E), b"\x03", 3, 1)
    format = TypedEnum(Byte, E)
    obj = format.parse(b"\x03")
    assert int(obj) == 3
    data = format.build(3)
    assert data == b"\x03"
