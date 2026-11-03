# Data-free dataset specifications

These files support the [dataset reproducibility guide](../docs/dataset-reproducibility.md).
They contain prompt templates, response schemas and selected aggregate provenance
metadata, not source documents, rendered prompts, generated questions or raw API
responses. They are part of the MIT-licensed software/specification export; the
underlying datasets and third-party material are not redistributed or relicensed.

| Stage | Prompt | Response schema |
|---|---|---|
| First four training roles | `prompts/core4.md` | `schemas/core4.json` |
| Roles five through eight | `prompts/extension4.md` | `schemas/extension4.json` |
| Roles nine through twelve | `prompts/extension8.md` | `schemas/extension8.json` |
| Reused twelve-role pilot | `prompts/extension8-pilot.md` | `schemas/extension8.json` |
| Larger development set | `prompts/evaluation-sonnet.md` | `schemas/evaluation-sonnet.json` |

Prompts are exact data-free copies of their frozen source templates. Schema `$id`
metadata is replaced with a neutral URN and JSON is reserialized; validation fields
are unchanged and no schema uses `$ref`. `provenance.json` records both original
and bundled hashes and marks the transformation. Do not substitute a bundled
schema's byte hash for its historical source hash when verifying old contracts.

The original eight-to-twelve pilot also used an earlier prompt before the full
remaining-corpus prompt. Its accepted responses were imported with their original
provenance. The full prompt here is not a claim that reused pilot responses were
generated under a different prompt retroactively.

Reference artifact hashes identify undistributed research files. They do not
grant data access or promise that new API calls will reproduce the old bytes.
