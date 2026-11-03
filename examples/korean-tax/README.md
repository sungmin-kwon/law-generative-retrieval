# Korean tax-ruling retrieval: worked example

Run `genrag demo-ko` after installing the package. `--json` returns the same
example as structured JSON. Everything needed is packaged in the wheel, so the
command works from any directory without an API, model or database.

## The question and corpus

The reader asks **변질된 물건을 거래처에서 반품받아 동일한 제품으로 바꿔 주면
수정세금계산서도 발급해야 하나요?**
The expected document is `NTS-INTERP-VALUEADDTAX-0063027`, official reference
[부가46015-1636, 1995-09-07](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000088650).
The other three official rulings concern a foreign branch's head-office accounts,
mixed business/household vehicle costs and a return by a different counterparty.
That last case shares VAT/return terminology but concerns a different legal issue.

The [packaged JSON](../../src/genrag/data/korean_tax_rulings.json) is the single source
for the documents, four question–ID training-pair illustrations, example query
and channel rankings. The documents are real NTS interpretations with official
metadata, source URLs and short, contextualized excerpts. The summaries and
questions are project-authored. They describe historical rulings without asserting
current legal applicability. See [sources, selection and attribution](SOURCES.md).

## Follow the actual code

1. `load_korean_sample` reads the installed JSON resource.
2. `run_korean_demo` constructs the explicit four-document universe and checks
   the sample rankings and consistent NTS source attribution. Every identifier
   must resolve to one of the four documents.
3. `IdentifierTrie` validates candidate membership. Here IDs use Unicode
   character codes with EOS zero for teaching; this is not the private model's
   tokenizer. After prefix `NTS-INTERP-`, the permitted next characters are I and V.
4. `reciprocal_rank_fusion` combines dense and BM25 document ranks, then combines
   all three channels including the illustrative GR candidates. The example
   uses constant 60 and equal weights; these are demo settings, not tuned
   production recommendations.
5. `Prediction.gold_rank` locates the expected ID, and the selected ID is looked
   up in the sample to display its Korean title, official reference, source URL,
   project-authored summary and labeled official excerpt.

See [the demo implementation](../../src/genrag/demo.py) and
[its tests](../../tests/public/test_korean_demo.py).

## What the example demonstrates

In these deliberately constructed rankings, the expected ruling is third in the
two-channel hybrid list and first after adding GR. All candidate lists and the
expected rank are printed so the change is inspectable. This is an illustration
of ranking mechanics, not a measured performance improvement: the dense/BM25/GR
inputs were hand-authored and no embeddings or language-model predictions were
generated.

The four question–ID illustrations are newly authored for this walkthrough and
map different wordings to the same real ruling. The example query differs from
those strings. They are not copied from the frozen training/development files or
the original requester-question hold-out, and no model is trained by this command.

For real evaluation, use your own saved model/search outputs over a declared
eligible corpus, freeze independent question cohorts and compare full matching
inputs. See [evaluation methodology](../../docs/evaluation.md) and
[the real dataset's provenance method](../../docs/dataset-reproducibility.md).
