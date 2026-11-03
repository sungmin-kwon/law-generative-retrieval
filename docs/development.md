# Development

## Local checks

```bash
python -m pip install ".[dev]"
python -m unittest discover -s tests/public -v
ruff check src tests/public
ruff format --check src tests/public
python -m build
```

The portable tests run with only the Python standard library and the installed
package. They use invented data and temporary directories; there is no paid API,
database or GPU dependency. Ruff/build are optional development dependencies.
The CLI's exit code is zero on success and two for expected validation/file errors.

Tests cover rank preservation, truncated metrics, complete cohort alignment,
universe violations, deterministic fusion, chunk-selection regressions, malformed
inputs, output preservation, path traversal and public-export boundaries.
Add behavior/invariant tests for substantive changes instead of tests that repeat
the implementation line by line.

## Installing the built artifact

Validate a wheel in a fresh virtual environment, not just through a source-tree
import. Run the same synthetic CLI commands and portable tests there. Inspect
source-distribution members before publication; private experiment code and
operational documents must not enter the package via build-tool defaults.

## Research workspace compatibility

The legacy research tree may contain frozen scripts, configs and results. Their
paths and digests are load-bearing. Do not reformat, rename or replace them while
introducing the reusable package. Add a versioned runner that imports `genrag`
for future experiments, with explicit input/output roots and contract bindings.

Before adopting a refactored metric implementation, compare it against saved
predictions and authoritative reports on the full original evaluation cohort.
Retain any discrepancy and resolve it before using the new code for model selection.
This parity check does not require rerunning training or paid embedding generation.

The public CI intentionally discovers `tests/public` only. Private historical
tests may depend on local artifacts or image-specific runtimes and are not a
portable installation requirement.
