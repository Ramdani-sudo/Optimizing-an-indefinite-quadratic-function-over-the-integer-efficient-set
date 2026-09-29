# OQPES Benchmark — Proposed Method vs. Prerna–Sharma (2024)

**Exact benchmarking framework for optimizing an indefinite quadratic function over the integer efficient set of a multiobjective integer linear program (MOILP).**

This repository accompanies the research study **“Optimizing an indefinite quadratic function over the integer efficient set.”** It provides the computational framework used to compare a proposed exact method with an independent implementation of the exact ranking method of Prerna and Sharma (2024).

> **Research-use note.** The implementation of Prerna–Sharma (2024) in this project is an independent reconstruction from the published methodology. It is not official code from the original authors and should not be presented as such.

> **Current release status.** The original `src/oqpes/` implementation and `tests/` suite are included. All user-facing launcher messages are in English. The public package metadata is aligned with the validated stack (Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, pytest 9.0.2), for which the supplied suite reports `9 passed`. See [`RELEASE_STATUS.md`](RELEASE_STATUS.md).

## Authors

- **Ramdani Zoubir**¹,*
- **Brahmi Boualem**¹
- **Leila Younsi Abbaci**²
- **Iftissen El-Ghani**³

¹ Mathematical Analysis and Applications Laboratory, Faculty of Mathematics and Computer Science, University of Bordj Bou Arreridj, El Anasser, 34030, Bordj Bou Arreridj, Algeria  
² Department of Electrical Engineering, Faculty of Technology, Research Unit LAMOS, University of Bejaia, Algeria  
³ LIM Laboratory, Faculty of Exact Sciences, Bouira University, Bouira 10000, Algeria  
* Corresponding author: **Ramdani Zoubir** — `z.ramdani@univ-bba.dz`

## Problem studied

Let

[
X=\{x\in\mathbb Z_+^n:Ax\le b\}
]

be the feasible set of a multiobjective integer linear program

[
\operatorname{VMAX}\{Cx:x\in X\},
]

and let (E\subseteq X) denote its Pareto-efficient set. The computational problem considered here is

[
\max\{\varphi(x):x\in E\},
\qquad
\varphi(x)=x^TQx+d^Tx,
]

where (Q) is symmetric and may be indefinite. The efficient set is finite but is not explicitly enumerated by the proposed method.

## Methods compared

### 1. Proposed exact method

The proposed method uses an exact algebraic decomposition of the symmetric quadratic form into signed one-dimensional square terms. For the decomposition used by the implementation,

[
x^TQx=\sum_i \rho_i x_i^2+\sum_{i<j}Q_{ij}(x_i+x_j)^2,
\qquad
\rho_i=Q_{ii}-\sum_{j\ne i}Q_{ij}.
]

The algorithm then constructs a valid mixed-integer linear upper-approximation master problem:

- positive convex square terms are upper-bounded by secants over integer projection intervals;
- negative concave square terms are upper-bounded by global tangents;
- candidate solutions are checked for MOILP efficiency through a mixed-integer linear efficiency test;
- dominated regions are removed by valid criterion-space dominance cuts;
- projection approximations are refined only where needed;
- the algorithm terminates when an efficient incumbent closes the valid master upper bound.

In the current implementation, the proposed method solves **MILP subproblems**; its LP and pure-ILP counters are therefore normally zero.

### 2. Prerna–Sharma (2024) benchmark

The comparison method reconstructs the exact ranking approach described in:

> Prerna, V. Sharma, *Optimization of a quadratic programming problem over an integer efficient set*, Journal of Computational and Applied Mathematics 441 (2024), 115651. DOI: 10.1016/j.cam.2023.115651.

The implementation reconstructs the associated linear objective, successive linear ranks, quadratic ranks, the efficiency test, and the published stopping rule.

#### Tie-handling note

The general backend `exact_no_good` enumerates tied ranked solutions exactly. Because `scipy.optimize.milp` does not expose the final simplex tableau used by the published ranking procedure, exact tie enumeration may require additional ILP calls. These calls are counted explicitly. The output therefore distinguishes:

- `paper_core_SP`: subproblem count corresponding to the reconstructed published core;
- `implementation_tie_ILP_calls`: additional ILP calls required by the general tie backend;
- `SP`: total calls actually executed by this implementation;
- `comparison_safe`: flag indicating whether the reported subproblem count is directly comparable without tie-handling qualification.

The mode `paper_declared_unique` is reserved for regression tests where uniqueness of the relevant ranks is independently certified. It must not be used as the general campaign backend.

## Experimental design

The benchmark follows the coefficient ranges reported for the Prerna–Sharma computational protocol and makes additional reproducibility choices explicit.

### Configuration grid

- number of objectives: `p ∈ {5, 10, 20, 50}`;
- number of decision variables: `n ∈ {10, 20, 50}`;
- number of constraints: `m ∈ {10, 20, 30, 50}`;
- 48 configurations in total;
- 30 independently generated accepted instances per configuration;
- **1440 accepted benchmark instances in total**.

### Random coefficient ranges

Independent discrete-uniform draws are used over the following integer ranges:

- `A_ij ∈ {0, …, 20}`;
- `b_i ∈ {0, …, 100}`;
- `C_ij ∈ {-100, …, 100}`;
- `Q_ij, d_j ∈ {-100, …, 100}`.

