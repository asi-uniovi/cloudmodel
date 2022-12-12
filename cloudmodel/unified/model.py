# coding: utf-8
"""This module implements the base dataclasses which define a
problem to be solved by Malloovia, and the solution
"""

from dataclasses import dataclass
from typing import Tuple
from ..util import simplified_repr
from .. import __version__


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
        time_unit:str: unit of time for the timeslot (y, h, m , s)
        timeslot_length:float: duration of the timeslot (1 by default)
        intra_slot_distribution:str: name of the distribution for the
           interarrival times of the requests ("exponential" by default)
    """

    description: str
    values: Tuple[float, ...]
    time_unit: str  # "y", "h", "m", or "s"
    timeslot_length: float = 1.0
    intra_slot_distribution: str = "exponential"


@dataclass(frozen=True)
class Workload:
    """Workload for a single timeslot (to be deprecated, redundant with WorkloadSeries)

    Attributes:
        value:float: average number of requests arriving globally at the timeslot
        app:App: application to which the requests are addressed
        time_unit:str: unit of time for the timeslot (y, h, m , s)
        timeslot_length:float: duration of the timeslot (1 by default)
        intra_slot_distribution:str: name of the distribution for the
           interarrival times of the requests ("exponential" by default)
    """

    value: float
    time_unit: str
    timeslot_length: float = 1.0
    intra_slot_distribution: str = "exponential"


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
    max_cores: int = 0


@simplified_repr("name", "price", "cores", "mem")
@dataclass(frozen=True)
class InstanceClass:
    """InstanceClass characterization

    Attributes:
        name:str: name of the instance class, usually built from the name of the VM type
             and the name of the limiting set in which it is deployed.
        price:float: dollar per time unit
        time_unit:str:  - time unit for the price ("y", "h", "m", or "s").
        cores:float:  millicores available in the VM
        mem:float: GiB available in the VM
        limit:int: maximum number of VMs (0 means "no limit")
        limiting_sets:set[LimitingSet]: LimitingSet to which this instance class belongs.
        is_reserved:bool: True if the instance is reserved
        is_private:bool: True if this instance class belongs to a private cloud
    """

    name: str
    price: float
    time_unit: str
    cores: float
    mem: float
    limit: int
    limiting_sets: Tuple[LimitingSet]
    is_reserved: bool = False
    is_private: bool = False

    def __post_init__(self) -> None:
        if self.cores < 0 or self.cores > 1e9 or self.cores != self.cores:  # nan
            object.__setattr__(
                self, "cores", 0.0
            )  # Silently set to zero if the number of millicores is not valid
            # raise ValueError(f"Wrong number of millicores {self.cores}, must be between 0 and 1E9")


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
    cores: float
    mem: float
    app: App
    limit: int


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
        apps:list[App]: List of applications to be deployed
        ics:list[InstanceClass]: List of instance classes (cloud infrastructure)
        ccs:list[ContainerClass]: List of containers classes (runtime for apps)
        perfs:dict[tuple[InstanceClass, ContainerClass|ProcessClass], float]:
           Performance in requests-per-time-unit for each pair (InstanceClass, ContainerClass)
        time_unit:str: time unit for the performances (h, m , s)
    """

    name: str
    ics: list[InstanceClass]
    ccs: list[ContainerClass]
    perfs: dict[Tuple[InstanceClass, ContainerClass | ProcessClass | None, App], float]
    time_unit: str


@simplified_repr("name", "system", "version")
@dataclass(frozen=True)
class Problem:
    """Problem description.

    Attributes:
        name:str: name of the problem
        workloads:tuple["Workload", ...]:  Tuple of workloads, one per application.
        instance_classes:tuple["InstanceClass", ...]: Infrastructure of VMs
           in which deploy the apps
        performances:PerformanceSet: Object describing the performance of each
           instance class for each kind of application.
        description:str: Optional description for the problem
    """

    name: str
    system: System
    workloads: dict[App, WorkloadSeries]
    version: str = __version__


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
