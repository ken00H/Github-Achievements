# GitHub Achievements Unlocker

Interactive Python automation for running one selected GitHub achievement workflow at a time. The script targets the account identified by the supplied Personal Access Token (PAT); it does not loop toward higher achievement tiers.

## Supported Achievements

- **Quickdraw** — creates and closes one issue immediately.
- **Pair Extraordinaire** — creates and merges one PR containing a co-authored commit. The PAT account receives co-author credit; the script asks for the other contributor's username.
- **YOLO** — creates and merges one PR without a review.
- **Pull Shark** — creates and merges two PRs, GitHub's base badge requirement.

## Requirements

- Python 3
- Git CLI
- A GitHub classic PAT with `repo` scope for the account receiving the achievement
- A public `Github-Achievements` repository, or permission for the script to create it

## Usage

Run from the project directory:

```bash
python3 unlock_achievements.py
```

The script will:

1. Ask which achievement to run.
2. Request the target account's PAT through a hidden prompt.
3. Resolve the account username and noreply commit email through GitHub's API.
4. Display the target account and selected achievement for confirmation.
5. Perform only the selected workflow.

If `Github-Achievements` already exists on the target account, the script reuses it. Git operations run in a temporary local clone, which is deleted after completion. Achievement badges may take 10–15 minutes to appear on the profile.

## Security

Never paste tokens into source files, command arguments, issues, or chat. Token input is hidden and is not saved by the script. Use minimum required scopes, revoke unused tokens, and prefer a secondary/test account.

## Responsible Use

This project is intended for educational testing of GitHub API and Git workflows. Excessive or inauthentic automation may violate GitHub's Terms of Service.
