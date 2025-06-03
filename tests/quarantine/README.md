# Quarantined Tests

This directory contains tests that have been temporarily disabled due to various issues. The tests are marked with `@pytest.mark.skip` and include detailed explanations for their quarantine status.

## Test Categories

### 1. Permission/File Access Issues
- Windows file permission problems
- File access conflicts during test execution
- Test files being used by other processes
- Affected tests:
  - `test_is_logged_in_when_login_form_present`
  - `test_login_success`
  - `test_twitter_strategy_is_logged_in`

### 2. Configuration Issues
- Missing Reddit configuration
- Invalid configuration values
- Configuration path resolution problems
- Affected tests:
  - `test_retry_on_login_failure`
  - `test_max_retries_exceeded`
  - `test_rate_limit_persistent`
  - `test_invalid_media_rejection`
  - `test_valid_media_processing`

### 3. Log Manager Issues
- Log file creation and access issues
- File locking problems
- Log rotation conflicts
- Affected tests:
  - `test_basic_logging`
  - `test_log_levels`
  - `test_get_entries`
  - `test_metadata`
  - `test_error_handling`

### 4. Authentication/Login Issues
- Session validation problems
- Login form interaction failures
- Cookie handling issues
- Affected tests:
  - `test_verify_session_valid`
  - `test_login_failure_missing_button`
  - `test_login_retry_click_failure`
  - `test_login_missing_credentials`

### 5. Integration Issues
- Reddit API integration failures
- Error recovery problems
- Devlog embed validation issues
- Affected tests:
  - `test_reddit_strategy_integration`
  - `test_reddit_strategy_error_recovery`
  - `test_devlog_embed_validation`

### 6. Configuration Path Issues
- Default configuration loading problems
- Custom configuration validation failures
- Affected tests:
  - `test_config_defaults`
  - `test_config_custom_values`

## Next Steps

1. **File Permission Issues**
   - [ ] Investigate Windows file permission problems
   - [ ] Implement proper file locking mechanisms
   - [ ] Add cleanup procedures for test files

2. **Configuration Issues**
   - [ ] Add missing Reddit configuration
   - [ ] Validate configuration values
   - [ ] Fix configuration path resolution

3. **Log Manager Issues**
   - [ ] Fix log file access problems
   - [ ] Implement proper file locking
   - [ ] Resolve log rotation conflicts

4. **Authentication Issues**
   - [ ] Fix session validation
   - [ ] Improve login form interaction
   - [ ] Enhance cookie handling

5. **Integration Issues**
   - [ ] Fix Reddit API integration
   - [ ] Improve error recovery
   - [ ] Fix Devlog embed validation

6. **Configuration Path Issues**
   - [ ] Fix default configuration loading
   - [ ] Improve custom configuration validation

## Contributing

When working on fixing these issues:

1. Create a new branch for each category of fixes
2. Address one category at a time
3. Update this README with progress
4. Add test cases to verify fixes
5. Document any workarounds or temporary solutions

## Status Tracking

- [ ] Permission/File Access Issues
- [ ] Configuration Issues
- [ ] Log Manager Issues
- [ ] Authentication/Login Issues
- [ ] Integration Issues
- [ ] Configuration Path Issues

## Notes

- All original test code has been moved to `test_quarantine.py`
- Each test is marked with `@pytest.mark.skip` and includes a reason
- Tests are organized by category with clear section headers
- Fixtures and imports are preserved for easy re-enabling 