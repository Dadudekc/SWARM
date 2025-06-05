# Directory Duplication Analysis

This report highlights duplicated or overlapping files across key folders. The analysis helps plan consolidation work.

## Diff Summary

### `src/` vs `dreamos/`
```
Only in dreamos: __init__.py
Only in dreamos: apps
Only in src: auth
Only in dreamos: bridge.py
Only in dreamos: config
Only in dreamos/core: __init__.py
Only in dreamos/core: agent_control
Only in dreamos/core: agent_interface.py
Only in dreamos/core: agent_logger.py
Only in dreamos/core: agent_loop.py
Only in dreamos/core: agents
Only in dreamos/core: ai
Only in dreamos/core: autonomy
Only in dreamos/core: autonomy_loop_runner.py
Only in dreamos/core: captain
Only in dreamos/core: cell_phone.py
Only in dreamos/core: cli.py
Only in dreamos/core: codex
Only in dreamos/core: config
Only in dreamos/core: config.py
Only in dreamos/core: content_loop.py
Only in dreamos/core: coordinate_manager.py
Only in dreamos/core: coordinate_utils.py
Only in dreamos/core: cursor_controller.py
Only in dreamos/core: devlog.py
Only in dreamos/core: dreamscribe.py
Only in dreamos/core: integrations
Only in dreamos/core: log_manager.py
Only in dreamos/core: memory_querier.py
Only in dreamos/core: menu.py
Only in dreamos/core: message.py
Only in dreamos/core: message_loop.py
Only in dreamos/core: message_processor.py
Only in dreamos/core: messaging
Only in dreamos/core: messaging.py
Only in dreamos/core: metrics.py
Only in dreamos/core: persistent_queue.py
Only in dreamos/core: region_finder.py
Only in dreamos/core: response_collector.py
Only in dreamos/core: self_discovery
Only in dreamos/core: shared
Only in dreamos/core: system_init.py
Only in dreamos/core: ui
Only in dreamos/core/utils: coords.py
Only in src/core/utils: fix_log_tests.py
```
These directories house distinct modules. `src/` mostly contains authentication helpers, while `dreamos/` holds the full core implementation. No direct file overlap was found.

### `config/` vs `dreamos/config/`
```
Only in config: agent_config.yaml
Only in config: agent_ownership.json
Only in config: agent_regions.json
Files config/autonomy_config.json and dreamos/config/autonomy_config.json differ
Only in config: chatgpt_bridge.yaml
Only in config: config.json
Only in config: content_loop_behavior.yaml
Only in config: episode-09.yaml
Only in config: example.env
Only in config: reddit.json
Only in config: social.json
Only in config: stealth_bridge.yaml
Only in config: system_config.yaml
Only in config: test_devlog_config.json
```
Both contain `autonomy_config.json`, but the remaining files only exist in `config/`. Root-level duplicates such as `config.json` and `system_config.yaml` appear in two places.

### `tools/` vs `scripts/`
```
Only in tools: analyze_logs.py
Only in tools: autopitch_machine.py
Only in tools: backup_restore.py
Only in tools: calibrate_coordinates.py
Only in tools: capture_copy_button.py
Only in tools: check_cursor_coords.py
Only in tools: create_minimal_core.py
Only in tools: daily_trigger.py
Only in tools: devlog_pitcher.py
Only in tools: fix_test_issues.py
Only in tools: layout_snapshot.py
Only in tools: life_os_dashboard.py
Only in tools: odyssey_board.py
Only in tools: odyssey_generator.py
Only in tools: overlap_heatmap.py
Only in tools: performance_monitor.py
Only in tools: prepare_release.py
Only in tools: print_metrics_summary.py
Only in tools: recalibrate_coords.py
Only in tools: reorganize_social.py
Only in scripts: requirements.txt
Only in tools: run_menu.py
Only in tools: send_task.py
Only in tools: send_test_messages.py
Only in tools: test_log_analyzer.py
Only in tools: visualize_agent_layout.py
Only in tools: zip_resolver.py
```
Utility scripts are split across these folders. `dry_scanner.py` exists in both locations, while the rest are unique to `tools/`.

## Recommendations
- Consolidate config files under `dreamos/config/`.
- Merge `tools/` and `scripts/` to avoid confusion.
- Unify any redundant test directories so all tests live under `tests/`.
- Review `src/` and `dreamos/` for possible integration.
