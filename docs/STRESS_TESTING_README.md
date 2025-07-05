# MCP Servers Stress and Performance Testing Suite

This comprehensive testing suite provides stress testing, performance benchmarking, and load testing capabilities for both the Email MCP and Day Management MCP servers.

## Features

### 🔥 Stress Testing
- **High-volume operations**: Tests both servers with concurrent users and batch operations
- **Concurrent connections**: Tests up to 100+ simultaneous connections
- **Memory usage monitoring**: Tracks memory consumption and detects potential leaks
- **Resource management**: Monitors CPU, memory, network, and disk I/O

### 📊 Performance Benchmarking
- **Individual tool benchmarks**: Tests each MCP tool separately
- **Response time analysis**: P95, P99, average, min, max response times
- **Throughput measurement**: Operations per second under load
- **Error rate tracking**: Success/failure rates under stress

### 🔄 Reliability Testing
- **OAuth token refresh**: Tests token refresh behavior under load
- **Rate limiting**: Tests API rate limiting and retry logic
- **Error recovery**: Tests graceful degradation and error handling
- **Connection resilience**: Tests connection pooling and recovery

### 📈 Load Testing
- **Locust integration**: Web-based load testing with real-time metrics
- **Configurable scenarios**: Customizable user count, operations, and duration
- **Real-time monitoring**: Live performance metrics during tests

## Installation

1. Install the stress testing dependencies:
```bash
pip install -r stress_test_requirements.txt
```

2. Ensure both MCP servers are running:
```bash
# Terminal 1 - Email MCP Server
cd MCP_Servers/Email_MCP
python email_mcp_server.py

# Terminal 2 - Day Management MCP Server  
cd MCP_Servers/Day_Management_MCP
python day_management_mcp_server.py
```

## Usage

### Quick Start - Run All Tests
```bash
python run_stress_tests.py --test-type all
```

### Specific Test Types

#### Email MCP Only
```bash
python run_stress_tests.py --test-type email --concurrent-users 20 --duration 180
```

#### Day Management MCP Only
```bash
python run_stress_tests.py --test-type day --concurrent-users 15 --duration 120
```

#### OAuth Token Refresh Testing
```bash
python run_stress_tests.py --test-type oauth
```

#### Rate Limiting Tests
```bash
python run_stress_tests.py --test-type rate-limit
```

#### Memory Leak Testing
```bash
python run_stress_tests.py --test-type memory
```

#### Concurrent Connections Testing
```bash
python run_stress_tests.py --test-type connections
```

#### Individual Tool Benchmarks
```bash
python run_stress_tests.py --test-type tools
```

#### Error Recovery Testing
```bash
python run_stress_tests.py --test-type errors
```

#### Locust Load Testing
```bash
python run_stress_tests.py --test-type locust --concurrent-users 50 --duration 300
```

### Advanced Configuration

#### High-Load Testing
```bash
python run_stress_tests.py \
  --test-type all \
  --concurrent-users 100 \
  --operations-per-user 200 \
  --duration 600 \
  --verbose
```

#### Custom Ports
```bash
python run_stress_tests.py \
  --test-type all \
  --email-port 5002 \
  --day-port 5003
```

#### Custom Output File
```bash
python run_stress_tests.py \
  --test-type all \
  --output-file my_stress_test_results.txt
```

## Test Scenarios

### 1. Email MCP Stress Tests
- **Batch email operations**: Send/read/search multiple emails concurrently
- **High-volume email retrieval**: Get recent emails with large limits
- **Email search performance**: Search across large email datasets
- **Label management**: Test Gmail label operations under load
- **Attachment handling**: Test email attachment processing

### 2. Day Management MCP Stress Tests
- **Calendar event operations**: Create/read/update/delete events in bulk
- **Task management**: Bulk task operations across multiple task lists
- **Day overview generation**: Generate comprehensive day overviews
- **Concurrent calendar access**: Multiple users accessing calendar simultaneously
- **Time zone handling**: Test operations across different time zones

### 3. OAuth Token Refresh Tests
- **Expired token scenarios**: Simulate token expiration during operations
- **Concurrent refresh requests**: Multiple simultaneous token refreshes
- **Network delay simulation**: Test refresh with network latency
- **Refresh failure recovery**: Test retry logic for failed refreshes

### 4. Rate Limiting Tests
- **Burst request testing**: Send burst of requests to test rate limits
- **Sustained load testing**: Test sustained request rates
- **Backoff strategy testing**: Verify exponential backoff implementation
- **Rate limit recovery**: Test recovery after rate limit periods

### 5. Memory and Resource Tests
- **Memory leak detection**: Monitor memory usage during long-running tests
- **Resource cleanup**: Verify proper resource cleanup after operations
- **Connection pool management**: Test connection pool behavior
- **Garbage collection impact**: Monitor GC behavior under load

