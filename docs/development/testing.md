# Dream.OS Testing Documentation

## Overview
This document outlines the testing strategy, current status, and implementation plan for Dream.OS.

## Current Status (2024-03-19)

### Test Collection Summary
- Total Tests Found: 626
- Collection Errors: 5
- Warnings: 12

### Critical Issues
1. LogConfig Initialization Error
   - **File**: `tests/core/test_agent_loop_dreamscribe.py`
   - **Error**: `LogConfig.__init__() got an unexpected keyword argument 'log_dir'`
   - **Impact**: Blocks core agent loop testing
   - **Priority**: HIGH

2. Discord Mock Context Issues
   - **Files Affected**:
     - `tests/discord/test_discord_commands.py`
     - `tests/quarantine/test_discord_commands__with_coords.py`
     - `tests/voice/test_tts.py`
     - `tests/voice/test_voicebot.py`
   - **Error**: `'types.SimpleNamespace' object has no attribute 'Context'`
   - **Impact**: Blocks all Discord-related tests
   - **Priority**: HIGH

### Warnings
1. Deprecated Imports
   - `dreamos.core.cell_phone` is deprecated
   - **Fix**: Use `dreamos.core.messaging.cell_phone` instead

2. Unknown Pytest Marks
   - `@pytest.mark.swarm_core`
   - `@pytest.mark.bridge_integration`
   - `@pytest.mark.cellphone_pipeline`
   - **Action**: Register these marks in `pytest.ini`

3. Test Class Constructor Issues
   - Multiple test classes with `__init__` constructors:
     - `TestError`
     - `TestFeedbackLoop`
   - **Impact**: These classes cannot be collected as tests

## Test Coverage

### 1. Agent Control Tests
```python
tests/agent_control/
├── test_agent_controller.py
├── test_agent_operations.py
├── test_agent_restarter.py
└── test_dispatcher.py
```

#### Critical Paths:
- Agent initialization
- State management
- Error recovery
- Task routing

### 2. Cursor Tests
```python
tests/cursor/
├── test_cursor_controller.py
├── test_coordinate_transform.py
└── test_calibration.py
```

#### Critical Paths:
- Coordinate mapping
- Screen calibration
- Edge cases
- Error handling

### 3. UI Tests
```python
tests/ui/
├── test_automation.py
├── test_menu.py
└── test_dialogs.py
```

#### Critical Paths:
- Menu navigation
- Dialog handling
- Error recovery
- State management

### 4. Task Tests
```python
tests/tasks/
├── test_task_manager.py
├── test_scheduler.py
└── test_monitoring.py
```

#### Critical Paths:
- Task scheduling
- State tracking
- Error handling
- Resource management

## PyQt5 Test Coverage

### Tagged Test Files
1. `tests/core/test_agent_loop_dreamscribe.py`
   - Status: Tagged with `@pytest.mark.pyqt5`
   - Purpose: Tests Qt widget mocking and core functionality
   - Windows Behavior: Skipped

2. `tests/agent_control/test_devlog_manager.py`
   - Status: Tagged with `@pytest.mark.pyqt5`
   - Purpose: Tests Qt widget integration
   - Windows Behavior: Skipped

3. `tests/test_imports.py`
   - Status: Tagged with `@pytest.mark.pyqt5`
   - Purpose: Tests PyQt5 import functionality
   - Windows Behavior: Skipped

4. `tests/utils/gui_test_utils.py`
   - Status: Tagged with `@pytest.mark.pyqt5`
   - Purpose: GUI testing utilities
   - Windows Behavior: Skipped

5. `scripts/dev/test_import_pyqt5.py`
   - Status: Tagged with `@pytest.mark.pyqt5`
   - Purpose: PyQt5 import verification
   - Windows Behavior: Skipped

6. `bridge/test_bridge_loop.py`
   - Status: Tagged with `@pytest.mark.pyqt5`
   - Purpose: Qt integration in bridge layer
   - Windows Behavior: Skipped

## Implementation Plan

### Phase 1: Controller Tests

1. **Base Controller Tests**
   ```python
   def test_base_controller_initialization():
       """Test base controller setup"""
       pass

   def test_base_controller_state_management():
       """Test state handling"""
       pass

   def test_base_controller_error_handling():
       """Test error recovery"""
       pass
   ```

2. **Agent Controller Tests**
   ```python
   def test_agent_controller_initialization():
       """Test agent setup"""
       pass

   def test_agent_controller_operations():
       """Test agent operations"""
       pass

   def test_agent_controller_recovery():
       """Test error recovery"""
       pass
   ```

