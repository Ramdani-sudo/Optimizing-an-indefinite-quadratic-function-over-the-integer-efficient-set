import numpy as np

from oqpes.config import SolverConfig
from oqpes.instance import OQPESInstance, published_example_51
from oqpes.methods.proposed_method import decompose_quadratic, solve
from oqpes.validation import exhaustive_optimum


def _small_instance():
    A = np.array([[1, 1], [2, 1]], dtype=np.int64)
    b = np.array([5, 7], dtype=np.int64)
    C = np.array([[1, 2], [3, -1]], dtype=np.int64)
    Q = np.array([[2, -3], [-3, -1]], dtype=np.int64)
    d = np.array([1, 4], dtype=np.int64)
    return OQPESInstance(A, b, C, Q, d, 0.0, np.array([0, 0]), np.array([3, 5]), 2, 2, 2)


def test_square_decomposition_exact():
    inst = _small_instance()
    terms = decompose_quadratic(inst)
    for x0 in range(4):
        for x1 in range(6):
            x = np.array([x0, x1], dtype=np.int64)
            lhs = int(x @ inst.Q @ x)
            rhs = 0
            for t in terms:
                proj = sum(a * int(x[j]) for j, a in t.projection.items())
                rhs += t.coeff * proj * proj
            assert lhs == rhs


def test_proposed_matches_exhaustive_small():
    inst = _small_instance()
    truth = exhaustive_optimum(inst)
    r = solve(inst, SolverConfig(time_limit=20))
    assert r.status == "OPTIMAL", r.termination_reason
    assert r.objective_value == truth["objective"]
    assert r.solution_vector in truth["solutions"]
    assert r.SP == r.LP_calls + r.ILP_calls + r.MILP_calls


def test_proposed_on_published_example():
    inst = published_example_51()
    truth = exhaustive_optimum(inst)
    r = solve(inst, SolverConfig(time_limit=20))
    assert r.status == "OPTIMAL", r.termination_reason
    assert r.objective_value == truth["objective"] == 820
