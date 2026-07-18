#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

# Configuration
REPO_NAME = "Github-Achievements"
DEFAULT_USERNAME = "ken00H"

def check_git_installed():
    try:
        subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except Exception:
        print("[-] Error: Git CLI must be installed and configured on your system.", file=sys.stderr)
        sys.exit(1)

def make_github_request(url, token, data=None, method="GET"):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Achievement-Hunter-Bot")
    
    if data is not None:
        req.add_header("Content-Type", "application/json")
        json_data = json.dumps(data).encode("utf-8")
    else:
        json_data = None

    try:
        with urllib.request.urlopen(req, data=json_data) as response:
            return json.loads(response.read().decode("utf-8")), response.status
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"[-] HTTP Error {e.code}: {e.reason}\nBody: {error_body}", file=sys.stderr)
        return None, e.code
    except Exception as e:
        print(f"[-] Request failed: {e}", file=sys.stderr)
        return None, None

def run_command(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=cwd)
    if result.returncode != 0:
        print(f"[-] Command failed: {cmd}\nError: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True

def main():
    print("=== GitHub Achievement Automation Setup ===")
    
    # Attempt to read token from local file
    token_file_path = "/home/jamal-alshrjabe/Documents/Github Token"
    auto_token = None
    
    username_input = input(f"Enter your secondary GitHub username [{DEFAULT_USERNAME}]: ").strip()
    username = username_input if username_input else DEFAULT_USERNAME
    
    if os.path.exists(token_file_path):
        try:
            with open(token_file_path, "r") as f:
                for line in f:
                    if "=" in line:
                        key, val = line.split("=", 1)
                        if key.strip() == username:
                            auto_token = val.strip()
                            break
        except Exception as e:
            print(f"[*] Note: Could not read local token file: {e}")
            
    if auto_token:
        print(f"[+] Loaded token for '{username}' automatically from '{token_file_path}'.")
        token = auto_token
    else:
        token = input("Enter your GitHub Personal Access Token (classic): ").strip()
    
    email_input = input(f"Enter your secondary GitHub email (e.g. {username}@users.noreply.github.com): ").strip()
    email = email_input if email_input else f"{username}@users.noreply.github.com"

    if not token or not username or not email:
        print("[-] All inputs are required to proceed.", file=sys.stderr)
        sys.exit(1)

    check_git_installed()

    # 1. Create remote repository via API
    print(f"\n[+] Creating repository '{REPO_NAME}' on GitHub...")
    create_url = "https://api.github.com/user/repos"
    repo_data = {
        "name": REPO_NAME,
        "description": "Repo for triggering achievements",
        "private": False,
        "auto_init": True
    }
    
    res, status = make_github_request(create_url, token, data=repo_data, method="POST")
    if status == 201:
        print(f"[+] Repository created successfully.")
    elif status == 422:
        print(f"[*] Repository '{REPO_NAME}' already exists. Continuing...")
    else:
        print("[-] Failed to create repository. Check your token scopes.", file=sys.stderr)
        sys.exit(1)

    # Clone the repo locally
    clone_url = f"https://{username}:{token}@github.com/{username}/{REPO_NAME}.git"
    local_dir = os.path.join(os.getcwd(), REPO_NAME)
    
    if os.path.exists(local_dir):
        print(f"[*] Local directory {REPO_NAME} exists. Removing it to start fresh...")
        import shutil
        shutil.rmtree(local_dir)

    print(f"[+] Cloning {REPO_NAME} locally...")
    if not run_command(f'git clone "{clone_url}" "{local_dir}"'):
        sys.exit(1)

    # Set local repository configs
    run_command(f"git config user.name '{username}'", cwd=local_dir)
    run_command(f"git config user.email '{email}'", cwd=local_dir)

    # --- 1. Quickdraw Badge (Open & close issue within 5 mins) ---
    print("\n[+] Triggering 'Quickdraw' (Issue portion)...")
    issue_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/issues"
    issue_payload = {"title": "Quickdraw Trigger Issue", "body": "Temporary issue"}
    issue, status = make_github_request(issue_url, token, data=issue_payload, method="POST")
    if issue:
        issue_number = issue["number"]
        print(f"[+] Created issue #{issue_number}. Closing immediately...")
        close_url = f"{issue_url}/{issue_number}"
        close_payload = {"state": "closed"}
        make_github_request(close_url, token, data=close_payload, method="PATCH")
        print("[+] Issue closed.")

    # --- 2. Pair Extraordinaire Badge ---
    # Requires a commit containing: Co-authored-by: Name <email>
    print("\n[+] Triggering 'Pair Extraordinaire' (Co-authored commit)...")
    readme_path = os.path.join(local_dir, "README.md")
    with open(readme_path, "a") as f:
        f.write("\n\nContribution by pair programming partners.")
    
    run_command("git add README.md", cwd=local_dir)
    commit_msg = "Add collaborative notes\n\nCo-authored-by: Octocat <octocat@github.com>"
    run_command(f'git commit -m "{commit_msg}"', cwd=local_dir)
    run_command("git push origin main", cwd=local_dir)
    print("[+] Pushed co-authored commit.")

    # --- 3. Pull Shark & YOLO Badges ---
    # YOLO: Merge a PR with no reviews
    # Pull Shark: Merge PRs. We will automate 3 rapid PRs to ensure it registers.
    print("\n[+] Triggering 'YOLO' and 'Pull Shark'...")
    for i in range(1, 4):
        branch_name = f"patch-feature-{i}"
        print(f"\n[*] Creating PR cycle {i}/3...")
        
        # Create and switch to new branch
        run_command(f"git checkout -b {branch_name}", cwd=local_dir)
        
        # Make a change
        with open(os.path.join(local_dir, f"file_{i}.txt"), "w") as f:
            f.write(f"Feature modification {i}")
        
        run_command(f"git add file_{i}.txt", cwd=local_dir)
        run_command(f'git commit -m "Update file {i}"', cwd=local_dir)
        run_command(f"git push origin {branch_name}", cwd=local_dir)

        # Open Pull Request
        pr_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/pulls"
        pr_payload = {
            "title": f"Feature integration {i}",
            "head": branch_name,
            "base": "main",
            "body": f"Automated PR #{i}"
        }
        pr, status = make_github_request(pr_url, token, data=pr_payload, method="POST")
        
        if pr:
            pr_number = pr["number"]
            print(f"[+] Opened PR #{pr_number}.")
            
            # Merge Pull Request
            merge_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/pulls/{pr_number}/merge"
            merge_payload = {"commit_title": f"Merge pull request #{pr_number}"}
            res, status = make_github_request(merge_url, token, data=merge_payload, method="PUT")
            if status == 200:
                print(f"[+] PR #{pr_number} merged successfully.")
            
        # Clean up local state
        run_command("git checkout main", cwd=local_dir)
        run_command("git pull origin main", cwd=local_dir)

    print("\n=== Automation Sequence Completed ===")
    print("[!] Go check your GitHub profile page. It may take up to 10-15 minutes for the badges to appear.")

if __name__ == "__main__":
    main()
