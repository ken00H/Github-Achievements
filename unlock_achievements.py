#!/usr/bin/env python3
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


REPO_NAME = "Github-Achievements"
ACHIEVEMENTS = {
    "1": "Quickdraw",
    "2": "Pair Extraordinaire",
    "3": "YOLO",
    "4": "Pull Shark",
}


def check_git_installed():
    try:
        subprocess.run(
            ["git", "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception:
        print(
            "[-] Error: Git CLI must be installed and configured on your system.",
            file=sys.stderr,
        )
        sys.exit(1)


def make_github_request(
    url, token, data=None, method="GET", quiet_statuses=()
):
    request = urllib.request.Request(url, method=method)
    request.add_header("Authorization", f"token {token}")
    request.add_header("Accept", "application/vnd.github.v3+json")
    request.add_header("User-Agent", "Achievement-Hunter-Bot")

    if data is not None:
        request.add_header("Content-Type", "application/json")
        json_data = json.dumps(data).encode("utf-8")
    else:
        json_data = None

    try:
        with urllib.request.urlopen(request, data=json_data) as response:
            return json.loads(response.read().decode("utf-8")), response.status
    except urllib.error.HTTPError as error:
        if error.code not in quiet_statuses:
            error_body = error.read().decode("utf-8") if error.fp else ""
            print(
                f"[-] HTTP Error {error.code}: {error.reason}\nBody: {error_body}",
                file=sys.stderr,
            )
        return None, error.code
    except Exception as error:
        print(f"[-] Request failed: {error}", file=sys.stderr)
        return None, None


def github_account_from_token(token):
    account, status = make_github_request("https://api.github.com/user", token)
    if status != 200 or not account:
        print("[-] Could not identify account from token.", file=sys.stderr)
        return None
    return {
        "login": account["login"],
        "email": account.get("email")
        or f"{account['id']}+{account['login']}@users.noreply.github.com",
    }


def github_account_from_username(username, token):
    account, status = make_github_request(
        f"https://api.github.com/users/{username}", token
    )
    if status != 200 or not account:
        print(f"[-] Could not find GitHub account '{username}'.", file=sys.stderr)
        return None
    return {
        "login": account["login"],
        "email": account.get("email")
        or f"{account['id']}+{account['login']}@users.noreply.github.com",
    }


def run_command(command, cwd=None):
    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        print(f"[-] Git command failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True


def prepare_local_repository(username, token, git_name, git_email):
    workspace = tempfile.mkdtemp(prefix="github-achievements-")
    local_dir = os.path.join(workspace, REPO_NAME)
    clone_url = f"https://{username}:{token}@github.com/{username}/{REPO_NAME}.git"

    print(f"[+] Cloning {REPO_NAME} into a temporary workspace...")
    if not run_command(["git", "clone", clone_url, local_dir]):
        shutil.rmtree(workspace)
        sys.exit(1)

    if not run_command(["git", "config", "user.name", git_name], cwd=local_dir):
        shutil.rmtree(workspace)
        sys.exit(1)
    if not run_command(["git", "config", "user.email", git_email], cwd=local_dir):
        shutil.rmtree(workspace)
        sys.exit(1)

    return workspace, local_dir


def trigger_quickdraw(username, token):
    print("\n[+] Triggering 'Quickdraw'...")
    issue_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/issues"
    issue, _ = make_github_request(
        issue_url,
        token,
        data={"title": "Quickdraw Trigger Issue", "body": "Temporary issue"},
        method="POST",
    )
    if not issue:
        return False

    _, status = make_github_request(
        f"{issue_url}/{issue['number']}",
        token,
        data={"state": "closed"},
        method="PATCH",
    )
    if status != 200:
        return False

    print(f"[+] Created and closed issue #{issue['number']}.")
    return True


def create_and_merge_pull_request(
    local_dir,
    username,
    token,
    achievement,
    sequence=1,
    coauthor=None,
):
    slug = achievement.lower().replace(" ", "-")
    unique_id = f"{int(time.time())}-{sequence}"
    branch_name = f"achievement-{slug}-{unique_id}"
    filename = f"{slug}-{unique_id}.txt"

    if not run_command(["git", "checkout", "main"], cwd=local_dir):
        return False
    if not run_command(["git", "pull", "origin", "main"], cwd=local_dir):
        return False
    if not run_command(["git", "checkout", "-b", branch_name], cwd=local_dir):
        return False

    with open(os.path.join(local_dir, filename), "w") as change:
        change.write(f"{achievement} trigger {sequence}\n")

    commit_message = f"Add {achievement} trigger"
    if coauthor:
        commit_message += f"\n\nCo-authored-by: {coauthor[0]} <{coauthor[1]}>"

    if not run_command(["git", "add", filename], cwd=local_dir):
        return False
    if not run_command(["git", "commit", "-m", commit_message], cwd=local_dir):
        return False
    if not run_command(["git", "push", "origin", branch_name], cwd=local_dir):
        return False

    pull_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/pulls"
    pull_request, _ = make_github_request(
        pull_url,
        token,
        data={
            "title": f"{achievement} trigger {sequence}",
            "head": branch_name,
            "base": "main",
            "body": f"One-time {achievement} workflow",
        },
        method="POST",
    )
    if not pull_request:
        return False

    _, status = make_github_request(
        f"{pull_url}/{pull_request['number']}/merge",
        token,
        data={"commit_title": f"Merge {achievement} trigger {sequence}"},
        method="PUT",
    )
    if status != 200:
        return False

    print(f"[+] Created and merged pull request #{pull_request['number']}.")
    return True


def main():
    global REPO_NAME

    print("=== GitHub Achievement Automation Setup ===")
    print("\nChoose one achievement:")
    print("1. Quickdraw\n2. Pair Extraordinaire\n3. YOLO\n4. Pull Shark")

    achievement_choice = input("Selection [1-4]: ").strip()
    if achievement_choice not in ACHIEVEMENTS:
        print("[-] Invalid achievement selection.", file=sys.stderr)
        sys.exit(1)
    achievement = ACHIEVEMENTS[achievement_choice]

    repo_input = input(f"Repository name [{REPO_NAME}]: ").strip()
    if repo_input:
        REPO_NAME = re.sub(r"[^A-Za-z0-9._-]+", "-", repo_input).strip("-")
        if not REPO_NAME:
            print("[-] Invalid repository name.", file=sys.stderr)
            sys.exit(1)
        if REPO_NAME != repo_input:
            print(f"[*] Using sanitized repository name '{REPO_NAME}'.")

    token = getpass.getpass(
        "Personal access token for the account receiving the achievement "
        "(input hidden): "
    ).strip()
    if not token:
        print("[-] Account token is required.", file=sys.stderr)
        sys.exit(1)

    target_account = github_account_from_token(token)
    if not target_account:
        sys.exit(1)

    username = target_account["login"]
    email = target_account["email"]
    coauthor = None
    git_name = username
    git_email = email

    if achievement != "Quickdraw":
        check_git_installed()

    if achievement == "Pair Extraordinaire":
        print(f"[*] '{username}' will be credited as the co-author.")
        contributor_username = input(
            "Other contributor's GitHub username (commit author): "
        ).strip()
        contributor = github_account_from_username(contributor_username, token)
        if not contributor:
            sys.exit(1)
        if contributor["login"].lower() == username.lower():
            print(
                "[-] Pair Extraordinaire requires another contributor.",
                file=sys.stderr,
            )
            sys.exit(1)
        git_name = contributor["login"]
        git_email = contributor["email"]
        coauthor = (username, email)

    print(f"\nTarget account: {username}")
    print(f"Selected achievement: {achievement}")
    confirmation = input(f"Continue for '{username}'? [y/N]: ").strip().lower()
    if confirmation not in {"y", "yes"}:
        print("[*] Cancelled before making GitHub changes.")
        return

    print(f"\n[+] Creating repository '{REPO_NAME}' on GitHub...")
    _, status = make_github_request(
        "https://api.github.com/user/repos",
        token,
        data={
            "name": REPO_NAME,
            "description": "Repo for triggering achievements",
            "private": False,
            "auto_init": True,
        },
        method="POST",
        quiet_statuses=(422,),
    )
    if status == 201:
        print("[+] Repository created successfully.")
    elif status == 422:
        print(f"[*] Repository '{REPO_NAME}' already exists. Continuing...")
    else:
        print(
            "[-] Failed to create repository. Check your token scopes.",
            file=sys.stderr,
        )
        sys.exit(1)

    if achievement == "Quickdraw":
        success = trigger_quickdraw(username, token)
    else:
        workspace, local_dir = prepare_local_repository(
            username, token, git_name, git_email
        )
        try:
            print(f"\n[+] Triggering '{achievement}'...")
            success = create_and_merge_pull_request(
                local_dir,
                username,
                token,
                achievement,
                coauthor=coauthor,
            )
            if achievement == "Pull Shark" and success:
                success = create_and_merge_pull_request(
                    local_dir,
                    username,
                    token,
                    achievement,
                    sequence=2,
                )
        finally:
            shutil.rmtree(workspace)

    if not success:
        print(f"[-] {achievement} workflow failed.", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== {achievement} workflow completed ===")
    print(
        "[!] Go check your GitHub profile page. "
        "It may take up to 10-15 minutes for the badges to appear."
    )


if __name__ == "__main__":
    main()
