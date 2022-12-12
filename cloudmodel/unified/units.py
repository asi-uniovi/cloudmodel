import pint

def foo(x: pint.Quantity) -> float:
    return x.magnitude