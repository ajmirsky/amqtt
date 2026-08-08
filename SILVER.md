# OpenSSF Best Practices Silver Audit

Audit date: 2026-08-08

Badge entry: https://www.bestpractices.dev/en/projects/13571/silver

BadgeApp snapshot: the public Silver page for `amqtt` showed 55 Silver
criteria, with 5 marked `Met`, 2 marked `N/A`, 1 marked `Unmet`, and 47
unknown. The page itself reported that the entry was last updated on
2026-08-07 18:53:28 UTC.

This audit evaluates the Silver criteria against the current local repository
and public GitHub project metadata. The result here is stricter than the
BadgeApp snapshot: unknown entries are treated as unmet unless there is clear
evidence in the repository or public project metadata.

Independent audit count:

- Met: 30
- Unmet: 19
- N/A: 6

Silver requires all MUST/MUST NOT criteria to be met. SHOULD and SUGGESTED
criteria may remain unmet only with an explicit justification in BadgeApp.

## Primary Blockers

These are the highest-impact items to close before Silver is realistic:

- Passing badge is not achieved yet. BadgeApp still records `achieve_passing`
  as unmet.
- Governance, key roles, continuity, and bus-factor evidence are missing.
- Roadmap, architecture, and product security documentation are incomplete or
  stale for Silver's documentation requirements.
- Releases and important version tags are not consistently signed, and there
  is no user-facing release-signature verification process.
- A full assurance case is missing.
- Input validation is not comprehensively demonstrated. For example,
  `amqtt/codecs_amqtt.py` converts invalid UTF-8 bytes into a string
  representation instead of rejecting them.
- Secure network protocols are supported, but plaintext MQTT is enabled by
  default in the shipped broker and client configs.

## Evidence Checked

- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `ROADMAP.md`
- `docs/quickstart.md`
- `docs/changelog.md`
- `docs/references/broker_config.md`
- `docs/references/client_config.md`
- `docs/plugins/packaged_plugins.md`
- `pyproject.toml`
- `uv.lock`
- `requirements.txt`
- `.github/workflows/ci.yml`
- `.github/workflows/codeql-analysis.yml`
- `.github/workflows/clusterfuzzlite.yml`
- `.github/workflows/publish-pypi.yml`
- `.github/workflows/scorecard.yml`
- `.github/renovate.json`
- `.pre-commit-config.yaml`
- `amqtt/scripts/default_broker.yaml`
- `amqtt/scripts/default_client.yaml`
- `amqtt/client.py`
- `amqtt/broker.py`
- `amqtt/codecs_amqtt.py`
- `tests/mqtt/test_fuzz_packet.py`
- GitHub advisory `GHSA-2hjf-7455-w946`
- GitHub branch protection, releases, tags, contributors, and recent merged PRs

Local checks run:

```bash
uv run --frozen pytest --cov=amqtt --cov-report=term -q
uv build --sdist --wheel --out-dir /private/tmp/amqtt-build1
uv build --sdist --wheel --out-dir /private/tmp/amqtt-build2
shasum -a 256 /private/tmp/amqtt-build1/* /private/tmp/amqtt-build2/*
git tag -v v0.11.0
git tag -v v0.11.4
```

The two package builds were bit-for-bit identical:

```text
9391817a624908dabbe8279e3544c9ec04fc86c3bf6615a1a5c4757176d61ce1  amqtt-0.12.0-py3-none-any.whl
5d2376ac5d1dc84fe9eaeb34a848743dd47a94241449aa282d09b385d5d7d6b0  amqtt-0.12.0.tar.gz
```

## Criteria

