# LinkedIn Outreach Agent: Design & Rationale

A simple, self-hosted version of HeyReach / PhantomBuster that drives **your own**
logged-in LinkedIn (via an AI agent in your browser) on a daily cadence. You stay
in control: human-paced actions, hard caps, and explicit safety gates.

---

## 1. Goal

Each day, semi-autonomously:

1. Send **blank connection requests** to leads from your source list (target set by
   `limits.connection_requests_per_day`).
2. **Cold-DM Open Profiles for free** (no connection or credit needed), with a
   short intro (`limits.open_profile_dms_per_day`). Open Profiles also get a
   connection request.
3. After someone **accepts** a connection, wait `post_accept_dm_delay_hours`, then
   send your `post_connect_dm` copy.
4. Keep a clean state store so nobody is ever double-contacted, and produce a daily
   report.

Keep copy short. You supply the open-profile DM copy and the post-connect line
before anything sends.

---

## 2. Detection signals (verified on a live account; UI can drift)

- **Degree** ("1st" / "2nd" / "3rd") shown next to the name. It is **independent**
  of Open Profile status.
- **Open Profile**: open the Message compose. Header shows **"Free message"** ->
  free DM, no credit, no connection needed.
- **Not Open Profile**: compose shows **"Use 1 of N InMail credits"** -> would
  cost a credit. The default flow does NOT spend InMail credits.
- **Connect button**: sometimes hidden under the **More** menu rather than
  top-level. Flow: try top-level Connect, else More -> Connect -> "Send without a
  note".
- **Already requested**: profile button reads **"Pending"** -> skip.
- **Accepted / connected**: primary **"Message"** button + **"1st"** badge.

---

## 3. Conservative starting limits

- The example configuration uses a rolling weekly cap and a smaller daily cap.
  These are starting points, not guaranteed safe limits. LinkedIn may restrict an
  account earlier based on its age, standing and activity.
- Blank requests tend to accept better than noted ones, so the default sends blank.
- DMs to new connections land best ~24-48h after accept; default is 24h.
- Free open-profile messages can be rate-limited too, hence a separate daily cap.
- Randomized delays (`min/max_seconds_between_actions`), working hours only
  (`working_hours_local_24h`), and per-day caps throttle everything. Stale invites
  can be withdrawn to protect your acceptance rate.

Tune the defaults downward for new or previously restricted accounts. Stop at the
first warning rather than trying to discover a platform limit.

---

## 4. Architecture

**Run model:** an AI agent session (Claude Code) opens your Chrome, drives your real
logged-in LinkedIn session via a browser-control integration, and reads/writes local
state. Deterministic data logic lives in small Python scripts so the agent spends
effort only on browser actions and judgement calls.

```
repo root/
  config.json                  all knobs, caps, copy, safety flags (gitignored)
  data/leads.csv               source list (gitignored)
  scripts/
    build_state.py             CSV -> state/leads.json (merge-safe, dedupe)
    select_batch.py            pick today's work -> state/daily/batch_<date>.json
    update_state.py            apply run results back into leads.json
    report.py                  pipeline status dashboard
  state/
    leads.json                 master state, 1 record per lead
    blocklist.csv              never-contact list
    daily/  batch_<date>.json  results_<date>.json
```

### State model (per lead)
`id/slug`, profile fields (first/last/full name, company, title, city, state,
email, linkedin_url), plus progress: `degree`, `is_open_profile`
(unknown/yes/no), `connect_status` (none/pending/accepted/declined/skipped/error)
+ dates, `openprofile_dm_status` + date, `post_connect_dm_status` + date,
`last_checked_date`, `name_mismatch`, `notes`.

---

## 5. Daily routing logic

For each never-contacted lead visited today (capped by `max_profile_visits_per_day`):

1. Load profile, read **name** (flag `name_mismatch` if it differs from the CSV),
   **degree**, and **connect state**.
2. If button is **Pending** or already **1st-degree** -> record and skip outreach.
3. Detect **Open Profile** via the compose "Free message" check.
   - **Open Profile** -> (a) send free intro DM [needs copy], **and** (b) send a
     blank connection request. Counts against both daily caps.
   - **Not Open Profile** -> send a blank connection request only.
4. Stop sending connects at the daily cap, open-profile DMs at theirs (and respect
   the weekly connect ceiling).

Separately, the **follow-up pass**: for leads now `accepted` whose acceptance is
>= `post_accept_dm_delay_hours` old and have no `post_connect_dm` yet -> send the
post-connect copy. Open Profiles already cold-DMed are skipped if
`routing.send_post_connect_dm_to_open_profiles_already_dmed` is false.

---

## 6. Safety model

Gates in `config.json` -> `safety`:
- `sending_enabled: false` -> the run does everything except the final
  click-to-send. Flip true only after a supervised dry run.
- `require_dm_copy_before_send: true` -> DMs refuse to send while copy is a
  `[PLACEHOLDER`.
- `withdraw_invites_enabled: false` -> stale-invite cleanup is opt-in.

Every send-type action is also rate-limited, working-hours-gated, and logged.

---

## 7. Suggested rollout phases

- **Phase 0:** install, build state from your CSV, generate a dry batch + report.
- **Phase 1:** provide copy; supervised live test on ~3-5 leads with
  `sending_enabled` on only for that test.
- **Phase 2 (optional):** withdraw old stale invites.
- **Phase 3:** turn on a conservative daily cadence and keep each run supervised.
- **Phase 4:** monitor acceptance/reply rates via `report.py`; tune caps and copy.
