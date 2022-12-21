# coding: utf-8
"""This module implements the base dataclasses which define a
problem to be solved by Malloovia, and the solution
"""

from dataclasses import dataclass
from typing import Tuple
from ..util import simplified_repr
from .. import __version__
from .units import *


@simplified_repr("name", show_field_names=False)
@dataclass(frozen=True)
class App:
    """App identifier.

    Attributes:
        name:str: name of the application
    """

    name: str = "unnamed"


@simplified_repr("name", "app", "time_unit")
@dataclass(frozen=True, repr=False)
class WorkloadSeries:
    """Workload as a sequence for different timeslots

    Attributes:
        name:str: name of this workload
        values:tuple[float,...]: sequence of workloads for each timeslot
            as the average number of requests arriving globally at the timeslot
            It can be a tuple with a single element, for a single timeslot
        app:App: application to which the requests are addressed
        time_slot_size:float: duration of the timeslot
        intra_slot_distribution:str: name of the distribution for the
           interarrival times of the requests ("exponential" by default)
    """

    description: str
    values: Tuple[Requests, ...]
    time_slot_size: Time
    intra_slot_distribution: str = "exponential"

    # def __post_init__(self):
    #     """Checks dimensions of the time_slot_size are valid."""
    #     self.time_slot_size.to("hour")


@dataclass(frozen=True)
class Workload:
    """Workload for a single timeslot (to be deprecated, redundant with WorkloadSeries)

    Attributes:
        value:float: average number of requests arriving globally at the timeslot
        app:App: application to which the requests are addressed
        time_slot_size: duration of the timeslot
        intra_slot_distribution:str: name of the distribution for the
           interarrival times of the requests ("exponential" by default)
    """

    value: Requests
    time_slot_size: Time
    intra_slot_distribution: str = "exponential"

    # def __post_init__(self):
    #     """Checks dimensions of the time_slot_size are valid."""
    #     self.time_slot_size.to("hour")


@dataclass(frozen=True)
class LimitingSet:
    """LimitingSet restrictions.

    Attributes:
        name:str: name of this limiting set (usually a region name)
        max_vms:int: limit of the maximum number of VMs that can be
           running in this limiting set. Defaults to 0 which means
           "no limit"
        max_cores: int: limit on the maximum number of vcores that can
           be running in this limiting set. Defaults to 0 which means
           "no limits"
    """

    name: str
    max_vms: int = 0
    max_cores: ComputationalUnits = ComputationalUnits("0 cores")


@simplified_repr("name", "price", "cores", "mem")
@dataclass(frozen=True)
class InstanceClass:
    """InstanceClass characterization

    Attributes:
        name:str: name of the instance class, usually built from the name of the VM type
             and the name of the limiting set in which it is deployed.
        price:float: dollar per time unit
        cores:float:  millicores available in the VM
        mem:float: GiB available in the VM
        limit:int: maximum number of VMs (0 means "no limit")
        limiting_sets:set[LimitingSet]: LimitingSet to which this instance class belongs.
        is_reserved:bool: True if the instance is reserved
        is_private:bool: True if this instance class belongs to a private cloud
    """

    name: str
    price: CurrencyPerTime
    cores: ComputationalUnits
    mem: Storage
    limit: int
    limiting_sets: Tuple[LimitingSet]
    is_reserved: bool = False
    is_private: bool = False

    # def __post_init__(self):
    #     """Checks dimensions are valid and store them in the standard units."""
    #     object.__setattr__(self, "price", self.price.to("usd/hour"))
    #     object.__setattr__(self, "cores", self.cores.to("cores"))
    #     object.__setattr__(self, "mem", self.mem.to("gibibytes"))


