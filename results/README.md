# Results Directory

The campaign result table is expected to contain one row per method-instance execution.

## Core columns

- `method`
- `status`
- `termination_reason`
- `objective_value`
- `solution_vector`
- `criterion_vector`
- `wall_time`
- `cpu_time`
- `LP_calls`
- `ILP_calls`
- `MILP_calls`
- `SP`
- `iterations`
- `cuts`
- `refinements`
- `efficiency_tests`
- `linear_ranks`
- `quadratic_ranks`
- `ranked_solutions`
- `solver`
- `solver_seed`
- `comparison_safe`
- `metadata`
- `instance_file`
- `instance_sha256`

`SP` is defined as

```text
SP = LP_calls + ILP_calls + MILP_calls
```

For the Prerna–Sharma reconstruction, retain `paper_core_SP` and `implementation_tie_ILP_calls` whenever they are present. These fields distinguish the reconstructed published-core workload from extra exact tie-enumeration work.

Recommended public summaries should be computed by ((p,n,m)) configuration and should include mean, median, minimum, and maximum runtime, subproblem counts, status counts, and paired statistical comparisons based only on correctness-compatible pairs.
