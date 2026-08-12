# OpenSSF Baseline Level 2 Assessment

Evaluated against OpenSSF Best Practices Baseline Level 2 criteria version
`v2026.02.19` from:

https://www.bestpractices.dev/en/projects/13571/baseline-2

The badge page itself currently has all Level 2 criteria set to `?`, so this is
an evidence-based assessment of the `Yakifo/amqtt` repository and GitHub project
as of August 10, 2026.

## Summary

- Met: 11
- Unmet: 8

Current blocker themes: GitHub workflow default permissions, signed release
artifacts/provenance, governance docs, required status checks, architecture
docs, and security-assessment docs.

## Criteria Assessment

| Criterion | Result | Evidence / Gap |
|---|---:|---|
| `OSPS-AC-04.01` default lowest CI/CD permissions | Unmet | GitHub API reports default workflow permissions as `write`; workflows mostly set `contents: read`, but repo default is not lowest. |
| `OSPS-BR-02.01` unique release version | Met | Releases use unique tags like `v0.11.4`; publish workflow validates tag format in `.github/workflows/publish-pypi.yml`. |
| `OSPS-BR-04.01` descriptive release log | Met | `v0.11.4` release notes and `docs/changelog.md` include security and functional changes. |
| `OSPS-BR-05.01` standardized dependency ingestion | Met | Build uses `uv build`; dependencies are in `pyproject.toml` and `uv.lock`. |
| `OSPS-BR-06.01` signed release or signed manifest with hashes | Unmet | PyPI `0.11.4` files have `has_sig: false`; PyPI integrity endpoint says no provenance; GitHub release has no signed assets or manifest. |
| `OSPS-DO-06.01` dependency selection/obtain/track docs | Unmet | `CONTRIBUTING.md` documents obtain/track via `uv`, `uv.lock`, and `requirements.txt`, but not how dependencies are selected. |
| `OSPS-DO-07.01` build instructions | Met | Contributor docs cover Python/uv setup, install, test dependencies, and commands in `CONTRIBUTING.md`. |
| `OSPS-GV-01.01` members with sensitive access | Unmet | No public `MAINTAINERS`, `GOVERNANCE`, or equivalent access list found. |
| `OSPS-GV-01.02` member roles/responsibilities | Unmet | No public role/responsibility document found. |
| `OSPS-GV-03.02` contributor guide | Met | `CONTRIBUTING.md` and the PR template define test, coverage, and lint expectations. |
| `OSPS-LE-01.01` legal authorization assertion | Met | Project is on GitHub with MIT license; GitHub Terms section D.6 says contributors license content under repository terms and assert they have the right to do so. No explicit DCO found, but GitHub ToS is acceptable per criterion detail. |
| `OSPS-QA-03.01` required status checks pass/bypass | Unmet | Branch protection exists, but required status checks list is empty via GitHub API. |
| `OSPS-QA-06.01` CI runs automated tests | Met | CI runs pytest across Python versions plus interop tests in `.github/workflows/ci.yml`. |
| `OSPS-SA-01.01` design docs with actors/actions | Unmet | API/plugin docs exist, but no design/architecture document demonstrating all actors and actions was found. |
| `OSPS-SA-02.01` external interface docs | Met | MkDocs navigation covers CLI, API, configuration, and plugin interfaces in `mkdocs.rtd.yml`. |
| `OSPS-SA-03.01` security assessment | Unmet | Security policy and tooling exist, but no threat model or security assessment document was found. |
| `OSPS-VM-01.01` CVD policy with timeframe | Met | `SECURITY.md` defines acknowledgment, assessment, and disclosure timelines. |
| `OSPS-VM-03.01` private vulnerability reporting | Met | GitHub Security Advisories and email are listed in `SECURITY.md`. |
| `OSPS-VM-04.01` public vulnerability data | Met | `v0.11.4` release/changelog publishes GHSA, affected versions, and mitigation context in `docs/changelog.md`. |

## Key Evidence

- `SECURITY.md` includes private vulnerability reporting through GitHub Security
  Advisories and `support@amqtt.io`, plus response/disclosure timelines.
- `CONTRIBUTING.md` includes development setup, local checks, testing
  expectations, fuzzing guidance, and dependency tracking with `uv.lock`.
- `.github/workflows/ci.yml` runs code quality checks, static security checks,
  secret scanning, interoperability tests, and pytest.
- `.github/workflows/publish-pypi.yml` validates release tags, builds wheel and
  sdist artifacts, and publishes to PyPI using trusted publishing permissions.
- `docs/changelog.md` contains the `0.11.4` security release note with GHSA,
  affected versions, and regression-test references.
- `mkdocs.rtd.yml` exposes CLI, API, configuration, plugin, changelog, security,
  support, and contribution documentation through the public docs site.

## Recommended Remediation

1. Change repository Actions default workflow permissions from write to read.
2. Add release signing or provenance, for example PyPI trusted-publishing
   attestations, Sigstore, or a signed manifest containing artifact hashes.
3. Add dependency selection criteria to `CONTRIBUTING.md` or a dependency policy.
4. Add `MAINTAINERS.md` or `GOVERNANCE.md` listing sensitive-resource access,
   roles, and responsibilities.
5. Configure required branch status checks for the CI checks that must pass
   before merging to `main`.
6. Add architecture/design documentation covering actors, actions, data flows,
   and trust boundaries.
7. Add a threat model or security assessment covering likely and impactful
   security problems for the broker, client, plugins, protocol parsing,
   authentication/authorization, TLS/transport handling, and release pipeline.

## Sources

- Best Practices Baseline Level 2 page:
  https://www.bestpractices.dev/en/projects/13571/baseline-2
- GitHub release `v0.11.4`:
  https://github.com/Yakifo/amqtt/releases/tag/v0.11.4
- PyPI JSON for `amqtt` `0.11.4`:
  https://pypi.org/pypi/amqtt/0.11.4/json
- GitHub Terms of Service:
  https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
