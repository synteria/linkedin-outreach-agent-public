# LinkedIn Outreach Agent

This repository manages conservative LinkedIn outreach through a visible,
user-controlled browser. Read `README.md` and `docs/RUNBOOK.md` before acting.

## Operating boundary

- Work only on the logged-in account named in `config.json`.
- Treat the selected daily batch and configured caps as hard limits.
- Never send while `safety.sending_enabled` is false.
- Never send placeholder copy.
- Never spend an InMail credit.
- Never bypass a CAPTCHA, restriction, invitation warning or security prompt.
- Stop on an account mismatch, unexpected dialog or ambiguous result.
- Do not schedule or run outreach unattended.
- Do not contact anyone in `state/blocklist.csv`.

## Daily flow

1. Read `config.json` and confirm the requested run is authorised.
2. Run `python3 scripts/build_state.py`.
3. Run `python3 scripts/select_batch.py` and inspect the generated batch.
4. Open LinkedIn in the visible browser and verify the account name.
5. Process eligible follow-ups, accepted connections and new connection requests
   within the configured caps.
6. Confirm each action from the visible LinkedIn state before recording it.
7. Write outcomes to `state/daily/results_<date>.json`.
8. Run `python3 scripts/update_state.py <results-file>`.
9. Run `python3 scripts/report.py` and report the completed and skipped counts.

## Privacy

`config.json`, real lead CSVs and all generated state are gitignored. Before any
commit or push, inspect `git status --short` and scan tracked files for personal
data, credentials, conversation URLs and message history.

## LinkedIn behaviour

- A primary Message button does not prove that a profile can receive a free
  message. Confirm the compose window says `Free message`.
- If the compose window says an InMail credit will be used, close it.
- Connection requests are blank unless the user explicitly supplies and approves
  a note.
- Confirm a connection request only after LinkedIn shows `Pending` or an
  equivalent success state.
- Confirm a message only after it appears in the conversation.
- Use moderate pacing and stay within the configured working hours.

The scripts prepare and update local data. They do not send anything by
themselves.
