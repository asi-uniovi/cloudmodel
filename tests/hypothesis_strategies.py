"""Define strategies for generating quantities with the appropriate units
and to generate random problems which have a consistent set of apps, 
ics and ccs, for use via hypothesis package in testing
"""
import itertools
from cloudmodel.unified.units import (
    Time,
    Currency,
    CurrencyPerTime,
    Requests,
    RequestsPerTime,
    Storage,
    ComputationalUnits,
)
from cloudmodel.unified import model
from hypothesis import strategies as st

# Function to create a string of the form "20.3 minute" for example
# The numeric part is drawn randomly from floats, and the units part
# is drawn randomly from the given list f allowable units
def str_float_quantity_strategy(
    allowable_units: list[str], min_value=0, max_value=1e30
):
    value = st.floats(
        min_value=min_value,
        max_value=max_value,
        allow_nan=False,
        allow_subnormal=False,
        allow_infinity=False,
    )
    unit = st.sampled_from(allowable_units)
    return st.tuples(value, unit).map(lambda v: f"{v[0]} {v[1]}")


def model_unit_strategy(t: type):
    """Strategie to generate a random Quantity with the appropriate units depending
    on the type received. For example, for Time type the quantity generated will
    be of the subclass Time and the units will be time units, and so on."""
    if t == Time:
        return st.builds(
            Time, str_float_quantity_strategy(["hour", "minute", "second"])
        )
    elif t == Currency:
        return st.builds(Currency, str_float_quantity_strategy(["usd"]))
    elif t == CurrencyPerTime:
        return st.builds(
            CurrencyPerTime,
            str_float_quantity_strategy(["usd/hour", "usd/minute", "usd/second"]),
        )
    elif t == Requests:
        return st.builds(Requests, str_float_quantity_strategy(["req"]))
    elif t == RequestsPerTime:
        return st.builds(
            RequestsPerTime,
            str_float_quantity_strategy(["req/hour", "req/minute", "req/second"]),
        )
    elif t == Storage:
        return st.builds(Storage, str_float_quantity_strategy(["MiB", "GiB"]))
    elif t == ComputationalUnits:
        return st.builds(
            ComputationalUnits, str_float_quantity_strategy(["cores", "millicores"])
        )
    else:
        raise TypeError(f"Invalid type {t} for strategy")


# Register the previous function as strategy for our unit types
st.register_type_strategy(Time, model_unit_strategy)
st.register_type_strategy(Currency, model_unit_strategy)
st.register_type_strategy(CurrencyPerTime, model_unit_strategy)
st.register_type_strategy(Requests, model_unit_strategy)
st.register_type_strategy(RequestsPerTime, model_unit_strategy)
st.register_type_strategy(Storage, model_unit_strategy)
st.register_type_strategy(ComputationalUnits, model_unit_strategy)


@st.composite
def model_problem_strategy(draw):
    """Strategy to create a random problem which has consistent sets of (implicit) apps,
    instance classes and container classes.

    The problem is that, since the instance (and container) classes are used as keys in the
    performance dictionary, but also appear as a list in the system class, it should be ensured that
    the same instance/container class objects are listed in both parts.

    Similarly, apps appear as keys in the performance dict, and also as keys in the workload dicts,
    and also a values for containers. It must be ensured that the same apps are used elsewhere.

    The "source of truth" for the instance/container classes and apps will be the performance dict,
    since this one has to list all combinations of (ic, cc, app). The instance/container classes
    and apps which appear elsewhere in the model need to be a subset of the ones used as keys in
    this dictionary.
    """

    # Create a random list of instance classes
    ics = draw(st.lists(st.from_type(model.InstanceClass), min_size=1, max_size=4))

    # Create a random list of apps
    apps = draw(st.lists(st.from_type(model.App), min_size=1, max_size=4))

    # Create a random list of container classes, but ensuring that the app
    # assigned to each cc is drawn from the previous list of apps

    # First we create a list with the parameters to be used to instantate
    # each ContainerClass, using appropriate strategies for each field
    ccs_data = draw(
        st.lists(
            st.tuples(
                st.text(),  # container name
                st.from_type(ComputationalUnits),  # cores
                st.from_type(Storage),  # memory
                st.sampled_from(apps),  # app
                st.integers(),  # limit
            ),
            min_size=0,
            max_size=3,
        )
    )
    # Now instantiate all these ContainerClasses
    ccs = [
        model.ContainerClass(name=name, cores=cores, mem=mem, app=app, limit=limit)
        for (name, cores, mem, app, limit) in ccs_data
    ]
    # The list may be empty (to allow malloovia models which do not use containers),
    # but for this case `None` has to be used as containerclass key for the performance dict
    if not ccs:
        ccs = [None]

    # Create a random dict of performances. The keys of the dict are formed by all
    # combinations of (ic, cc, app) from the previous list of ics, ccs and apps
    # The values are drawn from strategie WorkloadSeries
    perfs = {}
    for ic, cc, app in itertools.product(ics, ccs, apps):
        perfs[ic, cc, app] = draw(st.from_type(RequestsPerTime))
    system = model.System(name=draw(st.text()), ics=ics, ccs=ccs, perfs=perfs)
    workloads = draw(
        st.dictionaries(st.sampled_from(apps), st.from_type(model.WorkloadSeries))
    )

    # Create the problem with all of the above parameters
    return model.Problem(
        name=draw(st.text()),
        system=system,
        workloads=workloads,
        sched_time_size=draw(st.from_type(Time)),
        version="0.2.0",
    )
