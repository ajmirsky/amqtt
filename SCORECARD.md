# OpenSSF Scorecard Improvement Tracker

Baseline run: 2026-07-08

Latest public rerun: 2026-07-08 20:10 EDT against `source/main`
commit `31995b2feaa60fbfc918a2040685fc0a2126391b`.

Aggregate score: 5.4 / 10

This file tracks the work needed to improve the OpenSSF Scorecard result for
`Yakifo/amqtt`. Prefer small pull requests and rerun Scorecard after each
completed section.

The public Scorecard result still reflects `source/main`. Local branch
`openssf` contains remediation commits that are not reflected in the public
score until they are merged into the upstream default branch.

## Run Scorecard

```bash
scorecard --repo=github.com/Yakifo/amqtt --show-details
```

Use an authenticated run to avoid GitHub API rate limits:

```bash
GITHUB_AUTH_TOKEN="$(gh auth token)" scorecard --repo=github.com/Yakifo/amqtt --show-details
```

Local mode may fail if it scans `.venv`; use the GitHub-backed run as the
authoritative project score.

## Highest Impact

### Branch Protection

Current public score: 0 / 10

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

Current public score: 0 / 10

Reason: GitHub workflow tokens have excessive permissions.

- [x] Add restrictive top-level permissions to `.github/workflows/ci.yml`.
- [x] Add restrictive top-level permissions to `.github/workflows/codeql-analysis.yml`.
- [x] Keep `.github/workflows/scorecard.yml` on restrictive top-level permissions.
- [x] Use job-level write permissions only where required, such as `security-events: write`.
- [x] Confirm no workflow has implicit broad token permissions.
- [ ] Rerun Scorecard after these changes are merged to `source/main`.

### Pinned Dependencies

Current public score: 0 / 10

Reason: dependencies are not pinned by hash or immutable digest.

Local status: local Scorecard reports 10 / 10 for Pinned-Dependencies after
pinning GitHub Actions, container images, and pip install commands.

- [x] Pin all GitHub Actions in `.github/workflows/ci.yml` by full commit SHA.
- [x] Pin all GitHub Actions in `.github/workflows/codeql-analysis.yml` by full commit SHA.
- [x] Pin all GitHub Actions in `.github/workflows/scorecard.yml` by full commit SHA.
- [x] Pin `Dockerfile` base images by digest.
- [x] Replace or pin `pip install uv` in `Dockerfile`.
- [x] Use hash-checked pip installs in ClusterFuzzLite build integration.
- [x] Keep generated `requirements.txt` with hashes up to date.
- [x] Keep the CI check that verifies `requirements.txt` matches `pyproject.toml`.
- [ ] Rerun Scorecard after these changes are merged to `source/main`.

### Vulnerabilities

Current public score: 0 / 10

Reason: Scorecard reported 103 existing vulnerabilities.

Local status: `uv.lock` and `docs_test/package-lock.json` currently scan clean
with OSV Scanner; `docs_test/package-lock.json` also passes `npm audit`.

- [x] Run an advisory scanner against `pyproject.toml` and `uv.lock`.
- [x] Map each advisory to the vulnerable package and dependency group.
- [x] Update direct runtime dependencies first.
- [x] Update optional, docs, and dev dependencies next.
- [x] Regenerate `uv.lock`.
- [x] Confirm hashed `requirements.txt` is up to date.
- [x] Scan `docs_test/package-lock.json` with `npm audit` and OSV Scanner.
- [x] Update vulnerable `docs_test` transitive dependencies.
- [x] Run focused Python tests affected by dependency updates.
- [x] Run `docs_test` production build.
- [x] Run the full test suite after dependency updates.
- [ ] Rerun Scorecard after these changes are merged to `source/main`.

## Medium Impact

### Security Policy

Current public score: 4 / 10

Reason: a security policy exists, but it lacks linked/reporting details.

- [x] Update `SECURITY.md` with a private vulnerability reporting contact.
- [x] Document supported versions.
- [x] Document expected acknowledgement and remediation timelines.
- [x] Document coordinated disclosure expectations.
- [x] Link to `SECURITY.md` from `README.md`.
- [ ] Rerun Scorecard after these changes are merged to `source/main`.

### CII Best Practices

Current public score: 0 / 10

Reason: no OpenSSF Best Practices badge effort was detected.

- [ ] Create an OpenSSF Best Practices project entry.
- [ ] Complete the initial badge questionnaire.
- [ ] Add the badge to `README.md`.
- [ ] Rerun Scorecard and record the new score.

### Fuzzing

Current public score: 0 / 10

Reason: no recognized fuzzer integration was found.

- [x] Decide on a recognized fuzzing path, such as OSS-Fuzz or ClusterFuzzLite.
- [x] Add fuzz targets for MQTT packet parsing.
- [x] Add a recognized ClusterFuzzLite/Atheris fuzz target for MQTT packet parsing.
- [ ] Add fuzz targets for MQTT 5 property decoding as that implementation lands.
- [x] Add CI coverage for fuzz target build or smoke tests.
- [x] Document how to run fuzz targets locally.
- [x] Confirm local Scorecard detects recognized fuzzing integration.
- [ ] Rerun public Scorecard after ClusterFuzzLite integration lands on `source/main`.

