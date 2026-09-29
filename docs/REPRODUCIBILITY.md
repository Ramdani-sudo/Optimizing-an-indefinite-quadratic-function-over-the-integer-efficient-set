# Reproducibility Guide

## Recommended environment

The public environment pins:

- Python 3.12.14;
- NumPy 2.3.5;
- SciPy 1.17.0;
- highspy 1.15.1;
- pytest 9.0.2.

Create it with:

```bat
conda env create -f environment.yml
conda activate oqpes_py
```

The package metadata requires Python `>=3.12,<3.13`.

## Historical validation-report caveat

The supplied historical test report states that its nine passing tests were executed under Python 3.13.5. This differs from the public package range and the pinned Conda environment.

For traceability, the historical report is retained. It should not be treated as final release certification. Before tagging an archival release, rerun the complete test suite under Python 3.12.14 and replace the environment section of `TEST_REPORT.txt` with the newly observed output.

## Instance reproducibility

The benchmark uses the deterministic seed

```text
100000000 + 1000000*p + 10000*n + 100*m + rep
```

for each target configuration and replicate.

Because rejection criteria are applied during generation, exact regeneration also requires the same pseudorandom-number generator, draw order, symmetrization rule, and acceptance logic.

Each accepted serialized instance should be identified by a SHA-256 hash. The hash is the definitive identity check for a paired comparison.

## Solver reproducibility

For a fair comparison, keep fixed across both methods:

- HiGHS backend through `scipy.optimize.milp`;
- one solver thread;
- presolve setting;
- MIP gap settings;
- solver random seed;
- per-method time limit;
- hardware and operating system when reproducing runtime tables.

Wall-clock times can vary across machines. Objective values, statuses, instance hashes, and algorithmic call counts are stronger reproducibility targets than exact timing equality.

## Correctness before performance

Before interpreting runtime, verify for every paired instance that both methods report compatible exact outcomes. Any disagreement in status or objective value should be investigated before the instance is included in aggregate performance statistics.

## Suggested archival-release procedure

1. Create `oqpes_py` from `environment.yml`.
2. Record Python and package versions.
3. Run `python -m pytest -q`.
4. Run the smoke test.
5. Reproduce the published Prerna–Sharma example.
6. Reproduce the independent exhaustive-validation example.
7. Generate a small deterministic benchmark subset and verify hashes across two runs.
8. Run the full paired campaign.
9. Archive result tables, environment metadata, and the exact Git commit hash.