@dataclass(frozen=True)
class ContainerClass:
    """ContainerClass characterization

    Attributes:
        name:str: name of the container class
        cores:float: number of millicores available in this container
        mem:float: GiB available in this container
        app:App: application (container image) run in this container
        limit:int: cpu limit enforced by the container orchestrator
    """

    name: str
    cores: ComputationalUnits
    mem: Storage
    app: App
    limit: int

    # def __post_init__(self):
    #     """Checks dimensions are valid and store them in the standard units."""
    #     object.__setattr__(self, "cores", self.cores.to("millicores"))
    #     object.__setattr__(self, "mem", self.mem.to("gibibytes"))


@dataclass(frozen=True)
class ProcessClass:
    """Running process characterization (TODO: same than ContainerClass?)

    Attributes:
        name:str: name of the process
        ecu:float: units of computation that the process can give when running
        mem:float: amount of memory that the process can use
        app:App: application run by the process
    """

    name: str
    ecu: float
    mem: float
    app: App
    limit: int


@simplified_repr("name")
@dataclass(frozen=True)
class System:
    """Model for the system, infrastructure and apps

    Attributes:
        name:str: Name of the system modelled
        ics:list[InstanceClass]: List of instance classes (cloud infrastructure)
        ccs:list[ContainerClass]: List of containers classes (runtime for apps)
        perfs:dict[tuple[InstanceClass, ContainerClass|ProcessClass], float]:
           Performance in requests-per-time-unit for each pair (InstanceClass, ContainerClass)
    """

    name: str
    ics: list[InstanceClass]
    ccs: list[ContainerClass]
    perfs: dict[
        Tuple[InstanceClass, ContainerClass | ProcessClass | None, App],
        RequestsPerTime,
    ]

    # def __post_init__(self):
    #     """Checks dimensions are valid and store them in the standard units."""
    #     new_perfs = {}
    #     for key, value in self.perfs.items():
    #         new_perfs[key] = value.to("req/hour")
    #     object.__setattr__(self, "perfs", new_perfs)


@simplified_repr("name", "system", "version")
@dataclass(frozen=True)
class Problem:
    """Problem description.

    Attributes:
        name:str: name of the problem
        workloads:dict[App, WorkloadSeries]:  Workload for each app
        sched_time_size:Q["[time]"]:  Size of the scheduling window
        description:str: Optional description for the problem
    """

    name: str
    system: System
    workloads: dict[App, WorkloadSeries]
    sched_time_size: Time
    version: str = __version__


def normalize_time_units(problem: Problem, units="minute") -> Problem:
    sched_time_size = problem.sched_time_size.to(units)
    workloads = {}
    for app, wl_series in problem.workloads.items():
        if wl_series.time_slot_size.magnitude != 0:
            factor = (
                wl_series.time_slot_size.magnitude
                / wl_series.time_slot_size.to(units).magnitude
            )
        else:
            factor = 0
        values = tuple(wl * factor for wl in wl_series.values)
        workloads[app] = WorkloadSeries(
            wl_series.description,
            values,
            Time(units),
            wl_series.intra_slot_distribution,
        )
    ics = []
    for ic in problem.system.ics:
        ics.append(
            InstanceClass(
                name=ic.name,
                price=ic.price.to(f"usd/{units}"),
                cores=ic.cores,
                mem=ic.mem,
                limit=ic.limit,
                limiting_sets=ic.limiting_sets,
                is_reserved=ic.is_reserved,
                is_private=ic.is_private,
            )
        )
    perfs = {}
    for k, v in problem.system.perfs.items():
        ic, cc, app = k
        ic_idx = problem.system.ics.index(ic)
        perfs[ics[ic_idx], cc, app] = v.to(f"req/{units}")
    sys = System(
        name=problem.system.name,
        ics=ics,
        ccs=problem.system.ccs,
        perfs=perfs,
    )
    return Problem(
        name=problem.name,
        system=sys,
        workloads=workloads,
        sched_time_size=sched_time_size,
        version=problem.version,
    )


__all__ = [
    "App",
    "ContainerClass",
    "InstanceClass",
    "LimitingSet",
    "Problem",
    "ProcessClass",
    "System",
    "WorkloadSeries",
]
