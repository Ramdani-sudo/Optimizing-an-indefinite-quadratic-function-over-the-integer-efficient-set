# Prerna–Sharma (2024) Benchmark Implementation

## Reference

Prerna and Vikas Sharma, “Optimization of a quadratic programming problem over an integer efficient set,” *Journal of Computational and Applied Mathematics*, vol. 441, 115651, 2024. DOI: 10.1016/j.cam.2023.115651.

## Scope

The code used in this project is an **independent implementation** of the method described in the published paper. It is included solely to provide a reproducible benchmark for the accompanying comparative study.

This repository does not claim that the implementation is official code released or endorsed by the original authors.

## Reconstructed algorithmic elements

The implementation reconstructs:

- the quantities used to form the associated linear objective;
- the corresponding integer linear problem;
- successive linear ranks;
- quadratic ranks;
- Pareto-efficiency testing;
- the stopping logic based on the first quadratic rank containing an efficient solution.

## Tie handling

The public SciPy MILP interface used in this project does not expose the final simplex-tableau information assumed by the published ranking procedure. The general backend therefore uses exact no-good constraints to enumerate tied ranked solutions.

This preserves exact tie handling, but it can introduce additional ILP calls. The software reports them separately through:

- `paper_core_SP`;
- `implementation_tie_ILP_calls`;
- actual `ILP_calls`, `MILP_calls`, and `SP`;
- `comparison_safe`.

The `paper_declared_unique` mode is reserved for controlled regression tests in which uniqueness is independently known. It should not be used as the general campaign backend.

## Published-example regression check

The supplied validation report records:

- optimal solution: `[0, 10]`;
- objective value: `820`;
- linear ranks: `24`;
- quadratic ranks: `7`;
- reconstructed published-core count: `ILP = 27`, `MILP = 7`, `SP = 34`.

With the general exact no-good tie backend, the same optimum is obtained while additional tie-enumeration ILP calls are explicitly reported.