## Longer Term

### Code Review

Current public score: 5 / 10

Reason: only 9 of 17 recent changesets were approved.

- [ ] Enforce review requirements through branch protection.
- [ ] Avoid direct pushes to protected branches.
- [ ] Keep PR approvals visible on merged changes.
- [ ] Rerun Scorecard after several reviewed PRs have merged.

### CI Tests

Current public score: 8 / 10

Reason: 15 of 17 merged PRs were checked by CI.

- [ ] Require CI on protected branches.
- [ ] Confirm all PR workflows run on `pull_request`.
- [ ] Confirm required checks include tests for supported Python versions.
- [ ] Rerun Scorecard after several CI-checked PRs have merged.

### SAST

Current public score: 9 / 10

Reason: CodeQL is configured, but not all recent commits were checked.

- [x] Keep CodeQL running on pull requests.
- [x] Keep CodeQL running on pushes to protected branches.
- [x] Consider enabling the scheduled CodeQL run.
- [ ] Require CodeQL in branch protection.
- [ ] Rerun Scorecard after recent commits are covered.

### Packaging

Current public score: not scored

Reason: no publishing workflow was detected.

Local status: local Scorecard reports 10 / 10 for Packaging after adding a
release-published PyPI trusted publishing workflow.

- [x] Decide whether releases should publish to PyPI from GitHub Actions.
- [x] Add a trusted-publishing PyPI release workflow if appropriate.
- [x] Add release provenance or attestations if practical.
- [x] Confirm local Scorecard detects the packaging workflow.
- [ ] Configure the PyPI trusted publisher for project `amqtt` with repository `Yakifo/amqtt`, workflow `publish-pypi.yml`, and environment `pypi`.
- [ ] Rerun public Scorecard after this workflow lands on `source/main`.

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

Add dated entries after each Scorecard rerun or remediation batch.

| Date | Aggregate | Notes |
|---|---:|---|
| 2026-07-08 | local Packaging 10 / 10 | Added release-published PyPI trusted publishing workflow with separate build and OIDC publish jobs; local Scorecard keeps Token-Permissions and Pinned-Dependencies at 10 / 10. |
| 2026-07-08 | full suite pass | `uv run --frozen pytest tests/` passed: 478 passed, 44 warnings. |
| 2026-07-08 | local Pinned-Dependencies 10 / 10 | Added hash-checked Docker build dependency install and hash-checked ClusterFuzzLite build dependency install. |
| 2026-07-08 | local Fuzzing 10 / 10 | Added ClusterFuzzLite PR workflow, Python/Atheris MQTT packet fuzzer, and `.clusterfuzzlite` build integration; local Scorecard detects ClusterFuzzLite and PythonAtherisFuzzer. |
| 2026-07-08 | local clean | Fixed `docs_test/package-lock.json` vulnerabilities; `npm audit` and OSV Scanner are clean, and `docs_test` build passes. |
| 2026-07-08 | 5.4 / 10 | Authenticated GitHub-backed rerun against `source/main` commit `31995b2`; unchanged because local `openssf` branch remediations are not merged upstream. |
| 2026-07-08 | local remediation | Completed local workflow hardening, action pinning, Docker pinning, security policy updates, local MQTT parser fuzz tests, dependency vulnerability updates, and scheduled CodeQL. |
| 2026-07-08 | 5.4 / 10 | Baseline run before remediation work. |

## OpenSSF Baseline Level 1 Badge Entries

Source: https://www.bestpractices.dev/en/projects/13571/baseline-1

