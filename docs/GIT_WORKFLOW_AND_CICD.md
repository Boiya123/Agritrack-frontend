# AgriTrack Git Branching Strategy & CI/CD Pipeline

## Branching Strategy: GitFlow (Modified for Small Team)

### Core Branches

#### 1. **main** (Production)

- **Purpose**: Production-ready code only
- **Protection**:
  - Require pull request reviews (2 approvals minimum)
  - Require status checks to pass
  - No direct commits allowed
  - Enforce linear history
- **Merges from**: `release/*` and `hotfix/*` branches only
- **Deployed to**: Production environment

#### 2. **develop** (Integration)

- **Purpose**: Integration branch for features
- **Protection**:
  - Require pull request reviews (1 approval minimum)
  - Require status checks to pass
  - No direct commits (except urgent fixes)
- **Merges from**: `feature/*`, `bugfix/*` branches
- **Deployed to**: Staging environment
- **Default branch**: Set this as default for new PRs

### Working Branches

#### 3. **feature/** (New Features)

- **Naming**: `feature/<ticket-id>-<short-description>`
- **Examples**:
  - `feature/AGR-123-batch-qr-generation`
  - `feature/AGR-124-hyperledger-integration`
- **Created from**: `develop`
- **Merged into**: `develop`
- **Lifespan**: Delete after merge
- **Developer workflow**:
  ```bash
  git checkout develop
  git pull origin develop
  git checkout -b feature/AGR-123-batch-qr-generation
  # ... work on feature ...
  git push origin feature/AGR-123-batch-qr-generation
  # Create PR to develop
  ```

#### 4. **bugfix/** (Non-Critical Bugs)

- **Naming**: `bugfix/<ticket-id>-<short-description>`
- **Example**: `bugfix/AGR-125-fix-batch-status-validation`
- **Created from**: `develop`
- **Merged into**: `develop`
- **Lifespan**: Delete after merge

#### 5. **hotfix/** (Production Emergencies)

- **Naming**: `hotfix/<version>-<critical-issue>`
- **Example**: `hotfix/v1.2.1-auth-token-expiry`
- **Created from**: `main`
- **Merged into**: BOTH `main` AND `develop`
- **Lifespan**: Delete after double merge
- **Trigger**: Critical production bugs only

#### 6. **release/** (Pre-Production)

- **Naming**: `release/<version>`
- **Example**: `release/v1.2.0`
- **Created from**: `develop`
- **Merged into**: `main` (then tagged)
- **Purpose**: Final testing, version bumps, changelog
- **Workflow**:
  ```bash
  git checkout develop
  git pull origin develop
  git checkout -b release/v1.2.0
  # Update version numbers, changelog
  # Final QA testing
  git checkout main
  git merge --no-ff release/v1.2.0
  git tag -a v1.2.0 -m "Release version 1.2.0"
  git push origin main --tags
  ```

---

## Team Workflow (3 Developers)

### Developer Responsibilities

**Developer 1: Backend Lead**

- Auth routes, security
- Database migrations (Alembic)
- API endpoint development

**Developer 2: Domain Expert**

- Batch/lifecycle routes
- Processing/regulatory routes
- Business logic validation

**Developer 3: Integration Specialist**

- Logistics routes
- Hyperledger blockchain integration
- External API integrations

### Daily Workflow

```bash
# Morning: Sync with develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/AGR-XXX-my-feature

# Work and commit frequently
git add .
git commit -m "feat(batch): add QR code generation endpoint"

# Push to remote
git push origin feature/AGR-XXX-my-feature

# Create Pull Request to develop
# Request review from 1 other developer

# After approval and CI passes
# Merge using "Squash and merge" on GitHub
```

### Commit Message Convention (Conventional Commits)

