# Getting started

## Install

Use Python 3.11 or newer in a virtual environment. The installed package has no
runtime dependencies; PyTorch, database SDKs and provider keys are unnecessary.

```bash
python -m venv .venv
# Activate .venv using the command for your operating system.
python -m pip install .
genrag --help
genrag doctor
```

This installs the distribution `generative-retrieval-lab`, importable as `genrag`.
`python -m genrag` and the `genrag` command expose the same interface.

## Input contracts

The universe is a JSON object listing every eligible document ID:

```json
{"document_ids": ["DOC-A", "DOC-B", "DOC-C"]}
```

Predictions are UTF-8 JSONL, one object per question:

```json
{"query_id":"Q-1","gold_evidence_id":"DOC-A","candidates":["DOC-B","DOC-A"],"depth":10}
```

`depth` describes the requested maximum result count, not necessarily the number
returned. An empty candidate list is a miss. A `null` candidate occupies an
unknown position. Duplicates retain their saved positions during scoring.
Omitting depth uses the CLI's explicit/default depth of ten.

The adapter also reads `documents` objects with `evidence_id` and optional
consecutive `rank`, plus `requested_depth`. Captures with both depth-five and
depth-ten rows are selected with `--depth`; they are never merged. If `gold_rank`
is saved, the adapter independently verifies it against candidate positions.
Candidate objects using `text` are supported for saved decoder predictions.

A fixed cohort is a JSON object such as `{"query_ids":["Q-1"]}`. Supply it with
`--cohort cohort.json`; every cohort question must be present in the inputs.

## Commands

```bash
genrag score examples/synthetic/dense.jsonl --universe examples/synthetic/universe.json
genrag score examples/synthetic/dense.jsonl --universe examples/synthetic/universe.json --cohort examples/synthetic/cohort.json
genrag compare examples/synthetic/dense.jsonl examples/synthetic/generative.jsonl --universe examples/synthetic/universe.json
genrag fuse examples/synthetic/dense.jsonl examples/synthetic/generative.jsonl --universe examples/synthetic/universe.json --left-weight 1 --right-weight 0.25 --output output/fused.jsonl
genrag verify public-export-manifest.json
```

`score` and `compare` print JSON and optionally save it with `--output`.
`fuse` saves JSONL and a `.manifest.json` sidecar containing settings, source
hashes and metrics. Existing output files are rejected; choose a versioned path
for another experiment. Input files are never overwritten.

File hashes identify the supplied artifacts, not their quality or truthfulness.
The universe must be the actual eligible corpus for the upstream retrieval run.
Supplying the same universe declaration does not independently audit a remote index.
