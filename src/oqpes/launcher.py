from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from .benchmark import generate_benchmark, run_campaign, run_pair
from .config import SolverConfig
from .instance import generate_instance, save_instance


ROOT = Path.cwd()


def _pause():
    input("\nPress Enter to continue...")


def _run_tests():
    print("\n=== UNIT TESTS ===")
    cp = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=ROOT)
    print("Tests finished with exit code", cp.returncode)
    _pause()


def _smoke_pair():
    print("\n=== CONTROLLED TEST ON A SMALL INSTANCE ===")
    tmp = ROOT / "instances_smoke"
    tmp.mkdir(exist_ok=True)
    inst = generate_instance(3, 4, 4, 1)
    path = tmp / f"P03_N004_M004_R01_seed{inst.seed}.npz"
    save_instance(inst, path)
    cfg = SolverConfig(time_limit=60.0)
    results, validation, out = run_pair(path, ROOT / "results_smoke", cfg, validate=True, tie_backend="exact_no_good")
    for r in results:
        print(f"{r.method}: {r.status} | phi={r.objective_value} | SP={r.SP} | wall={r.wall_time:.4f}s")
    print("Independent validation:", validation)
    print("Result file:", out)
    _pause()


def _generate_full():
    print("\nWARNING: 48 configurations x 30 instances = 1440 instances.")
    ans = input("Generate the full benchmark now? [y/N] ").strip().lower()
    if ans != "y":
        return
    manifest = generate_benchmark(ROOT / "instances", replicates=30)
    print("Benchmark generation completed:", manifest)
    _pause()


def _run_full():
    instdir = ROOT / "instances"
    if not instdir.exists() or not any(instdir.glob("*.npz")):
        print("No benchmark instances were found. Run option 3 first.")
        _pause()
        return
    try:
        tl = float(input("Time limit per method-instance pair in seconds [60]: ").strip() or "60")
    except ValueError:
        tl = 60.0
    print("\nThe full campaign may take a long time. Results are saved after every instance.")
    ans = input("Start the complete campaign? [y/N] ").strip().lower()
    if ans != "y":
        return
    cfg = SolverConfig(time_limit=tl)
    out = run_campaign(instdir, ROOT / "results", cfg, tie_backend="exact_no_good")
    print("Campaign completed:", out)
    _pause()


def _run_one_file():
    path = input("Full path to the .npz instance file: ").strip().strip('"')
    if not path:
        return
    cfg = SolverConfig(time_limit=60.0)
    results, validation, out = run_pair(Path(path), ROOT / "results_single", cfg, validate=False, tie_backend="exact_no_good")
    for r in results:
        print(f"{r.method}: {r.status} | phi={r.objective_value} | SP={r.SP} | wall={r.wall_time:.4f}s")
    print("Details:", out)
    _pause()


def main():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=" * 70)
        print(" OQPES - PROPOSED_METHOD vs PRERNA_SHARMA_2024")
        print(" HiGHS | 1 thread | relative gap=0 | absolute gap=0 | common presolve")
        print("=" * 70)
        print("1. Run unit tests")
        print("2. Controlled test: one small instance, both methods")
        print("3. Generate the full benchmark (48 x 30 = 1440 instances)")
        print("4. Run the complete campaign")
        print("5. Run one specific .npz instance")
        print("0. Exit")
        choice = input("\nYour choice: ").strip()
        if choice == "1":
            _run_tests()
        elif choice == "2":
            _smoke_pair()
        elif choice == "3":
            _generate_full()
        elif choice == "4":
            _run_full()
        elif choice == "5":
            _run_one_file()
        elif choice == "0":
            return
        else:
            _pause()


if __name__ == "__main__":
    main()
