# Dataset collection and reproducibility

This guide describes how the Korean tax-ruling question–identifier datasets were
assembled. It documents the reference release without distributing source
documents, generated questions, protected hold-outs or model weights. MIT applies
to the public software/specification materials, not to those external artifacts.

## 1. Source corpus: an exported snapshot, not a fresh crawl

The underlying 해석례 originate from the Korean National Tax Service's
[국세법령정보시스템](https://taxlaw.nts.go.kr/). This project started from an
**existing Milvus chunk collection**, exported read-only on 13 August 2026.
It did not construct its reference corpus by crawling the current portal anew.

The frozen export contains **135,991 rulings and 434,740 chunks**. The collection
row count was checked before and after export and against the identity scan.
One JSONL record was written per document, preserving scalar metadata and the
complete ordered chunk list. Partial output was resumable, and the completed
file was atomically finalized with a SHA-256 manifest.

For an equivalent export:

1. Scan `doc_id`, human-facing case number and detail link; require consistent
   identity across each document's chunks.
2. Extract the unique 18-digit `ntstDcmId` from the detail link. A human-facing
   case number is not unique and must not be used as the immutable key.
3. Require one-to-one source-ID/document-ID mapping. Sort document IDs numerically
   when numeric, then lexically for nonnumeric values.
4. Group chunks by document and sort by `part`, numeric `chunk_id`, then `pk`.
   Preserve chunk text, section type, chunk counts, dates, title, related laws,
   source URL and source identifiers without silently truncating source content.
5. Write the export and record schema version, counts, timestamps and content hash.

The original ingestion/crawling and chunking system predates this export. Its
configuration is not reconstructed by the portable package. A current public
portal crawl can yield different documents, text or chunk boundaries; matching
the historical counts alone does not establish the same snapshot.

## 2. Immutable source identity and versioned target IDs

The immutable source UID is `NTS-{18-digit ntstDcmId}`. The v2 training target is
`NTS-INTERP-{LAW_CODE}-{SERIAL7}`. The seven-digit serial is inherited from the
frozen earlier registry and migration map; **do not remint it by sorting a new
snapshot**. Retain the source UID, database doc ID, target ID and alias mappings.

Tax categories were reconciled against official source classifications through
a versioned normalization bridge. Explicit classification exceptions and unknown
categories remain recorded; do not guess new categories during reproduction.
Audit uniqueness, registry/corpus coverage and every chunk link. The full eligible
retrieval universe remains 135,991 even though only 135,989 rulings have retained
training questions.

## 3. Grounded question generation: four, eight, then twelve roles

Generation sees only `case_title`, `authority_date`, `related_laws`, concatenated
`reply_text` and `summary_text`. Reply/summary chunks follow frozen corpus order,
joined by newlines. Original requester questions, `detail`/`combined` chunks,
source/database/target IDs and evaluation questions are excluded from prompts.
Extensions may see already-generated training questions for that ruling, as a
separate input to discourage repetition; those questions are not citation evidence.

| Stage | Four roles introduced |
|---|---|
| Core four | Plain-language question; keyword search; fact pattern; statute-grounded application |
| Expansion to eight | Alternative plain language; concise practitioner question; alternative fact pattern; ruling-search request |
| Expansion toward twelve | Decisive condition; practical decision; focused subissue; natural search fragment |

The training generator used OpenRouter, requested `openai/gpt-5.6-luna`, canonical
revision `openai/gpt-5.6-luna-20260709`, with the authenticated Azure provider
route frozen in a runtime lock. Strict JSON-schema output was required. Core-four
and first-extension completion limits were 1,200 tokens; the last extension used
1,500. `temperature`, `top_p` and legacy `max_tokens` were not sent.

Request seeds were the signed int32 interpretation of the first four bytes of
`SHA256(contract_sha256 + NUL + condition_key + NUL + evidence_id)`. Request
idempotency also included the rendered-request hash. Save the exact prompt,
schema, safe-context hash, contract, model/provider response identity, usage and
every raw attempt. Keep content repairs and transport retries separate. Resume
only unfinished assignments and retain prior responses/failures under new attempt
names; do not overwrite a rejected response with its accepted replacement.

The last expansion reused an existing 5,000-ruling pilot and generated only the
remaining eligible rulings. Record that import's source/context provenance rather
than pretending all responses came from one generation contract.

Data-free copies of the actual Core4, extension and larger-evaluation prompts
are under [dataset_specs](../dataset_specs/README.md), alongside response schemas.
Schema `$id` metadata is anonymized; validation constraints are unchanged. The
provenance JSON records original and bundled hashes. No rendered source text or
provider response is included.

## 4. QA, leakage guards and acceptance

Accept only schema-valid Korean questions supported by the supplied ruling's
reply/summary. Reject identifier leakage, source-reference phrasing, unsupported
law/article citations, duplicate roles/text within a response and excessive title
copying. The frozen title checks reject character-trigram Jaccard at or above
0.60 and full normalized title containment when the title has at least 20
characters. Preserve validator versions and any adjudicated false positives.

For the last extension, the frozen guards reject same-document character-trigram
Jaccard at or above **0.65** against either development set or the protected
original requester-question hold-out, and at or above **0.70** against existing
training questions. Trigram comparison uses whitespace-free, lowercase NFKC text.
Protected text is checked locally, never inserted into a provider prompt or a
repair request; repairs receive failure codes only. Guard access is not permission
to train on or repeatedly evaluate model performance on the final hold-out.

These are lexical contamination guards, not a guarantee of semantic independence.
QA thresholds also evolved through versioned amendments; retain the original
validators/decisions to reconstruct historical releases instead of retroactively
applying the newest policy to every earlier question.

## 5. Consolidation and the reversal of near-duplicate removal

The historical releases are separate, immutable artifacts:

| Release | Retained training pairs |
|---|---:|
| Original Core4 before the disputed deduplication | 543,867 |
| Core4 after historical exact/near deduplication | 533,710 |
| Initial expanded-eight release using that base | 1,077,069 |
| Restored expanded-eight exact-only base | 1,080,148 |
| Final expanded-twelve release | **1,622,929** |

The old near-duplicate rule used a 0.85 similarity threshold and removed useful
nonidentical wording. The restored eight-question release returned to the original
Core4 rows, retained near-duplicates, and applied normalized exact cross-document
collision handling with a deterministic one-question floor. Its historical
normalizer retained only alphanumeric characters after NFKC/lowercasing. Existing
extension questions were rechecked against the restored base. The resulting base
contains **536,790 Core4 rows + 543,358 extension rows = 1,080,148**. Its coverage
exception is preserved; it is not a claim of zero ambiguous base questions.

The twelve-question release **copies every restored-base row and byte unchanged**.
Its addition policy uses a more conservative formatting-equivalence key:

- NFKC, lowercase and remove whitespace.
- Ignore commas only when not between digits; ignore specified middle-dot forms
  only between Hangul syllables.
- Strip terminal `!`, `?`, `。` and terminal periods except immediately after a digit.
- Preserve numeric separators, decimal points, operators, dates, percent signs,
  slashes, hyphens, colons, brackets and unreviewed punctuation.

Apply the key to additions and base comparisons, without rewriting question text:

1. If a new question matches any base question, omit the new row, retain the base.
2. If the same new key points to multiple rulings, omit all new copies; do not
   assign an arbitrary target.
3. For repeated new keys within one ruling, retain the lowest deterministic
   query ID. Question IDs use `Q-` plus the first 32 hex digits of
   `SHA256(contract_sha256 + NUL + evidence_id + NUL + role)`.
4. Retain nonidentical near-duplicates. Do not apply a new fuzzy-deletion threshold.

Thirty-four punctuation-dependent collision groups were reviewed before the policy
was frozen. The release had **543,948 accepted new candidates**, omitted **1,167**
rows (1,164 cross-ruling copies, two same-ruling base repeats, one other-ruling
base match), and retained **542,781 additions**. Thus:

`1,080,148 preserved base rows + 542,781 additions = 1,622,929 pairs`.

Two rulings had provider-filtered new-generation attempts and retained their base
questions. They were not deleted from training. There are 135,989 training rulings,
128,780 with all twelve roles, averaging 11.9343 questions/ruling. "Twelve" is the
design, not a promise of exactly twelve accepted rows for every ruling. Save every
omission with reason and raw-response provenance, then audit independently before
freezing the manifest. Do not conflate exact collisions with legal equivalence:
an omitted single-target question can still have multiple relevant rulings.

## 6. Independent development questions and final hold-out

| Artifact | Origin and use |
|---|---|
| Older development set | 988 Gemini 3.7 Flash synthetic questions; continuity reference, fixed subset 931 |
| Larger development set | 4,992 Sonnet 5 synthetic questions, one per sampled ruling; fixed subset 4,697 |
| Original requester-question hold-out | 121,833 questions retained separately for the intended final real-voice test |

The larger development set cost-record/manifest identifies a different generator
vendor from training. It spans tax categories, forbids article numbers in its
questions and is disjoint from the older development set at the target-document
sample level. Its 4,697 subset is frozen by the rulings' original four-role training
coverage; expanding training to eight/twelve does not redefine that subset.

Train and development target documents overlap intentionally in closed-corpus GR;
the held-out item is the question. Do not put training questions into the model's
evaluation set, and do not split rows randomly after generation without recording
their role/provenance. Existing synthetic development sets were repeatedly used
for checkpoint decisions; they are not a fresh independent final benchmark.

## 7. Reference checksums and reproduction boundary

[dataset_specs/provenance.json](../dataset_specs/provenance.json) records selected
counts and SHA-256 identities for the frozen corpus, registry, restored base,
final training pairs and both development files. It contains no research rows,
source URLs identifying individual rulings, internal hosts, local paths or secrets.
The checksums are reference identities, not downloadable dataset artifacts.

For byte-identical reproduction, authorized access is needed to the original
snapshot, registry/migration/classification bridge, accepted and failed raw
responses, prompt rendering/validators, recovery imports, manual exception and
omission decisions, exact serializers/order and frozen build implementations.
These are not all distributed with the code-only package. Even the same seeded
API call may return different text later or cease to be available; regenerate a
new versioned dataset instead of claiming it is the historical release.

For a new dataset following the same method, preserve a manifest at each stage:
collection → registry → generation/QA → restored base → additions → consolidated
training → frozen evaluation. Verify identity coverage, counts, hashes, role
distribution, omission reconciliation, question contamination and byte preservation
of imported releases before training. The portable package can verify relative-path
artifact manifests with `genrag verify`; it does not crawl the portal or execute
the private generation/consolidation pipeline.
