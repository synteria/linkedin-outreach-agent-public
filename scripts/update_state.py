"""
update_state.py
Apply the results of a daily run back into state/leads.json.

Input: a JSON file (the "results" file) shaped as a list of updates:
  [
    {"slug": "john-smith-example",
     "is_open_profile": "yes",
     "degree": "3rd",
     "connect_status": "pending",
     "openprofile_dm_status": "sent"},
    ...
  ]

Allowed update keys (anything else is ignored, for safety):
  degree, is_open_profile, connect_status, connect_sent_date,
  connect_accepted_date, openprofile_dm_status, openprofile_dm_date,
  post_connect_dm_status, post_connect_dm_date, name_mismatch, notes

Convenience: if a status is set to "sent"/"pending"/"accepted" and the matching
date field is omitted, it is auto-stamped with now().

Local files only.

Usage:
    python scripts/update_state.py path/to/results.json
"""

import json
import os
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE_DIR = os.path.join(ROOT, "state")
LEADS_PATH = os.path.join(STATE_DIR, "leads.json")

ALLOWED = {
    "degree", "is_open_profile", "connect_status", "connect_sent_date",
    "connect_accepted_date", "openprofile_dm_status", "openprofile_dm_date",
    "post_connect_dm_status", "post_connect_dm_date", "name_mismatch", "notes",
}

AUTO_DATE = {
    "connect_status": {"pending": "connect_sent_date", "accepted": "connect_accepted_date"},
    "openprofile_dm_status": {"sent": "openprofile_dm_date"},
    "post_connect_dm_status": {"sent": "post_connect_dm_date"},
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/update_state.py <results.json>", file=sys.stderr)
        sys.exit(1)
    results_path = sys.argv[1]

    with open(results_path, "r", encoding="utf-8") as f:
        updates = json.load(f)
    with open(LEADS_PATH, "r", encoding="utf-8") as f:
        leads = json.load(f)

    by_slug = {r["slug"]: r for r in leads}
    now_iso = datetime.now().isoformat(timespec="seconds")
    applied, missing = 0, []

    for upd in updates:
        slug = upd.get("slug")
        rec = by_slug.get(slug)
        if not rec:
            missing.append(slug)
            continue
        for k, v in upd.items():
            if k == "slug" or k not in ALLOWED:
                continue
            rec[k] = v
            # auto-stamp companion date if caller didn't provide one
            date_field = AUTO_DATE.get(k, {}).get(v)
            if date_field and not upd.get(date_field):
                rec[date_field] = now_iso
        rec["last_checked_date"] = now_iso
        applied += 1

    with open(LEADS_PATH, "w", encoding="utf-8") as f:
        json.dump(leads, f, indent=2, ensure_ascii=False)

    print(f"Applied updates to {applied} lead(s).")
    if missing:
        print(f"WARNING: {len(missing)} slug(s) not found: {missing[:10]}")


if __name__ == "__main__":
    main()