Additional reproducibility rules used by this project are:

- `Q` is symmetrized;
- instances are rejected unless `Q` is strictly indefinite;
- the benchmark model is `X = {x integer >= 0 : Ax <= b}`;
- instances with an all-zero column of `A` are rejected so that each decision variable receives a finite structural upper bound;
- the deterministic seed is

  `100000000 + 1000000*p + 10000*n + 100*m + rep`;

- each accepted instance is saved before either method is run;
- a SHA-256 digest identifies the exact instance supplied to both methods.

The full 1440-row configuration/seed manifest is provided in [`benchmark/benchmark_manifest.csv`](benchmark/benchmark_manifest.csv).

## Fair comparison protocol

Both methods use the same optimization backend through `scipy.optimize.milp` (HiGHS) and are run on the same instance object. The intended common solver settings are:

- one solver thread;
- presolve enabled;
- zero relative MIP gap;
- zero absolute MIP gap passed to HiGHS;
- identical solver random seed;
- identical global time limit for each method-instance pair.

The primary runtime measure is **wall-clock time** recorded with `time.perf_counter`. CPU time is also recorded with `time.process_time` as a secondary diagnostic.

## Recorded performance indicators

Each method-instance result records, when available:

- `status`;
- `termination_reason`;
- objective value and solution vector;
- criterion vector;
- wall-clock time;
- CPU time;
- `LP_calls`;
- `ILP_calls`;
- `MILP_calls`;
- `SP = LP_calls + ILP_calls + MILP_calls`;
- number of iterations;
- number of dominance cuts;
- number of refinements;
- number of efficiency tests;
- numbers of linear and quadratic ranks for the ranking method;
- solver and seed metadata;
- `comparison_safe` and implementation-specific metadata.

Independent exhaustive validation, when used on small instances, is not included in the algorithmic runtime or in `SP`.

## Validation checks supplied with the project

The supplied regression report records nine passing tests in the build environment used when the package was assembled. It also reports:

- the published Prerna–Sharma example is reproduced with `x* = (0, 10)` and `phi* = 820`;
- the published-core ranking workload is reconstructed as 24 linear ranks, 7 quadratic ranks, `ILP = 27`, `MILP = 7`, `SP = 34`;
- the general exact no-good tie backend produces the same optimum but executes additional tie-enumeration ILPs;
- on the same published example, the proposed method returns the same optimum with `SP = 16`, 8 iterations, 6 dominance cuts, and 8 refinements;
- an independent small-instance exhaustive check gives the same optimum for both exact methods.

See [`TEST_REPORT.txt`](TEST_REPORT.txt) and [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) for the environment caveat that must be considered when interpreting this historical test report.

## Quick start on Windows with Anaconda

### One-click launcher

1. Clone or download the **complete** repository.
2. Make sure Anaconda or Miniconda is installed under the standard user directory.
3. Double-click `START_OQPES.bat`.
4. The launcher creates `oqpes_py` from `environment.yml` if necessary, activates it, and starts the project menu.

### Manual setup

```bat
conda env create -f environment.yml
conda activate oqpes_py
python -m pip install -e .
set PYTHONPATH=%CD%\src;%PYTHONPATH%
python -m pytest -q
```

### Smoke test

```bat
python -m oqpes smoke --time-limit 60
```

### Generate the full benchmark

```bat
python -m oqpes generate-benchmark --replicates 30 --output instances
```

### Run the full paired campaign

```bat
python -m oqpes run-campaign --instances instances --output results --time-limit 60
```

## Repository structure

A complete executable release is expected to contain:

```text
.
├── src/oqpes/                 # algorithm implementations and CLI
├── tests/                     # unit/regression tests
├── benchmark/                 # deterministic benchmark manifest
├── results/                   # result files and result documentation
├── docs/                      # methodological/reproducibility notes
├── README.md
├── AUTHORS.md
├── CITATION.cff
├── environment.yml
├── requirements.txt
├── pyproject.toml
├── START_OQPES.bat
├── RUN_TESTS.bat
└── RUN_SMOKE_TEST.bat
```

## Documentation for researchers

- [`docs/EXPERIMENTAL_STUDY.md`](docs/EXPERIMENTAL_STUDY.md): detailed benchmark protocol and interpretation guidance.
- [`docs/METHOD_OVERVIEW.md`](docs/METHOD_OVERVIEW.md): mathematical and algorithmic overview.
- [`docs/PRERNA_SHARMA_IMPLEMENTATION.md`](docs/PRERNA_SHARMA_IMPLEMENTATION.md): scope and fairness notes for the independent benchmark implementation.
- [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md): environment, instance identity, timing, and validation rules.
- [`results/README.md`](results/README.md): result schema and reporting conventions.

## Reproducibility policy

A performance comparison is considered valid only when both methods are run on the same instance hash, with the same solver backend, thread count, time limit, and campaign-level settings. Objective values should be checked for agreement before runtime conclusions are drawn.

## Citation

If this repository is used in scientific work, please cite the accompanying manuscript once its final bibliographic information is available. Machine-readable software citation metadata are provided in [`CITATION.cff`](CITATION.cff).

## License

No software license was specified in the supplied project material. Before inviting third parties to reuse, modify, or redistribute the code, the authors should add an explicit license.
