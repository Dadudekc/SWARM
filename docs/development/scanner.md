# 🧠 Scanner Module — High-Level Overview

The Project Scanner is a modular, concurrency-enabled analysis system for navigating and inspecting source files across large codebases. Its purpose is to generate metadata-rich summaries and ChatGPT context for downstream AI processing.

## 1. ProjectScanner (👁️ Orchestrator)
- Recursively walks the `project_root`, filtering out known noise (e.g., `venv/`, `__pycache__/`, `node_modules/`).
- Delegates per-file decisions to `FileProcessor`.
- Tracks file hashes in `dependency_cache.json` to skip unchanged files.
- Detects renamed/moved files by matching hashes across paths.
- Dispatches analysis tasks via `MultibotManager` for parallel processing.
- Persists unified results into `project_analysis.json`.
- Optionally generates:
  - `chatgpt_project_context.json` for LLM context loading.
  - `__init__.py` scaffolding for Python packages.
  - A test analysis report for test coverage planning.
- Runs on a pre-push hook to ensure analysis is up-to-date before code is pushed.

## 2. LanguageAnalyzer (🧬 Parser Brain)
- Analyzes source code using:
  - `ast` for Python.
  - `tree-sitter` (if available) for Rust, JS/TS.
- Extracts:
  - Language, classes, functions, routes (e.g., `@app.route()`), and complexity.
- Returns normalized data for aggregation.

## 3. FileProcessor (🧹 File Handler)
- Computes file hash with `hashlib.md5`.
- Checks if file is eligible via exclusion logic.
- Consults the hash cache to avoid duplicate work.
- If a file has changed, reads it and passes contents to `LanguageAnalyzer`.

## 4. ReportGenerator (📦 Merger + Exporter)
- Merges current analysis into persistent `project_analysis.json`.
- Preserves data for unchanged or missing files from previous scans.
- Generates:
  - ChatGPT context file (`chatgpt_project_context.json`)
  - `__init__.py` auto-stubs (if requested)
  - A test analysis report for test coverage planning.

## 5. MultibotManager + BotWorker (⚙️ Parallelism Engine)
- `MultibotManager` creates a thread pool of `BotWorker` instances.
- `BotWorker` pulls file tasks from a shared queue, processes them, and appends results.
- Enables scalable, high-speed scanning on multicore machines.

## 6. CLI Entrypoint (🛠️ User Access)
- `scanner.py` can be run via CLI with arguments:
  - `--project-root`
  - `--ignore`
  - `--categorize-agents`
  - `--generate-init-files`
  - `--export-context`
- Initializes `ProjectScanner`, runs scan, and triggers optional post-processing.

---

## 🧩 Summary

This pipeline enables:
- Efficient project-wide scanning with caching
- Cross-language support via `LanguageAnalyzer`
- Concurrent execution for speed
- Modular outputs for AI workflows

Use cases:
- Agent context generation
- Complexity audits
- Auto-refactoring prep
- Test coverage planning 