# Method Overview

## Optimization problem

The project studies optimization of an additional indefinite quadratic preference function over the efficient set of a multiobjective integer linear program (MOILP).

The MOILP is
[
operatorname{VMAX}{Cx:xin X},
qquad
X={xinmathbb Z_+^n:Axle b}.
]

A feasible solution (ar xin X) is efficient if no (xin X) satisfies (Cxge Car x) componentwise with at least one strict inequality. Let (E) denote the efficient set. The target problem is
[
max_{xin E}arphi(x),
qquad
arphi(x)=x^TQx+d^Tx,
]
where (Q) is symmetric and may be indefinite.

## Proposed exact method

The implementation uses the exact decomposition
[
x^TQx
=
sum_{i=1}^n ho_i x_i^2
+
sum_{1le i<jle n}Q_{ij}(x_i+x_j)^2,
]
with
[
ho_i=Q_{ii}-sum_{j
e i}Q_{ij}.
]

The identity itself is exact. Relaxation is introduced only when the one-dimensional square terms are replaced by valid linear upper estimators.

### Positive square terms

For a positive coefficient, the convex term is upper-bounded by secants over integer projection intervals. The intervals are refined dynamically.

### Negative square terms

For a negative coefficient, the concave term is upper-bounded by global tangents. Tangents are added only when required by the current candidate.

### MILP master problem

The linearized components are embedded in a mixed-integer linear master problem. Its optimum provides a valid global upper bound for the original quadratic preference over the remaining admissible search region.

### Efficiency test

Each master candidate is tested for Pareto efficiency through a mixed-integer linear efficiency test. Only certified efficient candidates can become incumbents.

### Dominance cuts

When a candidate is dominated, a valid criterion-space cut removes the dominated orthant while preserving every efficient solution that can still improve the incumbent.

### Refinement and stopping

After candidate processing, the projection approximations are refined at the current candidate. The algorithm terminates when an efficient incumbent closes the master upper bound.

## Actual order used by the implementation

The audited Python implementation follows this sequence:

1. construct the exact quadratic decomposition;
2. compute projection bounds;
3. build and solve the MILP master;
4. check upper-bound closure if an efficient incumbent exists;
5. test the current master candidate for efficiency;
6. update the incumbent when the candidate is efficient and improves the true quadratic value;
7. add a dominance cut when the candidate is not efficient;
8. refine the one-dimensional approximations at the current candidate;
9. terminate when the valid global upper bound equals the incumbent value within the implemented numerical tolerance.

## Solver classification

For the proposed method:

- master problem: **MILP**;
- efficiency test: **MILP**;
- projection bounds: algebraic calculation;
- quadratic decomposition: algebraic calculation;
- dominance-cut generation: algebraic/logical construction;
- secant/tangent refinement: data-structure update.

Thus the proposed implementation does not use QP or MIQP as its principal optimization subproblem.
