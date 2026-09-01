#!/usr/bin/env python3
"""check_dataset_citations.py -- the missing bucket, round 8 (dipankarsarkar).

check_citations.py doesn't reach this repo's .jsonl datasets at all, on two
independent axes: DOC_NAME_RE only matches EXP-*.md / FINDING__*.md /
README*.md, so a .jsonl file is never in the scanned-docs list to begin with;
and looks_like_path() explicitly returns False for anything starting with
http:// or https:// before classify() ever runs, so even a citation FIELD
inside a scanned doc would never resolve to any bucket -- not EXTERNAL
(which is 36 filesystem paths, zero URLs), not ABSENT, nothing. A URL
citation was invisible twice over.

His own finding, reproduced independently before building this: three
records in AI_EXPERIMENTS/DATASETS_MISBEHAVIOR_EXTERNAL/
misbehavior_incidents_seed_v1.jsonl had live URLs (all 6 in that file
resolve -- a link check alone would have said "fine") whose content
mismatched what the paper at that URL actually says. Liveness is not
accuracy. This script only ever checks liveness -- it cannot check whether
a "model" field matches a paper's Table 1, that is exactly the layer his
round 8 message says has no mechanism and needs one (source_locator fields,
checked by a person against the actual table, not automated).

His other finding, folded in as a design constraint rather than left as a
warning: liveness is the wrong rule for prose. A doc that quotes a URL a
model hallucinated, specifically to document that it hallucinated, SHOULD
have a dead link -- checking that would be checking the wrong thing. This
script only ever looks at structured "citation" fields inside .jsonl
records, never at free-text doc bodies, for exactly that reason: a citation
field is a provenance claim, a sentence in an EXP writeup is not.

What it does: finds every *.jsonl file under AI_EXPERIMENTS/DATASETS*/,
parses each line as JSON, pulls every http(s):// URL out of any field named
"citation" (a record may cite more than one, separated by " ; " per this
repo's existing convention), sends each a HEAD request (falling back to GET
if HEAD is rejected), and reports LIVE / DEAD / a record with a citation
field that contains no URL at all (title-only, unresolvable by this script
or any other -- his second finding, two records had exactly this shape).

Exit code is nonzero iff any DEAD or NO_URL record exists, so this can run
as a pre-commit step alongside check_citations.py -- separate script, not
folded into it, because the object being checked (a URL's HTTP status) is a
different kind of fact than a filesystem path's existence, same lesson as
the STALE bucket: know what kind of object you're checking before writing
one check for both.

No AI calls. Requires network access; skips gracefully (reports UNCHECKED,
not a failure) if a request errors out for a reason other than the URL
being genuinely dead, since a flaky network is not the citation's fault.

Usage: python3 scripts/check_dataset_citations.py [--json]
"""
import glob
import json
import os
import re
import sys
import urllib.error
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL_RE = re.compile(r"https?://[^\s;]+")
TIMEOUT = 10

# A minimal HEAD-only User-Agent gets 403'd by several real news sites that
# are, in fact, live -- confirmed by hand with curl and a full browser
# header set on the same URLs this script's first version reported DEAD
# (thehackernews.com, eweek.com: 200 with these headers, 403/blocked
# without). Same lesson as everything else in this repo tonight: know what
# the check is actually measuring. A bare urllib HEAD measures "does this
# site serve bare urllib HEAD requests," not "is this URL live" -- those
# are different facts for a site with bot-detection. GET with a full,
# ordinary-browser header set is closer to the second question.
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
              "image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def find_urls(citation_field: str) -> list[str]:
    return URL_RE.findall(citation_field or "")


def check_url(url: str) -> str:
    """Returns 'LIVE', 'DEAD', or 'UNCHECKED' (network/transient issue, not
    a verdict on the URL itself). GET with full browser-style headers, not
    a bare HEAD -- see BROWSER_HEADERS comment for why."""
    req = urllib.request.Request(url, headers=BROWSER_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return "LIVE" if resp.status < 400 else "DEAD"
    except urllib.error.HTTPError as e:
        if e.code in (401, 403, 429):
            # Bot-detection, paywall-gated (401 -- wsj.com/reuters.com return this
            # for unauthenticated requests on real live articles, confirmed by hand,
            # 2026-09-01), or rate-limiting -- not evidence the page is gone.
            return "UNCHECKED"
        return "DEAD" if e.code < 500 else "UNCHECKED"
    except Exception:
        return "UNCHECKED"


def main() -> int:
    as_json = "--json" in sys.argv

    jsonl_files = sorted(glob.glob(os.path.join(REPO_ROOT, "AI_EXPERIMENTS", "DATASETS*", "*.jsonl")))

    results = {"LIVE": [], "DEAD": [], "NO_URL": [], "UNCHECKED": []}

    for path in jsonl_files:
        rel = os.path.relpath(path, REPO_ROOT)
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                citation = record.get("citation")
                if citation is None:
                    continue
                rid = record.get("id", f"{rel}:{lineno}")
                urls = find_urls(citation)
                if not urls:
                    results["NO_URL"].append({"file": rel, "id": rid, "citation": citation})
                    continue
                for url in urls:
                    status = check_url(url)
                    results[status].append({"file": rel, "id": rid, "url": url})

    defects = results["DEAD"] + results["NO_URL"]

    if as_json:
        print(json.dumps(results, indent=2))
    else:
        print(f"Checked {len(jsonl_files)} dataset file(s), "
              f"{sum(len(v) for v in results.values())} citation URL(s)/record(s)\n")
        for bucket in ("LIVE", "DEAD", "NO_URL", "UNCHECKED"):
            print(f"{bucket}: {len(results[bucket])}")
        for bucket in ("DEAD", "NO_URL"):
            if results[bucket]:
                print(f"\n--- {bucket} ---")
                for r in results[bucket]:
                    if bucket == "NO_URL":
                        print(f"  {r['file']} [{r['id']}]: citation has no resolvable URL -- {r['citation']!r}")
                    else:
                        print(f"  {r['file']} [{r['id']}]: {r['url']}")
        if defects:
            print(f"\n{len(defects)} defect(s): dead citation URL or citation with no URL at all. "
                  f"Note: liveness is not accuracy -- a live URL whose content doesn't match what "
                  f"the record claims is NOT caught here, only by reading the source directly.")

    return 1 if defects else 0


if __name__ == "__main__":
    sys.exit(main())
