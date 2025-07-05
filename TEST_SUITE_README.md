# Friday MCP Integration Test Suite

This comprehensive test suite validates Friday's integration with both Email MCP and Day Management MCP servers.

## Overview

The test suite covers 8 key areas:

1. **Tool Configuration** - Verifies Friday's MCP server configurations
2. **End-to-End Workflows** - Tests complex workflows like "Schedule meeting and send invites"
3. **Memory Integration** - Tests memory system integration with MCP tool usage
4. **Error Handling** - Tests robust error handling across MCP connections
5. **Concurrent Operations** - Tests Friday's ability to handle multiple MCP calls
6. **Cross-MCP Integration** - Tests Friday using both MCPs together
7. **Performance Benchmarks** - Tests MCP call performance and response times
8. **Memory Persistence** - Tests memory retention across conversation sessions

## Key Features

- **Comprehensive Coverage**: Tests all major integration points between Friday and MCP servers
- **Mocked External APIs**: Uses sophisticated mocking to avoid external dependencies
- **Performance Metrics**: Tracks response times, call counts, and failure rates
- **Detailed Reporting**: Generates JSON, HTML, and Markdown reports
- **Isolated Testing**: Uses temporary databases for clean test environments
- **Error Simulation**: Tests error handling with configurable failure rates

## Files

- `test_friday_mcp_integration.py` - Main test suite implementation
- `run_integration_tests.py` - Test runner with reporting capabilities
- `TEST_SUITE_README.md` - This documentation

## Usage

### Run All Tests

```bash
python run_integration_tests.py
```

### Run Specific Tests

```bash
python run_integration_tests.py --tests email_operations calendar_operations
```

### List Available Tests

```bash
python run_integration_tests.py --list-tests
```

### Verbose Output

```bash
python run_integration_tests.py --verbose
```

### Skip Report Generation

```bash
python run_integration_tests.py --no-report
```

## Test Categories

### Basic Operations
- `tool_configuration` - MCP server configuration validation
- `email_operations` - Basic email operations (get, send, search)
- `calendar_operations` - Basic calendar operations (events, tasks)

### Integration Tests
- `end_to_end` - Complete workflow testing
- `memory_integration` - Memory system integration
- `cross_mcp` - Multi-MCP coordination
- `complex_workflow` - Complex multi-step workflows

### Reliability Tests
- `error_handling` - Error handling and recovery
- `concurrent_operations` - Concurrent operation handling
- `performance` - Performance benchmarking
- `memory_persistence` - Cross-session memory persistence

## Test Reports

The test suite generates three types of reports:

1. **JSON Report** - Machine-readable test results
2. **HTML Report** - Interactive web-based report
3. **Markdown Report** - Human-readable documentation

Reports are saved in the `test_reports/` directory with timestamps.

## Mock System

The test suite uses a sophisticated mocking system that:

- Simulates realistic MCP server responses
- Tracks call history and performance metrics
- Allows configurable failure rates for error testing
- Provides realistic response times and delays
- Maintains separate mock responses for each MCP server

## Performance Benchmarks

The test suite includes performance benchmarks that verify:

- Average response times under 500ms
- Total test execution under reasonable time limits
- Proper handling of concurrent operations
- Memory efficiency during extended test runs

## Prerequisites

- Friday AI system with memory management
- Both Email MCP and Day Management MCP server code available
- Python 3.7+ with required dependencies
- SQLite for test database management

## Test Environment

The test suite creates an isolated environment with:

- Temporary SQLite database for memory testing
- Mocked MCP server responses
- Controlled test data and scenarios
- Automatic cleanup after test completion

## Extending the Tests

To add new tests:

1. Add a new test method to `FridayMCPIntegrationTester`
2. Update the test runner's available tests dictionary
3. Add appropriate mock responses if needed
4. Update documentation

## Continuous Integration

The test suite is designed for CI/CD integration:

- Returns appropriate exit codes (0 for success, 1 for failure)
- Generates machine-readable reports
- Provides detailed error information
- Supports selective test execution

## Troubleshooting

Common issues and solutions:

- **Import Errors**: Ensure all Friday modules are in the Python path
- **Database Errors**: Check write permissions for temporary files
- **Mock Failures**: Verify mock responses match expected formats
- **Performance Issues**: Check system resources during test execution

## Contributing

When contributing to the test suite:

1. Follow existing test patterns and naming conventions
2. Include both positive and negative test cases
3. Add appropriate mock responses for new scenarios
4. Update documentation and help text
5. Ensure tests are deterministic and repeatable