# Experimental Study

## Objective

The experimental study evaluates the computational performance of the proposed exact method against the exact method of Prerna and Sharma (2024) on randomly generated instances of indefinite quadratic optimization over the integer efficient set of an MOILP.

Because the instances are random, each configuration ((p,n,m)) is represented by **30 independently generated accepted instances**. These are not 30 repetitions of the same instance. This design supports paired descriptive and statistical comparison while reducing dependence on one random realization.

## Benchmark configurations

The campaign uses:

- (pin{5,10,20,50}) objectives;
- (nin{10,20,50}) decision variables;
- (min{10,20,30,50}) constraints.

This gives (4	imes3	imes4=48) configurations. With 30 accepted instances per configuration, the complete study contains **1440 accepted instances**.

## Random-generation protocol

The coefficient ranges adopted from the Prerna–Sharma protocol are:

- (A_{ij}): integer values from 0 to 20;
- (b_i): integer values from 0 to 100;
- (C_{ij}): integer values from -100 to 100;
- (Q_{ij}) and (d_j): integer values from -100 to 100.

The public benchmark makes the additional reproducibility choices explicit:

- draws are independent discrete-uniform draws;
- (Q) is symmetrized;
- an instance is rejected unless (Q) is strictly indefinite;
- the feasible set is (X={xinmathbb Z_+^n:Axle b});
- an instance is rejected if a column of (A) is identically zero, so that every variable receives a finite structural upper bound;
- the deterministic target seed is

```text
100000000 + 1000000*p + 10000*n + 100*m + rep
```

for replicate `rep`.

Each accepted instance should be serialized before either algorithm is run and identified by a SHA-256 hash. The same serialized instance must be supplied to both methods.

## Computational environment

The public reproducibility environment is based on:

- Python 3.12.14;
- NumPy 2.3.5;
- SciPy 1.17.0;
- HiGHS through `scipy.optimize.milp`;
- highspy 1.15.1 for version checking or future extensions;
- pytest 9.0.2.

The study was designed for Windows/Anaconda execution. The manuscript should additionally report the actual experimental machine: Intel Core i7 11th generation, 16 GB RAM, Windows.

## Fair solver settings

Both methods must use the same:

- HiGHS backend;
- one solver thread;
- presolve setting;
- zero relative MIP gap;
- zero absolute MIP gap when passed through the backend;
- solver random seed;
- global method-instance time limit.

The primary runtime indicator is wall-clock time measured with `time.perf_counter`. CPU time measured with `time.process_time` is retained as a secondary diagnostic.

## Recorded indicators

For each method-instance run, record whenever available:

- status and termination reason;
- objective value;
- solution vector and criterion vector;
- wall-clock and CPU time;
- LP, ILP, and MILP call counts;
- `SP = LP_calls + ILP_calls + MILP_calls`;
- number of iterations;
- number of dominance cuts;
- number of refinements;
- number of efficiency tests;
- linear ranks and quadratic ranks for Prerna–Sharma;
- solver metadata;
- `comparison_safe`;
- `paper_core_SP` and `implementation_tie_ILP_calls` where applicable.

Independent exhaustive validation on small instances must not be counted in the algorithmic runtime or in `SP`.

## Statistical comparison

The two methods are applied to the same generated instance, so the observations are **paired**.

A suitable primary nonparametric comparison of paired runtime values is the Wilcoxon signed-rank test when the distribution of paired differences cannot be treated as normal. If a paired t-test is also reported, its assumptions should be checked on the paired differences rather than separately on the two method samples.

For configuration-wise testing across many ((p,n,m)) groups, multiplicity should be controlled, for example with the Holm procedure. Statistical significance should be complemented by an effect-size measure and by descriptive statistics.

At minimum, report for each configuration and each method:

- number of valid paired runs;
- mean runtime;
- median runtime;
- minimum and maximum runtime;
- mean and median `SP`;
- mean and median LP/ILP/MILP counts where relevant;
- status counts.

## Figures

Recommended figures include:

- wall-clock time versus (n);
- wall-clock time versus (p);
- wall-clock time versus (m), when informative;
- subproblem workload;
- paired runtime-difference or distribution plots.

For the accompanying manuscript, use a consistent visual code: **dark red** for the proposed method and **dark blue** for Prerna–Sharma.

## Interpretation

Distinguish carefully between:

- a descriptive numerical difference;
- statistical evidence from paired tests;
- practical magnitude of the difference.

Do not use “significantly faster” unless a statistical test supports that statement. Do not describe one method as “always superior” unless every relevant paired observation supports it.
