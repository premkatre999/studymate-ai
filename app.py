import os
import re
import json
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests
from flask import Flask, render_template, request, jsonify, make_response

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

GITHUB_API = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()


def github_headers():
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


def parse_repo_url(value):
    value = (value or "").strip()
    if not value:
        raise ValueError("Paste a public GitHub repository URL.")
    parsed = urlparse(value if "://" in value else "https://" + value)
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        raise ValueError("Please use a github.com repository URL.")
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 2:
        raise ValueError("The URL should look like https://github.com/owner/repository")
    owner, repo = parts[0], parts[1]
    repo = re.sub(r"\.git$", "", repo)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", owner) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ValueError("That repository URL does not look valid.")
    return owner, repo


def api_get(path, params=None):
    response = requests.get(
        f"{GITHUB_API}{path}",
        headers=github_headers(),
        params=params,
        timeout=15,
    )
    if response.status_code == 404:
        raise ValueError("Repository not found. Check the URL and make sure the repository is public.")
    if response.status_code == 403 and "rate limit" in response.text.lower():
        raise ValueError("GitHub API rate limit reached. Wait a little and try again, or configure GITHUB_TOKEN.")
    if response.status_code >= 400:
        raise ValueError(f"GitHub returned an error ({response.status_code}). Try again in a moment.")
    return response.json()


def has_any(names, *needles):
    lower_names = [n.lower() for n in names]
    return any(any(needle in name for needle in needles) for name in lower_names)