```
<type>(<scope>): <subject>

<optional body>

<optional footer>
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```
feat(batch): add QR code generation endpoint
fix(auth): correct token expiration validation
docs(api): update authentication flow documentation
test(lifecycle): add mortality event tests
chore(deps): upgrade SQLAlchemy to 2.0.25
```

---

## CI/CD Pipeline Architecture

### Pipeline Overview

```
┌─────────────┐
│   PR Created│
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Stage 1: Code Quality (2-3 min)    │
│  - Linting (Black, Flake8, isort)   │
│  - Type checking (mypy)              │
│  - Security scan (Bandit)            │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Stage 2: Testing (5-8 min)         │
│  - Unit tests (pytest)               │
│  - Integration tests                 │
│  - Coverage report (80% minimum)     │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Stage 3: Build (2-3 min)           │
│  - Docker image build                │
│  - Image scan (Trivy)                │
│  - Push to registry                  │
└──────┬──────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Stage 4: Deploy (3-5 min)          │
│  - Deploy to staging (develop)       │
│  - Deploy to production (main)       │
│  - Database migrations               │
│  - Health checks                     │
└─────────────────────────────────────┘
```

### Pipeline Execution Details

#### **Trigger Events**

1. **On Pull Request** (to `develop` or `main`):

   - Stage 1: Code Quality ✓
   - Stage 2: Testing ✓
   - Stage 3: Build ✓
   - Stage 4: Deploy (Staging preview) ✓

2. **On Merge to `develop`**:

   - All stages + Deploy to Staging

3. **On Merge to `main`**:

   - All stages + Deploy to Production

4. **On Tag Push** (`v*.*.*`):
   - Create GitHub Release
   - Deploy to Production
   - Notify team

---

### Execution Times (Estimated)

| Stage            | Tasks                          | Time          | Parallelizable? |
| ---------------- | ------------------------------ | ------------- | --------------- |
| **Code Quality** | Linting, type checks, security | 2-3 min       | ✓ Yes           |
| **Testing**      | Unit + Integration + Coverage  | 5-8 min       | ✓ Partial       |
| **Build**        | Docker build + scan            | 2-3 min       | ✗ No            |
| **Deploy**       | Deploy + migrations + health   | 3-5 min       | ✗ No            |
| **TOTAL**        | Full pipeline                  | **12-19 min** | -               |

#### Optimizations:

- **Caching**: Docker layers, pip dependencies, pytest cache → **-30% time**
- **Parallel testing**: Split tests across runners → **-40% test time**
- **Matrix builds**: Test multiple Python versions → **Same time, more coverage**

**Optimized Total: 8-12 minutes**

---

### Possible Bottlenecks

#### 1. **Database Migrations** (High Risk)

- **Issue**: Slow migrations on large datasets
- **Impact**: 2-10 min delay
- **Mitigation**:
  - Test migrations on staging first
  - Use Alembic's batch mode for SQLite
  - Zero-downtime migrations (blue-green deployment)

#### 2. **Integration Tests** (Medium Risk)

- **Issue**: Tests hitting real database/APIs slow down
- **Impact**: 3-5 min extra
- **Mitigation**:
  - Use in-memory SQLite for tests
  - Mock external API calls
  - Parallel test execution

#### 3. **Docker Build** (Medium Risk)

- **Issue**: Full rebuilds without caching
- **Impact**: 5-10 min for full rebuild
- **Mitigation**:
  - Multi-stage Docker builds
  - Layer caching in CI
  - Pre-built base images

#### 4. **Blockchain Integration** (Future Risk)

- **Issue**: Hyperledger network connectivity in CI
- **Impact**: Unknown (5-15 min if network required)
- **Mitigation**:
  - Mock blockchain writes in CI
  - Integration tests in separate nightly pipeline
  - Use testnet for staging

#### 5. **Concurrent Deployments** (Low Risk)

- **Issue**: Multiple devs merging simultaneously
- **Impact**: Deployment queue delays
- **Mitigation**:
  - Deployment queue with GitHub Actions
  - Merge trains (auto-merge when green)
  - Communication (Slack notifications)

---

### Time Allocation for CI/CD Setup

#### **Phase 1: Basic Pipeline (Week 1)**

**Time: 8-12 hours**

- [ ] GitHub Actions workflow files (2h)
- [ ] Linting + formatting setup (Black, Flake8) (1h)
- [ ] Pytest configuration + basic tests (2h)
- [ ] Docker multi-stage build (2h)
- [ ] Staging environment setup (Azure/AWS) (3h)

**Deliverable**: PR checks running (linting + unit tests)

#### **Phase 2: Full Testing (Week 2)**

**Time: 12-16 hours**

- [ ] Integration test suite (4h)
- [ ] Code coverage enforcement (1h)
- [ ] Security scanning (Bandit, Safety) (2h)
- [ ] Database migration CI tests (3h)
- [ ] Test parallelization setup (2h)

**Deliverable**: Full test coverage + security checks

#### **Phase 3: Deployment Automation (Week 3)**

**Time: 16-20 hours**

- [ ] Azure Container Apps deployment (4h)
- [ ] Environment variable management (secrets) (2h)
- [ ] Database migration automation (Alembic) (3h)
- [ ] Health check endpoints + monitoring (2h)
- [ ] Rollback procedures (3h)
- [ ] Production deployment (main branch) (2h)

**Deliverable**: Automated staging + production deploys

#### **Phase 4: Observability (Week 4)**

**Time: 8-12 hours**

- [ ] Logging aggregation (Azure Monitor) (3h)
- [ ] Error tracking (Sentry/Application Insights) (2h)
- [ ] Performance monitoring (APM) (2h)
- [ ] Slack/Email notifications (1h)
- [ ] Dashboard creation (2h)

**Deliverable**: Full visibility into deployments

#### **Phase 5: Advanced Features (Week 5+)**

**Time: 12-16 hours**

- [ ] Canary deployments (3h)
- [ ] Feature flags (LaunchDarkly/custom) (4h)
- [ ] Load testing in CI (Locust) (3h)
- [ ] Automated dependency updates (Dependabot) (1h)
- [ ] Compliance scanning (3h)

**Deliverable**: Production-grade enterprise CI/CD

---

### Total Time Estimate

| Phase                   | Time            | Priority     |
| ----------------------- | --------------- | ------------ |
| Phase 1: Basic Pipeline | 8-12h           | **Critical** |
| Phase 2: Full Testing   | 12-16h          | **Critical** |
| Phase 3: Deployment     | 16-20h          | **High**     |
| Phase 4: Observability  | 8-12h           | **High**     |
| Phase 5: Advanced       | 12-16h          | Medium       |
| **TOTAL**               | **56-76 hours** | -            |

**Realistic Timeline**:

- **MVP (Phases 1-2)**: 2 weeks (1 dev part-time)
- **Production-Ready (Phases 1-4)**: 4-5 weeks (1 dev part-time)
- **Enterprise-Grade (All phases)**: 6-7 weeks (1 dev part-time)

---

## Quick Start Commands

```bash
# Initialize branch protection (GitHub CLI)
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["ci/tests","ci/lint"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2}'

# Create develop branch
git checkout -b develop
git push origin develop

# Set develop as default branch
gh repo edit --default-branch develop

# Create first feature
git checkout -b feature/AGR-001-setup-ci-cd
```

---

## Recommended Tools

### CI/CD Platform

- **GitHub Actions** (recommended - free for public repos, tight integration)
- Azure DevOps Pipelines (if enterprise Azure environment)

### Code Quality

- **Black** (formatting)
- **Flake8** (linting)
- **isort** (import sorting)
- **mypy** (type checking)

### Security

- **Bandit** (Python security linter)
- **Safety** (dependency vulnerability scanner)
- **Trivy** (Docker image scanner)

### Testing

- **pytest** (test framework)
- **pytest-cov** (coverage)
- **pytest-xdist** (parallel execution)

### Monitoring

- **Azure Application Insights** (recommended for Azure)
- **Sentry** (error tracking)
- **Prometheus + Grafana** (metrics)

---

## Next Steps

1. **Today**: Protect `main` and `develop` branches
2. **This Week**: Set up Phase 1 (Basic Pipeline)
3. **Next Week**: Complete Phase 2 (Full Testing)
4. **Month 1**: Production deployment automation
5. **Month 2**: Observability and monitoring
