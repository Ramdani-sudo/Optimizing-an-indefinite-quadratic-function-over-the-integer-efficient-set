from __future__ import annotations

import math
import numpy as np

from ..config import SolverConfig
from ..instance import OQPESInstance
from ..results import MethodResult
from ..solver import MilpBuilder, SolverSession, add_base_x_model
from .common import efficiency_test, integerize_solution


def _solve_linear(instance: OQPESInstance, session: SolverSession, objective: np.ndarray, *, maximize: bool, upper_q: tuple[np.ndarray, int] | None = None):
    model = MilpBuilder()
    xidx = add_base_x_model(model, instance.A, instance.b, instance.lb, instance.ub, objective=objective)
    if upper_q is not None:
        q, rhs = upper_q
        model.add_le({xidx[j]: float(q[j]) for j in range(instance.n) if q[j] != 0}, float(rhs))
    return session.solve(model, kind="ILP", maximize=maximize)


def _add_nogood(model: MilpBuilder, xidx: list[int], instance: OQPESInstance, point: np.ndarray) -> None:
    selectors: list[int] = []
    for j in range(instance.n):
        v = int(point[j])
        if v > int(instance.lb[j]):
            lo = model.add_var(lb=0, ub=1, obj=0, integer=True)
            M = int(instance.ub[j]) - v + 1
            # lo=1 -> x_j <= v-1; lo=0 -> x_j <= ub_j
            model.add_le({xidx[j]: 1.0, lo: float(M)}, float(instance.ub[j]))
            selectors.append(lo)
        if v < int(instance.ub[j]):
            hi = model.add_var(lb=0, ub=1, obj=0, integer=True)
            M = v + 1 - int(instance.lb[j])
            # hi=1 -> x_j >= v+1; hi=0 -> x_j >= lb_j
            model.add_ge({xidx[j]: 1.0, hi: -float(M)}, float(instance.lb[j]))
            selectors.append(hi)
    if not selectors:
        # Only one feasible box point exists; an impossible row makes the model infeasible.
        model.add_ge({}, 1.0)
    else:
        model.add_ge({k: 1.0 for k in selectors}, 1.0)


def _enumerate_rank_exact(instance: OQPESInstance, session: SolverSession, q: np.ndarray, level: int, first: np.ndarray):
    """Enumerate all solutions with q'x = level using exact no-good MILPs/ILPs.

    These extra calls reproduce the mathematical rank set, but they are implementation-specific
    because the published paper enumerates alternate optima from the final simplex tableau.
    """
    found = [first.copy()]
    extra_calls = 0
    while True:
        model = MilpBuilder()
        xidx = add_base_x_model(model, instance.A, instance.b, instance.lb, instance.ub)
        model.add_eq({xidx[j]: float(q[j]) for j in range(instance.n) if q[j] != 0}, float(level))
        for point in found:
            _add_nogood(model, xidx, instance, point)
        r = session.solve(model, kind="ILP", maximize=True)
        extra_calls += 1
        if r.status == "INFEASIBLE":
            return "OPTIMAL", found, extra_calls
        if r.status != "OPTIMAL" or r.x is None:
            return r.status, found, extra_calls
        x = integerize_solution(r.x, instance.n)
        if any(np.array_equal(x, z) for z in found):
            return "ERROR", found, extra_calls
        found.append(x)


def _next_rank(instance: OQPESInstance, session: SolverSession, q: np.ndarray, upper_level: int | None, tie_backend: str):
    model = MilpBuilder()
    xidx = add_base_x_model(model, instance.A, instance.b, instance.lb, instance.ub, objective=q)
    if upper_level is not None:
        model.add_le({xidx[j]: float(q[j]) for j in range(instance.n) if q[j] != 0}, float(upper_level))
    r = session.solve(model, kind="ILP", maximize=True)
    if r.status != "OPTIMAL" or r.x is None:
        return r.status, None, [], 0, r
    x = integerize_solution(r.x, instance.n)
    level = int(q @ x)
    if tie_backend == "paper_declared_unique":
        return "OPTIMAL", level, [x], 0, r
    if tie_backend != "exact_no_good":
        return "ERROR", level, [x], 0, r
    st, points, extra = _enumerate_rank_exact(instance, session, q, level, x)
    return st, level, points, extra, r


