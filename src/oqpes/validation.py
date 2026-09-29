from __future__ import annotations

import itertools
import math
import numpy as np

from .instance import OQPESInstance


def exhaustive_optimum(instance: OQPESInstance, *, max_points: int = 2_000_000):
    sizes = [int(u - l + 1) for l, u in zip(instance.lb, instance.ub)]
    total_box = math.prod(sizes)
    if total_box > max_points:
        raise ValueError(f"box too large for independent validation: {total_box}")
    feasible: list[np.ndarray] = []
    for tpl in itertools.product(*(range(int(l), int(u) + 1) for l, u in zip(instance.lb, instance.ub))):
        x = np.asarray(tpl, dtype=np.int64)
        if np.all(instance.A @ x <= instance.b):
            feasible.append(x)
    if not feasible:
        return None
    efficient: list[np.ndarray] = []
    ys = [instance.criteria(x) for x in feasible]
    for i, x in enumerate(feasible):
        y = ys[i]
        dominated = False
        for j, z in enumerate(ys):
            if i != j and np.all(z >= y) and np.any(z > y):
                dominated = True
                break
        if not dominated:
            efficient.append(x)
    values = [instance.phi(x) for x in efficient]
    best = max(values)
    opts = [x for x, v in zip(efficient, values) if abs(v - best) <= 1e-9]
    return {
        "objective": float(best),
        "solutions": [x.tolist() for x in opts],
        "num_feasible": len(feasible),
        "num_efficient": len(efficient),
    }
