# Public Release Checklist

Before creating an archival/public release, verify all items below.

- [ ] `src/oqpes/` contains the complete algorithm source code.
- [ ] `tests/` contains the complete test suite.
- [ ] All user-facing console messages are in English.
- [ ] `python -m pytest -q` passes in the pinned Python 3.12.14 environment.
- [ ] `TEST_REPORT.txt` has been regenerated in that environment.
- [ ] The published Prerna–Sharma example is reproduced.
- [ ] The independent exhaustive-validation example is reproduced.
- [ ] The full campaign uses the exact same instance hash for both methods.
- [ ] Public result files retain `comparison_safe`, `paper_core_SP`, and tie-backend metadata.
- [ ] No absolute local Windows paths are committed.
- [ ] No passwords, tokens, API keys, or personal machine identifiers are committed.
- [ ] The final manuscript citation is added when available.
- [ ] The authors select an explicit software license if third-party reuse is intended.
- [ ] A Git tag/release records the exact code version used for the paper.