def solve(instance: OQPESInstance, config: SolverConfig | None = None, *, tie_backend: str = "exact_no_good") -> MethodResult:
    cfg = config or SolverConfig()
    session = SolverSession(cfg)
    try:
        n = instance.n
        V = np.zeros(n, dtype=np.int64)
        core_ilp = 0
        tie_ilp = 0

        # Eq. (6): V_j = max x' Q_j.
        for j in range(n):
            r = _solve_linear(instance, session, instance.Q[:, j], maximize=True)
            core_ilp += 1
            if r.status == "TIME_LIMIT":
                return _finish(instance, session, cfg, "TIME_LIMIT", "time limit while constructing V", None, None, 0, 0, 0, core_ilp, tie_ilp, tie_backend)
            if r.status != "OPTIMAL" or r.x is None:
                return _finish(instance, session, cfg, r.status if r.status in {"INFEASIBLE", "ERROR"} else "ERROR", "failed while constructing V", None, None, 0, 0, 0, core_ilp, tie_ilp, tie_backend)
            x = integerize_solution(r.x, n)
            V[j] = int(instance.Q[:, j] @ x)

        q = V + instance.d

        # g_min.
        rg = _solve_linear(instance, session, q, maximize=False)
        core_ilp += 1
        if rg.status != "OPTIMAL" or rg.x is None:
            return _finish(instance, session, cfg, rg.status, "failed to compute g_min", None, None, 0, 0, 0, core_ilp, tie_ilp, tie_backend)
        xg = integerize_solution(rg.x, n)
        gmin_level = int(q @ xg)

        scanned: list[np.ndarray] = []
        hvals: list[float] = []
        current_level: int | None = None
        upper_level: int | None = None
        linear_ranks = quadratic_ranks = ranked_solutions = efficiency_tests = 0
        previous_h: float | None = None
        optimal_x: np.ndarray | None = None
        optimal_h: float | None = None

        def generate_one_rank():
            nonlocal current_level, upper_level, linear_ranks, ranked_solutions, core_ilp, tie_ilp
            st, level, pts, extra, raw = _next_rank(instance, session, q, upper_level, tie_backend)
            core_ilp += 1
            tie_ilp += extra
            if st != "OPTIMAL" or level is None:
                return st
            current_level = int(level)
            upper_level = current_level - 1
            linear_ranks += 1
            ranked_solutions += len(pts)
            for x in pts:
                scanned.append(x.copy())
                hvals.append(instance.phi(x))
            return "OPTIMAL"

        st = generate_one_rank()
        if st != "OPTIMAL":
            return _finish(instance, session, cfg, st, "failed to generate first linear rank", None, None, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions)

        while True:
            if session.remaining <= 0:
                return _finish(instance, session, cfg, "TIME_LIMIT", "common method-instance time limit", optimal_x, optimal_h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions)

            eligible = [h for h in hvals if previous_h is None or h < previous_h - 1e-9]
            while not eligible:
                if current_level is not None and current_level <= gmin_level:
                    return _finish(instance, session, cfg, "ERROR", "no lower quadratic rank exists before g_min", optimal_x, optimal_h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions)
                st = generate_one_rank()
                if st != "OPTIMAL":
                    return _finish(instance, session, cfg, st, "failed while seeking next quadratic rank", optimal_x, optimal_h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions)
                eligible = [h for h in hvals if previous_h is None or h < previous_h - 1e-9]

            candidate_h = max(eligible)
            # Algorithm 1 / Algorithm 9 stopping test: keep scanning while current g upper level can beat candidate_h.
            while (current_level + instance.alpha) > candidate_h + 1e-9 and current_level > gmin_level:
                st = generate_one_rank()
                if st != "OPTIMAL":
                    return _finish(instance, session, cfg, st, "failed during linear-rank certification", optimal_x, optimal_h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions)
                eligible = [h for h in hvals if previous_h is None or h < previous_h - 1e-9]
                candidate_h = max(eligible)

            quadratic_ranks += 1
            Tk = [x for x, h in zip(scanned, hvals) if abs(h - candidate_h) <= 1e-9]
            efficient_members: list[np.ndarray] = []
            for x in Tk:
                st_eff, eff, witness, er = efficiency_test(instance, x, session)
                efficiency_tests += 1
                if st_eff != "OPTIMAL":
                    return _finish(instance, session, cfg, st_eff, "efficiency test did not finish", optimal_x, optimal_h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions)
                if eff:
                    efficient_members.append(x.copy())
            if efficient_members:
                optimal_x = efficient_members[0]
                optimal_h = float(candidate_h)
                return _finish(instance, session, cfg, "OPTIMAL", "first quadratic rank containing an efficient solution", optimal_x, optimal_h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions, V=V, q=q, gmin_level=gmin_level)
            previous_h = float(candidate_h)
    except Exception as exc:
        return _finish(instance, session, cfg, "ERROR", repr(exc), None, None, 0, 0, 0, 0, 0, tie_backend)


def _finish(instance, session, cfg, status, reason, x, h, linear_ranks, quadratic_ranks, efficiency_tests, core_ilp, tie_ilp, tie_backend, ranked_solutions=0, **extra):
    c = session.counters
    comparison_safe = tie_backend != "exact_no_good" or tie_ilp == 0
    metadata = {
        "paper_core_ILP_calls": core_ilp,
        "implementation_tie_ILP_calls": tie_ilp,
        "paper_core_SP": core_ilp + c.MILP_calls,
        "tie_backend": tie_backend,
        "solver_calls": session.calls,
    }
    metadata.update({k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in extra.items()})
    return MethodResult(
        method="PRERNA_SHARMA_2024",
        status=status if status in {"OPTIMAL", "TIME_LIMIT", "INFEASIBLE", "ERROR", "INVALID"} else "ERROR",
        termination_reason=reason,
        objective_value=None if h is None else float(h),
        solution_vector=None if x is None else np.asarray(x, dtype=int).tolist(),
        criterion_vector=None if x is None else instance.criteria(x).astype(int).tolist(),
        wall_time=session.wall_time,
        cpu_time=session.cpu_time,
        LP_calls=c.LP_calls, ILP_calls=c.ILP_calls, MILP_calls=c.MILP_calls, SP=c.SP,
        iterations=linear_ranks + quadratic_ranks,
        efficiency_tests=efficiency_tests,
        linear_ranks=linear_ranks,
        quadratic_ranks=quadratic_ranks,
        ranked_solutions=ranked_solutions,
        solver_seed=cfg.random_seed,
        comparison_safe=comparison_safe,
        metadata=metadata,
    )
