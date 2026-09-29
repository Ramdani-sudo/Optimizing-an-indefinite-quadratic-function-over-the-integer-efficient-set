from oqpes.config import SolverConfig
from oqpes.instance import published_example_51
from oqpes.methods.prerna_sharma_2024 import solve


def test_published_example_paper_declared_unique():
    inst = published_example_51()
    r = solve(inst, SolverConfig(time_limit=20), tie_backend="paper_declared_unique")
    assert r.status == "OPTIMAL", r.termination_reason
    assert r.solution_vector == [0, 10]
    assert r.objective_value == 820
    assert r.linear_ranks == 24
    assert r.quadratic_ranks == 7
    assert r.efficiency_tests == 7
    assert r.LP_calls == 0
    assert r.ILP_calls == 27
    assert r.MILP_calls == 7
    assert r.SP == 34
    assert r.metadata["paper_core_SP"] == 34


def test_published_example_exact_nogood_same_optimum():
    inst = published_example_51()
    r = solve(inst, SolverConfig(time_limit=20), tie_backend="exact_no_good")
    assert r.status == "OPTIMAL", r.termination_reason
    assert r.solution_vector == [0, 10]
    assert r.objective_value == 820
    assert r.metadata["paper_core_SP"] == 34
    assert r.metadata["implementation_tie_ILP_calls"] >= 24
    assert r.SP > 34
    assert r.comparison_safe is False
