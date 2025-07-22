from typing import Union
from cloudmodel.unified import model
from pint import DimensionalityError, UndefinedUnitError
import pytest
from cloudmodel.unified.units import (
    ComputationalUnits,
    CurrencyPerTime,
    Requests,
    Time,
    RequestsPerTime,
    Storage,
    assert_approx,
)
from hypothesis import HealthCheck, given, reproduce_failure, settings, strategies as st

from .hypothesis_strategies import model_problem_strategy


@pytest.mark.property_testing
class TestPropertyTesting:
    @given(model_problem_strategy())
    @settings(
        max_examples=25, suppress_health_check=[HealthCheck.too_slow], print_blob=True
    )
    def test_model_creation(self, problem: model.Problem):
        """Check that all random problems created by the given strategy can be
        createwd without errors, and that the set of ics, ccs and apps inside
        the problem are consistent"""
        apps_from_workloads = set(app for app, region in problem.workloads)
        apps_from_performances = set(app for ic, cc, app in problem.system.perfs)
        apps_from_containers = set(c.app for c in problem.system.ccs if c is not None)

        assert apps_from_containers <= apps_from_performances
        assert apps_from_workloads <= apps_from_performances

        ics_from_performances = set(ic for ic, cc, app in problem.system.perfs)
        assert ics_from_performances <= set(problem.system.ics)

        ccs_from_performances = set(cc for ic, cc, app in problem.system.perfs)
        assert ccs_from_performances <= set(problem.system.ccs)

    @given(model_problem_strategy(), st.sampled_from(["hour", "minute", "second"]))
    @settings(
        max_examples=25, suppress_health_check=[HealthCheck.too_slow], print_blob=True
    )
    def test_model_normalization(self, problem: model.Problem, unit: str):
        """Check the fucntion normalize_time_units"""
        norm = model.normalize_time_units(problem, units=unit)

        # Now norm has all the times normalized as minutes, but the
        # quantities should match (it is neccesary to use assert_approx because
        # otherwise the == operator may fail due to float rounding errors)

        # Scheduling interval
        assert str(norm.sched_time_size.units) == unit
        assert_approx(norm.sched_time_size, problem.sched_time_size)

        # Prices
        for ic, icn in zip(problem.system.ics, norm.system.ics):
            assert str(icn.price.units) == f"usd / {unit}"
            assert_approx(ic.price, icn.price)

        # Performances
        for perf, perfn in zip(
            problem.system.perfs.values(), norm.system.perfs.values()
        ):
            assert str(perfn.value.units) == f"req / {unit}"
            assert_approx(perf.value, perfn.value)
            assert str(perfn.slo95.units) == unit
            assert_approx(perf.slo95, perfn.slo95)

        # Workloads
        for wl, wln in zip(problem.workloads.values(), norm.workloads.values()):
            assert str(wln.time_slot_size.units) == unit
            assert_approx(wl.time_slot_size, wln.time_slot_size)

    @given(
        st.from_type(model.WorkloadSeries),
        st.sampled_from(["hour", "minute", "second"]),
    )
    @settings(
        max_examples=25,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
        print_blob=True,
    )
    def test_workloadSeries_scaling(self, wl_series: model.WorkloadSeries, unit: str):
        scaled = model.workloadSeries_scale(wl_series, to=Time(unit))
        assert scaled.description == wl_series.description
        assert scaled.intra_slot_distribution == wl_series.intra_slot_distribution
        assert scaled.time_slot_size.units == unit
        assert_approx(scaled.time_slot_size, wl_series.time_slot_size)
        assert len(scaled.values) == len(wl_series.values)
        for wl, wls in zip(scaled.values, wl_series.values):
            assert_approx(wl, wls)


