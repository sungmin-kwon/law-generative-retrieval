# Contributing

Start with [architecture](docs/architecture.md) and
[evaluation contracts](docs/evaluation.md). Use a virtual environment and run the
portable checks in [development](docs/development.md).

Keep the runtime dependency-free and provider execution outside import paths.
Changes to candidate handling, cohort selection or fusion need tests showing
their effect on rank/coverage and malformed inputs. Preserve deterministic output
and explicit provenance. Do not drop missing questions, unknown ranks or duplicate
beams to make a score look better.

Use small, reviewable changes that explain the behavior, motivation and validation.
Examples and tests must contain invented data. Do not attach provider keys,
private logs, personal questions, model weights or proprietary experiment records.
Historical hash-bound runners in a research workspace are not formatting targets.
