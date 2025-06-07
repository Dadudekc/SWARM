# Security Hardening

Phase 3 emphasizes running agents with restricted permissions and protecting log files.

- Log directories are created with mode `700` and new log files with mode `600`.
- When running Docker containers, use a non-root user and limit host mounts.
- Regularly audit `runtime/` for sensitive data and clean up old files with `tools.cleanup_project`.

These steps reduce exposure when deploying Dream.OS in multi-user environments.
