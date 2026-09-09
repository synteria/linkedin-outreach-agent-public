# Daily Run Runbook (for the agent session)

The step-by-step procedure for one daily run. It assumes Chrome is open with your
logged-in LinkedIn and that Claude Code can drive it via a browser-control
integration. **Do not send anything while `config.json -> safety.sending_enabled`
is `false`.**

---

## 0. Pre-flight
1. Confirm the user authorised this exact run. A configuration flag alone is not
   permission to contact people.
2. Load `config.json`. Read caps, timing, routing, safety, copy.
3. **Hard stop if** `safety.sending_enabled` is true but a DM copy body still
   contains `[PLACEHOLDER`. Never send placeholder copy.
4. Open `https://www.linkedin.com/feed/`, screenshot, confirm you are logged in as
   `account.name`. If not logged in, stop and notify.
5. Check local time is within `timing.working_hours_local_24h`. If outside, stop.

## 1. Build / refresh state and pick the batch
```
python3 scripts/build_state.py      # merge-safe; preserves progress
python3 scripts/select_batch.py     # writes state/daily/batch_<date>.json
```
Read the batch file: `outreach_candidates` (visit today) and `followup_candidates`.

## 2. Follow-up pass first (cheapest, highest value)
For each `followup_candidate`:
1. Open their profile. Confirm still 1st-degree (Message button + "1st").
2. Open Message compose. Type the `copy.post_connect_dm.body` (with `{first_name}`
   substituted).
3. If `sending_enabled` -> send. Else screenshot only, do not send.
4. Record `post_connect_dm_status = sent` (or `skipped`/`error`).
Stop at `post_connect_dms_per_day`.

## 3. Acceptance sweep
Re-check leads with `connect_status = pending`:
- Quick path: open `https://www.linkedin.com/notifications/` and read
  "X accepted your invitation" items; match names to pending leads.
- Or visit the profile: a **Message** button + **1st** badge = accepted.
Mark newly accepted leads `connect_status = accepted` (date auto-stamped). They
become follow-up candidates after the delay.

## 4. Outreach pass
Track two counters: `connects_sent`, `op_dms_sent`. For each `outreach_candidate`
until a cap blocks all remaining work:
1. Open the profile. Screenshot. Read name (set `name_mismatch` if it differs from
   CSV), `degree`, and the primary button.
2. If button is **Pending** -> record `connect_status = pending`, skip.
   If **1st-degree** already -> record `connect_status = accepted`, skip outreach.
3. **Open-profile check:** click **Message** to open compose.
   - Header **"Free message"** -> Open Profile.
     - If copy present and `sending_enabled` and `op_dms_sent < cap`: fill subject +
       body from config, send, `op_dms_sent += 1`, `openprofile_dm_status = sent`.
       Else screenshot only.
     - Close compose. Then also send a **blank connection request** (step 4a).
   - Header **"Use N InMail credits"** -> NOT open. Close compose (do NOT spend a
     credit). Go to step 4a.
4. **4a. Blank connection request** (if `connects_sent < cap` and weekly ceiling
   not breached):
   - Find **Connect**: top-level button if present, else **More -> Connect**.
   - In the modal choose **"Send without a note"**.
   - If `sending_enabled` -> confirm. Else cancel/screenshot only.
   - `connects_sent += 1`, `connect_status = pending`, `is_open_profile = yes/no`.
5. Wait a randomized `min..max_seconds_between_actions` between leads.
Stop when both caps are reached or candidates run out.

## 5. Persist + report
1. Write outcomes to `state/daily/results_<date>.json` (list of
   `{slug, ...updates}` per the keys in `update_state.py`).
2. ```
   python3 scripts/update_state.py state/daily/results_<date>.json
   python3 scripts/report.py
   ```
3. Summarize: connects sent, open-profile DMs sent, follow-ups sent, acceptances
   detected, any errors / name mismatches.

## 6. Stale-invite withdrawal (optional, if `safety.withdraw_invites_enabled`)
Open `mynetwork/invitation-manager/sent/`. The list is sorted newest-first and shows
age ("Sent 1 month ago"...). Withdraw up to `limits.withdraw_invites_per_day`
invites older than `timing.withdraw_stale_invites_after_days`. Capture each
withdrawn person (slug + name) into `state/blocklist.csv` first if not already there.

How to withdraw (IMPORTANT):
- The row "Withdraw" is an `<a>` and the confirm modal needs TRUSTED input, so
  synthetic JS `.click()` does NOT work. Use a real mouse / computer tool.
- The list collapses upward after each confirm, so the next item takes the top slot.
- Do small paced batches (~8 at a time) with a short wait after the row click and
  after confirm, then re-read the remaining count. Long blind bursts desync and can
  mis-click, keep them short and verify.

---

## Screenshot fallback (when the renderer lags)
If a screenshot times out, the page is usually still responsive. Use a JS evaluate
tool to locate elements and verify outcomes, e.g.:
- Connect/Pending state and a button's center coords: find the visible element whose
  text === 'Connect' / 'Pending', use getBoundingClientRect.
- Open-profile check: open Message compose, then test
  `/Free message/i.test(document.body.innerText)` (open) vs `/InMail credit/i`.
- Confirm a send: `/Invitation sent/i.test(document.body.innerText)` or the button
  flipped to 'Pending'.
Then click the JS-provided coordinates with the real mouse / computer tool.

## Guardrails (always)
- Never send placeholder copy. Never spend InMail credits in the default flow.
- Never treat an enabled config flag as permission for an unrequested run.
- Never exceed daily caps or the `weekly_connection_cap` rolling-week ceiling.
- One human-like action at a time with randomized delays; working hours only.
- On any unexpected modal, captcha, or "you're out of invitations" warning: stop and
  notify rather than retrying.
- Any pixel coordinates you cache are window-specific; re-verify with a screenshot or
  JS rect, layouts shift.
