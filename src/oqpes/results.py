from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_STATUSES = {"OPTIMAL", "TIME_LIMIT", "INFEASIBLE", "ERROR", "INVALID"}


@dataclass
class CallCounters:
    LP_calls: int = 0
    ILP_calls: int = 0
    MILP_calls: int = 0

    def add(self, kind: str) -> None:
        if kind == "LP":
            self.LP_calls += 1
        elif kind == "ILP":
            self.ILP_calls += 1
        elif kind == "MILP":
            self.MILP_calls += 1
        else:
            raise ValueError(f"Unknown call type: {kind}")

    @property
    def SP(self) -> int:
        return self.LP_calls + self.ILP_calls + self.MILP_calls


@dataclass
class MethodResult:
    method: str
    status: str
    termination_reason: str
    objective_value: float | None = None
    solution_vector: list[int] | None = None
    criterion_vector: list[int] | None = None
    wall_time: float = 0.0
    cpu_time: float = 0.0
    LP_calls: int = 0
    ILP_calls: int = 0
    MILP_calls: int = 0
    SP: int = 0
    iterations: int = 0
    cuts: int = 0
    refinements: int = 0
    efficiency_tests: int = 0
    linear_ranks: int = 0
    quadratic_ranks: int = 0
    ranked_solutions: int = 0
    solver: str = "HiGHS via scipy.optimize.milp"
    solver_seed: int = 0
    comparison_safe: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status {self.status}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
