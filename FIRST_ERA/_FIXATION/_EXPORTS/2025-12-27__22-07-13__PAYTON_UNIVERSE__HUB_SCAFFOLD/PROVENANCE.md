# Provenance — 2025-12-27 HUB_SCAFFOLD export

**Added 2026-08-11, unsigned.** This directory is a supplementary evidence
addition, not part of the original PGP-signed FIRST_ERA pack (signature
batch 2026-07-02, key created 2026-05-26). Nothing here is claimed to be
under that signature.

## Why this exists

Following dipankarsarkar's audit point (2026-08-11): the signed pack's
lower time bound is the signing key's creation date, 2026-05-26. Every
December-2025-dated document in the pack is cryptographically unbound
before that date on the signature alone. This directory adds an
independent partial answer.

## What was verified

The zip `2025-12-27__22-07-13__PAYTON_UNIVERSE__HUB_SCAFFOLD.zip` was
pulled live from a third device (X5, ZeroTier 172.27.202.218) at
`/storage/emulated/0/PROJECT/INCOMING/`, not from server-local storage.

- Zip sha256: `60e3f23b93e2bfccbec386053f04818e080f41ee277b7fad0424a598695716ac`
  — matches the entry on line 13 of `FIRST_ERA/INCOMING_SHA256_COMPLETE__2026-07-02.txt`
  (the already-signed manifest) exactly.
- All 8 `.log` files and the `MANIFEST_FILES.txt` inside the zip were
  individually re-hashed after extraction and verified against their own
  `.sha256` sidecars, also inside the zip. 9/9 match.

## What this does and does not prove

**Does:** the exact bytes referenced in the signed manifest exist,
byte-identical, on a separate physical device outside the signing
infrastructure. That device's own directory listing shows this file
alongside ~70 other December-2025/January-2026-dated archives never
touched since.

**Does not:** independently timestamp this specific zip's creation to
2025-12-27 the way a third-party server clock would (e.g. an email
header, a GitHub commit). The X5 device's own filesystem timestamps are
not "someone else's clock" — the same caveat dipankarsarkar raised about
git history applies here.

## Related independent evidence (different mechanism, same question)

Five GitHub repositories under Soul-In-PsyAbstract, each with GitHub's own
server-recorded creation timestamps, form a continuous cluster starting
before the May 2026 signing key existed:

| Repository | Created (GitHub server time) |
|---|---|
| payton-heart | 2025-12-29T15:17:37Z |
| payton-canon | 2025-12-29T18:06:40Z |
| SoulInPsyAbstract-AI | 2025-12-31T02:59:32Z |
| SoulInPsyAbstract-TERMUX | 2026-01-25T13:20:15Z |
| soul-in-psyabstract-site | 2026-02-01T01:15:09Z |

No direct hash cross-reference was found between this scaffold zip's
content and any of these five repos (checked via GitHub code search,
zero hits on both the zip hash and the eight individual file hashes).
The X5 device copy and the GitHub repo cluster are two separate,
independent lines of evidence pointing at the same window — not one
proof reinforcing itself.