@pytest.mark.units
class TestModelUnits:
    @staticmethod
    def test_bad_dimensionality_in_price():
        """Trying inappropriate units should raise an exception"""
        with pytest.raises(DimensionalityError):
            CurrencyPerTime("20 usd")

    @staticmethod
    def test_bad_dimensionality_in_cores():
        """Trying inappropriate units should raise an exception"""
        with pytest.raises(DimensionalityError):
            ComputationalUnits("2 liter")

    @staticmethod
    def test_bad_dimensionality_in_memory():
        """Trying inappropriate units should raise an exception"""
        with pytest.raises(DimensionalityError):
            Storage("2 cm")

    @staticmethod
    def test_bad_currency():
        """Trying inappropriate units should raise an exception"""
        with pytest.raises(UndefinedUnitError):
            CurrencyPerTime("20 eur / hour")

    @staticmethod
    def test_bad_dimensionality_in_performance():
        """Trying inappropriate units should raise an exception"""
        with pytest.raises(DimensionalityError):
            RequestsPerTime("20 req / cm")

    @staticmethod
    def test_time_conversion():
        t = Time("1h").to("minute")
        assert t.magnitude == 60

    # Conversion tests is to get 100% coverage, they are not really needed
    # since it is pint who makes the conversions
    @staticmethod
    def test_different_conversions():
        t = Time("1h").to("minute")
        assert t.magnitude == 60

        reqs = RequestsPerTime("1 req/s").to("req/min")
        assert reqs.magnitude == 60

        price = CurrencyPerTime("1 usd/min").to("usd/h")
        assert price.magnitude == 60

        cores = ComputationalUnits("1 cores").to("millicores")
        assert cores.magnitude == 1000


@pytest.mark.repr
class TestRepresentation:
    @staticmethod
    def test_repr_app():
        a = model.App("foo")
        assert repr(a) == "App('foo')"

    @staticmethod
    def test_repr_region():
        a = model.Region("Europe")
        assert repr(a) == "Region('Europe')"

    @staticmethod
    def test_repr_latency():
        a = model.Latency(Time("10ms"))
        assert repr(a) == "Latency(value='10 millisecond')"

    @staticmethod
    def test_repr_wl_series():
        wls = model.WorkloadSeries(
            description="foo",
            values=(Requests("1 req"), Requests("2 req")),
            time_slot_size=Time("1 s"),
            intra_slot_distribution="uniform",
        )
        assert (
            repr(wls) == "WorkloadSeries(description='foo', time_slot_size='1 second')"
        )

    @staticmethod
    def test_repr_wl():
        wl = model.Workload(
            value=Requests("20 req"),
            time_slot_size=Time("1 s"),
            intra_slot_distribution="uniform",
        )
        assert repr(wl) == "Workload(value='20 req', time_slot_size='1 second')"

    @staticmethod
    def test_repr_ls():
        ls = model.LimitingSet(
            name="foo", max_vms=0, max_cores=ComputationalUnits("200 cores")
        )
        assert repr(ls) == "LimitingSet(name='foo', max_vms=0, max_cores='200 core')"

    @staticmethod
    def test_repr_ic():
        ic = model.InstanceClass(
            name="foo",
            price=CurrencyPerTime("0.5 usd/h"),
            cores=ComputationalUnits("2 cores"),
            mem=Storage("4 GiB"),
            limit=0,
            limiting_sets=tuple(),
        )
        # name", "price", "cores", "mem"
        assert (
            repr(ic) == "InstanceClass(name='foo', price='0.5 usd / hour', "
            "cores='2 core', mem='4 gibibyte')"
        )

    @staticmethod
    def test_repr_cc():
        cc = model.ContainerClass(
            name="foo",
            cores=ComputationalUnits("1000 millicores"),
            mem=Storage("0.5 GiB"),
            app=model.App("bar"),
            limit=0,
        )
        assert (
            repr(cc) == "ContainerClass(name='foo', cores='1000 millicore', "
            "mem='0.5 gibibyte', app=App('bar'), limit=0)"
        )

    @staticmethod
    def test_repr_perf():
        perf = model.Performance(value=RequestsPerTime("1 req/s"), slo95=Time("10ms"))
        assert (
            repr(perf)
            == "Performance(value='1.0 req / second', slo95='10 millisecond')"
        )

    @staticmethod
    def test_repr_sys():
        sys = model.System(name="foo", ics=[], ccs=[], perfs={}, latencies={})
        assert repr(sys) == "System(name='foo')"

    @staticmethod
    def test_repr_problem():
        problem = model.Problem(
            name="foo",
            system=model.System("bar", [], [], {}, {}),
            workloads={},
            sched_time_size=Time("15 min"),
        )
        assert (
            repr(problem)
            == "Problem(name='foo', system=System(name='bar'), version='0.2.0')"
        )
