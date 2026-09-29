from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolverConfig:
    time_limit: float = 60.0
    threads: int = 1
    presolve: bool = True
    mip_rel_gap: float = 0.0
    mip_abs_gap: float = 0.0
    random_seed: int = 0
    feasibility_tol: float = 1e-9
    integrality_tol: float = 1e-9


PUBLISHED_P_VALUES = (5, 10, 20, 50)
PUBLISHED_N_VALUES = (10, 20, 50)
PUBLISHED_M_VALUES = (10, 20, 30, 50)
PUBLISHED_CONFIGS = tuple(
    (p, n, m)
    for p in PUBLISHED_P_VALUES
    for n in PUBLISHED_N_VALUES
    for m in PUBLISHED_M_VALUES
)


def deterministic_seed(p: int, n: int, m: int, rep: int) -> int:
    if not (1 <= rep <= 99):
        raise ValueError("rep must lie in 1..99")
    return 100_000_000 + 1_000_000 * p + 10_000 * n + 100 * m + rep
