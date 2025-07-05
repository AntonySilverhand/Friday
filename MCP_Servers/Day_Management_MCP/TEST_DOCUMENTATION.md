# Day Management MCP Server - Test Documentation

This document provides comprehensive information about the test suite for the Day Management MCP Server.

## Overview

The test suite provides complete coverage of the Day Management MCP Server functionality, including:

- **10 MCP Tools Testing**: All calendar and task management tools
- **OAuth2 Authentication**: Google API authentication flow
- **Timezone Handling**: Date parsing and timezone conversions
- **Smart Scheduling**: Conflict detection and free time calculation
- **Friday Integration**: AI assistant integration testing
- **Mock Testing**: Comprehensive Google API mocking
- **Error Handling**: Edge cases and error conditions
- **Performance Testing**: Large dataset handling

## Test Files

### `test_day_management_comprehensive.py`
Main comprehensive test suite with the following test classes:

- **TestDayManagementMCPServer**: Core server functionality
- **TestDayManagementServerInitialization**: Server setup and configuration
- **TestOAuth2Authentication**: Google OAuth2 authentication flow
- **TestCalendarEventManagement**: Calendar event operations
- **TestTaskManagement**: Task management operations
- **TestDayOverview**: Day overview and scheduling
- **TestTimezoneHandling**: Timezone and date parsing
- **TestSmartScheduling**: Conflict detection and free time calculation
- **TestMCPTools**: MCP tool interface testing
- **TestFridayIntegration**: Friday AI assistant integration
- **TestErrorHandling**: Error conditions and edge cases
- **TestDataConversion**: Data serialization and conversion
- **TestPerformanceAndScaling**: Performance and scaling tests

### `run_tests.py`
Test runner script with multiple execution modes:

```bash
# Run unit tests only
python run_tests.py --unit

# Run integration tests with mocked services
python run_tests.py --integration

# Run integration tests with live Google services
python run_tests.py --integration --live

# Run performance tests
python run_tests.py --performance

# Run all tests with coverage
python run_tests.py --all --coverage

# Check environment setup
python run_tests.py --check-env
```

## Test Categories

### 1. Unit Tests
Test individual components in isolation using mocks:

- Server initialization and configuration
- OAuth2 authentication flow
- Calendar event parsing and conversion
- Task parsing and conversion
- Date/timezone handling
- Data validation and error handling

### 2. Integration Tests
Test component interactions and workflows:

- Complete calendar event lifecycle (create, read, update, delete)
- Complete task lifecycle (create, read, update, complete)
- Day overview generation
- Free time calculation
- MCP tool interface functionality

### 3. Performance Tests
Test handling of large datasets and concurrent operations:

- Large event list processing
- Concurrent API calls
- Memory usage optimization
- Response time benchmarks

### 4. Authentication Tests
Test Google OAuth2 authentication scenarios:

- New credential setup
- Token refresh handling
- Invalid credential handling
- Scope validation

### 5. Friday Integration Tests
Test integration with Friday AI Assistant:

- Tool configuration validation
- MCP client interaction
- Response formatting
- Error propagation

## Test Data and Mocking

### Mock Services
The test suite uses comprehensive mocking for:

- **Google Calendar API**: All calendar operations
- **Google Tasks API**: All task operations
- **OAuth2 Credentials**: Authentication flow
- **File System**: Credentials and token storage
- **Network Requests**: API calls and responses

### Sample Data
Predefined test data includes:

- **Calendar Events**: Various event types (meetings, all-day events, recurring)
- **Tasks**: Different task states (pending, completed, overdue)
- **Tasklists**: Multiple task list configurations
- **Timezone Data**: Different timezone scenarios

## Running Tests

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional for mocked tests)
export GOOGLE_CREDENTIALS_PATH="path/to/credentials.json"
export USER_TIMEZONE="America/New_York"
export OPENAI_API_KEY="your-api-key"
```

### Quick Start
```bash
# Run all tests with coverage
python run_tests.py --all --coverage

# Run unit tests only
python run_tests.py --unit

# Check environment setup
python run_tests.py --check-env
```

### Advanced Usage
```bash
# Run specific test class
pytest test_day_management_comprehensive.py::TestCalendarEventManagement

