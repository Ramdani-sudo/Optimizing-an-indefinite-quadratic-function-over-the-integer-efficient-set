# Reproducibility Guide

## Validated environment

The public environment is aligned with the software stack recorded in the supplied validation report:

- Python 3.13.5;
- NumPy 2.3.5;
- SciPy 1.17.0;
- pytest 9.0.2.

Create the environment with:

```bat
conda env create -f environment.yml
conda activate oqpes_py
```

The package metadata requires Python `>=3.13,<3.14`.

The optimization backend is HiGHS accessed through `scipy.optimize.milp`. A separate `highspy` installation is not required by the current implementation.

## Validation

The supplied project validation report records:

```text
PYTHONPATH=src pytest -q
.........                                                                [100%]
9 passed
```

The test suite covers deterministic generation, serialization/checksums, the SciPy/HiGHS wrapper, the published Prerna–Sharma regression example, exact tie handling, exact quadratic decomposition, and agreement with independent exhaustive validation on small instances.

## Instance reproducibility

The benchmark uses the deterministic seed

```text
100000000 + 1000000*p + 10000*n + 100*m + rep
```

for each target configuration and replicate.

Because rejection criteria are applied during generation, exact regeneration also requires the same pseudorandom-number generator, draw order, symmetrization rule, and acceptance logic.

Each accepted serialized instance is identified by a SHA-256 hash. The hash is the definitive identity check for a paired comparison.

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
