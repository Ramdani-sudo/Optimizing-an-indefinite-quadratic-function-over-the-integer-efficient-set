from __future__ import annotations

import math
import os
import time
import warnings
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix

from .config import SolverConfig
from .results import CallCounters

# Keep numerical libraries single-threaded as well as HiGHS itself.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")


@dataclass
class SolveResult:
    status: str
    message: str
    x: np.ndarray | None
    objective: float | None
    raw_status: int | None = None


class MilpBuilder:
    def __init__(self) -> None:
        self.obj: list[float] = []
        self.lb: list[float] = []
        self.ub: list[float] = []
        self.integrality: list[int] = []
        self.rows: list[dict[int, float]] = []
        self.row_lb: list[float] = []
        self.row_ub: list[float] = []

    @property
    def nvars(self) -> int:
        return len(self.obj)

    def add_var(self, *, lb: float = 0.0, ub: float = math.inf, obj: float = 0.0, integer: bool = False) -> int:
        idx = self.nvars
        self.obj.append(float(obj))
        self.lb.append(float(lb))
        self.ub.append(float(ub))
        self.integrality.append(1 if integer else 0)
        return idx

    def add_constraint(self, coeffs: dict[int, float] | Iterable[tuple[int, float]], *, lb: float = -math.inf, ub: float = math.inf) -> None:
        if not isinstance(coeffs, dict):
            coeffs = dict(coeffs)
        row = {int(k): float(v) for k, v in coeffs.items() if abs(float(v)) > 0.0}
        self.rows.append(row)
        self.row_lb.append(float(lb))
        self.row_ub.append(float(ub))

    def add_eq(self, coeffs, rhs: float) -> None:
        self.add_constraint(coeffs, lb=rhs, ub=rhs)

    def add_le(self, coeffs, rhs: float) -> None:
        self.add_constraint(coeffs, ub=rhs)

    def add_ge(self, coeffs, rhs: float) -> None:
        self.add_constraint(coeffs, lb=rhs)

    def _matrix(self):
        if not self.rows:
            return coo_matrix((0, self.nvars)).tocsc()
        rr, cc, vv = [], [], []
        for i, row in enumerate(self.rows):
            for j, value in row.items():
                rr.append(i); cc.append(j); vv.append(value)
        return coo_matrix((vv, (rr, cc)), shape=(len(self.rows), self.nvars)).tocsc()


class SolverSession:
    def __init__(self, config: SolverConfig):
        self.config = config
        self.counters = CallCounters()
        self.started_wall = time.perf_counter()
        self.started_cpu = time.process_time()
        self.calls: list[dict] = []

    @property
    def wall_time(self) -> float:
        return time.perf_counter() - self.started_wall

    @property
    def cpu_time(self) -> float:
        return time.process_time() - self.started_cpu

    @property
    def remaining(self) -> float:
        return max(0.0, self.config.time_limit - self.wall_time)

    def solve(self, model: MilpBuilder, *, kind: str, maximize: bool = True) -> SolveResult:
        if self.remaining <= 0:
            return SolveResult("TIME_LIMIT", "global method time limit reached before solver call", None, None)
        self.counters.add(kind)
        c = np.asarray(model.obj, dtype=float)
        c_solve = -c if maximize else c
        A = model._matrix()
        constraints = LinearConstraint(A, np.asarray(model.row_lb), np.asarray(model.row_ub))
        bounds = Bounds(np.asarray(model.lb), np.asarray(model.ub))
        options = {
            "disp": False,
            "presolve": self.config.presolve,
            "time_limit": float(self.remaining),
            "mip_rel_gap": float(self.config.mip_rel_gap),
            # scipy passes unknown options to HiGHS verbatim.
            "mip_abs_gap": float(self.config.mip_abs_gap),
            "threads": int(self.config.threads),
            "random_seed": int(self.config.random_seed),
        }
        t0 = time.perf_counter()
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message="Unrecognized options detected.*")
                res = milp(
                    c=c_solve,
                    integrality=np.asarray(model.integrality, dtype=np.uint8),
                    bounds=bounds,
                    constraints=constraints,
                    options=options,
                )
        except Exception as exc:
            self.calls.append({"kind": kind, "status": "ERROR", "seconds": time.perf_counter() - t0})
            return SolveResult("ERROR", repr(exc), None, None)
        elapsed = time.perf_counter() - t0
        msg = str(getattr(res, "message", ""))
        status_code = int(getattr(res, "status", 4))
        if status_code == 0:
            status = "OPTIMAL"
        elif status_code == 1:
            status = "TIME_LIMIT" if "time" in msg.lower() else "TIME_LIMIT"
        elif status_code == 2:
            status = "INFEASIBLE"
        else:
            status = "ERROR"
        x = None if getattr(res, "x", None) is None else np.asarray(res.x, dtype=float)
        objective = None
        if x is not None:
            objective = float(c @ x)
        self.calls.append({"kind": kind, "status": status, "seconds": elapsed, "raw_status": status_code})
        return SolveResult(status, msg, x, objective, status_code)


def add_base_x_model(model: MilpBuilder, A: np.ndarray, b: np.ndarray, lb: np.ndarray, ub: np.ndarray, *, objective: np.ndarray | None = None) -> list[int]:
    n = len(lb)
    x_idx = [
        model.add_var(lb=float(lb[j]), ub=float(ub[j]), obj=0.0 if objective is None else float(objective[j]), integer=True)
        for j in range(n)
    ]
    for i in range(A.shape[0]):
        model.add_le({x_idx[j]: float(A[i, j]) for j in range(n) if A[i, j] != 0}, float(b[i]))
    return x_idx
