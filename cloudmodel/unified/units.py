import pint
from pint import Quantity
from typing import Generic, TypeVar, NewType 

T = TypeVar("T")
RequestsPerTimeUnit = NewType("RequestsPerTimeUnit", pint.Unit)
CurrencyPerTimeUnit = NewType("CurrencyPerTimeUnit", pint.Unit)
ComputationUnit = NewType("ComputationUnit", pint.Unit)
RequestsUnit = NewType("RequestsUnit", pint.Unit)
TimeUnit = NewType("TimeUnit", pint.Unit)
StorageUnit = NewType("StorageUnit", pint.Unit)

class Q(Quantity, Generic[T]):
    pass

ureg = pint.UnitRegistry()


# Define new units
ureg.define("usd = [currency]")
ureg.define("cores = [computation]")
ureg.define("millicores = 0.001 cores")
ureg.define("req = [requests]")

Q_ = ureg.Quantity
