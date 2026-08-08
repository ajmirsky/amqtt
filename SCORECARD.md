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

## OpenSSF Best Practices Passing Badge Entries

Sources:

- https://www.bestpractices.dev/en/projects/13571/passing
- https://www.bestpractices.dev/en/criteria/0?details=true&rationale=true

| Criterion | Current Status | Recommended Status | Suggested Justification or Needed Change |
|---|---|---|---|
| description_good | Met | Met | The README and project website describe aMQTT as an open source MQTT broker and client implemented with Python's asyncio. |
| interact | Met | Met | The README documents how to obtain the package from PyPI, report bugs through GitHub issues, join Discord, and contribute through the repository. |
| contribution | Met | Met | `CONTRIBUTING.md` explains the contribution process, including forking, cloning, opening pull requests, installing dependencies, and running local checks. |
| contribution_requirements | Met | Met | `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and the pull request template define expectations for acceptable contributions, tests, linting, and community behavior. |
| floss_license | Met | Met | The project is released under the MIT license, which is a FLOSS license. |
| floss_license_osi | Met | Met | The MIT license is approved by the Open Source Initiative. |
| license_location | Met | Met | The repository includes the project license in the top-level `LICENSE.md` file. |
| documentation_basics | Met | Met | Basic documentation is published at https://amqtt.readthedocs.io/ and includes installation, quickstart, broker/client usage, configuration, and plugin documentation. |
| documentation_interface | Met | Met | External interfaces are documented in the published docs, including CLI references, broker/client API references, configuration references, and plugin interfaces. |
| sites_https | Met | Met | The project homepage, documentation, repository, and package/distribution URLs use HTTPS. |
| discussion | Met | Met | Public project discussion happens through GitHub issues, pull requests, and discussions. |
| english | Met | Met | The project issue tracker, pull requests, documentation, and contribution guidance are available in English. |
| maintained | Met | Met | The project is active, has recent releases and repository activity, and is pursuing current OpenSSF remediation work. |
| repo_public | Met | Met | The source repository is publicly readable at https://github.com/Yakifo/amqtt. |
| repo_track | Met | Met | GitHub hosts the project in Git, providing a public history of changes, authors, and timestamps. |
| repo_interim | Met | Met | Proposed changes are visible through GitHub pull requests before merge. Enable branch protection for `main` to make this enforcement stronger. |
| repo_distributed | Met | Met | The repository uses Git, a distributed version control system. |
| version_unique | Met | Met | Official releases use unique version identifiers such as `v0.11.3`, and the package version is declared in `pyproject.toml`. |
| version_semver | Met | Met | The project uses SemVer-style version identifiers, such as `0.11.3` and `v0.11.3`. |
| version_tags | Met | Met | Release versions are recorded as Git tags at https://github.com/Yakifo/amqtt/tags. |
| release_notes | Met | Met | Release notes are maintained in `docs/changelog.md` and include linked pull requests, issues, API changes, bug fixes, and security-relevant notes. |
| release_notes_vulns | Met | Met | No publicly known runtime vulnerabilities with CVE or similar identifiers have been identified for recent releases; future fixed vulnerabilities should be listed in release notes. |
| report_process | Met | Met | Bug reporting is documented in the README, which directs users to open GitHub issues at https://github.com/Yakifo/amqtt/issues/new. |
| report_tracker | Met | Met | Bug reports are tracked publicly in GitHub Issues at https://github.com/Yakifo/amqtt/issues. |
| report_responses | Met | Met | The project responds to bug reports through GitHub Issues and associated pull requests. |
| enhancement_responses | Met | Met | Enhancement requests are handled through GitHub Issues, pull requests, milestones, and project discussion channels. |
| report_archive | Met | Met | Issue and discussion archives are publicly readable through GitHub Issues, Pull Requests, and Discussions. |
| vulnerability_report_process | ? | Unmet | Update `SECURITY.md` with a vulnerability reporting process. PR https://github.com/Yakifo/amqtt/pull/346 adds private GitHub Security Advisory reporting and can support marking this `Met` after merge. |
| vulnerability_report_private | ? | Unmet | Provide private vulnerability reporting instructions, preferably GitHub Security Advisories, in `SECURITY.md`. PR https://github.com/Yakifo/amqtt/pull/346 adds this and can support marking this `Met` after merge. |
| vulnerability_report_response | ? | N/A | If no vulnerability reports were received in the last 6 months, mark `N/A` and state that no reports were received. If reports were received, mark `Met` only if each initial response was within 14 days. |
| build | Met | Met | The project has a working build system through `pyproject.toml` and Hatch, with Docker image build targets in `Makefile`. |
| build_common_tools | Met | Met | The project uses common build tools: Python packaging via Hatch/uv and Docker Buildx for container builds. |
| build_floss_tools | Met | Met | Build and dependency tooling uses FLOSS tools, and Python dependencies are available through PyPI and tracked in `pyproject.toml` and `uv.lock`. |
| test | Met | Met | The repository includes an automated pytest test suite under `tests/`. |
| test_invocation | Met | Met | Tests are invoked with pytest, including the documented and CI command `uv run --frozen pytest tests/`. |
| test_most | Met | Met | The CI workflow runs the pytest suite with coverage reporting across supported Python versions. |
| test_continuous_integration | Met | Met | GitHub Actions runs tests on pull requests and pushes using `.github/workflows/ci.yml`. |
| test_policy | ? | Met | `CONTRIBUTING.md` states that new features should add tests, bug fixes should reproduce the issue in a test, and coverage should not decrease. |
| tests_are_added | ? | Unmet | Audit recent major changes and cite pull requests showing corresponding tests were added or updated. Add missing tests for recent major changes before marking this `Met`. |
| tests_documented_added | ? | Met | The policy for adding tests is documented in `CONTRIBUTING.md` under the testing guidance. |
| warnings | Met | Met | CI runs mypy, pylint, and ruff to detect code quality issues and common mistakes; CodeQL also runs for security analysis. |
| warnings_fixed | ? | Met | CI fails on mypy, pylint, and ruff findings, so warnings found by the configured tools must be fixed or explicitly addressed before the checks pass. |
| warnings_strict | ? | Met | The project uses multiple strict linting/type-checking tools in CI: ruff, pylint, and mypy. |
| know_secure_design | ? | Unmet | Confirm and document that at least one primary developer understands secure design principles, such as least privilege, fail-safe defaults, complete mediation, input validation, and limited attack surface. |
| know_common_errors | ? | Unmet | Confirm and document that at least one primary developer knows the common vulnerability classes for Python network services, such as injection, unsafe deserialization, authentication failures, secret exposure, and dependency risks. |
| crypto_published | Met | Met | Cryptographic functionality relies on published libraries and platforms such as Python `ssl` and the `cryptography` package. |
| crypto_call | Met | Met | The project calls published cryptographic libraries instead of implementing custom cryptographic algorithms. |
| crypto_floss | Met | Met | The cryptographic libraries used by the project are FLOSS dependencies available through Python packaging channels. |
| crypto_keylength | N/A | N/A | The project does not enforce or implement cryptographic key length policy itself; TLS/key choices are user configuration or delegated to underlying libraries. |
| crypto_working | N/A | N/A | The project does not implement cryptographic algorithms directly; cryptographic operation is delegated to maintained libraries. |
| crypto_weaknesses | N/A | N/A | The project does not implement cryptographic algorithms directly; weakness avoidance is delegated to Python `ssl` and cryptographic dependencies. |
| crypto_pfs | N/A | N/A | Perfect forward secrecy policy is not implemented by the project itself and depends on user TLS configuration and the underlying TLS stack. |
| crypto_password_storage | N/A | N/A | The project does not centrally enforce inbound password storage for external users; password storage is plugin/configuration dependent. |
| crypto_random | Met | Met | The certificate helper/plugin documentation uses platform cryptographic libraries for key and certificate generation rather than custom random generation. |
| delivery_mitm | Met | Met | Official distribution channels use HTTPS, including GitHub, PyPI, and documentation hosting. |
| delivery_unsigned | ? | Met | The project does not instruct users to retrieve cryptographic hashes over HTTP and trust them without signature verification; distribution channels use HTTPS. |
| vulnerabilities_fixed_60_days | Met | Met | No unpatched publicly known medium-or-higher severity runtime vulnerabilities are currently identified for the project. |
| vulnerabilities_critical_fixed | Met | Met | No unpatched publicly known critical runtime vulnerabilities are currently identified for the project. |
| no_leaked_credentials | Met | Met | No leaked credentials are known in the repository. PR https://github.com/Yakifo/amqtt/pull/346 adds Gitleaks scanning for stronger ongoing protection after merge. |
| static_analysis | ? | Met | CodeQL, mypy, pylint, and ruff are applied through CI before proposed production changes are released. |
| static_analysis_common_vulnerabilities | ? | Met | CodeQL includes security rules for common vulnerabilities in Python code, and it runs through the CodeQL workflow. |
| static_analysis_fixed | ? | Met | Static-analysis findings are expected to be fixed before release because CodeQL and lint/type checks run in CI; no medium-or-higher exploitable static-analysis findings are currently known. |
| static_analysis_often | ? | Met | Static analysis runs on pull requests and pushes through GitHub Actions workflows. |
| dynamic_analysis | ? | Unmet | Add dynamic analysis before major releases, such as fuzzing for MQTT packet parsing or documented automated test coverage of at least 80 percent branch coverage. PR https://github.com/Yakifo/amqtt/pull/346 adds fuzzing support and can support marking this `Met` after merge. |
| dynamic_analysis_unsafe | ? | N/A | The project is Python-based and does not include project-produced C/C++ or other memory-unsafe implementation code requiring sanitizer-backed dynamic analysis. |
| dynamic_analysis_enable_assertions | ? | Met | Tests run under normal Python execution through pytest, where Python assertions are enabled unless optimization is explicitly requested. |
| dynamic_analysis_fixed | ? | N/A | If no dynamic-analysis vulnerabilities have been found, mark `N/A`; once fuzzing or another dynamic-analysis tool is in use, mark `Met` only when all confirmed medium-or-higher findings are fixed in a timely way. |

## OpenSSF Baseline Level 1 Badge Entries

Source: https://www.bestpractices.dev/en/projects/13571/baseline-1

| Criterion | Status | Justification |
|---|---|---|
| OSPS-AC-01.01 | Met | The project is hosted on GitHub. GitHub requires 2FA for contributors who can perform sensitive repository actions, and repository administration is limited to maintainers using GitHub accounts. |
| OSPS-AC-02.01 | Met | The project is hosted on GitHub. Collaborator access is not granted automatically; a repository administrator must explicitly invite a person or team and choose the repository role to grant. The project follows least privilege: contributors use forks and pull requests by default, and elevated permissions such as Write, Maintain, or Admin are granted manually only when needed for the contributor's role. |
| OSPS-AC-03.01 | Met | The primary branch is main. GitHub branch protection/rulesets prevent direct commits to main; changes must be proposed through pull requests before being merged. |
| OSPS-AC-03.02 | Met | The primary branch is main. GitHub branch protection/rulesets protect main from deletion and require explicit privileged action to change protected branch settings. |
| OSPS-BR-01.01 | Met | CI workflows validate untrusted GitHub metadata before use. The workflows check base refs, head refs, ref names, and release tag formats before downstream CI/CD jobs run. |
| OSPS-BR-01.03 | Met | CI workflows that operate on untrusted pull request code run with restricted token permissions and do not persist checkout credentials. Privileged credentials and assets are not exposed to untrusted code snapshots. |
| OSPS-BR-03.01 | Met | Official project channels use encrypted HTTPS URLs: https://amqtt.io, https://github.com/Yakifo/amqtt, https://amqtt.readthedocs.io/, and https://pypi.org/project/amqtt/. |
| OSPS-BR-03.02 | Met | Distribution channels use HTTPS exclusively. |
| OSPS-BR-07.01 | Met | The project uses Gitleaks secret scanning through pre-commit and CI to detect hardcoded secrets, credentials, private keys, and similar sensitive data before they are stored in version control. |
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

## OpenSSF Baseline Level 2 Badge Entries

Source: https://www.bestpractices.dev/en/projects/13571/baseline-2

Current published status for each Level 2 entry is `?`. The table below provides
the recommended status and either copy-ready justification text or the change
needed before marking the entry `Met`.

| Criterion | Recommended Status | Suggested Justification or Needed Change |
|---|---|---|
| OSPS-AC-04.01 | Unmet | Set the GitHub Actions default `GITHUB_TOKEN` permissions to read-only at the repository or organization level, and add restrictive top-level `permissions` to every workflow. Grant write permissions only on jobs that require them. |
| OSPS-BR-02.01 | Met | Official releases use unique version identifiers. Releases are tagged with versioned Git tags such as `v0.11.3`, and the Python package version is declared in `pyproject.toml`. |
| OSPS-BR-04.01 | Met | Release changes are documented in `docs/changelog.md`, which lists functional changes, bug fixes, security-relevant fixes, and linked pull requests or issues for each release. |
| OSPS-BR-05.01 | Met | Build and CI dependency installation use standardized Python tooling: dependencies are declared in `pyproject.toml`, resolved in `uv.lock`, installed with `uv`, and built with the Python packaging build backend configured in `pyproject.toml`. |
| OSPS-BR-06.01 | Unmet | Add signed release artifacts or signed provenance/attestations for each official release. The signed manifest or attestation should include cryptographic hashes for every release asset. |
| OSPS-DO-06.01 | Unmet | Add project documentation describing how dependencies are selected, obtained, updated, and tracked. The documentation should reference `pyproject.toml`, `uv.lock`, Renovate, and the expected review/update process. |
| OSPS-DO-07.01 | Unmet | Add explicit build instructions to the documentation. Include supported Python versions, required system packages such as OpenLDAP/SASL development libraries when needed, `uv sync`, and the command to build release artifacts such as `uv build`. |
| OSPS-GV-01.01 | Unmet | Add governance documentation listing project members with access to sensitive resources, such as repository administration, release publishing, package publishing, and security advisory handling. |
| OSPS-GV-01.02 | Unmet | Add governance documentation describing maintainer, reviewer, release manager, and security contact roles and responsibilities. |
| OSPS-GV-03.02 | Met | `CONTRIBUTING.md` and the pull request template describe contributor expectations, including development setup, tests, linting, test coverage expectations, and the PR checklist for acceptable contributions. |
| OSPS-LE-01.01 | Unmet | Require a contributor legal authorization assertion on every commit. Add a DCO or CLA policy and enforce it with a required DCO/CLA check, such as signed-off commits through a DCO bot. |
| OSPS-QA-03.01 | Unmet | Enable branch protection or a repository ruleset for `main` that requires automated status checks to pass before merge, with any bypass limited to explicit maintainer override. |
| OSPS-QA-06.01 | Unmet | Require at least one automated test suite before commits are accepted to `main`. The existing test workflow can satisfy this once branch protection or rulesets require the test checks before merge. |
| OSPS-SA-01.01 | Unmet | Add design documentation that identifies major actors and actions in the broker/client system, such as clients, broker listeners, plugins, authentication/authorization flows, persistence, and external services. |
| OSPS-SA-02.01 | Met | External software interfaces are documented in the published documentation, including CLI references, broker/client API references, configuration references, and plugin interface documentation. |
| OSPS-SA-03.01 | Unmet | Perform and document a security assessment for the released software, covering likely and impactful security problems in MQTT parsing, authentication, authorization, plugin execution, TLS configuration, and broker/client network exposure. |
| OSPS-VM-01.01 | Unmet | Add a coordinated vulnerability disclosure policy with response timelines to `SECURITY.md`. PR https://github.com/Yakifo/amqtt/pull/346 adds this and can support marking the entry `Met` after merge. |
| OSPS-VM-03.01 | Unmet | Provide private vulnerability reporting directly to security contacts, such as GitHub Security Advisories, and document it in `SECURITY.md`. PR https://github.com/Yakifo/amqtt/pull/346 adds this and can support marking the entry `Met` after merge. |
| OSPS-VM-04.01 | Unmet | Document where vulnerability data is publicly published, such as GitHub Security Advisories, CVE/GHSA records, release notes, or a vulnerability history page, and publish discovered vulnerability records there. |

## OpenSSF Baseline Level 3 Badge Entries

Source: https://www.bestpractices.dev/en/projects/13571/baseline-3

Current published status for each Level 3 entry is `?`. The table below provides
the recommended status and either copy-ready justification text or the change
needed before marking the entry `Met`.

| Criterion | Recommended Status | Suggested Justification or Needed Change |
|---|---|---|
| OSPS-AC-04.02 | Unmet | Assign explicit least-privilege permissions in every CI/CD workflow. PR https://github.com/Yakifo/amqtt/pull/346 adds restrictive top-level permissions and job-level write permissions only where required; mark `Met` after that lands and all workflows follow the same pattern. |
| OSPS-BR-01.04 | N/A | The current workflows do not define manual `workflow_dispatch` inputs or other trusted collaborator-supplied workflow parameters. If trusted inputs are added later, validate and constrain them before use. |
| OSPS-BR-02.02 | Met | Release assets are associated with the release identifier through versioned Git tags and Python package filenames/metadata that include the project name and version, such as `amqtt` version `0.11.3`. |
| OSPS-BR-07.02 | Unmet | Add a documented secrets management policy covering where secrets may be stored, who may access them, how they are rotated, and what to do after suspected exposure. |
| OSPS-DO-03.01 | Unmet | Add release verification documentation explaining how users can verify release asset integrity and authenticity, including checksums, signatures, provenance, or attestations. |
| OSPS-DO-03.02 | Unmet | Add documentation explaining how users can verify the expected identity of the person or automated process that authored a release, such as trusted publisher identity, signing identity, or provenance issuer. |
| OSPS-DO-04.01 | Unmet | Add release support documentation describing the scope and duration of support for each supported release line. PR https://github.com/Yakifo/amqtt/pull/346 adds a basic supported-versions table, but Level 3 should also describe support scope and timing. |
| OSPS-DO-05.01 | Unmet | Add documentation stating when releases or versions stop receiving security updates. PR https://github.com/Yakifo/amqtt/pull/346 adds a starting supported-versions table; expand it into a clear end-of-support policy. |
| OSPS-GV-04.01 | Unmet | Add a policy requiring review of code collaborators before granting escalated access to sensitive resources such as repository administration, package publishing, release signing, and security advisories. |
| OSPS-QA-02.02 | Unmet | If wheels, containers, or other built release assets are official release artifacts, publish an SBOM for each release asset. If the project only releases source artifacts, document why this criterion is not applicable. |
| OSPS-QA-04.02 | N/A | The project is currently tracked as a single-repository project, so there are no released subprojects that need separate security requirement enforcement. |
| OSPS-QA-06.02 | Unmet | Document when and how tests run, including local test commands, CI triggers, supported Python version matrix, required checks, and when maintainers may rerun or bypass tests. |
| OSPS-QA-06.03 | Met | `CONTRIBUTING.md` states that new features should add corresponding tests, bug fixes should reproduce the issue in a test, and testing coverage should not decrease. |
| OSPS-QA-07.01 | Unmet | Enable branch protection or a repository ruleset for `main` that requires at least one non-author human approval before merge. |
| OSPS-SA-03.02 | Unmet | Perform and document threat modeling and attack surface analysis for critical code paths, including MQTT parsing, authentication, authorization, plugin execution, TLS configuration, persistence, and network listener behavior. |
| OSPS-VM-04.02 | Unmet | Publish VEX data for vulnerabilities in software components that do not affect the project, or document that no such non-affecting component vulnerabilities currently exist and where future VEX records will be published. |
| OSPS-VM-05.01 | Unmet | Add an SCA policy defining remediation thresholds for dependency vulnerabilities and license findings, including severity levels, timelines, and accepted suppression criteria. |
| OSPS-VM-05.02 | Unmet | Add a release policy requiring SCA violations to be resolved, suppressed with justification, or otherwise addressed before any release is published. |
| OSPS-VM-05.03 | Unmet | Add automated SCA checks for every change, backed by the documented SCA policy, and require the checks to pass before merge except for documented non-exploitable suppressions. |
| OSPS-VM-06.01 | Unmet | Add a SAST policy defining remediation thresholds for security weakness findings, including severity levels, timelines, and accepted suppression criteria. |
| OSPS-VM-06.02 | Unmet | Require SAST checks such as CodeQL on every change, block merges on policy violations through required checks, and document the allowed non-exploitable suppression process. |