def analyze_repo(owner, repo):
    data = api_get(f"/repos/{owner}/{repo}")
    contents = api_get(f"/repos/{owner}/{repo}/contents")
    root_names = [item.get("name", "") for item in contents if isinstance(item, dict)]
    root_lower = {name.lower() for name in root_names}

    readme = any(name.startswith("readme") for name in root_lower)
    manifest = has_any(root_names, "requirements.txt", "pyproject.toml", "package.json",
                       "pom.xml", "build.gradle", "cargo.toml", "go.mod", "gemfile",
                       "composer.json", "pubspec.yaml")
    license_file = any(name.startswith("license") or name.startswith("licence") for name in root_lower)
    tests = has_any(root_names, "test", "tests", "__tests__", "spec")
    workflows = ".github" in root_lower
    docs = "docs" in root_lower or "documentation" in root_lower
    screenshots = has_any(root_names, "screenshot", "screenshots", "demo", "assets", "images")
    contributing = "contributing.md" in root_lower
    issue_template = workflows  # A useful signal only; not proof of a template.
    has_description = bool(data.get("description"))
    has_topics = bool(data.get("topics"))
    has_homepage = bool(data.get("homepage"))
    archived = bool(data.get("archived"))
    is_fork = bool(data.get("fork"))
    default_branch = data.get("default_branch") or "main"

    checks = [
        {"name": "README / setup guide", "passed": readme, "points": 15,
         "detail": "Explains the problem, features, setup, and usage." if readme else "Add README.md with problem, features, installation, usage, and screenshots."},
        {"name": "Dependency / build manifest", "passed": manifest, "points": 10,
         "detail": "A dependency or build file was found." if manifest else "Add the correct manifest, such as requirements.txt or package.json."},
        {"name": "License", "passed": license_file, "points": 5,
         "detail": "A license file was found." if license_file else "Consider adding a LICENSE file if you want others to reuse the project."},
        {"name": "Tests or test directory", "passed": tests, "points": 15,
         "detail": "A likely test file or directory was found; this does not mean tests were run." if tests else "Add tests for important behavior and document how to run them."},
        {"name": "GitHub Actions / automation", "passed": workflows, "points": 10,
         "detail": "A .github directory exists; inspect it to confirm workflows are configured." if workflows else "Add .github/workflows/ci.yml for automated checks."},
        {"name": "Docs or documentation folder", "passed": docs, "points": 5,
         "detail": "A docs folder was found." if docs else "Add docs/ for architecture, API notes, or decisions."},
        {"name": "Demo assets / screenshots", "passed": screenshots or has_homepage, "points": 10,
         "detail": "Demo assets or a homepage URL were found." if screenshots or has_homepage else "Add screenshots or a live demo link so reviewers can understand the UI quickly."},
        {"name": "Repository description", "passed": has_description, "points": 5,
         "detail": "A repository description is set." if has_description else "Add a short description in GitHub repository settings."},
        {"name": "Topics / discoverability", "passed": has_topics, "points": 5,
         "detail": "Repository topics are set." if has_topics else "Add relevant topics, e.g. education, flask, github-api, developer-tools."},
        {"name": "Contribution guidance", "passed": contributing, "points": 5,
         "detail": "CONTRIBUTING.md exists." if contributing else "Add CONTRIBUTING.md explaining branches, commits, and pull requests."},
        {"name": "Project not archived", "passed": not archived, "points": 5,
         "detail": "Repository is active, not archived." if not archived else "This repository is archived; unarchive it if development is continuing."},
        {"name": "Original repo (not a fork)", "passed": not is_fork, "points": 5,
         "detail": "Repository is not marked as a fork." if not is_fork else "If this is your team's project, clearly document your original work and attribution."},
    ]
    max_points = sum(item["points"] for item in checks)
    score = round(100 * sum(item["points"] for item in checks if item["passed"]) / max_points)

    commits = api_get(f"/repos/{owner}/{repo}/commits", params={"per_page": 100})
    contributor_map = {}
    for commit in commits:
        author = commit.get("author")
        commit_data = commit.get("commit", {})
        author_name = (author or {}).get("login") or commit_data.get("author", {}).get("name") or "Unknown author"
        if author_name not in contributor_map:
            contributor_map[author_name] = {"name": author_name, "commits_seen": 0, "last_commit": None}
        contributor_map[author_name]["commits_seen"] += 1
        date = commit_data.get("author", {}).get("date")
        if date and (not contributor_map[author_name]["last_commit"] or date > contributor_map[author_name]["last_commit"]):
            contributor_map[author_name]["last_commit"] = date

    prs = api_get(f"/repos/{owner}/{repo}/pulls", params={"state": "all", "per_page": 100})
    issues = api_get(f"/repos/{owner}/{repo}/issues", params={"state": "all", "per_page": 100})
    # GitHub's issues endpoint also includes pull requests, so exclude those from issue count.
    real_issues = [item for item in issues if "pull_request" not in item]

    recommendations = [item["detail"] for item in checks if not item["passed"]]
    if not recommendations:
        recommendations.append("Great baseline. Now verify the project runs from a clean setup and add a short demo walkthrough.")
    if not commits:
        recommendations.append("No commits were returned. Add meaningful commits from each teammate and use pull requests for shared work.")
    if len(contributor_map) < 2:
        recommendations.append("Collaboration evidence is limited in the latest 100 commits. Have teammates contribute real work in separate branches and review each other's pull requests.")

    questions = [
        f"What problem does {data.get('name', repo)} solve, and who is the intended user?",
        "Walk through the main architecture and explain how data moves through the application.",
        "Which technical decision was hardest, and what alternatives did your team consider?",
        "What are the current limitations, and what would you improve with one more day?",
        "How did the team split work, review changes, and resolve merge conflicts?",
    ]

    return {
        "repo": {
            "name": data.get("full_name", f"{owner}/{repo}"),
            "description": data.get("description") or "No repository description has been added yet.",
            "url": data.get("html_url"),
            "stars": data.get("stargazers_count", 0),
            "forks": data.get("forks_count", 0),
            "open_issues": data.get("open_issues_count", 0),
            "language": data.get("language") or "Not detected",
            "default_branch": default_branch,
            "created_at": data.get("created_at", "")[:10],
            "updated_at": data.get("updated_at", "")[:10],
            "license": (data.get("license") or {}).get("spdx_id", "Not detected"),
            "homepage": data.get("homepage") or "",
        },
        "score": score,
        "checks": checks,
        "root_files": sorted(root_names, key=str.lower),
        "contributors": sorted(contributor_map.values(), key=lambda c: c["commits_seen"], reverse=True),
        "commit_count_seen": len(commits),
        "pull_requests_seen": len(prs),
        "issues_seen": len(real_issues),
        "recommendations": recommendations,
        "questions": questions,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "limitations": [
            "This is a heuristic repository checklist, not an official hackathon score.",
            "GitHub's latest 100 commits and pull requests are sampled; pagination is not exhaustive.",
            "The tool does not clone the repository, execute code, or run tests.",
            "A detected test folder does not prove that tests pass.",
            "Public repository analysis only; private repositories are not supported in this demo.",
        ],
    }


@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    error = None
    repo_url = ""
    if request.method == "POST":
        repo_url = request.form.get("repo_url", "").strip()
        try:
            owner, repo = parse_repo_url(repo_url)
            report = analyze_repo(owner, repo)
        except ValueError as exc:
            error = str(exc)
        except requests.RequestException:
            error = "Could not reach GitHub. Check your internet connection and try again."
        except Exception:
            app.logger.exception("Unexpected analysis error")
            error = "Something went wrong while analyzing this repository. Please retry."
    return render_template("index.html", report=report, error=error, repo_url=repo_url)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "StudyMate AI"})


@app.route("/report.json", methods=["POST"])
def report_json():
    repo_url = (request.json or {}).get("repo_url", "").strip()
    try:
        owner, repo = parse_repo_url(repo_url)
        report = analyze_repo(owner, repo)
        response = make_response(json.dumps(report, indent=2), 200)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Content-Disposition"] = 'attachment; filename="studymate-report.json"'
        return response
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except requests.RequestException:
        return jsonify({"error": "Could not reach GitHub. Check your internet connection and try again."}), 502


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG", "false").lower() == "true")
