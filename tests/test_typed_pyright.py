# ###############################################################################################################
# Test if Pyright recognizes missing or extraneous construct parameters in dataclasses and would generate errors.
# We do this by ignoring the issue with `ignore[reportCallIssue]` while at the same time forcing Pyright to
# throw an error for unnecessary ignores.
# ###############################################################################################################

# This rule is essential for these tests to work!
# pyright: reportUnnecessaryTypeIgnoreComment=error
import dataclasses
import typing as t

import construct as cs

from construct_typed import DataclassMixin, csdefault_field, csfield


def test_dataclass_const_default() -> None:
    @dataclasses.dataclass
    class ConstDefaultTest(DataclassMixin):
        const_bytes: bytes = csfield(cs.Const(b"BMP"))
        const_int: int = csfield(cs.Const(5, cs.Int8ub))
        default_int: int = csdefault_field(cs.Int8ub, 8)
        default_lambda: bytes = csdefault_field(cs.Bytes(cs.this.default_int), lambda ctx: bytes(ctx.default_int))
        computed: bytes = csfield(cs.Computed(lambda ctx: bytes(i + 49 for i in range(ctx.default_int))))
        # Construct allows to put non-default values after Default. Dataclass and Pyright don't like that too much. It is necessary to
        # specify the field `kw_only` and pass it "by keyword".
        normal_int: int = csfield(cs.Int8ub, kw_only=True)
        const_int2: int = csfield(cs.Const(5, cs.Int8ub))

    if t.TYPE_CHECKING:
        # Regression checks: MUST generate Pyright reportCallIssue or will trigger `reportUnnecessaryTypeIgnoreComment`.
        ConstDefaultTest(const_bytes=b"", normal_int=7)   # pyright: ignore[reportCallIssue]
        ConstDefaultTest(const_int=0, normal_int=7)       # pyright: ignore[reportCallIssue]
        ConstDefaultTest(computed=bytes(), normal_int=7)  # pyright: ignore[reportCallIssue]


def test_dataclass_padded() -> None:
    @dataclasses.dataclass
    class PaddingTest(DataclassMixin):
        padding: t.Optional[bytes] = csfield(cs.Padding(1))
        padded_pass: t.Optional[bytes] = csfield(cs.Padded(2, cs.Pass))
        padded_bytes: bytes = csfield(cs.Padded(7, cs.Bytes(5)))
        padded_string: str = csfield(cs.PaddedString(4, "utf-8"))

    if t.TYPE_CHECKING:
        # Regression checks: MUST generate Pyright reportCallIssue or will trigger `reportUnnecessaryTypeIgnoreComment`.
        PaddingTest(padding=b"\x00", padded_bytes=b"12345", padded_string="abc")  # pyright: ignore[reportCallIssue]
        PaddingTest(padded_pass=bytes(0), padded_bytes=b"12345", padded_string="abc")  # pyright: ignore[reportCallIssue]
        PaddingTest(padded_bytes=b"12345")  # pyright: ignore[reportCallIssue]  # padded_string missing
        PaddingTest(padded_string="abc")  # pyright: ignore[reportCallIssue]  # padded_bytes missing
