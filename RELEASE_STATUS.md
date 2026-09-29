# Release Status

The original OQPES Python source tree and test suite have now been imported from the supplied one-click project archive.

## Source now included

The repository contains the complete `src/oqpes/` package and `tests/` suite, including the proposed exact method, the independent Prerna–Sharma (2024) benchmark implementation, benchmark-generation utilities, paired-campaign code, SciPy/HiGHS solver wrappers, validation utilities, the CLI, and the interactive launcher.

All user-facing messages in `src/oqpes/launcher.py` were translated to English. The mathematical and algorithmic code was otherwise kept consistent with the supplied original project.

## Validation performed during import

The supplied source archive was extracted and tested in the available validation environment:

- Python 3.13.5
- NumPy 2.3.5
- SciPy 1.17.0
- pytest 9.0.2

Command:

```text
PYTHONPATH=src pytest -q
```

Result:

```text
.........                                                                [100%]
9 passed
```

## Remaining archival-release step

The public Conda environment pins Python 3.12.14 and `pyproject.toml` requires Python `>=3.12,<3.13`. Before creating a final archival GitHub release or tag, rerun the complete test suite under Python 3.12.14 and update `TEST_REPORT.txt` with that exact environment output.
