from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .config import PUBLISHED_CONFIGS, SolverConfig
from .instance import generate_instance, load_instance, save_instance
from .methods import prerna_sharma_2024, proposed_method
from .validation import exhaustive_optimum


def instance_filename(p: int, n: int, m: int, rep: int, seed: int) -> str:
    return f"P{p:02d}_N{n:03d}_M{m:03d}_R{rep:02d}_seed{seed}.npz"


def generate_benchmark(output_dir: str | Path, *, replicates: int = 30, configs: Iterable[tuple[int, int, int]] = PUBLISHED_CONFIGS) -> Path:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = out / "manifest.csv"
    rows = []
    for p, n, m in configs:
        for rep in range(1, replicates + 1):
            inst = generate_instance(p, n, m, rep)
            name = instance_filename(p, n, m, rep, inst.seed)
            save_instance(inst, out / name)
            rows.append({
                "file": name, "p": p, "n": n, "m": m, "rep": rep,
                "seed": inst.seed, "accepted_attempt": inst.accepted_attempt,
                "sha256": inst.digest(),
            })
    with manifest.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["file"])
        w.writeheader()
        w.writerows(rows)
    return manifest


def _flat_result(instance_file: str, digest: str, result) -> dict:
    d = result.to_dict()
    d["instance_file"] = instance_file
    d["instance_sha256"] = digest
    d["solution_vector"] = json.dumps(d["solution_vector"])
    d["criterion_vector"] = json.dumps(d["criterion_vector"])
    d["metadata"] = json.dumps(d["metadata"], default=str)
    return d


def run_pair(instance_path: str | Path, output_dir: str | Path, config: SolverConfig, *, validate: bool = False, tie_backend: str = "exact_no_good", proposed_first: bool = True):
    instance_path = Path(instance_path)
    inst = load_instance(instance_path)
    digest_before = inst.digest()
    methods = [
        ("PROPOSED_METHOD", lambda: proposed_method.solve(inst, config)),
        ("PRERNA_SHARMA_2024", lambda: prerna_sharma_2024.solve(inst, config, tie_backend=tie_backend)),
    ]
    if not proposed_first:
        methods.reverse()
    results = []
    for _, fn in methods:
        if inst.digest() != digest_before:
            raise RuntimeError("instance was modified between method runs")
        results.append(fn())
        if inst.digest() != digest_before:
            raise RuntimeError("a method modified the shared instance")
    validation = None
    if validate:
        try:
            validation = exhaustive_optimum(inst)
        except ValueError as exc:
            validation = {"skipped": str(exc)}
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / (instance_path.stem + "_pair.json")
    with json_path.open("w", encoding="utf-8") as f:
        json.dump({"instance": instance_path.name, "sha256": digest_before, "validation": validation, "results": [r.to_dict() for r in results]}, f, indent=2, default=str)
    return results, validation, json_path


def run_campaign(instances_dir: str | Path, output_dir: str | Path, config: SolverConfig, *, tie_backend: str = "exact_no_good") -> Path:
    instances_dir = Path(instances_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    files = sorted(instances_dir.glob("*.npz"))
    csv_path = output_dir / "results.csv"
    fieldnames = None
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = None
        for k, path in enumerate(files, 1):
            inst = load_instance(path)
            # Deterministic balanced order to reduce systematic order effects.
            proposed_first = (inst.rep % 2 == 1)
            results, _, _ = run_pair(path, output_dir / "details", config, validate=False, tie_backend=tie_backend, proposed_first=proposed_first)
            for r in results:
                row = _flat_result(path.name, inst.digest(), r)
                if writer is None:
                    fieldnames = list(row.keys())
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                writer.writerow(row)
                f.flush()
            print(f"[{k}/{len(files)}] {path.name}: " + ", ".join(f"{r.method}={r.status} SP={r.SP} t={r.wall_time:.3f}s" for r in results), flush=True)
    return csv_path
