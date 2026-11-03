# Architecture

The reusable package separates data normalization, evaluation and ranking from
provider/model execution. This makes the same checks usable with generative IDs,
dense retrieval, keyword search or an existing hybrid component.

| Module | Responsibility |
|---|---|
| `models` | Immutable prediction and candidate-universe contracts |
| `demo` | Four attributed official Korean rulings, actual fusion/lookup and a walkthrough |
| `trie` | Tokenizer-independent registered-ID decoding constraints |
| `adapters` | Strict conversion from saved JSONL formats |
| `evaluation` | Recall/MRR, fixed cohorts and paired hit transitions |
| `ranking` | Highest-score chunk aggregation and weighted document RRF |
| `embeddings` | Explicit model/dimension specification and backend protocol |
| `io` | Strict UTF-8 JSON, streaming input, hashing and atomic output |
| `integrity` | Portable artifact verification and path containment |
| `release` | Public-source allowlist and publication screening |
| `cli` | Thin orchestration, arguments and safe error presentation |

There are no global database clients, environment-file loads, model downloads
or import-time GPU operations. Provider SDKs belong in separately configured
adapters. A backend implementing `QueryEmbedder.embed_query` can be injected
without making the evaluation layer depend on its credentials or runtime.

The runnable Korean demo uses the installed `data/korean_tax_rulings.json` resource,
so it works without a repository checkout or a particular working directory.
Its prewritten channel rankings are fixtures, not substitutes for a real model
evaluation. The question, training-pair illustrations and returned document titles
make the Korean 해석례 use case concrete. Official titles, dates and excerpts
retain attribution; summaries/questions are project-authored. Research question
releases and full ruling texts are not bundled.

## Chunk and document boundaries

Retrievers usually return chunks; users and generative retrievers often target
documents. These are different ranking units. `collapse_chunks` selects the
highest-scoring chunk per document and orders documents deterministically. A
new lower-scoring chunk cannot reduce a document's selected score.

Apply `reciprocal_rank_fusion` to document rankings, with explicit channel
weights. A duplicate document votes once per channel. Unknown positions still
consume rank. Ties use total score, best input rank and identifier, making results
independent of channel insertion order.

These rules are an explicit recipe, not a guarantee of better retrieval. Compare
alternative aggregation and fusion rules on a fixed development cohort before
selecting a recipe for a fresh test.

## Immutable experiment compatibility

Research workspaces can retain frozen scripts and contracts whose paths and
SHA-256 digests are part of their provenance. The new package does not rewrite
or import those runners. New experiments should import reusable functions from
`genrag`; old runs keep their exact historical code. Migration therefore does
not silently alter a running experiment or retroactively change its metrics.

The public export includes the portable package, tests, examples and documentation.
It excludes the private experiment tree and research data/model artifacts;
the four-ruling public sample is explicitly allowlisted. A source
allowlist is stronger than relying on ignore patterns alone.
