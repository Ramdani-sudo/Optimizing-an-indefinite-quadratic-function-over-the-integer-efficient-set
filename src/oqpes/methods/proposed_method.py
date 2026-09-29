from __future__ import annotations

from dataclasses import dataclass, field
import math
import time
import numpy as np

from ..config import SolverConfig
from ..instance import OQPESInstance
from ..results import MethodResult
from ..solver import MilpBuilder, SolverSession, add_base_x_model
from .common import criterion_lower_bounds, efficiency_test, integerize_solution


@dataclass
class SquareTerm:
    coeff: int
    projection: dict[int, int]
    L: int
    U: int
    segments: list[tuple[int, int]] = field(default_factory=list)
    tangents: set[int] = field(default_factory=set)


def _projection_bounds(v: dict[int, int], lb: np.ndarray, ub: np.ndarray) -> tuple[int, int]:
    lo = 0
    hi = 0
    for j, a in v.items():
        if a >= 0:
            lo += a * int(lb[j]); hi += a * int(ub[j])
        else:
            lo += a * int(ub[j]); hi += a * int(lb[j])
    return int(lo), int(hi)


def decompose_quadratic(instance: OQPESInstance) -> list[SquareTerm]:
    """Exact integer square decomposition.

    x'Qx = sum_i a_i x_i^2 + sum_{i<j} Q_ij (x_i+x_j)^2,
    where a_i = Q_ii - sum_{j!=i} Q_ij.
    """
    Q = instance.Q
    diag = np.diag(Q).astype(np.int64).copy()
    terms: list[SquareTerm] = []
    for i in range(instance.n):
        for j in range(i + 1, instance.n):
            q = int(Q[i, j])
            if q:
                diag[i] -= q
                diag[j] -= q
                v = {i: 1, j: 1}
                L, U = _projection_bounds(v, instance.lb, instance.ub)
                terms.append(SquareTerm(q, v, L, U, segments=[(L, U)] if q > 0 else []))
    for i in range(instance.n):
        a = int(diag[i])
        if a:
            v = {i: 1}
            L, U = _projection_bounds(v, instance.lb, instance.ub)
            terms.append(SquareTerm(a, v, L, U, segments=[(L, U)] if a > 0 else []))
    return terms


def _square_value(a: int, t: int) -> int:
    return int(a * t * t)


def _term_true(term: SquareTerm, x: np.ndarray) -> int:
    t = sum(a * int(x[j]) for j, a in term.projection.items())
    return _square_value(term.coeff, t)


def _add_dominance_cut(model: MilpBuilder, xidx: list[int], instance: OQPESInstance, y: np.ndarray, minC: np.ndarray) -> None:
    z = [model.add_var(lb=0, ub=1, obj=0, integer=True) for _ in range(instance.p)]
    for i in range(instance.p):
        M = max(0, int(y[i]) + 1 - int(minC[i]))
        row = {xidx[j]: float(instance.C[i, j]) for j in range(instance.n) if instance.C[i, j] != 0}
        if M:
            row[z[i]] = -float(M)
        model.add_ge(row, float(int(y[i]) + 1 - M))
    model.add_ge({k: 1.0 for k in z}, 1.0)


def _build_master(instance: OQPESInstance, terms: list[SquareTerm], dominance_cuts: list[np.ndarray]) -> tuple[MilpBuilder, list[int]]:
    model = MilpBuilder()
    xidx = add_base_x_model(model, instance.A, instance.b, instance.lb, instance.ub, objective=instance.d)
    minC = criterion_lower_bounds(instance)
    for y in dominance_cuts:
        _add_dominance_cut(model, xidx, instance, y, minC)

    for term in terms:
        a = term.coeff
        vals = [_square_value(a, term.L), _square_value(a, term.U)]
        if term.L <= 0 <= term.U:
            vals.append(0)
        zlb = float(min(vals))
        zub = float(max(vals))
        zidx = model.add_var(lb=zlb, ub=zub, obj=1.0, integer=False)
        vrow = {xidx[j]: float(coef) for j, coef in term.projection.items()}
        if a > 0:
            segs = term.segments
            if len(segs) == 1:
                l, u = segs[0]
                slope = a * (l + u)
                intercept = -a * l * u
                row = {zidx: 1.0}
                for j, coef in vrow.items():
                    row[j] = row.get(j, 0.0) - slope * coef
                model.add_le(row, float(intercept))
            else:
                delta = [model.add_var(lb=0, ub=1, obj=0, integer=True) for _ in segs]
                model.add_eq({k: 1.0 for k in delta}, 1.0)
                global_ub = zub
                for ds, (l, u) in zip(delta, segs):
                    # t >= L + (l-L)*delta
                    row_lo = dict(vrow)
                    row_lo[ds] = row_lo.get(ds, 0.0) - float(l - term.L)
                    model.add_ge(row_lo, float(term.L))
                    # t <= U - (U-u)*delta
                    row_hi = dict(vrow)
                    row_hi[ds] = row_hi.get(ds, 0.0) + float(term.U - u)
                    model.add_le(row_hi, float(term.U))
                    slope = a * (l + u)
                    intercept = -a * l * u
                    # M valid over full projection interval.
                    sec_L = slope * term.L + intercept
                    sec_U = slope * term.U + intercept
                    min_sec = min(sec_L, sec_U)
                    M = max(0.0, global_ub - float(min_sec))
                    row = {zidx: 1.0, ds: M}
                    for j, coef in vrow.items():
                        row[j] = row.get(j, 0.0) - slope * coef
                    model.add_le(row, float(intercept) + M)
        else:
            # Concave term: constant global upper bound + globally valid tangents.
            model.add_le({zidx: 1.0}, zub)
            for r in sorted(term.tangents):
                slope = 2 * a * r
                intercept = -a * r * r
                row = {zidx: 1.0}
                for j, coef in vrow.items():
                    row[j] = row.get(j, 0.0) - slope * coef
                model.add_le(row, float(intercept))
    return model, xidx


