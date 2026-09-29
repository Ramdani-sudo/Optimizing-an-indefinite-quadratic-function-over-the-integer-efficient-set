# Release Status

The complete OQPES Python source tree and supplied test suite are included in this repository.

## Public source

The repository contains:

- the complete `src/oqpes/` package;
- the complete `tests/` suite;
- the proposed exact method;
- the independent Prerna–Sharma (2024) benchmark implementation;
- benchmark generation and paired-campaign utilities;
- SciPy/HiGHS solver wrappers;
- validation utilities;
- the command-line interface and Windows launcher;
- scientific documentation and reproducibility metadata.

All user-facing launcher messages are in English.

## Validated software stack

The public package metadata is aligned with the environment in which the supplied test suite was validated:

- Python 3.13.5;
- NumPy 2.3.5;
- SciPy 1.17.0;
- pytest 9.0.2.

The recorded validation command was:

```text
PYTHONPATH=src pytest -q
```

with result:

```text
.........                                                                [100%]
9 passed
```

The project version is **0.2.1**.

## Note on HiGHS

The implementation calls HiGHS through `scipy.optimize.milp`. The separate `highspy` package is not required by the current source code and has therefore been removed from the mandatory public environment to reduce unnecessary dependency risk.
