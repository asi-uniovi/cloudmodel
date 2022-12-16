from pint import Quantity, DimensionalityError, UnitRegistry
from typing import Union, cast

# Define new units
ureg = UnitRegistry()
ureg.define("usd = [currency]")
ureg.define("cores = [computation] = 2*vcores")
ureg.define("millicores = 0.001 cores")
ureg.define("req = [requests]")
# ureg.define("bit = [storage]")
ureg.define("[performance] = [requests]/[time]")
ureg.define("rps = [performance] = req/second")
ureg.define("rpm = req/minute")
ureg.define("rph = req/hour")


class CheckedDimensionality:
    _dimensionality = "[]"

    def __init_subclass__(cls, dimensionality="[]", **kwargs):
        # This function is called when this class is subclassed
        # We store the dimensionality value in the subclass
        super().__init_subclass__(**kwargs)
        cls._dimensionality = dimensionality

    def __new__(cls, v: Union[str, Quantity]) -> Quantity:
        # This method will be inherited by the subclasses and used to
        # create obejects of that subclass. During the creation,
        # the correct dimensionality is checked
        obj = ureg.Quantity(v)
        if not obj.check(cls._dimensionality):
            raise DimensionalityError(v, cls._dimensionality)
        return obj


# -----------------------------------------------------------------------------------
# New dimension types appropriate for the cloud model
# -----------------------------------------------------------------------------------
class Time(CheckedDimensionality, dimensionality="[time]"):
    ...


class Currency(CheckedDimensionality, dimensionality="[currency]"):
    ...


class Requests(CheckedDimensionality, dimensionality="[requests]"):
    ...


class Storage(CheckedDimensionality, dimensionality="[]"):
    ...


class RequestsPerTime(CheckedDimensionality, dimensionality="[requests]/[time]"):
    ...


class CurrencyPerTime(CheckedDimensionality, dimensionality="[currency]/[time]"):
    ...


class ComputationalUnits(CheckedDimensionality, dimensionality="[computation]"):
    ...

def first_char_of_unit(q: Quantity) -> str:
    return str(cast(Quantity, q).units)[0]

def magnitude_scaled_for_timeunit(q: RequestsPerTime, t: Time):
    new_units = (ureg.req / t).units
    return cast(Quantity, q).to(new_units).magnitude


__all__ = [
    "Time",
    "Currency",
    "CurrencyPerTime",
    "Requests",
    "RequestsPerTime",
    "Storage",
    "ComputationalUnits",
]
