from __future__ import annotations

import math
import numpy as np

from ..instance import OQPESInstance
from ..solver import MilpBuilder, SolverSession, add_base_x_model


def integerize_solution(x: np.ndarray, n: int, tol: float = 1e-6) -> np.ndarray:
    xv = np.rint(np.asarray(x[:n], dtype=float)).astype(np.int64)
    if np.max(np.abs(np.asarray(x[:n]) - xv)) > tol:
        raise ValueError("solver returned a nonintegral integer-variable solution")
    return xv


def efficiency_test(instance: OQPESInstance, candidate: np.ndarray, session: SolverSession):
    """Isermann-style exact efficiency test for a maximization MOILP.

    max sum psi_i
    s.t. C_i x - psi_i = C_i candidate, x in X, psi>=0.
    """
    y = instance.criteria(candidate)
    model = MilpBuilder()
    xidx = add_base_x_model(model, instance.A, instance.b, instance.lb, instance.ub)
    psi = [model.add_var(lb=0.0, ub=math.inf, obj=1.0, integer=False) for _ in range(instance.p)]
    for i in range(instance.p):
        row = {xidx[j]: float(instance.C[i, j]) for j in range(instance.n) if instance.C[i, j] != 0}
        row[psi[i]] = -1.0
        model.add_eq(row, float(y[i]))
    result = session.solve(model, kind="MILP", maximize=True)
    if result.status != "OPTIMAL":
        return result.status, False, None, result
    efficient = bool(result.objective is not None and result.objective <= 1e-7)
    witness = None if result.x is None else integerize_solution(result.x, instance.n)
    return "OPTIMAL", efficient, witness, result


def criterion_lower_bounds(instance: OQPESInstance) -> np.ndarray:
    mins = np.zeros(instance.p, dtype=np.int64)
    for i in range(instance.p):
        s = 0
        for j, c in enumerate(instance.C[i]):
            s += int(c) * int(instance.lb[j] if c >= 0 else instance.ub[j])
        mins[i] = s
    return mins
