#!/usr/bin/env python3
"""
Stress Test Runner for MCP Servers
Provides a command-line interface to run specific stress tests
"""

import asyncio
import argparse
import sys
from datetime import datetime
from test_mcp_stress_performance import (
    MCPStressTester, 
    LoadTestConfig, 
    run_comprehensive_stress_tests,
    run_locust_load_test
)

def main():
    parser = argparse.ArgumentParser(description='Run stress tests for MCP servers')
    parser.add_argument('--test-type', choices=[
        'all', 'email', 'day', 'oauth', 'rate-limit', 'memory', 
        'connections', 'tools', 'errors', 'locust'
    ], default='all', help='Type of test to run')
    
    parser.add_argument('--concurrent-users', type=int, default=10,
                        help='Number of concurrent users (default: 10)')
    parser.add_argument('--operations-per-user', type=int, default=50,
                        help='Operations per user (default: 50)')
    parser.add_argument('--duration', type=int, default=300,
                        help='Test duration in seconds (default: 300)')
    parser.add_argument('--email-port', type=int, default=5002,
                        help='Email MCP server port (default: 5002)')
    parser.add_argument('--day-port', type=int, default=5003,
                        help='Day Management MCP server port (default: 5003)')
    parser.add_argument('--output-file', type=str, default=None,
                        help='Output file for results (default: auto-generated)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test configuration
    config = LoadTestConfig(
        concurrent_users=args.concurrent_users,
        operations_per_user=args.operations_per_user,
        test_duration_seconds=args.duration
    )
    
    # Initialize tester
    tester = MCPStressTester(args.email_port, args.day_port)
    
    print(f"Starting MCP stress tests at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test type: {args.test_type}")
    print(f"Configuration: {args.concurrent_users} users, {args.operations_per_user} ops/user, {args.duration}s duration")
    print("-" * 80)
    
    if args.test_type == 'all':
        # Run comprehensive tests
        results = asyncio.run(run_comprehensive_stress_tests())
        print("All tests completed successfully!")
        
    elif args.test_type == 'email':
        # Run only email MCP tests
        results = asyncio.run(run_email_only_tests(tester, config))
        
    elif args.test_type == 'day':
        # Run only day management MCP tests
        results = asyncio.run(run_day_only_tests(tester, config))
        
    elif args.test_type == 'oauth':
        # Run OAuth token refresh tests
        results = asyncio.run(run_oauth_tests(tester))
        
    elif args.test_type == 'rate-limit':
        # Run rate limiting tests
        results = asyncio.run(run_rate_limit_tests(tester))
        
    elif args.test_type == 'memory':
        # Run memory leak tests
        results = asyncio.run(run_memory_tests(tester))
        
    elif args.test_type == 'connections':
        # Run concurrent connections tests
        results = asyncio.run(run_connection_tests(tester))
        
    elif args.test_type == 'tools':
        # Run tool benchmarks
        results = asyncio.run(run_tool_benchmarks(tester))
        
    elif args.test_type == 'errors':
        # Run error recovery tests
        results = asyncio.run(run_error_tests(tester))
        
    elif args.test_type == 'locust':
        # Run Locust load test
        print("Running Locust load test...")
        results = run_locust_load_test(
            host=f"http://127.0.0.1:{args.email_port}",
            users=args.concurrent_users,
            spawn_rate=max(1, args.concurrent_users // 10),
            duration=args.duration
        )
        print("Locust load test completed!")
        return
    
    # Generate and save report
    if results:
        report = tester.generate_performance_report(results)
        
        # Save results
        if args.output_file:
            output_file = args.output_file
        else:
            output_file = f"stress_test_results_{args.test_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"\nResults saved to: {output_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        print(report.split("RECOMMENDATIONS:")[0])  # Print everything before recommendations
        print("="*80)

async def run_email_only_tests(tester, config):
    """Run email MCP tests only"""
    print("Running Email MCP stress tests...")
    results = {}
    
    # Email stress test
    email_results = await tester.test_email_mcp_stress(config)
    results['email_stress_test'] = email_results
    
    # Email tool benchmarks
    email_tools = ['get_recent_emails', 'search_emails', 'send_email', 'read_email']
    for tool in email_tools:
        print(f"Benchmarking {tool}...")
        metrics = await tester._benchmark_tool(tester.email_mcp_base_url, tool, 'email')
        results[f'email_{tool}'] = metrics
    
    return results

async def run_day_only_tests(tester, config):
    """Run day management MCP tests only"""
    print("Running Day Management MCP stress tests...")
    results = {}
    
    # Day management stress test
    day_results = await tester.test_day_management_mcp_stress(config)
    results['day_stress_test'] = day_results
    
    # Day management tool benchmarks
    day_tools = ['get_calendar_events', 'get_tasks', 'create_calendar_event', 'create_task']
    for tool in day_tools:
        print(f"Benchmarking {tool}...")
        metrics = await tester._benchmark_tool(tester.day_mcp_base_url, tool, 'day')
        results[f'day_{tool}'] = metrics
    
    return results

async def run_oauth_tests(tester):
    """Run OAuth token refresh tests only"""
    print("Running OAuth token refresh tests...")
    results = {}
    
    oauth_results = await tester.test_oauth_token_refresh_under_load()
    results['oauth_test'] = oauth_results
    
    return results

async def run_rate_limit_tests(tester):
    """Run rate limiting tests only"""
    print("Running rate limiting tests...")
    results = {}
    
    rate_results = await tester.test_rate_limiting_and_retry_logic()
    results['rate_limiting_test'] = rate_results
    
    return results

async def run_memory_tests(tester):
    """Run memory leak tests only"""
    print("Running memory leak tests...")
    results = {}
    
    memory_results = await tester.test_memory_leaks_and_resource_management()
    results['memory_test'] = memory_results
    
    return results

async def run_connection_tests(tester):
    """Run concurrent connections tests only"""
    print("Running concurrent connections tests...")
    results = {}
    
    conn_results = await tester.test_concurrent_connections(100)
    results['concurrent_connections_test'] = conn_results
    
    return results

async def run_tool_benchmarks(tester):
    """Run tool benchmarks only"""
    print("Running tool benchmarks...")
    results = {}
    
    benchmark_results = await tester.benchmark_all_mcp_tools()
    results['tool_benchmarks'] = benchmark_results
    
    return results

async def run_error_tests(tester):
    """Run error recovery tests only"""
    print("Running error recovery tests...")
    results = {}
    
    error_results = await tester.test_error_recovery_and_graceful_degradation()
    results['error_recovery_test'] = error_results
    
    return results

if __name__ == "__main__":
    main()