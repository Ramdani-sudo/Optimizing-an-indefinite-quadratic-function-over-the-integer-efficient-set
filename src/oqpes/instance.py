from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .config import deterministic_seed


@dataclass
class OQPESInstance:
    A: np.ndarray
    b: np.ndarray
    C: np.ndarray
    Q: np.ndarray
    d: np.ndarray
    alpha: float
    lb: np.ndarray
    ub: np.ndarray
    p: int
    n: int
    m: int
    rep: int = 0
    seed: int = 0
    accepted_attempt: int = 1
    generator_version: str = "PS2024-ranges-v2"

    def __post_init__(self) -> None:
        self.A = np.asarray(self.A, dtype=np.int64)
        self.b = np.asarray(self.b, dtype=np.int64).reshape(-1)
        self.C = np.asarray(self.C, dtype=np.int64)
        self.Q = np.asarray(self.Q, dtype=np.int64)
        self.d = np.asarray(self.d, dtype=np.int64).reshape(-1)
        self.lb = np.asarray(self.lb, dtype=np.int64).reshape(-1)
        self.ub = np.asarray(self.ub, dtype=np.int64).reshape(-1)
        self.alpha = float(self.alpha)
        self.validate()

    def validate(self) -> None:
        if self.A.shape != (self.m, self.n):
            raise ValueError("A has inconsistent shape")
        if self.b.shape != (self.m,):
            raise ValueError("b has inconsistent shape")
        if self.C.shape != (self.p, self.n):
            raise ValueError("C has inconsistent shape")
        if self.Q.shape != (self.n, self.n):
            raise ValueError("Q has inconsistent shape")
        if self.d.shape != (self.n,):
            raise ValueError("d has inconsistent shape")
        if self.lb.shape != (self.n,) or self.ub.shape != (self.n,):
            raise ValueError("bounds have inconsistent shape")
        if np.any(self.lb > self.ub):
            raise ValueError("invalid variable bounds")
        if not np.array_equal(self.Q, self.Q.T):
            raise ValueError("Q must be symmetric")
        if np.any(self.A < 0) or np.any(self.b < 0):
            raise ValueError("benchmark convention requires A>=0 and b>=0")
        if np.any(self.A @ self.lb > self.b):
            raise ValueError("lower-bound vector is infeasible")

    def phi(self, x: np.ndarray) -> float:
        x = np.asarray(x, dtype=np.int64)
        return float(x @ self.Q @ x + self.d @ x + self.alpha)

    def criteria(self, x: np.ndarray) -> np.ndarray:
        return self.C @ np.asarray(x, dtype=np.int64)

    def feasible(self, x: np.ndarray) -> bool:
        x = np.asarray(x, dtype=np.int64)
        return bool(
            x.shape == (self.n,)
            and np.all(x >= self.lb)
            and np.all(x <= self.ub)
            and np.all(self.A @ x <= self.b)
        )

    def digest(self) -> str:
        h = hashlib.sha256()
        for arr in (self.A, self.b, self.C, self.Q, self.d, self.lb, self.ub):
            h.update(np.ascontiguousarray(arr).tobytes())
            h.update(str(arr.shape).encode())
        h.update(repr(self.alpha).encode())
        return h.hexdigest()


def _derive_ub(A: np.ndarray, b: np.ndarray) -> np.ndarray | None:
    m, n = A.shape
    ub = np.empty(n, dtype=np.int64)
    for j in range(n):
        rows = np.flatnonzero(A[:, j] > 0)
        if rows.size == 0:
            return None
        ub[j] = min(int(b[i] // A[i, j]) for i in rows)
    return ub


def _strictly_indefinite(Q: np.ndarray) -> bool:
    eig = np.linalg.eigvalsh(Q.astype(float))
    tol = 1e-10 * max(1.0, float(np.linalg.norm(Q, 2)))
    return bool(eig[0] < -tol and eig[-1] > tol)


def generate_instance(p: int, n: int, m: int, rep: int, *, max_attempts: int = 10000) -> OQPESInstance:
    seed = deterministic_seed(p, n, m, rep)
    rng = np.random.default_rng(seed)
    for attempt in range(1, max_attempts + 1):
        A = rng.integers(0, 21, size=(m, n), dtype=np.int64)
        b = rng.integers(0, 101, size=m, dtype=np.int64)
        C = rng.integers(-100, 101, size=(p, n), dtype=np.int64)
        R = rng.integers(-100, 101, size=(n, n), dtype=np.int64)
        Q = np.triu(R)
        Q = Q + np.triu(Q, 1).T
        d = rng.integers(-100, 101, size=n, dtype=np.int64)
        ub = _derive_ub(A, b)
        if ub is None:
            continue
        if not _strictly_indefinite(Q):
            continue
        lb = np.zeros(n, dtype=np.int64)
        return OQPESInstance(
            A=A, b=b, C=C, Q=Q, d=d, alpha=0.0,
            lb=lb, ub=ub, p=p, n=n, m=m,
            rep=rep, seed=seed, accepted_attempt=attempt,
        )
    raise RuntimeError(f"Could not generate valid instance after {max_attempts} attempts")


def save_instance(instance: OQPESInstance, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "p": instance.p,
        "n": instance.n,
        "m": instance.m,
        "rep": instance.rep,
        "seed": instance.seed,
        "accepted_attempt": instance.accepted_attempt,
        "generator_version": instance.generator_version,
        "sha256": instance.digest(),
        "alpha": instance.alpha,
    }
    np.savez_compressed(
        path,
        A=instance.A,
        b=instance.b,
        C=instance.C,
        Q=instance.Q,
        d=instance.d,
        lb=instance.lb,
        ub=instance.ub,
        metadata=np.array(json.dumps(meta)),
    )
    return path


def load_instance(path: str | Path) -> OQPESInstance:
    with np.load(Path(path), allow_pickle=False) as z:
        meta = json.loads(str(z["metadata"].item()))
        inst = OQPESInstance(
            A=z["A"], b=z["b"], C=z["C"], Q=z["Q"], d=z["d"],
            alpha=float(meta["alpha"]), lb=z["lb"], ub=z["ub"],
            p=int(meta["p"]), n=int(meta["n"]), m=int(meta["m"]),
            rep=int(meta["rep"]), seed=int(meta["seed"]),
            accepted_attempt=int(meta["accepted_attempt"]),
            generator_version=str(meta["generator_version"]),
        )
        if inst.digest() != meta["sha256"]:
            raise ValueError("instance checksum mismatch")
        return inst


def published_example_51() -> OQPESInstance:
    # Prerna-Sharma 2024 numerical example (called Example 5.1 / 6.5.1 in derivative sources).
    A = np.array([[1, -3], [16, 3]], dtype=np.int64)
    b = np.array([0, 51], dtype=np.int64)
    C = np.array([[5, -7], [-6, 5]], dtype=np.int64)
    Q = np.array([[2, 0], [0, -8]], dtype=np.int64)
    d = np.array([81, 158], dtype=np.int64)
    # A contains a negative entry, so construct first and bypass benchmark-convention validation.
    obj = object.__new__(OQPESInstance)
    obj.A, obj.b, obj.C, obj.Q, obj.d = A, b, C, Q, d
    obj.alpha = 40.0
    obj.lb = np.array([0, 0], dtype=np.int64)
    obj.ub = np.array([3, 17], dtype=np.int64)
    obj.p, obj.n, obj.m = 2, 2, 2
    obj.rep, obj.seed, obj.accepted_attempt = 0, 0, 1
    obj.generator_version = "published-example"
    return obj
