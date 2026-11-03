# Synthetic demonstration

All identifiers and predictions here are invented. They are not documents,
training examples, private questions or measured research results. The short
rankings have a declared maximum depth of ten; empty results count as misses.

Expected dense results: Recall@1 = 0.2, Recall@5/10 = 0.6, MRR@10 = 11/30.
Expected generative results: Recall@1 = 0.6, Recall@5/10 = 0.8, MRR@10 = 2/3.
The runs have two shared hits, one dense-only hit, two generative-only hits and
zero shared misses. Their oracle union covers all five questions, but this is
not a claim that an actual fused ranking will achieve the same result.

`cohort.json` selects three fixed query IDs to demonstrate cohort evaluation.
