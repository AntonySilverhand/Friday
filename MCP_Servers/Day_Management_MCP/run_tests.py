#!/usr/bin/env python3
"""
Test Runner for Day Management MCP Server

This script provides convenient commands for running different types of tests:
- Unit tests with mocking
- Integration tests with live services (optional)
- Performance tests
- Coverage reports

Usage:
    python run_tests.py [options]

Options:
    --unit          Run unit tests only (default)
    --integration   Run integration tests with mocked services
    --live          Run integration tests with live Google services
    --performance   Run performance tests
    --coverage      Generate coverage report
    --all           Run all tests
    --verbose       Verbose output
    --help          Show this help message
"""

import os
import sys
import subprocess
import argparse
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_command(cmd, check=True):
    """Run a shell command and return the result"""
    print(f"🏃 Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    return result

def check_dependencies():
    """Check if required test dependencies are installed"""
    print("🔍 Checking test dependencies...")
    
    required_packages = [
        'pytest',
        'pytest-asyncio',
        'pytest-mock',
        'pytest-cov',
        'google-api-python-client',
        'fastmcp'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ All required dependencies are installed")
    return True

def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests with mocking"""
    print("\n🧪 Running unit tests...")
    
    cmd = "pytest test_day_management_comprehensive.py -m 'not integration'"
    
    if verbose:
        cmd += " -v -s"
    
    if coverage:
        cmd += " --cov=day_management_mcp_server --cov-report=html --cov-report=term-missing"
    
    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_integration_tests(use_live_services=False, verbose=False):
    """Run integration tests"""
    print(f"\n🔄 Running integration tests {'with live services' if use_live_services else 'with mocked services'}...")
    
    cmd = "pytest test_day_management_comprehensive.py -m integration"
    
    if verbose:
        cmd += " -v -s"
    
    if use_live_services:
        cmd += " --live"
        print("⚠️  Note: Live service tests require Google OAuth2 credentials")
    
    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_performance_tests(verbose=False):
    """Run performance tests"""
    print("\n⚡ Running performance tests...")
    
    cmd = "pytest test_day_management_comprehensive.py::TestPerformanceAndScaling"
    
    if verbose:
        cmd += " -v -s"
    
    result = run_command(cmd, check=False)
    return result.returncode == 0

def run_all_tests(verbose=False, coverage=False):
    """Run all tests"""
    print("\n🚀 Running all tests...")
    
    cmd = "pytest test_day_management_comprehensive.py"
    
    if verbose:
        cmd += " -v -s"
    
    if coverage:
        cmd += " --cov=day_management_mcp_server --cov-report=html --cov-report=term-missing"
    
    result = run_command(cmd, check=False)
    return result.returncode == 0

def generate_coverage_report():
    """Generate detailed coverage report"""
    print("\n📊 Generating coverage report...")
    
    # Run tests with coverage
    run_command("pytest test_day_management_comprehensive.py --cov=day_management_mcp_server --cov-report=html --cov-report=xml --cov-report=term-missing")
    
    print("\n📋 Coverage report generated:")
    print("  - HTML report: htmlcov/index.html")
    print("  - XML report: coverage.xml")
    print("  - Terminal report shown above")

def run_basic_integration_check():
    """Run basic integration check from existing test"""
    print("\n🔍 Running basic integration check...")
    
    try:
        # Run the existing integration test
        from test_day_management_integration import DayManagementIntegrationTester
        
        tester = DayManagementIntegrationTester()
        success = tester.run_all_tests()
        
        if success:
            print("✅ Basic integration check passed")
            return True
        else:
            print("❌ Basic integration check failed")
            return False
    except Exception as e:
        print(f"❌ Integration check failed: {e}")
        return False

def check_environment():
    """Check environment setup"""
    print("\n🔧 Checking environment setup...")
    
    checks = {
        "GOOGLE_CREDENTIALS_PATH": os.getenv("GOOGLE_CREDENTIALS_PATH"),
        "GOOGLE_TOKEN_PATH": os.getenv("GOOGLE_TOKEN_PATH"),
        "USER_TIMEZONE": os.getenv("USER_TIMEZONE"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")
    }
    
    warnings = []
    
    for var_name, value in checks.items():
        if value:
            print(f"✅ {var_name} is set")
        else:
            print(f"⚠️  {var_name} is not set")
            if var_name in ["GOOGLE_CREDENTIALS_PATH", "OPENAI_API_KEY"]:
                warnings.append(var_name)
    
    # Check credentials file
    creds_path = checks.get("GOOGLE_CREDENTIALS_PATH", "day_credentials.json")
    if os.path.exists(creds_path):
        print(f"✅ Google credentials file found at {creds_path}")
    else:
        print(f"⚠️  Google credentials file not found at {creds_path}")
        warnings.append("CREDENTIALS_FILE")
    
    if warnings:
        print(f"\n⚠️  Warnings: {len(warnings)} configuration issues found")
        print("Some tests may be limited without proper configuration")
    else:
        print("\n✅ Environment setup looks good")
    
    return len(warnings) == 0

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="Test Runner for Day Management MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_tests.py --unit                    # Run unit tests only
    python run_tests.py --integration             # Run integration tests (mocked)
    python run_tests.py --integration --live      # Run integration tests (live services)
    python run_tests.py --all --coverage          # Run all tests with coverage
    python run_tests.py --performance             # Run performance tests
    python run_tests.py --check-env               # Check environment setup
        """
    )
    
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--live', action='store_true', help='Use live Google services for integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--check-env', action='store_true', help='Check environment setup')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies')
    parser.add_argument('--basic-check', action='store_true', help='Run basic integration check')
    
    args = parser.parse_args()
    
    # If no specific test type is specified, run unit tests
    if not any([args.unit, args.integration, args.performance, args.all, 
               args.check_env, args.check_deps, args.basic_check]):
        args.unit = True
    
    print("🏁 Day Management MCP Server Test Runner")
    print("=" * 50)
    
    success = True
    
    # Check dependencies first
    if args.check_deps or args.all:
        if not check_dependencies():
            success = False
    
    # Check environment
    if args.check_env or args.all:
        if not check_environment():
            print("⚠️  Environment check found issues (tests may still work)")
    
    # Run basic integration check
    if args.basic_check:
        if not run_basic_integration_check():
            success = False
    
    # Run specific test types
    if args.unit:
        if not run_unit_tests(verbose=args.verbose, coverage=args.coverage):
            success = False
    
    if args.integration:
        if not run_integration_tests(use_live_services=args.live, verbose=args.verbose):
            success = False
    
    if args.performance:
        if not run_performance_tests(verbose=args.verbose):
            success = False
    
    if args.all:
        if not run_all_tests(verbose=args.verbose, coverage=args.coverage):
            success = False
    
    if args.coverage and not args.all:
        generate_coverage_report()
    
    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed. Check the output above for details.")
    
    print("\n📋 Test Summary:")
    print("- Unit tests: Test individual components with mocking")
    print("- Integration tests: Test component interactions")
    print("- Performance tests: Test handling of large datasets")
    print("- Coverage report: Measure test coverage")
    print("- Environment check: Verify configuration")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()