### 6. Error Recovery Tests
- **Network timeout simulation**: Test timeout handling and retries
- **Server error simulation**: Test 500 error handling
- **Authentication failure recovery**: Test auth failure scenarios
- **Partial service failure**: Test graceful degradation

## Output and Reports

### Performance Metrics
Each test generates detailed performance metrics including:
- **Response Times**: Average, P95, P99, min, max
- **Throughput**: Operations per second
- **Error Rates**: Success/failure percentages
- **Resource Usage**: CPU, memory, network I/O
- **Concurrency**: Connection pool utilization

### Generated Files
- **Results JSON**: Machine-readable test results
- **Performance Report**: Human-readable comprehensive report
- **Test Logs**: Detailed execution logs
- **Memory Profiles**: Memory usage analysis

### Sample Report Structure
```
================================================================================
MCP SERVERS STRESS AND PERFORMANCE TEST REPORT
================================================================================
Generated: 2024-01-15 14:30:00

EMAIL MCP STRESS TEST RESULTS:
----------------------------------------
Total Operations: 2000
Successful Operations: 1950
Failed Operations: 50
Success Rate: 97.50%
Average Response Time: 145.23 ms
P95 Response Time: 280.15 ms
P99 Response Time: 450.78 ms
Throughput: 13.45 ops/sec
Memory Usage: 125.67 MB
CPU Usage: 45.23%

DAY MANAGEMENT MCP STRESS TEST RESULTS:
----------------------------------------
[Similar metrics for Day Management MCP]

RECOMMENDATIONS:
----------------------------------------
• Email MCP response times are acceptable for production use
• Consider implementing connection pooling optimization
• Memory usage is within acceptable limits
• Set up monitoring for P99 response times in production
```

## Monitoring and Observability

### Real-Time Monitoring
The test suite includes real-time monitoring of:
- CPU usage percentage
- Memory consumption (RSS, virtual)
- Network I/O (bytes sent/received)
- Disk I/O (read/write operations)
- Connection pool status

### Performance Thresholds
Default performance thresholds for recommendations:
- **Error Rate**: > 5% triggers recommendations
- **Response Time**: > 1000ms triggers optimization suggestions  
- **Memory Growth**: > 50MB triggers leak investigation
- **CPU Usage**: > 80% triggers scaling recommendations

## Troubleshooting

### Common Issues

#### 1. Connection Refused Errors
```bash
# Ensure MCP servers are running
ps aux | grep mcp
netstat -tlnp | grep -E "(5002|5003)"
```

#### 2. High Memory Usage
```bash
# Monitor memory during tests
watch -n 1 'ps aux | grep python | head -10'
```

#### 3. OAuth Authentication Errors
```bash
# Check credentials files exist
ls -la MCP_Servers/*/credentials.json
ls -la MCP_Servers/*/token.pickle
```

#### 4. Rate Limiting from Google APIs
```bash
# Check Google API quotas in console
# Implement exponential backoff
# Consider API key rotation
```

### Performance Tuning

#### System-Level Optimizations
```bash
# Increase file descriptor limits
ulimit -n 65536

# Optimize network settings
echo 'net.core.somaxconn = 65536' >> /etc/sysctl.conf
sysctl -p
```

#### Application-Level Optimizations
- Connection pooling configuration
- Async operation batching
- Memory pool management
- Request/response caching

## CI/CD Integration

### GitHub Actions Example
```yaml
name: MCP Stress Tests
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  stress-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r stress_test_requirements.txt
      - name: Run stress tests
        run: python run_stress_tests.py --test-type all --duration 180
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: stress-test-results
          path: '*_results_*.txt'
```

### Docker Integration
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY stress_test_requirements.txt .
RUN pip install -r stress_test_requirements.txt

COPY . .
CMD ["python", "run_stress_tests.py", "--test-type", "all"]
```

## Best Practices

### Production Deployment
1. **Gradual Load Increase**: Start with low load and gradually increase
2. **Circuit Breakers**: Implement circuit breakers for external APIs
3. **Health Checks**: Regular health check endpoints
4. **Monitoring**: Comprehensive monitoring and alerting
5. **Rate Limiting**: Implement proper rate limiting strategies

### Testing Strategy
1. **Regular Testing**: Run stress tests on schedule
2. **Performance Baselines**: Establish performance baselines
3. **Regression Testing**: Test after each deployment
4. **Capacity Planning**: Use results for capacity planning
5. **Incident Response**: Use for incident investigation

## Contributing

To add new test scenarios:

1. **Extend MCPStressTester class**: Add new test methods
2. **Update test runner**: Add new test types to CLI
3. **Add documentation**: Update this README
4. **Performance thresholds**: Update recommendation logic

### Example New Test Method
```python
async def test_new_scenario(self) -> Dict[str, Any]:
    """Test new scenario"""
    # Implementation here
    return results
```

## Support

For issues and questions:
- Check the troubleshooting section above
- Review log files generated during tests
- Monitor system resources during test execution
- Verify MCP server configurations and credentials