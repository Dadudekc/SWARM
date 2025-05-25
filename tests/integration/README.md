# Integration Tests

This directory contains integration tests for the social media management system, focusing on end-to-end workflows and platform-specific strategies.

## Test Architecture

### Core Components

- **ContentScheduler**: Manages post scheduling and optimization
- **AudienceAnalytics**: Handles engagement tracking and insights
- **Platform APIs**: Mocked external services (Twitter, Reddit)

### Test Structure

```
tests/integration/
├── README.md
├── test_twitter_workflow.py    # Twitter-specific tests
├── test_reddit_strategy.py     # Reddit-specific tests
└── test_edge_cases.py          # Cross-platform edge cases
```

## Mock Structure

### API Mocks

Each platform mock implements:
- Post creation/submission
- Metrics retrieval
- Engagement tracking
- Error simulation

Example:
```python
@pytest.fixture
def mock_twitter_api():
    mock = MagicMock()
    mock.post_tweet.return_value = {"id": "123456", "text": "Test tweet"}
    mock.get_user_metrics.return_value = {...}
    return mock
```

### Test Data

- Uses `temp_config_dir` and `temp_log_dir` fixtures
- Isolates test data from production
- Cleans up after test completion

## Test Categories

### 1. Content Scheduling
- Post creation and validation
- Timing optimization
- Queue management
- Platform-specific formatting

### 2. Analytics & Insights
- Growth tracking
- Demographics analysis
- Engagement metrics
- Report generation

### 3. Platform-Specific Features
- Twitter: Tweets, retweets, likes
- Reddit: Subreddits, upvotes, awards

### 4. Error Handling
- Network failures
- API rate limits
- Invalid content
- Authentication errors

## Adding New Tests

### 1. Platform Integration

```python
@pytest.mark.asyncio
async def test_platform_workflow(platform_strategy):
    # 1. Setup test data
    # 2. Execute workflow
    # 3. Verify results
    # 4. Clean up
```

### 2. Edge Cases

```python
@pytest.mark.asyncio
async def test_platform_edge_case(platform_strategy):
    # 1. Setup edge case scenario
    # 2. Execute with error conditions
    # 3. Verify error handling
    # 4. Validate recovery
```

## Best Practices

1. **Isolation**
   - Use fixtures for setup/teardown
   - Mock external dependencies
   - Clean up test data

2. **Coverage**
   - Test happy path
   - Test error paths
   - Test edge cases
   - Validate metrics

3. **Performance**
   - Use async/await
   - Minimize I/O
   - Cache expensive operations

4. **Maintenance**
   - Document test purpose
   - Keep mocks up to date
   - Review coverage regularly

## Expansion Points

1. **New Platforms**
   - Add platform-specific test file
   - Implement platform mock
   - Add platform fixtures

2. **New Features**
   - Add feature-specific tests
   - Update existing tests
   - Document changes

3. **Error Handling**
   - Add failure scenarios
   - Test recovery paths
   - Validate logging

## Running Tests

```bash
# Run all integration tests
pytest tests/integration/

# Run specific platform tests
pytest tests/integration/test_twitter_workflow.py
pytest tests/integration/test_reddit_strategy.py

# Run with coverage
pytest --cov=social.community tests/integration/
```

## Contributing

1. Follow test structure
2. Add appropriate fixtures
3. Document new tests
4. Update README if needed
5. Ensure cleanup 