"""Cache-aware fetching, with a manifest so every raw file is traceable to its source."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
MANIFEST = RAW / "manifest.json"

UA = "nyc-supply-rents/0.1 (research; contact via repo)"


def _manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {}


def record(name: str, url: str, path: Path) -> None:
    """Note where a raw file came from, when, and what it hashed to."""
    m = _manifest()
    m[name] = {
        "url": url,
        "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(m, indent=2, sort_keys=True))


def fetch(url: str, dest: Path, *, name: str | None = None, force: bool = False,
          retries: int = 3) -> Path:
    """Download `url` to `dest` unless it is already cached."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not force:
        print(f"  cached  {dest.name} ({dest.stat().st_size:,} bytes)")
        return dest

    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            dest.write_bytes(data)
            print(f"  fetched {dest.name} ({len(data):,} bytes)")
            record(name or dest.name, url, dest)
            return dest
        except Exception as exc:  # network flakiness, not logic errors
            last = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"failed to fetch {url}: {last}")


def socrata(dataset: str, dest: Path, *, select: str, where: str | None = None,
            group: str | None = None, order: str | None = None,
            limit: int = 50_000, offset: int | None = None, **kw) -> Path:
    """Build a Socrata query URL and fetch it through the cache."""
    params = {"$select": select, "$limit": str(limit)}
    if where:
        params["$where"] = where
    if group:
        params["$group"] = group
    if order:
        params["$order"] = order
    if offset is not None:
        params["$offset"] = str(offset)
    url = (f"https://data.cityofnewyork.us/resource/{dataset}.json?"
           + urllib.parse.urlencode(params))
    return fetch(url, dest, **kw)
