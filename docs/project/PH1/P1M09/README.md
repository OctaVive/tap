# P1-M09 - Runtime capability probe and typed agent create/inspect/stop

Status: **In progress; NOT PASSED**.

## Requirement and acceptance contract

- Scope: Runtime capability probe and typed agent create/inspect/stop.
- Prerequisites: [P1-M08](../P1M08/README.md).
- Acceptance gate: SEC-05/08/16; real engine constraints verified, no host ports.
- Source: [PH1 minimal plan](../../../plans/PH1/minimal.md).
- Requirements: [project requirements](../../requirements.md), [requirement-to-milestone map](../../requirement-milestones.md) and [evidence checklist](../../requirement-evidence.md).
- Security coverage: SEC-03, SEC-05, SEC-08, SEC-16.

## Documents

- [Implementation plan](implementation-plan.md)
- [Implementation evidence](implementation-evidence.md)
- [Test plan](test-plan.md)
- [Acceptance report — INCOMPLETE](testing/acceptance-report.md)
- [Runtime execution contract](../../specifications/runtime-execution.md)
- [deployment agent](../../specifications/deployment-agent.md)

The implementation includes app-scoped provisioning, measured enforcement,
durable authorization and separate agent/controller process wiring. Real single-
and two-service development lifecycles have passed; full runtime acceptance is
incomplete (R01 FAIL, R02–R10 NOT_RUN). No accepted production runtime template
has been delivered. Earlier software counts and feasibility failures remain
historical evidence. See [current execution plan](execution-plan.md),
[operational handoff](remaining-work.md) and the
[required constituent catalog](testing/constituents.json) for current work.
