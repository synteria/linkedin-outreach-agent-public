# LinkedIn Outreach Agent

A local, human-supervised workflow for managing LinkedIn connection requests and
follow-up messages from your own browser.

The repository provides deterministic Python scripts for preparing batches,
tracking outcomes, enforcing limits and preventing duplicate outreach. An AI agent
handles the visible browser steps under the rules in `CLAUDE.md` and
`docs/RUNBOOK.md`.

## Important warning

Automating LinkedIn may violate the
[LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement) and can
result in restrictions or account suspension. This project is intended for
conservative, supervised use on your own account. It is not affiliated with
LinkedIn.

Do not use it for spam, deceptive messaging, unlawful discrimination or outreach
that violates privacy, marketing or data-protection law.

## What it does

- Imports and deduplicates a CSV of LinkedIn profiles.
- Creates a daily batch within configurable limits.
- Supports blank connection requests and free messages to Open Profiles.
- Queues a follow-up after an accepted connection.
- Tracks every outcome locally so the same person is not contacted twice.
- Applies a local blocklist.
- Starts with sending disabled and message placeholders blocked.

The Python scripts never log into LinkedIn or send messages themselves. Browser
actions are performed visibly by the agent while you are logged into your own
account.

## Requirements

- Python 3.9 or newer.
- Google Chrome logged into your LinkedIn account.
- Claude Code, Codex or another agent that can read the repository and control
  your visible browser.

There are no required Python packages outside the standard library.

## Quick start

```bash
git clone https://github.com/synteria/linkedin-outreach-agent-public.git
cd linkedin-outreach-agent-public
cp config.example.json config.json
cp data/leads.example.csv data/leads.csv
python3 scripts/build_state.py
python3 scripts/select_batch.py
python3 scripts/report.py
```

Edit `config.json` and replace the sample lead data before using the workflow.
Keep `safety.sending_enabled` set to `false` for the first run.

With Chrome open and logged into the correct LinkedIn account, ask your agent:

> Run today's outreach by following CLAUDE.md and docs/RUNBOOK.md. Keep sending
> disabled and show me the batch first.

## Private files

The following are ignored by git:

- `config.json`
- `.env` and `.env.*`
- every non-example CSV under `data/`
- everything generated under `state/`
- logs and Python caches

Run `git status --short` before every push. Never commit lead lists, message
history, browser data, conversation links, cookies, credentials or generated
reports.

## Lead CSV

`data/leads.example.csv` shows the supported columns:

```text
first_name,last_name,company_name,job_title,city,state,email,linkedin_url
```

Only `linkedin_url` is required. If your headers differ, map them in
`config.json` under `csv_columns`.

## Safety controls

The defaults are deliberately restrictive:

- `sending_enabled` is `false`.
- DM copy contains placeholders and must not be sent.
- stale-invite withdrawal is disabled.
- daily and weekly caps are explicit.
- the run stops on CAPTCHAs, restrictions, invitation warnings, login problems
  or unexpected dialogs.
- the visible account must match `account.name` before any outreach.

When you decide to test sending, start with a few connections while watching the
run. A configuration flag is not permission by itself. The person operating the
browser remains responsible for each action.

## Workflow

1. `scripts/build_state.py` imports your CSV into ignored local state.
2. `scripts/select_batch.py` creates a capped daily batch.
3. The agent verifies the logged-in account and handles browser actions visibly.
4. Outcomes are written to an ignored results file.
5. `scripts/update_state.py` merges those results into local state.
6. `scripts/report.py` prints a compact status report.

The daily run is intentionally manual. This repository does not include an
unattended scheduler.

## Repository layout

```text
config.example.json
CLAUDE.md
docs/
  PLAN.md
  RUNBOOK.md
data/
  leads.example.csv
  blocklist.example.csv
scripts/
  build_state.py
  select_batch.py
  update_state.py
  report.py
state/
  .gitkeep
  daily/.gitkeep
tests/
  test_pipeline.py
```

## Security and privacy

Read [SECURITY.md](SECURITY.md) before publishing a fork or sharing operational
data. All real lead data should remain local and ignored.

## Licence

MIT. See [LICENSE](LICENSE).
