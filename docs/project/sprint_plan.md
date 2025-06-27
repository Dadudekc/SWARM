# Beta Sprint Plan

This sprint focuses on achieving Beta readiness by completing outstanding items from the PRD and roadmap.

## Objectives
- Finalize containerization, metrics dashboard and security hardening.
- Expand the Dreamscribe lore system with ingestion and query APIs.
- Lay groundwork for community deployment and persistent code loops.
- Ensure full test coverage and integration validation.

## Task Breakdown

| ID | Phase | Objective | Status |
| --- | --- | --- | --- |
| VALIDATE-CONTAINER-BUILD-004 | Scalability & Hardening | Validate Docker builds across all agents | pending |
| COMPLETE-GRAFANA-DASHBOARD-005 | Scalability & Hardening | Finalize Grafana dashboard for metrics endpoint | pending |
| INGEST-DEVLOG-FAILURES-006 | Lore Creation & Memory Ecosystem | Import devlogs and failures via Dreamscribe | pending |
| LORE-QUERY-API-007 | Lore Creation & Memory Ecosystem | Implement query interface to surface lore | pending |
| LOCAL-INSTANCE-DEPLOYMENT-008 | Self-Growing Community Platform | Enable users to deploy Dream.OS locally or via Discord | pending |
| PERSISTENT-LOOPS-009 | Self-Growing Community Platform | Add persistent loops for code evolution and testing | pending |
| EXTENSION-HOOKS-010 | Self-Growing Community Platform | Provide extension hooks for broad domain usage | pending |
| BETA-TEST-SUITE-011 | Testing & Quality | Run full test suite and validate new features | pending |

Each task corresponds to an entry in `dreamos/tasks/phase_plan_tasks.yaml` so agents can coordinate work using the YAML file.

## Testing
Run the standard suite before closing the sprint:

```bash
python run_tests.py
```

All new features must include unit tests and pass continuous integration checks.
