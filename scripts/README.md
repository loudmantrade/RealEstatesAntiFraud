# Scripts Directory

Automation scripts for the RealEstatesAntiFraud project.

## GitHub Issues Management

### create_github_issues.py
Creates 30+ GitHub Issues from Core Development Plan with proper labels, milestones, and dependencies.

**Usage:**
```bash
export GITHUB_TOKEN=your_token_here
python scripts/create_github_issues.py
```

### run_create_issues.py
Interactive wrapper that prompts for GitHub token.

**Usage:**
```bash
python scripts/run_create_issues.py
```

### create_otel_issues.py ⭐ NEW
Creates 5 comprehensive GitHub Issues for OpenTelemetry integration (tasks 3.4-3.8).

**Usage:**
```bash
python scripts/create_otel_issues.py
```

**Features:**
- Auto-instrumentation setup (FastAPI, PostgreSQL, Redis, HTTP)
- Custom spans for plugins and fraud detection
- Custom metrics for performance monitoring
- Logs integration with trace correlation
- OpenTelemetry Collector deployment

**Created Issues:**
- #98: Base OTel integration
- #99: Custom spans
- #100: Custom metrics
- #101: Logs integration
- #102: Collector deployment

**Labels Created:**
```bash
gh label create opentelemetry --description "OpenTelemetry integration" --color "0E8A16"
gh label create metrics --description "Metrics and monitoring" --color "D4C5F9"
gh label create infrastructure --description "Infrastructure" --color "BFD4F2"
gh label create "priority:high" --description "High priority" --color "E99695"
gh label create "priority:medium" --description "Medium priority" --color "FBCA04"
```

## Manifest Validation

### test_manifest_validation.py
Tests plugin manifest validation against JSON schema.

**Usage:**
```bash
python scripts/test_manifest_validation.py
```

## Documentation

See `docs/GITHUB_ISSUES_SETUP.md` for detailed setup instructions.
