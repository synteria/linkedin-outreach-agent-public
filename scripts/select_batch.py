"""
select_batch.py
Pick the work for one daily run and write it to state/daily/batch_<date>.json.

Produces two lists:
  1. outreach_candidates  -> never-contacted leads to visit today. For each, the
     daily run visits the profile, detects degree / open-profile / connect-state,
     then (when sending is enabled) sends a connection request and, if it is an
     Open Profile, also a free intro DM. Capped by max_profile_visits_per_day; the
     per-action caps (connection_requests_per_day, open_profile_dms_per_day) are
     enforced live during the run since open-profile status is unknown until visit.
  2. followup_candidates  -> leads that ACCEPTED a connection at least
     post_accept_dm_delay_hours ago and have not yet received the post-connect DM.
     Open Profiles already cold-DMed are skipped if
     routing.send_post_connect_dm_to_open_profiles_already_dmed is false.

Selection also skips block-listed slugs from state/blocklist.csv.

Read-only. Local files only. Selecting a batch does NOT send anything.

Usage:
    python scripts/select_batch.py
"""

import csv
import json
import os
import sys
from datetime import datetime, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE_DIR = os.path.join(ROOT, "state")
DAILY_DIR = os.path.join(STATE_DIR, "daily")
LEADS_PATH = os.path.join(STATE_DIR, "leads.json")
BLOCKLIST_PATH = os.path.join(STATE_DIR, "blocklist.csv")
CONFIG_PATH = os.path.join(ROOT, "config.json")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_blocklist_slugs():
    slugs = set()
    if os.path.exists(BLOCKLIST_PATH):
        with open(BLOCKLIST_PATH, "r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                s = (row.get("slug") or "").strip().lower()
                if s:
                    slugs.add(s)
    return slugs


def main():
    if not os.path.exists(CONFIG_PATH):
        print("ERROR: config.json not found. Copy config.example.json first.",
              file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(LEADS_PATH):
        print("ERROR: state/leads.json not found. Run build_state.py first.",
              file=sys.stderr)
        sys.exit(1)

    cfg = load_json(CONFIG_PATH)
    leads = load_json(LEADS_PATH)
    os.makedirs(DAILY_DIR, exist_ok=True)

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    visit_cap = cfg["limits"]["max_profile_visits_per_day"]
    delay = timedelta(hours=cfg["timing"]["post_accept_dm_delay_hours"])
    skip_open_followup = not cfg["routing"]["send_post_connect_dm_to_open_profiles_already_dmed"]
    blocked = load_blocklist_slugs()

    # 1) never-contacted leads, in stable order
    skipped = {"blocklist": 0}
    outreach = []
    for r in leads:
        if (r["connect_status"] == "none"
                and r["openprofile_dm_status"] == "none"
                and r.get("post_connect_dm_status", "none") == "none"):
            if r["slug"].lower() in blocked:
                skipped["blocklist"] += 1
                continue
            outreach.append({
                "slug": r["slug"],
                "full_name": r["full_name"],
                "first_name": r["first_name"],
                "company_name": r["company_name"],
                "linkedin_url": r["linkedin_url"],
            })
        if len(outreach) >= visit_cap:
            break

    # 2) accepted, delay elapsed, no follow-up yet
    followup = []
    for r in leads:
        if r["connect_status"] != "accepted":
            continue
        if r["post_connect_dm_status"] != "none":
            continue
        if skip_open_followup and r["openprofile_dm_status"] == "sent":
            continue
        acc = r.get("connect_accepted_date")
        if acc:
            try:
                acc_dt = datetime.fromisoformat(acc)
                if now - acc_dt < delay:
                    continue
            except ValueError:
                pass
        followup.append({
            "slug": r["slug"],
            "full_name": r["full_name"],
            "first_name": r["first_name"],
            "linkedin_url": r["linkedin_url"],
        })

    batch = {
        "date": today,
        "generated_at": now.isoformat(timespec="seconds"),
        "caps": {
            "connection_requests_per_day": cfg["limits"]["connection_requests_per_day"],
            "open_profile_dms_per_day": cfg["limits"]["open_profile_dms_per_day"],
            "post_connect_dms_per_day": cfg["limits"]["post_connect_dms_per_day"],
            "max_profile_visits_per_day": visit_cap,
        },
        "sending_enabled": cfg["safety"]["sending_enabled"],
        "outreach_candidates": outreach,
        "followup_candidates": followup,
    }

    out_path = os.path.join(DAILY_DIR, f"batch_{today}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(batch, f, indent=2, ensure_ascii=False)

    print("Wrote batch ->", out_path)
    print(f"  Outreach candidates (visit today): {len(outreach)} (cap {visit_cap})")
    print(f"  Follow-up DM candidates:           {len(followup)}")
    print(f"  Skipped block-listed:              {skipped['blocklist']}")
    print(f"  Sending enabled:                   {cfg['safety']['sending_enabled']}")
    if not cfg["safety"]["sending_enabled"]:
        print("  NOTE: sending is OFF. This is a dry batch for review only.")


if __name__ == "__main__":
    main()
