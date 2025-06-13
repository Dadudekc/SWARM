# Dream.OS Refactor Plan

## 🎯 Overview

This document outlines the strategic refactoring of Dream.OS core components to reduce duplication and improve maintainability.

## 📊 Current State Analysis

### 1. Agent Controllers (`agent_control/`)
Current files:
- `agent_controller.py` (10KB)
- `agent_control.py` (2.6KB)
- `controller.py` (14KB)

Issues:
- Overlapping responsibilities
- Duplicate control logic
- Unclear boundaries between system and agent control

### 2. Cursor Management
Current files:
- `core/cursor_controller.py`
- `agent_control/cursor_controller.py`
- `coordinate_transformer.py`
- `coordinate_calibrator.py`

Issues:
- Scattered cursor control logic
- Duplicate coordinate handling
- Unclear calibration flow

### 3. UI Automation
Current files:
- `ui_automation.py` (50KB)
- `menu_builder.py`
- `agent_selection_dialog.py`

Issues:
- Monolithic automation file
- Mixed concerns
- Hard to test

### 4. Task Management
Current files:
- `task_manager.py`
- `system_orchestrator.py`
- `periodic_restart.py`

Issues:
- Scattered task logic
- Unclear orchestration boundaries
- Duplicate scheduling code

## 🎯 Refactor Goals

1. **Consolidate Controllers**
   - Create clear hierarchy
   - Eliminate duplicate logic
   - Establish clear interfaces

2. **Unify Cursor Management**
   - Single source of truth
   - Clear calibration flow
   - Consistent coordinate handling

3. **Modularize UI Automation**
   - Break down large files
   - Separate concerns
   - Improve testability

4. **Centralize Task Management**
   - Unified task orchestration
   - Clear scheduling
   - Consistent monitoring

## 📋 Implementation Plan

### Phase 1: Preparation (Week 1)
1. Create new directory structure
2. Add test coverage for critical paths
3. Document current interfaces

### Phase 2: Controller Consolidation (Week 2)
1. Create base controller
2. Migrate agent controller
3. Migrate system controller
4. Update imports

### Phase 3: Cursor Management (Week 3)
1. Unify cursor control
2. Implement calibration
3. Add coordinate transforms
4. Update callers

### Phase 4: UI Automation (Week 4)
1. Break down ui_automation.py
2. Create menu system
3. Implement dialogs
4. Update references

### Phase 5: Task Management (Week 5)
1. Create task manager
2. Implement scheduler
3. Add monitoring
4. Migrate existing tasks

## 🧪 Testing Strategy

1. **Unit Tests**
   - Controller interfaces
   - Cursor operations
   - UI automation
   - Task scheduling

2. **Integration Tests**
   - End-to-end flows
   - Cross-component interaction
   - Error handling

3. **Performance Tests**
   - Response times
   - Resource usage
   - Memory leaks

## 📝 Documentation Updates

1. **Code Documentation**
   - Update docstrings
   - Add type hints
   - Document interfaces

2. **Architecture Documentation**
   - Update module overview
   - Document dependencies
   - Add sequence diagrams

## 🚀 Migration Steps

1. **For Each Component:**
   - Create new structure
   - Add tests
   - Migrate code
   - Update imports
   - Verify functionality
   - Remove old code

2. **Validation:**
   - Run test suite
   - Check performance
   - Verify integrations
   - Update documentation

## ⚠️ Risk Mitigation

1. **Code Freeze**
   - Tag current version
   - Create backup branch
   - Document current state

2. **Rollback Plan**
   - Keep old code until verified
   - Maintain compatibility layer
   - Document rollback steps

## 📅 Timeline

- Week 1: Preparation
- Week 2: Controllers
- Week 3: Cursor
- Week 4: UI
- Week 5: Tasks
- Week 6: Testing & Documentation

## 🎯 Success Criteria

1. **Code Quality**
   - Reduced duplication
   - Improved test coverage
   - Clear interfaces

2. **Performance**
   - No regression
   - Improved response times
   - Better resource usage

3. **Maintainability**
   - Clear documentation
   - Easy to extend
   - Simple to test 