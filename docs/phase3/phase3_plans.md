# Phase 3 Preparation

This document outlines the preparation work for **Phase 3 – Scalability & Hardening**.
The initial milestones are now complete and prototypes are available.

## CONTAINERIZE-AGENTS-001
- Dockerfile added for the core agent runtime.
- CI can build the container using `docker build`.
- Docker Compose exploration is ongoing.

## SETUP-METRICS-DASHBOARD-002
- Real-time metrics feed implemented using `LogMetrics` data.
- Flask endpoint `/metrics` serves JSON for Grafana/Prometheus.
- Example dashboard configuration provided.

## SECURITY-HARDENING-003
- Log directories default to `700` and files to `600`.
- Documentation lists container hardening best practices.
- Further sandboxing work planned.