| Criterion | Result | Why |
|---|---:|---|
| `achieve_passing` | Unmet | BadgeApp records the passing-level prerequisite as unmet. The passing page still has at least one unmet criterion. |
| `contribution_requirements` | Met | `CONTRIBUTING.md`, `.github/pull_request_template.md`, and `CODE_OF_CONDUCT.md` document contribution expectations, tests, linting, and conduct. |
| `dco` | Unmet | No DCO, CLA, signed-off-by requirement, or equivalent legal contribution assertion is documented or enforced. This is a SHOULD criterion, so it can be justified if intentionally omitted. |
| `governance` | Unmet | No public governance model describes how decisions are made or identifies decision-making roles. |
| `code_of_conduct` | Met | `CODE_OF_CONDUCT.md` exists in the standard location. Caveat: the enforcement contact still contains `{{ email }}` and should be fixed. |
| `roles_responsibilities` | Unmet | The repository does not clearly document key project roles, role responsibilities, and who holds those roles. |
| `access_continuity` | Unmet | No public evidence shows that issues, changes, releases, DNS, PyPI, or other critical access can continue within a week if one person is unavailable. |
| `bus_factor` | Unmet | Recent commit history is dominated by one maintainer, and no public maintainer/release-access backup is documented. This is a SHOULD criterion and could be justified if private continuity arrangements exist. |
| `documentation_roadmap` | Unmet | `ROADMAP.md` exists, but it only extends to 2027-01-01 from an audit date of 2026-08-08 and contains stale statuses for already-published releases. Silver asks for at least the next year. |
| `documentation_architecture` | Unmet | API and plugin reference docs exist, but there is no high-level architecture/design document covering the broker, client, protocol stack, plugins, persistence, and trust boundaries. |
| `documentation_security` | Unmet | `SECURITY.md` documents vulnerability reporting and scope, but not a product security model stating what users can and cannot expect from aMQTT security behavior, defaults, and deployment responsibilities. |
| `documentation_quick_start` | Met | `docs/quickstart.md` gives installation and basic broker/publish/subscribe usage. |
| `documentation_current` | Unmet | Known stale documentation exists: `ROADMAP.md` has past targets marked in progress, `CONTRIBUTING.md` omits Python 3.14 and has an upstream typo, and `CODE_OF_CONDUCT.md` has an unresolved contact placeholder. |
| `documentation_achievements` | Met | `README.md` links project achievements and status badges, including CI, CodeQL, OpenSSF Best Practices, OpenSSF Baseline, Scorecard, PyPI, and docs. |
| `accessibility_best_practices` | Unmet | No accessibility review or accessibility-specific documentation was found for the project sites or generated dashboard. This is a SHOULD criterion and can be justified if the project limits its user-facing surface to accessible standard tools. |
| `internationalization` | N/A | aMQTT is primarily a protocol library, broker, and CLI tool. It does not provide an end-user localized UI or locale-sensitive user content. |
| `sites_password_security` | N/A | The project-controlled sites do not appear to store external-user passwords. Authentication is handled by GitHub, PyPI, Read the Docs, or similar providers. |
| `maintenance_or_update` | Met | `SECURITY.md` documents supported release lines, and `docs/changelog.md` documents upgrade, deprecation, and migration notes. |
| `report_tracker` | Met | GitHub Issues is used as the issue tracker. |
| `vulnerability_report_credit` | Met | `GHSA-2hjf-7455-w946`, published 2026-07-29, credits the reporter and acknowledges the researchers. |
| `vulnerability_response_process` | Met | `SECURITY.md` documents private reporting, scope, safe harbor, acknowledgement targets, assessment targets, remediation timing, and coordinated disclosure expectations. |
| `coding_standards` | Met | `CONTRIBUTING.md` requires tests/linting, and `pyproject.toml` defines Ruff, mypy, pylint, pytest, and coverage policy. |
| `coding_standards_enforced` | Met | CI enforces mypy, pylint, Bandit, Semgrep, Ruff, secret scanning, and requirements lock consistency. |
| `build_standard_variables` | N/A | The project does not generate native binaries with compiler/linker variables such as `CC`, `CFLAGS`, or `LDFLAGS`. |
| `build_preserve_debug` | N/A | There is no native build/install flow that strips or preserves compiler debug information. |
| `build_non_recursive` | Met | Python packaging uses Hatchling and does not recursively build subdirectories with cross-dependencies. |
| `build_repeatable` | Met | Two consecutive `uv build --sdist --wheel` runs produced identical wheel and sdist SHA-256 hashes. |
| `installation_common` | Met | End users can install with the standard Python package convention: `pip install amqtt`. |
| `installation_standard_variables` | Met | Python packaging delegates install-location behavior to standard pip/venv/user/prefix/target conventions. |
| `installation_development_quick` | Met | `CONTRIBUTING.md` documents quick developer setup with `uv`, editable install, dev/doc dependencies, tests, and pre-commit hooks. |
| `external_dependencies` | Met | Dependencies are listed in processable files: `pyproject.toml`, `uv.lock`, `requirements.txt`, `docs_test/package-lock.json`, and Go module files for test support. |
| `dependency_monitoring` | Met | Renovate is configured, CI checks lock/export consistency, Scorecard runs, and OSV/npm audit evidence exists in the repo workflow. |
| `updateable_reused_components` | Met | Reused components are managed through standard package managers and lock files rather than vendored forks. |
| `interfaces_current` | Unmet | The code still carries deprecated compatibility paths such as native `crypt` usage for legacy `sha512_crypt` verification and documented compatibility shims. This SHOULD criterion may be justifiable as backward-compatibility support, but it is not fully met as written. |
| `automated_integration_testing` | Met | `.github/workflows/ci.yml` runs automated tests on pull requests and pushes, across Python 3.10 through 3.14, and uploads JUnit and coverage artifacts. |
| `regression_tests_added50` | Met | Recent bug/security PRs commonly include regression tests, including `GHSA-2hjf-7455-w946` tests in `tests/test_broker.py`, empty packet read tests, auth failure tests, dependency/security remediation tests, and interoperability fixes. |
| `test_statement_coverage80` | Met | A full local `pytest --cov=amqtt` run reports 5,988 statements and 854 missed statements, so statement-only coverage is 85.7%. The displayed pytest-cov `Cover` value is 83% because branch coverage is enabled. |
| `test_policy_mandated` | Met | `CONTRIBUTING.md` requires tests for new features and says PRs must maintain or increase reported coverage. |
| `tests_documented_added` | Met | BadgeApp already marks this met; `CONTRIBUTING.md` documents that major new functionality and bug fixes require tests. |
| `warnings_strict` | Met | Ruff selects `ALL`, mypy is strict, pylint is configured, and CI blocks on Ruff, mypy, pylint, Bandit, and Semgrep findings where practical. |
| `implement_secure_design` | Unmet | Security tooling and several secure implementation choices exist, but there is no documented mapping from secure design principles to implementation decisions, and plaintext/anonymous defaults weaken the claim. |
| `crypto_weaknesses` | Met | New password hashing uses Argon2/Bcrypt, TLS uses Python's SSL defaults, and legacy SHA512 verification is deprecated compatibility behavior rather than a default new-security mechanism. |
| `crypto_algorithm_agility` | Met | TLS algorithm negotiation is delegated to Python/OpenSSL, and password storage supports modern alternatives such as Argon2 and Bcrypt. |
| `crypto_credential_agility` | Met | Password files, database-backed credentials, JWT secrets, and certificate/key files are external to code and can be replaced without recompilation. |
| `crypto_used_network` | Unmet | TLS and WSS are supported, but the default broker and client configs use plaintext `mqtt://` on port 1883, so insecure protocols are enabled by default. This is a SHOULD criterion and could be justified as MQTT compatibility. |
| `crypto_tls12` | Met | `ssl.create_default_context()` is used for TLS. On the local Python runtime, both client and server contexts report minimum TLS version `TLSv1_2`. |
| `crypto_certificate_verification` | Met | Client TLS verification and hostname checking are enabled by default through `ClientConfig.verify_cert = True`, `check_hostname = True`, and `ssl.create_default_context()`. |
| `crypto_verification_private` | N/A | aMQTT does not send HTTP headers containing private information. MQTT credentials are sent after TLS setup when a secure MQTT URL is used. |
| `signed_releases` | Unmet | GitHub releases have no signature assets, and there is no documented user process for obtaining signing keys and verifying release signatures. |
| `version_tags_signed` | Unmet | `v0.11.0` is an unsigned annotated tag, and `v0.11.4` is a lightweight tag pointing at a signed commit. Important release tags are not consistently signed and verifiable as tags. |
| `input_validation` | Unmet | Some MQTT topic validation is strong, but input validation is not comprehensive. Invalid UTF-8 in MQTT strings is converted to a Python string representation instead of rejected, and no project-wide allowlist validation assurance exists. |
| `hardening` | Unmet | No clear runtime hardening mechanism was found for the produced software or container image. This is a SHOULD criterion and can be justified if hardening is intentionally delegated to deployment configuration. |
| `assurance_case` | Unmet | No assurance case exists that includes threat model, trust boundaries, secure design argument, and common weakness mitigation argument. |
| `static_analysis_common_vulnerabilities` | Met | CI runs Bandit and Semgrep with security rules, and also runs CodeQL, mypy, pylint, and Ruff. |
| `dynamic_analysis_unsafe` | N/A | The produced software is Python, not memory-unsafe C/C++/Rust-style native code. Dynamic memory-safety tooling is not applicable. |

## Suggested Remediation Order

1. Finish Passing badge blockers, especially the currently unmet passing-level
   knowledge criterion.
2. Add governance, roles/responsibilities, continuity, and bus-factor docs.
3. Replace or extend `ROADMAP.md` so it covers at least through 2027-08-08 and
   remove stale statuses.
4. Add architecture, product security requirements, and assurance-case docs.
5. Fix stale docs: `CODE_OF_CONDUCT.md` contact, `CONTRIBUTING.md` Python 3.14
   and upstream typo, changelog formatting issues.
6. Decide whether to enforce DCO/CLA or document why it is not used.
7. Add release signing and tag-signing policy, then sign future release tags and
   artifacts.
8. Decide whether plaintext MQTT defaults are justified for compatibility or
   change defaults/document secure-by-default profiles.
9. Tighten input validation, especially MQTT UTF-8 string rejection, then
    document the validation model.
