"""
report.py
Print a status dashboard of the whole pipeline from state/leads.json.

Local files only. Read-only.

Usage:
    python scripts/report.py
"""

import json
import os
from collections import Counter
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LEADS_PATH = os.path.join(ROOT, "state", "leads.json")


def main():
    with open(LEADS_PATH, "r", encoding="utf-8") as f:
        leads = json.load(f)

    total = len(leads)
    connect = Counter(r["connect_status"] for r in leads)
    openp = Counter(r["is_open_profile"] for r in leads)
    op_dm = Counter(r["openprofile_dm_status"] for r in leads)
    pc_dm = Counter(r["post_connect_dm_status"] for r in leads)

    contacted = sum(1 for r in leads
                    if r["connect_status"] != "none" or r["openprofile_dm_status"] != "none")
    remaining = total - contacted

    def line(label, counter):
        parts = ", ".join(f"{k}={v}" for k, v in sorted(counter.items()))
        print(f"  {label:24} {parts}")

    print("=" * 56)
    print(f"LinkedIn outreach status  ({datetime.now():%Y-%m-%d %H:%M})")
    print("=" * 56)
    print(f"  Total leads:             {total}")
    print(f"  Contacted (any channel): {contacted}")
    print(f"  Untouched / remaining:   {remaining}")
    print("-" * 56)
    line("Connection status:", connect)
    line("Open-profile detected:", openp)
    line("Open-profile DM:", op_dm)
    line("Post-connect DM:", pc_dm)
    print("=" * 56)


if __name__ == "__main__":
    main()
