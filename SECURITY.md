# Handling sensitive material

The portable package does not load environment files, inspect provider credentials
or contact services. Keep external backend authentication in your own runtime.
Use the public-export allowlist and review its output before publication.

Never include tokens, credentials, private user questions, internal hosts or raw
provider responses in a public issue or pull request. Describe the problem using
invented data. For a suspected secret exposure, use the hosting platform's private
reporting channel when available and contact the repository maintainer privately;
do not repost the secret as evidence. This project does not configure a reporting
address or claim a guaranteed response SLA.

Artifact manifests verify content identity and containment. They are not digital
signatures and do not establish the trustworthiness of an untrusted source.