# Run with verbose output
pytest test_day_management_comprehensive.py -v -s

# Run with coverage report
pytest test_day_management_comprehensive.py --cov=day_management_mcp_server --cov-report=html

# Run integration tests with live services (requires setup)
python run_tests.py --integration --live
```

## Coverage Goals

The test suite aims for:

- **>90% Code Coverage**: Comprehensive function and branch coverage
- **All MCP Tools**: 100% coverage of all 10 MCP tools
- **Error Paths**: Coverage of all error handling paths
- **Edge Cases**: Coverage of boundary conditions and edge cases

## Mock Strategy

### Google Calendar API Mocking
```python
@pytest.fixture
def mock_calendar_service(self):
    mock_service = Mock()
    mock_service.events.return_value = Mock()
    return mock_service
```

### Google Tasks API Mocking
```python
@pytest.fixture
def mock_tasks_service(self):
    mock_service = Mock()
    mock_service.tasks.return_value = Mock()
    mock_service.tasklists.return_value = Mock()
    return mock_service
```

### OAuth2 Credentials Mocking
```python
@pytest.fixture
def mock_credentials(self):
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.expired = False
    return mock_creds
```

## Test Fixtures

### Server Fixture
```python
@pytest.fixture
def day_server(self, mock_credentials, mock_calendar_service, mock_tasks_service):
    # Returns fully configured server with mocked services
```

### Data Fixtures
```python
@pytest.fixture
def sample_calendar_event(self):
    # Returns sample calendar event data

@pytest.fixture
def sample_task(self):
    # Returns sample task data
```

## Assertion Patterns

### Successful Operations
```python
assert result['success'] is True
assert result['event_id'] == 'expected_id'
assert 'calendar_link' in result
```

### Error Conditions
```python
assert 'error' in result
assert 'Invalid datetime format' in result['error']
```

### Data Validation
```python
assert len(events) == expected_count
assert all('event_id' in event for event in events)
assert event['is_all_day'] is False
```

## Continuous Integration

### GitHub Actions (Example)
```yaml
name: Test Day Management MCP
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --all --coverage
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Solution: Install all requirements
   pip install -r requirements.txt
   ```

2. **Import Errors**
   ```bash
   # Solution: Check Python path
   export PYTHONPATH="${PYTHONPATH}:/path/to/Friday"
   ```

3. **Authentication Errors** (Live Tests)
   ```bash
   # Solution: Set up Google OAuth2 credentials
   # Download credentials.json from Google Cloud Console
   export GOOGLE_CREDENTIALS_PATH="path/to/credentials.json"
   ```

4. **Timezone Issues**
   ```bash
   # Solution: Set valid timezone
   export USER_TIMEZONE="America/New_York"
   ```

### Debug Mode
```bash
# Run with maximum verbosity
pytest test_day_management_comprehensive.py -v -s --tb=long

# Run specific failing test
pytest test_day_management_comprehensive.py::TestClassName::test_method_name -v -s
```

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_*` for test functions
2. **Use appropriate fixtures**: Leverage existing fixtures for consistency
3. **Add docstrings**: Document what each test verifies
4. **Test both success and failure cases**: Include positive and negative tests
5. **Use descriptive assertions**: Make test failures easy to understand
6. **Update documentation**: Add new test categories to this document

## Test Results Interpretation

### Success Indicators
- All tests pass (green checkmarks)
- Coverage percentage meets targets (>90%)
- No skipped tests due to missing dependencies
- Performance tests complete within acceptable timeframes

### Failure Analysis
- **Unit test failures**: Check mocking setup and test data
- **Integration test failures**: Verify service configurations
- **Performance test failures**: Check resource constraints
- **Coverage failures**: Identify untested code paths

## Future Enhancements

Planned test improvements:

1. **Load Testing**: High-concurrency scenarios
2. **Security Testing**: Authentication and authorization edge cases
3. **Compatibility Testing**: Multiple Python versions and dependency versions
4. **Regression Testing**: Automated detection of functionality breaking changes
5. **Property-Based Testing**: Using hypothesis for generated test cases

## Reference

- [pytest Documentation](https://docs.pytest.org/)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)
- [FastMCP Documentation](https://fastmcp.readthedocs.io/)
- [Day Management MCP Server](./day_management_mcp_server.py)