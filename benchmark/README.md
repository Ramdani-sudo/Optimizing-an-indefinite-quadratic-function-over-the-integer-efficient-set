# Benchmark Manifest

`benchmark_manifest.csv` contains the complete deterministic target grid for the 1440 accepted benchmark instances:

- 4 values of `p`;
- 3 values of `n`;
- 4 values of `m`;
- 30 accepted replicates per configuration.

The manifest records the deterministic target seed and an expected filename convention. It does **not** replace the serialized-instance SHA-256 digest. After generation, the actual `.npz` hash should be recorded and used as the definitive instance identity in paired result files.
