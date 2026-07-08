# OpenSSF Scorecard Improvement Tracker

Baseline run: 2026-07-08

Aggregate score: 5.4 / 10

This file tracks the work needed to improve the OpenSSF Scorecard result for
`Yakifo/amqtt`. Prefer small pull requests and rerun Scorecard after each
completed section.

## Run Scorecard

```bash
scorecard --repo=github.com/Yakifo/amqtt --show-details
```

Local mode may fail if it scans `.venv`; use the GitHub-backed run as the
authoritative project score.

## Highest Impact

### Branch Protection

Current score: 0 / 10

Reason: branch protection is not enabled on development/release branches.

- [ ] Enable branch protection for `main`.
- [ ] Require pull requests before merging.
- [ ] Require at least one approving review.
- [ ] Require CI checks before merge.
- [ ] Require CodeQL analysis before merge.
- [ ] Disable force pushes on protected branches.
- [ ] Decide whether `dev` and release branches should receive the same rules.
- [ ] Rerun Scorecard and record the new score.

### Token Permissions

Current score: 0 / 10

Reason: GitHub workflow tokens have excessive permissions.

- [ ] Add restrictive top-level permissions to `.github/workflows/ci.yml`.
- [ ] Add restrictive top-level permissions to `.github/workflows/codeql-analysis.yml`.
- [ ] Keep `.github/workflows/scorecard.yml` on restrictive top-level permissions.
- [ ] Use job-level write permissions only where required, such as `security-events: write`.
- [ ] Confirm no workflow has implicit broad token permissions.
- [ ] Rerun Scorecard and record the new score.

### Pinned Dependencies

Current score: 0 / 10

Reason: dependencies are not pinned by hash or immutable digest.

- [ ] Pin all GitHub Actions in `.github/workflows/ci.yml` by full commit SHA.
- [ ] Pin all GitHub Actions in `.github/workflows/codeql-analysis.yml` by full commit SHA.
- [ ] Pin all GitHub Actions in `.github/workflows/scorecard.yml` by full commit SHA.
- [ ] Pin `Dockerfile` base images by digest.
- [ ] Replace or pin `pip install uv` in `Dockerfile`.
- [ ] Keep generated `requirements.txt` with hashes up to date.
- [ ] Keep the CI check that verifies `requirements.txt` matches `pyproject.toml`.
- [ ] Rerun Scorecard and record the new score.

### Vulnerabilities

Current score: 0 / 10

Reason: Scorecard reported 103 existing vulnerabilities.

- [ ] Run an advisory scanner against `pyproject.toml` and `uv.lock`.
- [ ] Map each advisory to the vulnerable package and dependency group.
- [ ] Update direct runtime dependencies first.
- [ ] Update optional, docs, and dev dependencies next.
- [ ] Regenerate `uv.lock`.
- [ ] Regenerate hashed `requirements.txt`.
- [ ] Run the full test suite after dependency updates.
- [ ] Rerun Scorecard and record the new score.

## Medium Impact

### Security Policy

Current score: 4 / 10

Reason: a security policy exists, but it lacks linked/reporting details.

- [ ] Update `SECURITY.md` with a private vulnerability reporting contact.
- [ ] Document supported versions.
- [ ] Document expected acknowledgement and remediation timelines.
- [ ] Document coordinated disclosure expectations.
- [ ] Link to `SECURITY.md` from `README.md`.
- [ ] Rerun Scorecard and record the new score.

### CII Best Practices

Current score: 0 / 10

Reason: no OpenSSF Best Practices badge effort was detected.

- [ ] Create an OpenSSF Best Practices project entry.
- [ ] Complete the initial badge questionnaire.
- [ ] Add the badge to `README.md`.
- [ ] Rerun Scorecard and record the new score.

### Fuzzing

Current score: 0 / 10

Reason: no recognized fuzzer integration was found.

- [ ] Decide on a recognized fuzzing path, such as OSS-Fuzz or ClusterFuzzLite.
- [ ] Add fuzz targets for MQTT packet parsing.
- [ ] Add fuzz targets for MQTT 5 property decoding as that implementation lands.
- [ ] Add CI coverage for fuzz target build or smoke tests.
- [ ] Document how to run fuzz targets locally.
- [ ] Rerun Scorecard and record the new score.

## Longer Term

### Code Review

Current score: 5 / 10

Reason: only 9 of 17 recent changesets were approved.

- [ ] Enforce review requirements through branch protection.
- [ ] Avoid direct pushes to protected branches.
- [ ] Keep PR approvals visible on merged changes.
- [ ] Rerun Scorecard after several reviewed PRs have merged.

### CI Tests

Current score: 8 / 10

Reason: 15 of 17 merged PRs were checked by CI.

- [ ] Require CI on protected branches.
- [ ] Confirm all PR workflows run on `pull_request`.
- [ ] Confirm required checks include tests for supported Python versions.
- [ ] Rerun Scorecard after several CI-checked PRs have merged.

### SAST

Current score: 9 / 10

Reason: CodeQL is configured, but not all recent commits were checked.

- [ ] Keep CodeQL running on pull requests.
- [ ] Keep CodeQL running on pushes to protected branches.
- [ ] Consider enabling the scheduled CodeQL run.
- [ ] Require CodeQL in branch protection.
- [ ] Rerun Scorecard after recent commits are covered.

### Packaging

Current score: not scored

Reason: no publishing workflow was detected.

- [ ] Decide whether releases should publish to PyPI from GitHub Actions.
- [ ] Add a trusted-publishing PyPI release workflow if appropriate.
- [ ] Add release provenance or attestations if practical.
- [ ] Rerun Scorecard and confirm whether Packaging is now scored.

### Signed Releases

Current score: not scored

Reason: no releases were found.

- [ ] Decide whether the project will publish GitHub releases.
- [ ] Sign release artifacts or publish verifiable provenance if releases are added.
- [ ] Rerun Scorecard after a release exists.

## Already Healthy

These checks were already strong in the baseline run.

- [x] Binary-Artifacts: 10 / 10
- [x] Contributors: 10 / 10
- [x] Dangerous-Workflow: 10 / 10
- [x] Dependency-Update-Tool: 10 / 10
- [x] License: 10 / 10
- [x] Maintained: 10 / 10

## Progress Log

Add dated entries after each Scorecard rerun.

| Date | Aggregate | Notes |
|---|---:|---|
| 2026-07-08 | 5.4 / 10 | Baseline run before remediation work. |
