# Evaluation methodology

## Define the comparison before looking at the result

Declare the eligible document universe, exact query IDs, expected document IDs,
requested retrieval depth and any fixed cohort. Match upstream query processing,
filters and index versions separately. The package enforces the declared inputs;
it cannot infer whether a remote service actually searched the declared corpus.

A generative retriever learns query-to-identifier behavior. In closed-corpus
evaluation, training and evaluation may target the same documents while using
different questions. A document-disjoint experiment asks a different question
and may make identifiers unlearnable. State which design is being tested.

## Metrics

For one expected document per query:

- **Recall@k:** fraction of questions whose expected document appears within k.
- **MRR@k:** mean reciprocal rank, assigning zero when the document is absent
  or below k. It is truncated at the reported cutoff.
- **Paired hit transitions:** both-hit, left-only, right-only and neither-hit.
  Their counts expose regressions hidden by a net gain.

Unknown candidates, duplicates and empty results retain their original rank or
denominator effects. Out-of-universe IDs are rejected rather than filtered out.
Saved ranks are checked against raw ordered candidates.

`compare` refuses query-set intersections: both complete runs must have identical
query IDs, targets and requested depths before a declared cohort is selected.
Separate k5 and k10 component calls can use different candidate pools and produce
different first-ranked documents; do not mix their metrics in one ranking table.

## Fusion and complementarity

Weighted reciprocal-rank fusion gives a document a contribution of
`weight / (constant + rank)` from each channel. Tune weights on development
questions, freeze them, then test independently. More channels or a larger
candidate pool do not automatically improve the final ranking.

The union of two systems' top-k hits can include up to 2k candidates. Its coverage
is an oracle measure of potential complementarity, not achieved fused Recall@k.
The comparison report labels it explicitly as `oracle_union_coverage`.

## Limits of the evidence

Different question generators can reduce shared phrasing, but synthetic evaluation
still does not represent real user traffic by itself. Repeated checkpoint and
parameter selection spends a development set; a fresh final test requires new,
independent questions. Preserve a designated final hold-out instead of using it
to guide every iteration.

Matching embedding dimensions does not establish matching vector spaces. Record
model identity, task/prompt construction, normalization and stored-index provenance.
Likewise, reproducing a source component does not establish parity with deployed
conversation rewriting, filters or caller parameters.

Latency measured with cached embeddings excludes original model/API latency.
Offline amortized throughput is not end-to-end serving p95. Report timing scopes,
generation costs and training budgets separately.
