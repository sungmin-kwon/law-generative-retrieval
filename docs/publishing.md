# Preparing a public repository

The research workspace and the public source tree have different contents.
Use the package's explicit allowlist rather than copying the workspace or staging
everything with `git add .`.

```bash
genrag export-public --source . --output ../generative-retrieval-public
# Add --forbid-text for organization names, internal hosts or other private terms.
cd ../generative-retrieval-public
genrag verify public-export-manifest.json
python -m pip install ".[dev]"
python -m unittest discover -s tests/public -v
python -m build
```

An existing destination is never overwritten. The command screens approved text
files for common provider tokens/private keys and optional confidential terms,
then copies and hashes the reviewed files into a new tree. It excludes environment
files, private meeting/operational documents, notebook outputs, research datasets,
weights and historical experiment contracts/runners by construction.

The scanner is a targeted check, not a proof that every secret, confidential fact
or ownership issue can be recognized automatically. Review the exported tree and
its build artifacts before publication. The code-only export uses MIT; preserve
LICENSE and NOTICE. The dataset guide and data-free specifications explain
provenance without distributing the full research data. The four-ruling worked
example separately identifies official excerpts and project-authored material;
preserve its source links and attribution. Do not apply the software
license to separately obtained datasets or model weights.

When the local tree is ready:

```bash
git init -b main
git status --short
# Review files, stage the approved tree, commit, then configure your chosen remote.
```

This project does not create a remote repository, push a branch or publish a
package automatically. If files in the export change, regenerate the manifest
from the reviewed source or create a new export; the old manifest should fail
verification rather than silently describe a different tree.
