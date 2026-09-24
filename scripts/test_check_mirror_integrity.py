"""Negative control for check_mirror_integrity.py (round 47).

Every resolve/ fetch returns the 307 redirect body instead of following
it (curl without -L). Expect exit 1 and SIZE MISMATCH on every sealed
file, with no hash compared.
"""
import os, sys, urllib.error, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import check_mirror_integrity as cmi


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def test_redirect_body_fails_on_size(monkeypatch, capsys):
    opener = urllib.request.build_opener(_NoRedirect)

    def no_follow(req, timeout=30):
        try:
            return opener.open(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if 300 <= e.code < 400:
                return e  # the 307 page itself
            raise

    monkeypatch.setattr(cmi.urllib.request, "urlopen", no_follow)
    hashed, real = [], cmi.hashlib.sha256
    monkeypatch.setattr(cmi.hashlib, "sha256", lambda b: hashed.append(b) or real(b))

    rc = cmi.check("main", os.environ.get("HF_TOKEN", ""))
    out = capsys.readouterr().out
    n = int(out.split("files with a .sha256 sidecar: ")[1].split()[0])

    assert rc == 1
    assert f"SIZE MISMATCH: {n} file(s)" in out
    assert hashed == []
