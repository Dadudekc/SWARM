# Phase 3 Preparation

This document outlines the initial preparation work for **Phase 3 – Scalability & Hardening**.

## CONTAINERIZE-AGENTS-001
- Draft Dockerfile for the core agent runtime.
- Integrate container build into CI using `docker build`.
- Explore Docker Compose for multi-agent orchestration.

## SETUP-METRICS-DASHBOARD-002
- Prototype a real-time metrics feed using the existing `LogMetrics` data.
- Expose metrics through a simple Flask endpoint for Grafana/Prometheus.
- Provide example dashboard configuration.

## SECURITY-HARDENING-003
- Review sandboxing of agent workspaces.
- Audit log file permissions and use restrictive defaults.
- Document best practices for running containers with least privilege.
