import numpy as np

from oqpes.config import SolverConfig
from oqpes.solver import MilpBuilder, SolverSession


def test_highs_scipy_ilp_wrapper():
    m = MilpBuilder()
    x = m.add_var(lb=0, ub=10, obj=1, integer=True)
    y = m.add_var(lb=0, ub=10, obj=2, integer=True)
    m.add_le({x: 1, y: 1}, 4)
    s = SolverSession(SolverConfig(time_limit=5))
    r = s.solve(m, kind="ILP", maximize=True)
    assert r.status == "OPTIMAL"
    assert abs(r.objective - 8) < 1e-7
    assert s.counters.ILP_calls == 1
    assert s.counters.SP == 1
