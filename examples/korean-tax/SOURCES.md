# Official ruling sample: sources and attribution

The public example contains four historical interpretations issued by the
**National Tax Service, Republic of Korea (국세청)** and published in its
[국세법령정보시스템](https://taxlaw.nts.go.kr/). Selection was made for an educational
walkthrough: one question target, a nearby VAT case and two different tax topics.
It is not a representative evaluation sample.

## Included sources

| Project retrieval ID | Official document number | Issued | Official source |
|---|---|---|---|
| `NTS-INTERP-VALUEADDTAX-0063027` | 부가46015-1636 | 1995-09-07 | [NTS 010000000000088650](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000088650) |
| `NTS-INTERP-INTLTAX-0109574` | 법규국조 2009-375 | 2009-11-16 | [NTS 010000000000138098](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000138098) |
| `NTS-INTERP-INCOMETAX-0009735` | 서면인터넷방문상담1팀-1308 | 2005-10-28 | [NTS 010000000000025811](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000025811) |
| `NTS-INTERP-VALUEADDTAX-0003682` | 부가22601-303 | 1992-03-10 | [NTS 010000000000009664](https://taxlaw.nts.go.kr/qt/USEQTA002P.do?ntstDcmId=010000000000009664) |

The `NTS-INTERP-…` identifiers come from the project's frozen retrieval registry.
They are project targets, not official NTS document numbers. The separate
18-digit source ID identifies the public record and is retained in each URL.
Do not assign new serials independently and expect compatibility with a trained
research checkpoint.

## Verification and transformations

Checked on **3 November 2026**: the official detail service returned matching
source IDs, titles and document numbers. Dates and selected quoted passages were
cross-checked against the official published records and the frozen corpus's
government reply/summary fields. Only a small attributed excerpt from each
reply or official 요지 is included, with its section and context recorded.
The sample is a compact representation of real rulings, not their full text.

The `summary` fields are project-authored Korean explanations. The four training
pair illustrations and alternate-wording query were authored for the public
walkthrough. They are not historical generated training rows or evaluation
questions. Original requester 질의 text, private notes and taxpayer identifiers
are not included. Candidate lists are deliberately authored to make rank fusion
inspectable; they are not saved model outputs.

For example, the target ruling distinguishes identical-product replacement from
similar-product replacement and cash refunds. The nearby VAT ruling concerns a
return from a different counterparty. Preserving those conditions matters more
than matching the shared word 반품. The excerpt from the target's paragraph 2
is explicitly labeled as concerning identical-product replacement, the branch
relevant to the example question; the summary also describes the other branches.

## Attribution and reuse boundary

Source attribution: **국세청, the four official documents and issue dates listed
above, 국세법령정보시스템**, with direct links in the sample and demo output.
No NTS sponsorship or endorsement is implied.

The [NTS copyright policy](https://www.nts.go.kr/nts/cm/cntnts/cntntsView.do?mi=6791&cntntsId=8169)
describes reuse of government-owned works and their applicable notices.
This educational example uses official metadata, brief attributed quotations
and original explanatory material. [Copyright Act Article 28](https://law.go.kr/lsLinkCommonInfo.do?chrClsCd=010202&lsJoLnkSeq=1025203557)
addresses quotations for education/research within a justifiable extent and fair
practice. Public access alone is not used to assert a blanket public-domain or
MIT status for every ruling or every item on the source website.

MIT applies to the project's code, authored summaries/questions and ranking
fixtures. Official source passages retain their source status, as recorded in
[NOTICE](../../NOTICE.md). Full-corpus redistribution is outside this sample.
Use the source links for full context and later revisions; these historical
interpretations are provided to explain retrieval, not to establish current tax advice.
