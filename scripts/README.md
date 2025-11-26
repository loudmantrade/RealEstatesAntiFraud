# Scripts Directory

Automation scripts for the RealEstatesAntiFraud project.

## create_github_issues.py
Creates 30+ GitHub Issues from Core Development Plan with proper labels, milestones, and dependencies.

**Usage:**
```bash
export GITHUB_TOKEN=your_token_here
python scripts/create_github_issues.py
```

## run_create_issues.py
Interactive wrapper that prompts for GitHub token.

**Usage:**
```bash
python scripts/run_create_issues.py
```

See `docs/GITHUB_ISSUES_SETUP.md` for details.
