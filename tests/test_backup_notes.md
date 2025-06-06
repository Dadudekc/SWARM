# Test Consolidation Notes

## Files to Consolidate

### Config Manager Tests
1. `tests/test_config.py` (8.1KB)
2. `tests/test_config/` (directory)
3. `tests/social/test_json_config.py` (1.2KB)

### Log Manager Tests
1. `tests/test_log_manager.py` (32KB)
2. `tests/core/test_log_manager.py` (9.8KB)

### Message Processing Tests
1. `tests/core/test_message_loop.py` (10KB)
2. `tests/core/test_persistent_queue.py` (1.6KB)
3. `tests/core/test_response_collector.py` (4.1KB)
4. `tests/test_response_collector.py` (4.9KB)

## Consolidation Plan

### 1. Config Manager Tests
- Keep `tests/test_config.py` as canonical
- Merge useful test cases from `test_json_config.py`
- Archive `tests/test_config/` directory

### 2. Log Manager Tests
- Keep `tests/test_log_manager.py` as canonical (more comprehensive)
- Merge unique test cases from `tests/core/test_log_manager.py`
- Update imports to use new config manager

### 3. Message Processing Tests
- Keep `tests/core/test_message_loop.py` as canonical
- Merge queue tests into a single `test_queue.py`
- Consolidate response collector tests into `tests/core/test_response_collector.py`

## Test Coverage Notes

### Config Manager
- Need to add tests for bridge-specific configuration
- Add validation test cases
- Test file permissions handling

### Log Manager
- Add tests for new log rotation features
- Test batch processing
- Verify Discord integration

### Message Processing
- Add tests for rate limiting
- Test error handling and retries
- Verify message persistence

## Migration Status

- [ ] Config Manager tests consolidated
- [ ] Log Manager tests consolidated
- [ ] Message Processing tests consolidated
- [ ] All tests passing
- [ ] Documentation updated 