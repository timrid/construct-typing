# -*- coding: utf-8 -*-

import dataclasses
import enum

import construct as cs
import construct_typed as cst
import pytest

from .declarativeunittest import common, raises, setattrs


def test_tcontainer_compare_with_dataclass() -> None:
    @dataclasses.dataclass
    class TestContainer:
        a: cst.Opt[int] = cst.TStructField(cs.Const(1, cs.Byte))
        b: int = cst.TStructField(cs.Int8ub)

    @dataclasses.dataclass
    class TestTContainer(cst.TContainerBase):
        a: cst.Opt[int] = cst.TStructField(cs.Const(1, cs.Byte))
        b: int = cst.TStructField(cs.Int8ub)

    datacls = TestContainer(b=1)
    tcontainer = TestTContainer(b=1)

    # ##### compare dot & dict access #####
    # dataclass
    assert datacls.a == None
    assert raises(lambda: datacls["a"]) == TypeError  # type: ignore
    assert datacls.b == 1
    assert raises(lambda: datacls["b"]) == TypeError  # type: ignore

    datacls.a = 5
    assert datacls.a == 5
    assert raises(lambda: datacls["a"]) == TypeError  # type: ignore
    try:
        datacls["a"] = 5  # type: ignore
    except Exception as e:
        assert e.__class__ == TypeError

    # tcontainer
    assert tcontainer.a == None
    assert tcontainer["a"] == None
    assert tcontainer.b == 1
    assert tcontainer["b"] == 1

    tcontainer.a = 5
    assert tcontainer.a == 5
    assert tcontainer["a"] == 5
    tcontainer["a"] = 5
    assert tcontainer.a == 5
    assert tcontainer["a"] == 5

    # ##### compare fields #####
    for datacls_field, tcontainer_field in zip(
        dataclasses.fields(TestContainer), dataclasses.fields(TestTContainer)
    ):
        assert repr(datacls_field) == repr(tcontainer_field)

    # ##### compare wrong creation #####
    assert raises(lambda: TestContainer(a=0, b=1)) == TypeError
    assert raises(lambda: TestTContainer(a=0, b=1)) == TypeError


def test_tcontainer_order() -> None:
    @dataclasses.dataclass
    class Image(cst.TContainerBase):
        signature: cst.Opt[bytes] = cst.TStructField(cs.Const(b"BMP"))
        width: int = cst.TStructField(cs.Int8ub)
        height: int = cst.TStructField(cs.Int8ub)

    format = cst.TStruct(Image)
    obj = Image(width=3, height=2)
    assert (
        str(obj) == "Container: \n    signature = None\n    width = 3\n    height = 2"
    )
    obj = format.parse(format.build(obj))
    assert (
        str(obj)
        == "Container: \n    signature = b'BMP' (total 3)\n    width = 3\n    height = 2"
    )


def test_tstruct() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerBase):
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    common(cst.TStruct(TestContainer), b"\x00\x01\x02", TestContainer(a=1, b=2), 3)


def test_tstruct_swapped() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerBase):
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    common(
        cst.TStruct(TestContainer, swapped=True),
        b"\x02\x00\x01",
        TestContainer(a=1, b=2),
        3,
    )
    normal = cst.TStruct(TestContainer)
    swapped = cst.TStruct(TestContainer, swapped=True)
    assert str(normal.parse(b"\x00\x01\x02")) == str(swapped.parse(b"\x02\x00\x01"))


def test_tstruct_nested() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerBase):
        @dataclasses.dataclass
        class InnerDataclass(cst.TContainerBase):
            b: int = cst.TStructField(cs.Byte)

        a: InnerDataclass = cst.TStructField(cst.TStruct(InnerDataclass))

    common(
        cst.TStruct(TestContainer),
        b"\x01",
        TestContainer(a=TestContainer.InnerDataclass(b=1)),
        1,
    )


def test_tstruct_default_field() -> None:
    @dataclasses.dataclass
    class Image(cst.TContainerBase):
        width: int = cst.TStructField(cs.Int8ub)
        height: int = cst.TStructField(cs.Int8ub)
        pixels: cst.Opt[bytes] = cst.TStructField(
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
    class TestContainer(cst.TContainerBase):
        const_field: cst.Opt[bytes] = cst.TStructField(cs.Const(b"\x00"))

    common(
        cst.TStruct(TestContainer),
        bytes(1),
        setattrs(TestContainer(), const_field=b"\x00"),
        1,
    )

    assert (
        raises(
            cst.TStruct(TestContainer).build,
            setattrs(TestContainer(), const_field=b"\x01"),
        )
        == cs.ConstError
    )


def test_tstruct_anonymus_fields_1() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerBase):
        _1: cst.Opt[bytes] = cst.TStructField(cs.Const(b"\x00"))
        _2: None = cst.TStructField(cs.Padding(1))
        _3: None = cst.TStructField(cs.Pass)
        _4: None = cst.TStructField(cs.Terminated)

    common(
        cst.TStruct(TestContainer),
        bytes(2),
        setattrs(TestContainer(), _1=b"\x00"),
        cs.SizeofError,
    )


def test_tstruct_anonymus_fields_2() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerBase):
        _1: int = cst.TStructField(cs.Computed(7))
        _2: cst.Opt[bytes] = cst.TStructField(cs.Const(b"JPEG"))
        _3: None = cst.TStructField(cs.Pass)
        _4: None = cst.TStructField(cs.Terminated)

    d = cst.TStruct(TestContainer)
    assert d.build(TestContainer()) == d.build(TestContainer())


def test_tstruct_no_dataclass() -> None:
    class TestContainer(cst.TContainerBase):
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    assert raises(lambda: cst.TStruct(TestContainer)) == TypeError


def test_tstruct_no_tcontainerbase() -> None:
    @dataclasses.dataclass
    class TestContainer:
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    assert raises(lambda: cst.TStruct(TestContainer)) == TypeError


def test_tstruct_wrong_container() -> None:
    @dataclasses.dataclass
    class TestContainer1(cst.TContainerBase):
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    @dataclasses.dataclass
    class TestContainer2(cst.TContainerBase):
        a: int = cst.TStructField(cs.Int16ub)
        b: int = cst.TStructField(cs.Int8ub)

    assert (
        raises(cst.TStruct(TestContainer1).build, TestContainer2(a=1, b=2)) == TypeError
    )


def test_tstruct_doc() -> None:
    @dataclasses.dataclass
    class TestContainer(cst.TContainerBase):
        a: int = cst.TStructField(cs.Int16ub, "This is the documentation of a")
        b: int = cst.TStructField(
            cs.Int8ub, doc="This is the documentation of b\nwhich is multiline"
        )
        c: int = cst.TStructField(
            cs.Int8ub,
            """
            This is the documentation of c
            which is also multiline
            """,
        )

    format = cst.TStruct(TestContainer)
    common(format, b"\x00\x01\x02\x03", TestContainer(a=1, b=2, c=3), 4)

    assert format.subcon.a.docs == "This is the documentation of a"
    assert format.subcon.b.docs == "This is the documentation of b\nwhich is multiline"
    assert format.subcon.c.docs == "This is the documentation of c\nwhich is also multiline"
    


@pytest.mark.xfail(reason="not implemented yet")
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
    class TestContainer(cst.TContainerBase):
        a: TestEnum = cst.TStructField(cst.TEnum(cs.Int8ub, TestEnum))
        b: int = cst.TStructField(cs.Int8ub)

    common(
        cst.TStruct(TestContainer),
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
