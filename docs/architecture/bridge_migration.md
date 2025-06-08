# Bridge System Migration

## Class Consolidation Map

### 1. Bridge Core (`dreamos/core/bridge/`)

#### `base.py`
- [x] `BaseBridge` (abstract)
- [x] `BridgeConfig`

#### `handlers/base.py`
- [ ] `BaseBridgeHandler` (from `dreamos/core/autonomy/handlers/bridge/base_bridge_handler.py`)
- [ ] `BridgeOutboxHandler` (from `dreamos/core/autonomy/handlers/bridge/bridge_outbox_handler.py`)
- [ ] `BridgeInboxHandler` (from `dreamos/core/autonomy/handlers/bridge/bridge_inbox_handler.py`)

#### `processors/base.py`
- [ ] `BaseBridgeProcessor` (from `dreamos/core/autonomy/processors/bridge_processor.py`)
- [ ] `PromptStreamer` (from `dreamos/core/autonomy/processors/prompt_streamer.py`)
- [ ] `ResponseValidator` (from `dreamos/core/autonomy/processors/response_validator.py`)

#### `monitoring/metrics.py`
- [ ] `BridgeMetrics` (from `dreamos/core/monitoring/bridge_metrics.py`)
- [ ] `BridgeHealthMonitor` (from `dreamos/core/monitoring/bridge_health.py`)

### 2. Response System (`dreamos/core/response/`)

#### `base.py`
- [x] `BaseResponse`
- [x] `BaseResponseProcessor`
- [x] `ResponseMemory`

#### `daemon.py`
- [ ] `ResponseLoopDaemon` (from `dreamos/core/autonomy/base/response_loop_daemon.py`)
- [ ] `EnhancedResponseLoopDaemon` (from `dreamos/core/autonomy/enhanced_response_loop_daemon.py`)

### 3. Integration Layer (`dreamos/core/integration/`)

#### `bridge.py`
- [x] `BridgeIntegration`

#### `chatgpt.py`
- [ ] `ChatGPTBridge` (from `dreamos/core/messaging/chatgpt_bridge.py`)
- [ ] `ChatGPTBridgeLoop` (from `dreamos/core/messaging/chatgpt_bridge_loop.py`)

## Migration Steps

1. **Test Coverage**
   - [x] Base bridge tests
   - [x] Handler tests
   - [ ] Processor tests
   - [ ] Integration tests

2. **Class Migration**
   - [ ] Move handlers
   - [ ] Move processors
   - [ ] Move monitoring
   - [ ] Move response daemons

3. **Integration Updates**
   - [ ] Update imports
   - [ ] Update configuration
   - [ ] Update documentation

4. **Cleanup**
   - [ ] Remove old files
   - [ ] Update references
   - [ ] Verify functionality

## Testing Strategy

1. **Unit Tests**
   - Test each component in isolation
   - Mock dependencies
   - Verify interfaces

2. **Integration Tests**
   - Test component interactions
   - Verify data flow
   - Check error handling

3. **System Tests**
   - Test full bridge loop
   - Verify monitoring
   - Check performance

## Rollback Plan

1. Keep old files until migration verified
2. Maintain backward compatibility
3. Document rollback procedures
4. Test rollback scenarios 