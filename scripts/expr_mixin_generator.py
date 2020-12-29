

testobjs = [
    int(10),
    bool(1),
    float(10.0),
]

operators_bin = [
    "__add__",
    "__sub__",
    "__mul__",
    "__floordiv__",
    "__truediv__",
    "__div__",
    "__mod__",
    "__pow__",
    "__xor__",
    "__rshift__",
    "__lshift__",
    "__and__",
    "__or__",

    "__radd__",
    "__rsub__",
    "__rmul__",
    "__rfloordiv__",
    "__rtruediv__",
    "__rdiv__",
    "__rmod__",
    "__rpow__",
    "__rxor__",
    "__rrshift__",
    "__rlshift__",
    "__rand__",
    "__ror__",

    "__contains__",
    "__gt__",
    "__ge__",
    "__lt__",
    "__le__",
    "__eq__",
    "__ne__",
]

operators_uni = [
    "__neg__",
    "__pos__",
    "__invert__",
    "__inv__",
]


def create_overload_bin(op, lhs=None, rhs=None):
    if lhs is None and rhs is None:
        print("    @t.overload")
        print(f"    def {op}(self, other: t.Any) -> BinExpr[t.Any]: ...")
    else:
        try:
            result = getattr(lhs, op)(rhs)
            lhs_type = type(lhs).__name__
            rhs_type = type(rhs).__name__
            result_type = type(result).__name__
            if result_type != "NotImplementedType":
                print("    @t.overload")
                print(f"    def {op}(self: ExprMixin[{lhs_type}], other: ConstOrCallable[{rhs_type}]) -> BinExpr[{result_type}]: ...")
        except AttributeError:
            pass

def create_overload_uni(op, obj=None):
    if obj is None:
        print("    @t.overload")
        print(f"    def {op}(self) -> UniExpr[t.Any]: ...")
    else:
        try:
            result = getattr(obj, op)()
            obj_type = type(obj).__name__
            result_type = type(result).__name__
            if result_type != "NotImplementedType":
                print("    @t.overload")
                print(f"    def {op}(self: ExprMixin[{obj_type}]) -> BinExpr[{result_type}]: ...")
        except AttributeError:
            pass


print("class ExprMixin(t.Generic[ReturnType], object):")
for op in operators_bin:
    print(f"    # {op} ".ljust(120, "#"))
    for lhs in testobjs:
        for rhs in testobjs:
            create_overload_bin(op, lhs, rhs)
    create_overload_bin(op)
    print("")

for op in operators_uni:
    print(f"    # {op} ".ljust(120, "#"))
    for obj in testobjs:
        create_overload_uni(op, obj)
    create_overload_uni(op)
    print("")