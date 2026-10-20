# START HERE — 30-minute submission checklist

## 1. Run it locally
Install Python, open this folder in VS Code, then run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000. If PowerShell blocks activation, use Command Prompt and `.venv\Scripts\activate.bat`.

## 2. Test it
In another terminal, run:

```powershell
python -m unittest discover -s tests -v
```

The tests cover URL validation and basic routes. They do not verify live GitHub API behavior. Record the actual result in `docs/TEST_PLAN.md`.

## 3. Publish to GitHub
Create a public repository named `studymate-ai`. Upload the contents of this folder (not the ZIP file), preserving `templates/`, `static/`, `tests/`, `docs/`, and `.github/`. Commit the upload.

## 4. Show real teamwork
Use `TEAM.md` as a template. Each teammate should make a real, useful change. For example:
- Aryansh: integration and demo script.
- Prem: test cases and GitHub error handling.
- Palak: responsive UI/accessibility.
- Anaya: docs, manual test plan, and screenshots.

These are suggestions, not claims that the work is already completed. Use actual commits and PRs as evidence.

## 5. Do not overclaim
This first version uses rules and public GitHub metadata. It is not yet connected to a generative AI model, does not run repository tests, and cannot guarantee hackathon selection. Explain what works and what remains on the roadmap.
