# StudyMate AI — GitHub Project Coach

> A student-team tool that reviews public GitHub repositories, identifies missing project-readiness signals, summarizes visible collaboration activity, and generates project-screening practice questions.

## Why we built it

Hackathon reviewers often have limited time to understand a team's repository. StudyMate AI turns public repository metadata into an actionable checklist so student teams can improve documentation, testing visibility, project discoverability, and their explanation of technical decisions.

## Features

- **GitHub repository scan:** validates a GitHub URL and fetches public repository metadata through the GitHub REST API.
- **12-point readiness checklist:** checks for a README, dependency/build manifest, license, tests, `.github` automation directory, docs, demo assets, description, topics, contribution guidance, archive status, and fork status.
- **Collaboration snapshot:** samples up to 100 commits and pull requests, and displays visible contributor activity.
- **Interview practice:** provides prompts about the problem, architecture, technical decisions, limitations, and team collaboration.
- **Shareable output:** print the report or save it as PDF from the browser; JSON report endpoint is also available.
- **Responsive interface:** designed for laptop and mobile screens.
- **Deployment-ready:** includes a `Procfile` for Gunicorn-based hosting.

## Tech stack

- Python 3
- Flask
- Requests
- GitHub REST API
- HTML, CSS, Jinja templates

## Run locally

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/).
2. Download or clone this repository.
3. Open a terminal in the project folder.
4. Create and activate a virtual environment.

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
.venv\Scripts\activate.bat
```

5. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

6. Start the app:

```bash
python app.py
```

7. Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

## Optional GitHub token

Unauthenticated GitHub API calls have a rate limit. For a demo with repeated scans, create a fine-grained token with no repository permissions for public metadata access, then set `GITHUB_TOKEN` as an environment variable. Never commit real tokens to GitHub.

PowerShell for the current terminal session:

```powershell
$env:GITHUB_TOKEN="paste-your-token-here"
python app.py
```

Do not put secrets in source code or screenshots. The application does not need a token for a single quick public-repository demo.

## How the checklist works

Each checklist item has a fixed point value. The score is:

`100 × points for detected checks ÷ total possible points`

The score is a **heuristic indicator**, not an official hackathon score, a code-quality verdict, or a guarantee of passing screening. A file's presence does not prove its quality.

## API notes

- `GET /health` — lightweight service health response.
- `POST /report.json` — JSON body `{"repo_url":"https://github.com/owner/repo"}`; returns a JSON report.
- `GET /` — browser interface; submit a repository URL to generate the report.

## Limitations and responsible use

- Public repositories only.
- The application does not clone source code or execute user code.
- It does not run tests or confirm that a test suite passes.
- GitHub activity is sampled from the latest 100 commits and pull requests; it is not exhaustive.
- Commit counts are not a fair measure of contribution quality on their own.
- API availability, rate limits, repository permissions, and network connectivity can affect results.
- The tool gives improvement suggestions and interview prompts; it does not make official selection decisions.

## Team collaboration

Replace the sample entries in [TEAM.md](TEAM.md) with the team's actual responsibilities and contributions. Each member should make real commits, open issues, and review pull requests. Do not fabricate contribution history.

## Roadmap

- [ ] Add automated tests for URL parsing, scoring, and GitHub API error handling.
- [ ] Add a CI workflow to run tests on every pull request.
- [ ] Add configurable rubric weights for different screening criteria.
- [ ] Add an optional LLM-generated explanation layer with a secure server-side API key.
- [ ] Add a downloadable Markdown report and accessibility checks.
- [ ] Improve pagination and compare activity across time ranges.

## Screenshots

Add genuine screenshots of the running app in `docs/screenshots/` and link them here before submission.

## License

MIT. See [LICENSE](LICENSE).
