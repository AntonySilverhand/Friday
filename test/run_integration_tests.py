#!/usr/bin/env python3
"""
Integration Test Runner for Friday MCP Integration Tests
This script provides a comprehensive test runner with detailed reporting
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from test_friday_mcp_integration import FridayMCPIntegrationTester
except ImportError as e:
    print(f"❌ Failed to import test suite: {e}")
    sys.exit(1)

class TestRunner:
    """Test runner with comprehensive reporting capabilities"""
    
    def __init__(self):
        self.output_dir = Path("test_reports")
        self.output_dir.mkdir(exist_ok=True)
        
    def run_tests(self, specific_tests=None, verbose=False, save_report=True):
        """Run tests with specified options"""
        print("🚀 Friday MCP Integration Test Runner")
        print("=" * 60)
        
        # Initialize tester
        tester = FridayMCPIntegrationTester()
        
        try:
            if specific_tests:
                # Run specific tests
                results = self._run_specific_tests(tester, specific_tests, verbose)
            else:
                # Run all tests
                results = tester.run_all_tests()
            
            # Generate report
            if save_report:
                self._generate_report(results, verbose)
            
            return results
            
        except Exception as e:
            print(f"❌ Test execution failed: {e}")
            return None
        finally:
            tester.teardown_test_environment()
    
    def _run_specific_tests(self, tester, test_names, verbose):
        """Run specific tests by name"""
        available_tests = {
            "tool_configuration": ("Tool Configuration", tester.test_friday_tool_configuration),
            "email_operations": ("Basic Email Operations", tester.test_basic_email_operations),
            "calendar_operations": ("Basic Calendar Operations", tester.test_basic_calendar_operations),
            "end_to_end": ("End-to-End Workflow", tester.test_end_to_end_workflow),
            "memory_integration": ("Memory Integration", tester.test_memory_integration),
            "error_handling": ("Error Handling", tester.test_error_handling),
            "concurrent_operations": ("Concurrent Operations", tester.test_concurrent_operations),
            "cross_mcp": ("Cross-MCP Integration", tester.test_cross_mcp_integration),
            "performance": ("Performance Benchmarks", tester.test_performance_benchmarks),
            "memory_persistence": ("Memory Persistence", tester.test_memory_persistence),
            "complex_workflow": ("Complex Workflow Memory", tester.test_complex_workflow_memory)
        }
        
        results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success_rate': 0,
            'total_time': 0,
            'test_results': []
        }
        
        start_time = time.time()
        
        for test_name in test_names:
            if test_name in available_tests:
                test_display_name, test_method = available_tests[test_name]
                result = tester.run_test(test_display_name, test_method)
                results['test_results'].append(result)
                
                if result.passed:
                    results['passed_tests'] += 1
                else:
                    results['failed_tests'] += 1
                    
                results['total_tests'] += 1
            else:
                print(f"⚠️  Unknown test: {test_name}")
        
        results['total_time'] = time.time() - start_time
        results['success_rate'] = (results['passed_tests'] / results['total_tests'] * 100) if results['total_tests'] > 0 else 0
        results['performance_metrics'] = tester.mock_manager.get_performance_metrics()
        
        return results
    
    def _generate_report(self, results, verbose):
        """Generate comprehensive test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate JSON report
        json_report_path = self.output_dir / f"integration_test_report_{timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(self._serialize_results(results), f, indent=2)
        
        # Generate HTML report
        html_report_path = self.output_dir / f"integration_test_report_{timestamp}.html"
        self._generate_html_report(results, html_report_path)
        
        # Generate markdown report
        md_report_path = self.output_dir / f"integration_test_report_{timestamp}.md"
        self._generate_markdown_report(results, md_report_path)
        
        print(f"\n📄 Reports generated:")
        print(f"   JSON: {json_report_path}")
        print(f"   HTML: {html_report_path}")
        print(f"   Markdown: {md_report_path}")
        
        # Print summary to console
        self._print_summary(results, verbose)
    
    def _serialize_results(self, results):
        """Serialize test results for JSON output"""
        serialized = results.copy()
        
        # Convert test results to serializable format
        serialized['test_results'] = []
        for result in results['test_results']:
            serialized['test_results'].append({
                'name': result.name,
                'passed': result.passed,
                'execution_time': result.execution_time,
                'error': result.error,
                'details': result.details
            })
        
        # Convert performance metrics
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            serialized['performance_metrics'] = {
                'total_calls': metrics.total_calls,
                'avg_response_time': metrics.avg_response_time,
                'min_response_time': metrics.min_response_time,
                'max_response_time': metrics.max_response_time,
                'failed_calls': metrics.failed_calls,
                'concurrent_calls': metrics.concurrent_calls
            }
        
        serialized['timestamp'] = datetime.now().isoformat()
        return serialized
    
    def _generate_html_report(self, results, output_path):
        """Generate HTML test report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Friday MCP Integration Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .passed {{ background-color: #d4edda; color: #155724; }}
        .failed {{ background-color: #f8d7da; color: #721c24; }}
        .test-result {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .test-details {{ margin-top: 10px; padding: 10px; background-color: #f9f9f9; border-radius: 3px; }}
        pre {{ background-color: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Friday MCP Integration Test Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Tests</h3>
            <p>{results['total_tests']}</p>
        </div>
        <div class="metric passed">
            <h3>Passed</h3>
            <p>{results['passed_tests']}</p>
        </div>
        <div class="metric failed">
            <h3>Failed</h3>
            <p>{results['failed_tests']}</p>
        </div>
        <div class="metric">
            <h3>Success Rate</h3>
            <p>{results['success_rate']:.1f}%</p>
        </div>
        <div class="metric">
            <h3>Total Time</h3>
            <p>{results['total_time']:.2f}s</p>
        </div>
    </div>
    
    <h2>Test Results</h2>
"""
        
        for result in results['test_results']:
            status_class = "passed" if result.passed else "failed"
            status_icon = "✅" if result.passed else "❌"
            
            html_content += f"""
    <div class="test-result {status_class}">
        <h3>{status_icon} {result.name}</h3>
        <p>Execution Time: {result.execution_time:.2f}s</p>
        {f'<p>Error: {result.error}</p>' if result.error else ''}
        {f'<div class="test-details"><pre>{json.dumps(result.details, indent=2)}</pre></div>' if result.details else ''}
    </div>
"""
        
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            html_content += f"""
    <h2>Performance Metrics</h2>
    <div class="summary">
        <div class="metric">
            <h3>Total Calls</h3>
            <p>{metrics.total_calls}</p>
        </div>
        <div class="metric">
            <h3>Avg Response Time</h3>
            <p>{metrics.avg_response_time:.3f}s</p>
        </div>
        <div class="metric">
            <h3>Min Response Time</h3>
            <p>{metrics.min_response_time:.3f}s</p>
        </div>
        <div class="metric">
            <h3>Max Response Time</h3>
            <p>{metrics.max_response_time:.3f}s</p>
        </div>
        <div class="metric">
            <h3>Failed Calls</h3>
            <p>{metrics.failed_calls}</p>
        </div>
    </div>
"""
        
        html_content += """
</body>
</html>
"""
        
        with open(output_path, 'w') as f:
            f.write(html_content)
    
    def _generate_markdown_report(self, results, output_path):
        """Generate Markdown test report"""
        md_content = f"""# Friday MCP Integration Test Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Tests | {results['total_tests']} |
| Passed | {results['passed_tests']} |
| Failed | {results['failed_tests']} |
| Success Rate | {results['success_rate']:.1f}% |
| Total Time | {results['total_time']:.2f}s |

## Test Results

"""
        
        for result in results['test_results']:
            status_icon = "✅" if result.passed else "❌"
            md_content += f"### {status_icon} {result.name}\n\n"
            md_content += f"- **Execution Time:** {result.execution_time:.2f}s\n"
            
            if result.error:
                md_content += f"- **Error:** {result.error}\n"
            
            if result.details:
                md_content += f"- **Details:**\n```json\n{json.dumps(result.details, indent=2)}\n```\n"
            
            md_content += "\n"
        
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            md_content += f"""## Performance Metrics

| Metric | Value |
|--------|-------|
| Total Calls | {metrics.total_calls} |
| Average Response Time | {metrics.avg_response_time:.3f}s |
| Min Response Time | {metrics.min_response_time:.3f}s |
| Max Response Time | {metrics.max_response_time:.3f}s |
| Failed Calls | {metrics.failed_calls} |
"""
        
        with open(output_path, 'w') as f:
            f.write(md_content)
    
    def _print_summary(self, results, verbose):
        """Print summary to console"""
        print(f"\n📊 DETAILED SUMMARY")
        print("=" * 60)
        
        if verbose:
            for result in results['test_results']:
                status_icon = "✅" if result.passed else "❌"
                print(f"\n{status_icon} {result.name}")
                print(f"   Time: {result.execution_time:.2f}s")
                
                if result.error:
                    print(f"   Error: {result.error}")
                
                if result.details and verbose:
                    print(f"   Details: {json.dumps(result.details, indent=2)}")
        
        print(f"\n🎯 FINAL RESULTS")
        print("=" * 60)
        print(f"Tests Run: {results['total_tests']}")
        print(f"Passed: {results['passed_tests']}")
        print(f"Failed: {results['failed_tests']}")
        print(f"Success Rate: {results['success_rate']:.1f}%")
        print(f"Total Execution Time: {results['total_time']:.2f}s")
        
        if 'performance_metrics' in results:
            metrics = results['performance_metrics']
            print(f"\nPerformance Summary:")
            print(f"  MCP Calls: {metrics.total_calls}")
            print(f"  Avg Response: {metrics.avg_response_time:.3f}s")
            print(f"  Failed Calls: {metrics.failed_calls}")

