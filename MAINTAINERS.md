# QUILL Maintainers

This file describes maintainer responsibilities and operational expectations.

## Named maintainers

| Role | Name | Contact |
|---|---|---|
| Code Maintainer | Jeff Bishop | jeff@jeffbishop.com |
| Translation Coordinator | Vacant — see below | open a GitHub issue with label `translation` |

## Maintainer team

- Community Access maintainers (`@Community-Access`)

## Responsibilities

1. Triage issues and guide contributors to the right template/workflow.
2. Review pull requests for correctness, accessibility, and maintainability.
3. Keep release process and documentation current.
4. Enforce `CODE_OF_CONDUCT.md` and `SECURITY.md`.
5. Protect user trust: no silent network behavior, no unsafe defaults.

## Triage and labeling standards

Maintainers should apply both a **type** and an **area** label:

- Type: `bug`, `feature`, `documentation`, `security`
- Area: `accessibility`, `ai`, `intake`, `snippets`, `dictation`, `performance`, `stability`

Priority labels:

- `p0`: release blocker (launch crash, data loss, severe accessibility break)
- `p1`: major workflow break

Triage target: new issues receive an initial maintainer response within 5 business days.

## Review expectations

Maintainers should request changes when a PR:

- introduces accessibility regressions,
- bypasses architecture boundaries from `docs/QUILL-PRD.md`,
- weakens security/privacy constraints,
- omits required tests/checks for changed behavior.

## Availability and handoff

If a maintainer is unavailable, another maintainer should take ownership of:

1. Security reports
2. Release-blocking regressions
3. Accessibility regressions

## Role descriptions

**Code Maintainer** — Reviews and merges pull requests, triages bug reports
and feature requests, cuts releases, enforces code quality gates and CI
requirements, and sets technical direction for the project.

**Translation Coordinator** — Sends translation calls to Language Coordinators
before each release, onboards new language teams, maintains the Crowdin project
configuration, resolves translation disputes that Language Coordinators
escalate, and ensures the Translation Style Guide stays current. Must be
available during the two-week pre-release window. This is a named maintainer
role, not a casual volunteer position.

To apply for Translation Coordinator, open a GitHub issue with the label
`translation`. For full information about translation contribution, including
the four-tier role model and how to get started, see
[docs/translating.md](docs/translating.md).

## Related docs

- `CONTRIBUTING.md`
- `GOVERNANCE.md`
- `SECURITY.md`
- `RELEASE.md`
- `docs/translating.md`
- `docs/TRANSLATION_STYLE_GUIDE.md`