3. **System Controller Tests**
   ```python
   def test_system_controller_initialization():
       """Test system setup"""
       pass

   def test_system_controller_operations():
       """Test system operations"""
       pass

   def test_system_controller_recovery():
       """Test error recovery"""
       pass
   ```

### Phase 2: Cursor Tests

1. **Cursor Control Tests**
   ```python
   def test_cursor_movement():
       """Test cursor positioning"""
       pass

   def test_cursor_click():
       """Test click operations"""
       pass

   def test_cursor_drag():
       """Test drag operations"""
       pass
   ```

2. **Coordinate Transform Tests**
   ```python
   def test_screen_to_relative():
       """Test screen coordinate conversion"""
       pass

   def test_relative_to_screen():
       """Test relative coordinate conversion"""
       pass

   def test_transform_edge_cases():
       """Test edge cases"""
       pass
   ```

3. **Calibration Tests**
   ```python
   def test_calibration_setup():
       """Test calibration initialization"""
       pass

   def test_calibration_accuracy():
       """Test calibration accuracy"""
       pass

   def test_calibration_recovery():
       """Test calibration recovery"""
       pass
   ```

### Phase 3: UI Tests

1. **Automation Tests**
   ```python
   def test_ui_interaction():
       """Test basic UI interaction"""
       pass

   def test_menu_navigation():
       """Test menu system"""
       pass

   def test_dialog_handling():
       """Test dialog system"""
       pass
   ```

2. **Menu Tests**
   ```python
   def test_menu_creation():
       """Test menu building"""
       pass

   def test_menu_navigation():
       """Test menu navigation"""
       pass

   def test_menu_state():
       """Test menu state management"""
       pass
   ```

3. **Dialog Tests**
   ```python
   def test_dialog_creation():
       """Test dialog building"""
       pass

   def test_dialog_interaction():
       """Test dialog interaction"""
       pass

   def test_dialog_state():
       """Test dialog state management"""
       pass
   ```

### Phase 4: Task Tests

1. **Task Manager Tests**
   ```python
   def test_task_creation():
       """Test task initialization"""
       pass

   def test_task_execution():
       """Test task execution"""
       pass

   def test_task_recovery():
       """Test task recovery"""
       pass
   ```

2. **Scheduler Tests**
   ```python
   def test_schedule_creation():
       """Test schedule setup"""
       pass

   def test_schedule_execution():
       """Test schedule execution"""
       pass

   def test_schedule_recovery():
       """Test schedule recovery"""
       pass
   ```

3. **Monitoring Tests**
   ```python
   def test_monitor_initialization():
       """Test monitor setup"""
       pass

   def test_monitor_tracking():
       """Test state tracking"""
       pass
   ```

## Immediate Action Items

1. **Fix LogConfig**
   - Update `LogConfig` initialization to match expected parameters
   - Remove or update `log_dir` parameter

2. **Fix Discord Mock**
   - Update `mock_discord.py` to properly mock `commands.Context`
   - Ensure all Discord-related mocks are consistent

3. **Clean Up Test Classes**
   - Remove `__init__` constructors from test classes
   - Convert to proper pytest fixtures where needed

4. **Register Custom Marks**
   - Add missing pytest marks to `pytest.ini`

## Next Steps

1. **High Priority**
   - Fix LogConfig initialization
   - Complete Discord mock fixes
   - Update deprecated imports

2. **Medium Priority**
   - Register custom pytest marks
   - Clean up test class constructors

3. **Low Priority**
   - Address logging errors in comtypes shutdown
   - Review and update test documentation

## Continuous Integration Status

- **Main Branch**: ❌ Failing
- **Test Collection**: ❌ Errors
- **Test Execution**: Not reached due to collection errors

## Test Configuration
- Platform-specific skipping enabled in `conftest.py`
- Manual test plan available in `docs/manual_test_plan.md`
- Windows tests automatically skipped
- Linux/other platforms run all tests

## Best Practices

1. **Test Organization**
   - Group related tests in appropriate directories
   - Use clear, descriptive test names
   - Follow consistent naming conventions

2. **Test Quality**
   - Write clear assertions
   - Handle edge cases
   - Test error conditions
   - Use appropriate fixtures

3. **Test Maintenance**
   - Keep tests up to date
   - Remove obsolete tests
   - Update test documentation
   - Monitor test coverage

---
*Last Updated: 2024-03-19*
*Next Review: 2024-03-20* 