def _refine_at(terms: list[SquareTerm], x: np.ndarray) -> int:
    refined = 0
    for term in terms:
        t = int(sum(a * int(x[j]) for j, a in term.projection.items()))
        if term.coeff > 0:
            for k, (l, u) in enumerate(list(term.segments)):
                if l <= t <= u:
                    if l < t < u:
                        new = [(l, t)]
                        if t + 1 <= u:
                            new.append((t + 1, u))
                        term.segments[k:k + 1] = new
                        refined += 1
                    break
        else:
            if t not in term.tangents:
                term.tangents.add(t)
                refined += 1
    return refined


def solve(instance: OQPESInstance, config: SolverConfig | None = None) -> MethodResult:
    cfg = config or SolverConfig()
    session = SolverSession(cfg)
    try:
        terms = decompose_quadratic(instance)
        cuts: list[np.ndarray] = []
        incumbent_x: np.ndarray | None = None
        incumbent_phi = -math.inf
        iterations = refinements = efficiency_tests = 0
        max_iterations = 100000
        for _ in range(max_iterations):
            iterations += 1
            if session.remaining <= 0:
                status = "TIME_LIMIT"
                reason = "common method-instance time limit"
                break
            model, xidx = _build_master(instance, terms, cuts)
            master = session.solve(model, kind="MILP", maximize=True)
            if master.status == "TIME_LIMIT":
                status, reason = "TIME_LIMIT", "master MILP time limit"
                break
            if master.status == "INFEASIBLE":
                if incumbent_x is not None:
                    status, reason = "OPTIMAL", "all remaining master regions eliminated"
                else:
                    status, reason = "INFEASIBLE", "master infeasible before any efficient incumbent"
                break
            if master.status != "OPTIMAL" or master.x is None:
                status, reason = "ERROR", f"master solver failure: {master.message}"
                break
            x = integerize_solution(master.x, instance.n)
            phi = instance.phi(x)
            ub_master = float(master.objective + instance.alpha)

            # A previously known efficient incumbent is globally optimal once the valid master UB cannot improve it.
            if incumbent_x is not None and ub_master <= incumbent_phi + 1e-7:
                status, reason = "OPTIMAL", "valid master upper bound closed the optimality gap"
                break

            et_status, efficient, witness, et_res = efficiency_test(instance, x, session)
            efficiency_tests += 1
            if et_status == "TIME_LIMIT":
                status, reason = "TIME_LIMIT", "efficiency-test time limit"
                break
            if et_status != "OPTIMAL":
                status, reason = "ERROR", f"efficiency test failed: {et_res.message}"
                break

            if efficient:
                if phi > incumbent_phi:
                    incumbent_phi = phi
                    incumbent_x = x.copy()
            else:
                y = instance.criteria(x)
                if not any(np.array_equal(y, old) for old in cuts):
                    cuts.append(y.copy())

            added = _refine_at(terms, x)
            refinements += added

            # If this efficient candidate is exact for the current master, it attains the valid global UB.
            if efficient and abs(ub_master - phi) <= 1e-7:
                status, reason = "OPTIMAL", "efficient candidate attains the global master upper bound"
                break
        else:
            status, reason = "ERROR", "iteration safeguard reached"

        c = session.counters
        return MethodResult(
            method="PROPOSED_METHOD",
            status=status,
            termination_reason=reason,
            objective_value=None if incumbent_x is None else float(incumbent_phi),
            solution_vector=None if incumbent_x is None else incumbent_x.astype(int).tolist(),
            criterion_vector=None if incumbent_x is None else instance.criteria(incumbent_x).astype(int).tolist(),
            wall_time=session.wall_time,
            cpu_time=session.cpu_time,
            LP_calls=c.LP_calls, ILP_calls=c.ILP_calls, MILP_calls=c.MILP_calls, SP=c.SP,
            iterations=iterations,
            cuts=len(cuts), refinements=refinements, efficiency_tests=efficiency_tests,
            solver_seed=cfg.random_seed,
            metadata={"square_terms": len(terms), "solver_calls": session.calls},
        )
    except Exception as exc:
        c = session.counters
        return MethodResult(
            method="PROPOSED_METHOD", status="ERROR", termination_reason=repr(exc),
            wall_time=session.wall_time, cpu_time=session.cpu_time,
            LP_calls=c.LP_calls, ILP_calls=c.ILP_calls, MILP_calls=c.MILP_calls, SP=c.SP,
            solver_seed=cfg.random_seed,
        )
