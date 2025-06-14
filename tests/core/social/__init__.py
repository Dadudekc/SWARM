# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

# EDIT START: lazy imports guarded for skip-safe test execution
def _lazy_import(name: str) -> None:  # noqa: D401
    try:
        globals()[name] = __import__(f"{__name__}.{name}", fromlist=[name])
    except BaseException:
        # Ignore any import-time skips or missing deps during partial test runs.
        pass


for _mod in [
    "base",
    "base_test",
    "cleanup_test",
    "conftest",
    "json_settings_test",
    "log_batcher_test",
    "log_config_test",
    "log_entry_test",
    "log_level_test",
    "log_manager_test",
    "log_pipeline_test",
    "log_rotator_test",
    "log_writer_test",
    "media_validator_test",
    "rate_limiter_test",
    "social_common_test",
]:
    _lazy_import(_mod)
# EDIT END

__all__ = [
    'base',
    'base_test',
    'cleanup_test',
    'conftest',
    'json_settings_test',
    'log_batcher_test',
    'log_config_test',
    'log_entry_test',
    'log_level_test',
    'log_manager_test',
    'log_pipeline_test',
    'log_rotator_test',
    'log_writer_test',
    'media_validator_test',
    'rate_limiter_test',
    'social_common_test',
]
