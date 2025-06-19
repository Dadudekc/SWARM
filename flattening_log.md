# Directory Flattening Log

This log summarizes structural changes applied to simplify the repository layout.

## agent_tools
- Moved `agent_tools/core/utils/file_utils.py` to `agent_tools/core/file_utils.py`.
- Removed the now-empty `agent_tools/core/utils` package.
- Updated `agent_tools/core/__init__.py` to expose `file_utils` under the legacy
  `agent_tools.core.utils` alias.

## dreamos/core
- Removed obsolete `dreamos/core/cursor` package and updated imports to use the
  existing `cursor_controller.py` module at the package root.
- Flattened automation browser helper: `browser/browser_control.py` is now
  `automation/browser_control.py`.
- Deleted unused `bridge/scripts` package; its contents already exist in
  `bridge/run_response_loop.py`.
- Moved `errors/bridge_errors.py` to `bridge_errors.py` and updated dependent
  imports. The `dreamos.core.errors` package now re-exports this module.
- Collapsed `nlp/keyword_extract.py` to `keyword_extract.py` and updated
  `dreamscribe` to import from the new path.