| Criterion | Status | Justification |
|---|---|---|
| OSPS-AC-01.01 | Met | The project is hosted on GitHub. GitHub requires 2FA for contributors who can perform sensitive repository actions, and repository administration is limited to maintainers using GitHub accounts. |
| OSPS-AC-02.01 | Met | The project is hosted on GitHub. Collaborator access is not granted automatically; a repository administrator must explicitly invite a person or team and choose the repository role to grant. The project follows least privilege: contributors use forks and pull requests by default, and elevated permissions such as Write, Maintain, or Admin are granted manually only when needed for the contributor's role. |
| OSPS-AC-03.01 | Met | The primary branch is main. GitHub branch protection/rulesets prevent direct commits to main; changes must be proposed through pull requests before being merged. |
| OSPS-AC-03.02 | Met | The primary branch is main. GitHub branch protection/rulesets protect main from deletion and require explicit privileged action to change protected branch settings. |
| OSPS-BR-01.01 | Unmet | Fixed with PR: https://github.com/Yakifo/amqtt/pull/346 |
| OSPS-BR-01.03 | Unmet | Fixed with PR: https://github.com/Yakifo/amqtt/pull/346 |
| OSPS-BR-03.01 | Met | Official project channels use encrypted HTTPS URLs: https://amqtt.io, https://github.com/Yakifo/amqtt, https://amqtt.readthedocs.io/, and https://pypi.org/project/amqtt/. |
| OSPS-BR-03.02 | Met | Distribution channels use HTTPS exclusively. |
| OSPS-BR-07.01 | Unmet | Fixed with PR: https://github.com/Yakifo/amqtt/pull/346 |
| OSPS-DO-01.01 | Met | User documentation for basic functionality is published at https://amqtt.readthedocs.io/ and includes quickstart, broker/client usage, configuration, and CLI reference documentation. |
| OSPS-DO-02.01 | Met | Defect reporting is documented in the README: users are directed to open GitHub issues at https://github.com/Yakifo/amqtt/issues/new for bugs, patches, and suggestions. |
| OSPS-GV-02.01 | Met | GitHub supports public discussions on proposed changes through pull requests and usage obstacles through issues. |
| OSPS-GV-03.01 | Met | Contribution process documented in repository. |
| OSPS-LE-02.01 | Met | The MIT license for the repository contents is approved by the Open Source Initiative (OSI). |
| OSPS-LE-02.02 | Met | The MIT license is approved by the Open Source Initiative (OSI). |
| OSPS-LE-03.01 | Met | License file found in repository. |
| OSPS-LE-03.02 | Met | Non-trivial license location file in repository: https://github.com/Yakifo/amqtt/blob/main/LICENSE.md. |
| OSPS-QA-01.01 | Met | Repository is publicly available on GitHub. |
| OSPS-QA-01.02 | Met | Repository git metadata is publicly available on GitHub. |
| OSPS-QA-02.01 | Met | Direct Python dependencies are declared in pyproject.toml, and the resolved dependency set is tracked in uv.lock: https://github.com/Yakifo/amqtt/blob/main/pyproject.toml and https://github.com/Yakifo/amqtt/blob/main/uv.lock. |
| OSPS-QA-04.01 | N/A | Single repository project. |
| OSPS-QA-05.01 | Met | The repository does not track generated executable artifacts; builds, distributions, caches, and compiled outputs are excluded from version control. |
| OSPS-QA-05.02 | Met | The repository does not track unreviewable binary artifacts such as executables, compiled libraries, wheels, archives, or generated application binaries. |
| OSPS-VM-02.01 | Met | Security contacts and private vulnerability reporting instructions are documented in SECURITY.md: https://github.com/Yakifo/amqtt/blob/main/SECURITY.md. |

## OpenSSF Baseline Level 1 Checklist

Source: https://baseline.openssf.org/versions/2026-02-19.html#level-1

### Access Control

- [ ] OSPS-AC-01.01: Confirm sensitive repository actions require MFA.
- [ ] OSPS-AC-02.01: Confirm new collaborators require manual permission assignment or default to least privilege.
- [ ] OSPS-AC-03.01: Confirm direct commits to the primary branch are blocked.
- [ ] OSPS-AC-03.02: Confirm primary branch deletion requires explicit confirmation.

### Build and Release

- [ ] OSPS-BR-01.01: Review CI/CD handling of untrusted metadata for sanitization and validation.
- [ ] OSPS-BR-01.03: Confirm CI/CD jobs for untrusted code snapshots cannot access privileged credentials or assets.
- [ ] OSPS-BR-03.01: Confirm official project channel URIs use encrypted channels.
- [ ] OSPS-BR-03.02: Confirm official distribution channels use cryptographically authenticated channels.
- [ ] OSPS-BR-07.01: Confirm controls prevent unencrypted secrets or credentials from being stored in version control.

### Documentation

- [ ] OSPS-DO-01.01: Confirm released project documentation includes user guides for basic functionality.
- [ ] OSPS-DO-02.01: Confirm released project documentation explains how to report defects.

### Governance

- [ ] OSPS-GV-02.01: Confirm the project has public mechanisms for discussing proposed changes and usage obstacles.
- [ ] OSPS-GV-03.01: Confirm project documentation explains the contribution process.

### Legal

- [ ] OSPS-LE-02.01: Confirm the source code license meets the OSI Open Source Definition or FSF Free Software Definition.
- [ ] OSPS-LE-02.02: Confirm the released software asset license meets the OSI Open Source Definition or FSF Free Software Definition.
- [ ] OSPS-LE-03.01: Confirm the source code license is maintained in a `LICENSE` file, `COPYING` file, or `LICENSE/` directory.
- [ ] OSPS-LE-03.02: Confirm the release asset license is included in released source code or alongside the release assets.

### Quality

- [ ] OSPS-QA-01.01: Confirm the source repository is publicly readable at a static URL.
- [ ] OSPS-QA-01.02: Confirm the version control system has a publicly readable change history with author and date metadata.
- [ ] OSPS-QA-02.01: Confirm the repository includes a dependency list for direct language dependencies.
- [ ] OSPS-QA-04.01: If multiple repositories are used, document the codebases that are part of the project.
- [ ] OSPS-QA-05.01: Confirm the version control system does not contain generated executable artifacts.
- [ ] OSPS-QA-05.02: Confirm the version control system does not contain unreviewable binary artifacts.

### Vulnerability Management

- [ ] OSPS-VM-02.01: Confirm project documentation contains security contacts.
