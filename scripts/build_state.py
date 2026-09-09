"""
build_state.py
Normalize your source CSV into the master state store (state/leads.json).

- Maps your CSV columns to canonical fields via config.json -> csv_columns.
- Extracts the LinkedIn slug from each linkedin_url and uses it as the stable id.
- De-duplicates by slug (keeps the first occurrence, counts the rest).
- MERGE-SAFE: if state/leads.json already exists, existing per-lead progress
  (connect_status, dates, dm status, etc.) is preserved. Only new leads are added
  and core profile fields are refreshed from the CSV.

Read-only with respect to LinkedIn. Touches local files only.

Usage:
    python scripts/build_state.py
"""

import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)               # repo root
STATE_DIR = os.path.join(ROOT, "state")
LEADS_PATH = os.path.join(STATE_DIR, "leads.json")
CONFIG_PATH = os.path.join(ROOT, "config.json")

# Default 1:1 column mapping. Override any of these in config.json -> csv_columns
# to match the headers in your own CSV.
DEFAULT_COLUMNS = {
    "first_name": "first_name",
    "last_name": "last_name",
    "company_name": "company_name",
    "job_title": "job_title",
    "city": "city",
    "state": "state",
    "email": "email",
    "linkedin_url": "linkedin_url",
}


def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("ERROR: config.json not found. Copy config.example.json to "
              "config.json and edit it first.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_slug(url):
    """Return the canonical /in/<slug> identifier from a LinkedIn profile URL."""
    if not url:
        return None
    u = url.strip().lower()
    u = u.split("?")[0].split("#")[0]
    m = re.search(r"/in/([^/]+)", u)
    if not m:
        return None
    return m.group(1).strip("/").strip()


def canonical_url(slug):
    return f"https://www.linkedin.com/in/{slug}/"


def get_col(row, columns, field):
    """Read a canonical field from a CSV row using the configured column mapping."""
    src = columns.get(field, DEFAULT_COLUMNS.get(field, field))
    return (row.get(src) or "").strip()


def blank_record(slug, row, columns):
    first = get_col(row, columns, "first_name")
    last = get_col(row, columns, "last_name")
    return {
        "id": slug,
        "slug": slug,
        "first_name": first,
        "last_name": last,
        "full_name": (first + " " + last).strip(),
        "company_name": get_col(row, columns, "company_name"),
        "job_title": get_col(row, columns, "job_title"),
        "city": get_col(row, columns, "city"),
        "state": get_col(row, columns, "state"),
        "email": get_col(row, columns, "email"),
        "linkedin_url": canonical_url(slug),
        # --- progress / detected state (filled in during daily runs) ---
        "degree": None,                       # "1st" | "2nd" | "3rd"
        "is_open_profile": "unknown",         # unknown | yes | no
        "connect_status": "none",             # none | pending | accepted | declined | skipped | error
        "connect_sent_date": None,
        "connect_accepted_date": None,
        "openprofile_dm_status": "none",      # none | sent | skipped | error
        "openprofile_dm_date": None,
        "post_connect_dm_status": "none",     # none | sent | skipped | error
        "post_connect_dm_date": None,
        "last_checked_date": None,
        "name_mismatch": False,               # set true if page name != csv name
        "notes": "",
    }


# Fields that come from the CSV and may be refreshed on rebuild.
CORE_FIELDS = ("first_name", "last_name", "full_name", "company_name",
               "job_title", "city", "state", "email", "linkedin_url")


def main():
    cfg = load_config()
    columns = {**DEFAULT_COLUMNS, **cfg.get("csv_columns", {})}
    csv_path = os.path.join(ROOT, cfg["source_csv"])
    if not os.path.exists(csv_path):
        print(f"ERROR: source CSV not found: {csv_path}", file=sys.stderr)
        print("Set config.json -> source_csv to a path (relative to the repo "
              "root) that points at your leads CSV.", file=sys.stderr)
        sys.exit(1)

    os.makedirs(STATE_DIR, exist_ok=True)

    existing = {}
    if os.path.exists(LEADS_PATH):
        with open(LEADS_PATH, "r", encoding="utf-8") as f:
            for rec in json.load(f):
                existing[rec["id"]] = rec

    seen = set()
    out = []
    stats = {"rows": 0, "added": 0, "merged": 0, "dupes": 0, "no_slug": 0}

    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stats["rows"] += 1
            slug = extract_slug(get_col(row, columns, "linkedin_url"))
            if not slug:
                stats["no_slug"] += 1
                continue
            if slug in seen:
                stats["dupes"] += 1
                continue
            seen.add(slug)

            if slug in existing:
                rec = existing[slug]
                # refresh core fields from CSV, keep progress fields
                fresh = blank_record(slug, row, columns)
                for k in CORE_FIELDS:
                    rec[k] = fresh[k]
                out.append(rec)
                stats["merged"] += 1
            else:
                out.append(blank_record(slug, row, columns))
                stats["added"] += 1

    with open(LEADS_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print("Built state ->", LEADS_PATH)
    print(f"  CSV rows read:        {stats['rows']}")
    print(f"  Leads in state:       {len(out)}")
    print(f"  New leads added:      {stats['added']}")
    print(f"  Existing merged:      {stats['merged']}")
    print(f"  Duplicate slugs:      {stats['dupes']}")
    print(f"  Rows without a slug:  {stats['no_slug']}")


if __name__ == "__main__":
    main()
