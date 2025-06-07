"""
Legacy Error Management Tests
----------------------------
Archived test cases from the error management system.
These tests were removed during the deduplication cycle to reduce bloat.
"""

# ErrorTracker Tests
def test_record_success(error_tracker):
    """Test success recording."""
    error_tracker.record_success("test_agent")
    
    assert error_tracker.can_execute("test_agent")
    assert error_tracker.get_error_count("test_agent") == 0

def test_error_count(error_tracker):
    """Test error counting."""
    # Record multiple errors
    for _ in range(3):
        error_tracker.record_error(
            error_type="TestError",
            message="Test error",
            severity=ErrorSeverity.LOW,
            agent_id="test_agent"
        )
    
    assert error_tracker.get_error_count("test_agent") == 3
    assert error_tracker.get_error_count("test_agent", ErrorSeverity.LOW) == 3
    assert error_tracker.get_error_count("test_agent", ErrorSeverity.HIGH) == 0

def test_error_filtering(error_tracker):
    """Test error filtering."""
    # Record errors of different severities
    error_tracker.record_error(
        error_type="LowError",
        message="Low error",
        severity=ErrorSeverity.LOW,
        agent_id="test_agent"
    )
    error_tracker.record_error(
        error_type="HighError",
        message="High error",
        severity=ErrorSeverity.HIGH,
        agent_id="test_agent"
    )
    
    # Filter by severity
    high_errors = error_tracker.get_errors(severity=ErrorSeverity.HIGH)
    assert len(high_errors) == 1
    assert high_errors[0]["error_type"] == "HighError"
    
    # Filter by agent
    agent_errors = error_tracker.get_errors(agent_id="test_agent")
    assert len(agent_errors) == 2

def test_error_summary(error_tracker):
    """Test error summary generation."""
    # Record various errors
    error_tracker.record_error(
        error_type="Error1",
        message="Error 1",
        severity=ErrorSeverity.LOW,
        agent_id="agent1"
    )
    error_tracker.record_error(
        error_type="Error2",
        message="Error 2",
        severity=ErrorSeverity.HIGH,
        agent_id="agent1"
    )
    error_tracker.record_error(
        error_type="Error3",
        message="Error 3",
        severity=ErrorSeverity.MEDIUM,
        agent_id="agent2"
    )
    
    summary = error_tracker.get_error_summary()
    assert summary["total_errors"] == 3
    assert summary["by_severity"][ErrorSeverity.LOW] == 1
    assert summary["by_severity"][ErrorSeverity.MEDIUM] == 1
    assert summary["by_severity"][ErrorSeverity.HIGH] == 1
    assert summary["by_agent"]["agent1"] == 2
    assert summary["by_agent"]["agent2"] == 1

# ErrorHandler Tests
async def test_retry_strategies(error_tracker):
    """Test different retry strategies."""
    strategies = [
        (RetryStrategy.NONE, 0),
        (RetryStrategy.LINEAR, 1),
        (RetryStrategy.EXPONENTIAL, 2),
        (RetryStrategy.FIBONACCI, 1)
    ]
    
    for strategy, expected_delay in strategies:
        handler = ErrorHandler(error_tracker, retry_strategy=strategy)
        error = ValueError("Test error")
        
        start_time = asyncio.get_event_loop().time()
        await handler.handle_error(error, "test_agent", "test_operation")
        end_time = asyncio.get_event_loop().time()
        
        # Allow small timing variance
        assert abs(end_time - start_time - expected_delay) < 0.1

async def test_max_retries(error_handler):
    """Test maximum retry limit."""
    error = ValueError("Test error")
    
    # Try max_retries + 1 times
    for _ in range(error_handler.max_retries + 1):
        should_retry = await error_handler.handle_error(
            error=error,
            agent_id="test_agent",
            operation="test_operation"
        )
    
    # Should not retry after max_retries
    assert not should_retry
    assert len(error_handler.error_tracker.get_errors()) == error_handler.max_retries + 1

async def test_with_retry_failure(error_handler):
    """Test failed retry."""
    async def test_func():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError):
        await error_handler.with_retry(
            operation="test_operation",
            agent_id="test_agent",
            func=test_func
        )
    
    assert len(error_handler.error_tracker.get_errors()) == error_handler.max_retries + 1

def test_error_severity_mapping(error_handler):
    """Test error severity mapping."""
    test_cases = [
        (ValueError(), ErrorSeverity.LOW),
        (TypeError(), ErrorSeverity.LOW),
        (IOError(), ErrorSeverity.MEDIUM),
        (OSError(), ErrorSeverity.MEDIUM),
        (RuntimeError(), ErrorSeverity.HIGH),
        (NotImplementedError(), ErrorSeverity.HIGH),
        (Exception(), ErrorSeverity.CRITICAL)
    ]
    
    for error, expected_severity in test_cases:
        severity = error_handler._get_error_severity(error)
        assert severity == expected_severity

# ErrorReporter Tests
def test_generate_filtered_report(error_reporter, error_tracker):
    """Test filtered report generation."""
    # Record errors for different agents
    error_tracker.record_error(
        error_type="Error1",
        message="Error 1",
        severity=ErrorSeverity.LOW,
        agent_id="agent1"
    )
    error_tracker.record_error(
        error_type="Error2",
        message="Error 2",
        severity=ErrorSeverity.HIGH,
        agent_id="agent2"
    )
    
    # Filter by agent
    agent1_report = error_reporter.generate_report(agent_id="agent1")
    assert agent1_report["total_errors"] == 1
    assert agent1_report["by_agent"]["agent1"] == 1
    
    # Filter by severity
    high_report = error_reporter.generate_report(severity=ErrorSeverity.HIGH)
    assert high_report["total_errors"] == 1
    assert high_report["by_severity"][ErrorSeverity.HIGH] == 1

def test_save_report_custom_filename(error_reporter, error_tracker):
    """Test report saving with custom filename."""
    # Record test error
    error_tracker.record_error(
        error_type="TestError",
        message="Test error",
        severity=ErrorSeverity.MEDIUM,
        agent_id="test_agent"
    )
    
    # Generate and save report with custom filename
    report = error_reporter.generate_report()
    custom_filename = "custom_report.json"
    report_path = error_reporter.save_report(report, filename=custom_filename)
    
    # Verify file exists with custom name
    assert report_path.name == custom_filename
    assert report_path.exists()

def test_report_directory_creation(error_tracker, tmp_path):
    """Test report directory creation."""
    # Create reporter with non-existent directory
    report_dir = tmp_path / "new_reports"
    reporter = ErrorReporter(error_tracker, report_dir)
    
    # Verify directory was created
    assert report_dir.exists()
    assert report_dir.is_dir()

def test_report_statistics(error_reporter, error_tracker):
    """Test report statistics calculation."""
    # Record errors of different types
    for i in range(3):
        error_tracker.record_error(
            error_type=f"Error{i}",
            message=f"Error {i}",
            severity=ErrorSeverity.LOW,
            agent_id="agent1"
        )
    
    error_tracker.record_error(
        error_type="CriticalError",
        message="Critical error",
        severity=ErrorSeverity.CRITICAL,
        agent_id="agent2"
    )
    
    report = error_reporter.generate_report()
    
    # Verify statistics
    assert report["total_errors"] == 4
    assert report["by_severity"][ErrorSeverity.LOW] == 3
    assert report["by_severity"][ErrorSeverity.CRITICAL] == 1
    assert report["by_agent"]["agent1"] == 3
    assert report["by_agent"]["agent2"] == 1
    assert len(report["by_type"]) == 4  # 4 different error types 