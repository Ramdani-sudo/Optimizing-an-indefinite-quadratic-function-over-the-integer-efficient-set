from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import generate_benchmark, run_campaign, run_pair
from .config import SolverConfig
from .instance import generate_instance, published_example_51, save_instance
from .methods import prerna_sharma_2024, proposed_method


def _config(args) -> SolverConfig:
    return SolverConfig(
        time_limit=float(args.time_limit),
        threads=1,
        presolve=True,
        mip_rel_gap=0.0,
        mip_abs_gap=0.0,
        random_seed=int(args.solver_seed),
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="oqpes")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate-benchmark")
    g.add_argument("--replicates", type=int, default=30)
    g.add_argument("--output", default="instances")

    s = sub.add_parser("smoke")
    s.add_argument("--time-limit", type=float, default=60.0)
    s.add_argument("--solver-seed", type=int, default=0)

    r = sub.add_parser("run-pair")
    r.add_argument("--instance", required=True)
    r.add_argument("--output", default="results")
    r.add_argument("--time-limit", type=float, default=60.0)
    r.add_argument("--solver-seed", type=int, default=0)
    r.add_argument("--tie-backend", choices=["exact_no_good", "paper_declared_unique"], default="exact_no_good")
    r.add_argument("--validate", action="store_true")

    c = sub.add_parser("run-campaign")
    c.add_argument("--instances", default="instances")
    c.add_argument("--output", default="results")
    c.add_argument("--time-limit", type=float, default=60.0)
    c.add_argument("--solver-seed", type=int, default=0)
    c.add_argument("--tie-backend", choices=["exact_no_good", "paper_declared_unique"], default="exact_no_good")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "generate-benchmark":
        manifest = generate_benchmark(args.output, replicates=args.replicates)
        print(f"Benchmark generated: {manifest}")
        return 0
    if args.cmd == "smoke":
        cfg = _config(args)
        inst = published_example_51()
        pr = prerna_sharma_2024.solve(inst, cfg, tie_backend="paper_declared_unique")
        print(json.dumps(pr.to_dict(), indent=2, default=str))
        return 0 if pr.status == "OPTIMAL" else 1
    if args.cmd == "run-pair":
        cfg = _config(args)
        results, validation, out = run_pair(args.instance, args.output, cfg, validate=args.validate, tie_backend=args.tie_backend)
        for r in results:
            print(f"{r.method}: {r.status}, phi={r.objective_value}, SP={r.SP}, wall={r.wall_time:.4f}s")
        print(f"Details: {out}")
        if validation is not None:
            print("Independent validation:", validation)
        return 0
    if args.cmd == "run-campaign":
        cfg = _config(args)
        out = run_campaign(args.instances, args.output, cfg, tie_backend=args.tie_backend)
        print(f"Campaign results: {out}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
