# Signing Key

`sipa-os-signing-key.asc` is the public key that produced every `.asc` signature in this repo
(23 files, all in `FIRST_ERA/`). Fingerprint:

```
575F D9C9 BCD5 A546 6C8C  0E0E E855 DCEA 1093 CB22
```

Verify a signature:

```bash
gpg --import KEYS/sipa-os-signing-key.asc
gpg --verify FIRST_ERA/<file>.asc
```

Prior to 2026-08-10 this key was never published here, so the 23 `.asc` files existed but could
not be verified by anyone outside this machine's local keyring. Independently audited by
dipankarsarkar (2026-08-10) — see `AI_EXPERIMENTS/` correction history for the full finding.
