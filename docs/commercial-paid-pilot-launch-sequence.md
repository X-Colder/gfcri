# GFCRI Paid Pilot Launch Sequence

Date: 2026-07-10
Goal: launch a paid GFCRI Institutional Edition pilot in 7-10 days without over-claiming production readiness.

## Entry Criteria

Start the buyer-facing pilot only when these are true:

- Sponsor, success owner, and pilot users are named.
- Use cases are narrowed to two recurring workflows.
- Non-advisory positioning is accepted.
- Data source and licensing caveats are acknowledged.
- Deployment mode is selected.
- Operator has run the smoke checklist or documented why it is deferred.

## Day-by-Day Sequence

| Day | Owner | Action | Output |
|---:|---|---|---|
| 1 | PM | Confirm buyer segment, sponsor, workflow, budget path, and success criteria | Pilot kickoff notes |
| 1 | DOCS | Send trust review pack and non-advisory language | Customer review package |
| 2 | OPS | Confirm deployment mode, host, ports, data refresh mode, secrets owner | Deployment plan |
| 2 | BE | Decide whether API key is required for this pilot | Integration scope decision |
| 3 | OPS | Deploy or prepare demo environment from runbook | Running pilot environment or dry-run report |
| 3 | QA | Run build, health, freshness, dashboard, institutional page, and report checks | Smoke-test record |
| 4 | Data/model owner | Run market-data refresh or CSV import; verify freshness and publication gate | Data readiness evidence |
| 5 | PM | Configure two buyer workflows and prepare demo narrative | Buyer-specific demo script |
| 6 | DOCS | Review methodology, source-tier, limitation, and disclaimer with customer reviewers | Trust review notes |
| 7 | ORCH/CR | Run internal dry-run, resolve launch blockers, freeze pilot scope | Launch/no-launch decision |
| 8-10 | All | Security questionnaire, environment tuning, or compliance copy updates if needed | Buyer kickoff readiness |

## Launch Meeting Agenda

1. Position GFCRI as macro risk monitoring and explanation infrastructure.
2. Show current GFCRI, alert level, index date, and data freshness state.
3. Explain the official publication gate and how blocked runs are disclosed.
4. Walk through key drivers, hidden risk, transmission channels, and source-tier disclosure.
5. Show Institutional Radar as official metadata mapping, not full-text ingestion.
6. Map the product to the buyer's two selected workflows.
7. Confirm the 30-day acceptance criteria and next commercial decision date.

## Required Artifacts

| Artifact | File |
|---|---|
| Commercial pilot package | `docs/commercial-pilot-package.md` |
| Customer trust review pack | `docs/commercial-trust-review-pack.md` |
| Delivery and operations runbook | `docs/commercial-delivery-runbook.md` |
| Engineering gap list | `docs/commercial-engineering-gap-list.md` |
| Pilot QA matrix | `docs/commercial-pilot-qa-matrix.md` |
| Progress board | `docs/commercialization-progress.md` |

## Go / No-Go Rules

Go if:

- Frontend and Python verification pass.
- API, data freshness, and report endpoints pass in the target environment.
- Data quality gate behavior is demonstrated or documented with evidence.
- Customer accepts non-advisory positioning and data-source caveats for pilot use.
- Rollback path is documented.

No-go if:

- Critical market data is missing and no approved offline import/backfill is available.
- The latest index is presented as current when it is only a held reliable observation.
- Customer requires production SSO/RBAC/audit logs before pilot and those are not scoped.
- Data redistribution or client-facing report rights are required but not legally cleared.
- No operator owns deployment, logs, backup, and incident response during the pilot.

## Week 2-4 Pilot Rhythm

| Cadence | Activity | Evidence |
|---|---|---|
| Daily | Check API health, data freshness, latest index date, and blocked quality events | Operator checklist |
| Weekly | Review top risk drivers, radar signals, and workflow usefulness with sponsor | Weekly risk walkthrough |
| Mid-pilot | Confirm whether value is research, risk, advisor communication, or integration | Sponsor feedback |
| Final week | Decide conversion, extension, enterprise scope, or no-go reason | Commercial decision memo |

## Next Implementation Choices

After the first paid pilot is scheduled, prioritize only the engineering work the buyer actually needs:

1. Pilot account provisioning if demo access is manual.
2. Market refresh event persistence if operators need stronger evidence.
3. API key skeleton if the buyer wants integration.
4. Report audit/export disclaimer if reports leave the internal team.
5. Full RBAC, SSO, audit logs, and signed exports only after pilot conversion signal.
