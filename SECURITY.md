# Security and privacy

## Keep operational data out of git

Do not commit:

- real lead lists or email addresses;
- LinkedIn conversation URLs or message transcripts;
- cookies, browser profiles, session tokens or credentials;
- generated state, reports, screenshots or recordings;
- private configuration or environment files.

The included `.gitignore` protects the expected local paths, but it is not a
substitute for reviewing `git status --short` before every commit.

## Safe publishing checklist

Before publishing a fork:

1. Start from a fresh git history.
2. Confirm only example data is tracked.
3. Search tracked files and history for secrets and personal information.
4. Verify `config.example.json` keeps sending disabled.
5. Run the test suite.

If private information is committed, making a later deletion does not remove it
from git history. Rotate exposed credentials, restrict exposed resources and
publish a clean repository with fresh history.

## Responsible use

Run the workflow only on an account you control. Keep volumes conservative,
respect opt-outs and applicable law, and stop when LinkedIn shows a security,
restriction or invitation-limit warning.
