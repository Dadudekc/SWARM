# AGENTS Instructions for SWARM Repository

This file contains guidance for the automated agent working with this repository.

## Directory Consolidation Guidance
- Several top‑level directories contain only a single script or configuration file.
- Consider merging the following directories to reduce clutter:
  - `examples/` -> move `llm_agent_example.py` under `docs/examples/`.
  - `episodes/` -> integrate `content_loop_behavior.yaml` into `config/` or `dreamos/`.
  - `metrics/` and `reports/` -> fold their single monitoring/report scripts into `scripts/` or `tools/`.
  - `scripts/` and `tools/` -> these serve a similar purpose; merging them keeps utilities together.
  - `self_discovery/` -> if its functionality belongs in `dreamos/core` or `src/`, relocate it accordingly.
  - `runtime/queue/` -> keep within `runtime/` but collapse the extra level if no other runtime assets exist.
- Directories to keep separate for clarity include `crime_report_generator`, `discord_bot`, `dreamos`, `social`, and `agent_tools`.

## Usage
- When modifying or adding code, attempt to maintain this streamlined structure.
- Run the test suite with `python run_tests.py` before submitting changes.