def main():
    """Main function with command-line interface"""
    parser = argparse.ArgumentParser(description="Friday MCP Integration Test Runner")
    parser.add_argument("--tests", nargs="*", help="Specific tests to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--no-report", action="store_true", help="Don't generate reports")
    parser.add_argument("--list-tests", action="store_true", help="List available tests")
    
    args = parser.parse_args()
    
    if args.list_tests:
        print("Available tests:")
        tests = [
            "tool_configuration - Test Friday's tool configuration",
            "email_operations - Test basic email operations",
            "calendar_operations - Test basic calendar operations", 
            "end_to_end - Test end-to-end workflow",
            "memory_integration - Test memory integration",
            "error_handling - Test error handling",
            "concurrent_operations - Test concurrent operations",
            "cross_mcp - Test cross-MCP integration",
            "performance - Test performance benchmarks",
            "memory_persistence - Test memory persistence",
            "complex_workflow - Test complex workflow memory"
        ]
        for test in tests:
            print(f"  {test}")
        return
    
    runner = TestRunner()
    results = runner.run_tests(
        specific_tests=args.tests,
        verbose=args.verbose,
        save_report=not args.no_report
    )
    
    if results is None:
        sys.exit(1)
    
    # Exit with error code if any tests failed
    if results['failed_tests'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()