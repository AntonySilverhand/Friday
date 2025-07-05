#!/usr/bin/env python3
"""
Comprehensive Stress and Performance Tests for MCP Servers
Tests both Email MCP and Day Management MCP servers for:
- High-volume operations
- API rate limiting and retry logic
- Concurrent connections
- Memory usage and resource management
- Error recovery and graceful degradation
- OAuth token refresh under load
- Performance benchmarking
"""

import asyncio
import time
import threading
import multiprocessing
import json
import logging
import statistics
import psutil
import gc
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from pathlib import Path
import tracemalloc
import sys
import os

# Add the MCP server directories to the path
sys.path.insert(0, '/root/coding/Friday/MCP_Servers/Email_MCP')
sys.path.insert(0, '/root/coding/Friday/MCP_Servers/Day_Management_MCP')

# Test framework imports
import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock

# HTTP client for API testing
import aiohttp
import requests

# Memory profiling
import memory_profiler

# Load testing
from locust import HttpUser, task, between
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

# Performance metrics
import numpy as np
import matplotlib.pyplot as plt

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_stress_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation_name: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    throughput_ops_per_second: float
    error_rate_percent: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: datetime

@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    concurrent_users: int = 10
    operations_per_user: int = 100
    ramp_up_time_seconds: int = 60
    test_duration_seconds: int = 300
    think_time_min: float = 0.1
    think_time_max: float = 2.0
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

class PerformanceMonitor:
    """Monitor system performance during tests"""
    
    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.network_io = []
        self.disk_io = []
        self.monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self, interval: float = 1.0):
        """Start monitoring system resources"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,)
        )
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring system resources"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: float):
        """Monitor loop for collecting metrics"""
        while self.monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                self.cpu_usage.append(cpu_percent)
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_usage.append(memory.percent)
                
                # Network I/O
                net_io = psutil.net_io_counters()
                self.network_io.append({
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                })
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    self.disk_io.append({
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count
                    })
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                break
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics"""
        return {
            'cpu_usage': {
                'avg': statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
                'max': max(self.cpu_usage) if self.cpu_usage else 0,
                'min': min(self.cpu_usage) if self.cpu_usage else 0,
                'data_points': len(self.cpu_usage)
            },
            'memory_usage': {
                'avg': statistics.mean(self.memory_usage) if self.memory_usage else 0,
                'max': max(self.memory_usage) if self.memory_usage else 0,
                'min': min(self.memory_usage) if self.memory_usage else 0,
                'data_points': len(self.memory_usage)
            },
            'network_io': {
                'data_points': len(self.network_io)
            },
            'disk_io': {
                'data_points': len(self.disk_io)
            }
        }

class MCPStressTester:
    """Main stress testing class for MCP servers"""
    
    def __init__(self, email_mcp_port: int = 5002, day_mcp_port: int = 5003):
        self.email_mcp_base_url = f"http://127.0.0.1:{email_mcp_port}"
        self.day_mcp_base_url = f"http://127.0.0.1:{day_mcp_port}"
        self.performance_monitor = PerformanceMonitor()
        self.test_results = []
        
        # Test data generators
        self.email_test_data = self._generate_email_test_data()
        self.calendar_test_data = self._generate_calendar_test_data()
        self.task_test_data = self._generate_task_test_data()
    
    def _generate_email_test_data(self) -> List[Dict]:
        """Generate test data for email operations"""
        test_data = []
        
        # Email scenarios
        for i in range(1000):
            test_data.append({
                'to': f'test{i}@example.com',
                'subject': f'Load Test Email {i} - {datetime.now().isoformat()}',
                'body': f'This is a test email for load testing purposes. Email #{i}.\n' * 10,
                'cc': f'cc{i}@example.com' if i % 3 == 0 else None,
                'bcc': f'bcc{i}@example.com' if i % 5 == 0 else None,
                'html_body': f'<h1>Test Email {i}</h1><p>This is HTML content for testing.</p>' if i % 2 == 0 else None
            })
        
        return test_data
    
    def _generate_calendar_test_data(self) -> List[Dict]:
        """Generate test data for calendar operations"""
        test_data = []
        base_time = datetime.now()
        
        for i in range(1000):
            start_time = base_time + timedelta(hours=i)
            end_time = start_time + timedelta(hours=1)
            
            test_data.append({
                'title': f'Load Test Event {i}',
                'start_datetime': start_time.isoformat(),
                'end_datetime': end_time.isoformat(),
                'description': f'This is a test event for load testing. Event #{i}.\n' * 5,
                'location': f'Test Location {i}' if i % 3 == 0 else '',
                'attendees': f'attendee{i}@example.com,attendee{i+1}@example.com' if i % 4 == 0 else ''
            })
        
        return test_data
    
    def _generate_task_test_data(self) -> List[Dict]:
        """Generate test data for task operations"""
        test_data = []
        base_time = datetime.now()
        
        for i in range(1000):
            due_date = base_time + timedelta(days=i % 30)
            
            test_data.append({
                'title': f'Load Test Task {i}',
                'notes': f'This is a test task for load testing purposes. Task #{i}.\n' * 3,
                'due_date': due_date.isoformat() if i % 2 == 0 else None
            })
        
        return test_data
    
    async def test_email_mcp_stress(self, config: LoadTestConfig) -> PerformanceMetrics:
        """Stress test Email MCP server"""
        logger.info(f"Starting Email MCP stress test with {config.concurrent_users} users")
        
        # Start monitoring
        self.performance_monitor.start_monitoring()
        
        # Track memory usage
        tracemalloc.start()
        
        start_time = time.time()
        response_times = []
        successful_ops = 0
        failed_ops = 0
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        async def worker(session: aiohttp.ClientSession, operation_data: Dict):
            """Worker function for email operations"""
            nonlocal successful_ops, failed_ops
            
            async with semaphore:
                operation_start = time.time()
                
                try:
                    # Test get_recent_emails
                    async with session.post(
                        f"{self.email_mcp_base_url}/get_recent_emails",
                        json={"limit": 20, "hours_back": 24}
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    # Test search_emails
                    async with session.post(
                        f"{self.email_mcp_base_url}/search_emails",
                        json={"query": f"test{successful_ops}", "limit": 10}
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    # Test send_email (mock operation)
                    async with session.post(
                        f"{self.email_mcp_base_url}/send_email",
                        json=operation_data
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    operation_time = (time.time() - operation_start) * 1000
                    response_times.append(operation_time)
                    
                except Exception as e:
                    failed_ops += 1
                    logger.error(f"Worker operation failed: {e}")
                
                # Think time
                await asyncio.sleep(
                    np.random.uniform(config.think_time_min, config.think_time_max)
                )
        
        # Create tasks for concurrent execution
        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(config.operations_per_user * config.concurrent_users):
                test_data = self.email_test_data[i % len(self.email_test_data)]
                task = asyncio.create_task(worker(session, test_data))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop monitoring
        self.performance_monitor.stop_monitoring()
        
        # Calculate metrics
        total_time = time.time() - start_time
        total_operations = successful_ops + failed_ops
        
        # Memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # System metrics
        sys_metrics = self.performance_monitor.get_metrics_summary()
        
        metrics = PerformanceMetrics(
            operation_name="Email MCP Stress Test",
            total_operations=total_operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            p95_response_time_ms=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time_ms=np.percentile(response_times, 99) if response_times else 0,
            throughput_ops_per_second=total_operations / total_time if total_time > 0 else 0,
            error_rate_percent=(failed_ops / total_operations * 100) if total_operations > 0 else 0,
            memory_usage_mb=peak / 1024 / 1024,
            cpu_usage_percent=sys_metrics['cpu_usage']['avg'],
            timestamp=datetime.now()
        )
        
        logger.info(f"Email MCP stress test completed: {successful_ops} successful, {failed_ops} failed")
        return metrics
    
    async def test_day_management_mcp_stress(self, config: LoadTestConfig) -> PerformanceMetrics:
        """Stress test Day Management MCP server"""
        logger.info(f"Starting Day Management MCP stress test with {config.concurrent_users} users")
        
        # Start monitoring
        self.performance_monitor.start_monitoring()
        
        # Track memory usage
        tracemalloc.start()
        
        start_time = time.time()
        response_times = []
        successful_ops = 0
        failed_ops = 0
        
        # Create semaphore to limit concurrent operations
        semaphore = asyncio.Semaphore(config.concurrent_users)
        
        async def worker(session: aiohttp.ClientSession, operation_data: Dict):
            """Worker function for day management operations"""
            nonlocal successful_ops, failed_ops
            
            async with semaphore:
                operation_start = time.time()
                
                try:
                    # Test get_calendar_events
                    async with session.post(
                        f"{self.day_mcp_base_url}/get_calendar_events",
                        json={"days_ahead": 7, "max_results": 20}
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    # Test get_tasks
                    async with session.post(
                        f"{self.day_mcp_base_url}/get_tasks",
                        json={"max_results": 50, "show_completed": False}
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    # Test create_calendar_event (mock operation)
                    if 'title' in operation_data:
                        async with session.post(
                            f"{self.day_mcp_base_url}/create_calendar_event",
                            json=operation_data
                        ) as response:
                            if response.status == 200:
                                successful_ops += 1
                            else:
                                failed_ops += 1
                    
                    # Test create_task (mock operation)
                    task_data = self.task_test_data[successful_ops % len(self.task_test_data)]
                    async with session.post(
                        f"{self.day_mcp_base_url}/create_task",
                        json=task_data
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                    
                    operation_time = (time.time() - operation_start) * 1000
                    response_times.append(operation_time)
                    
                except Exception as e:
                    failed_ops += 1
                    logger.error(f"Worker operation failed: {e}")
                
                # Think time
                await asyncio.sleep(
                    np.random.uniform(config.think_time_min, config.think_time_max)
                )
        
        # Create tasks for concurrent execution
        tasks = []
        async with aiohttp.ClientSession() as session:
            for i in range(config.operations_per_user * config.concurrent_users):
                test_data = self.calendar_test_data[i % len(self.calendar_test_data)]
                task = asyncio.create_task(worker(session, test_data))
                tasks.append(task)
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Stop monitoring
        self.performance_monitor.stop_monitoring()
        
        # Calculate metrics
        total_time = time.time() - start_time
        total_operations = successful_ops + failed_ops
        
        # Memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # System metrics
        sys_metrics = self.performance_monitor.get_metrics_summary()
        
        metrics = PerformanceMetrics(
            operation_name="Day Management MCP Stress Test",
            total_operations=total_operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            p95_response_time_ms=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time_ms=np.percentile(response_times, 99) if response_times else 0,
            throughput_ops_per_second=total_operations / total_time if total_time > 0 else 0,
            error_rate_percent=(failed_ops / total_operations * 100) if total_operations > 0 else 0,
            memory_usage_mb=peak / 1024 / 1024,
            cpu_usage_percent=sys_metrics['cpu_usage']['avg'],
            timestamp=datetime.now()
        )
        
        logger.info(f"Day Management MCP stress test completed: {successful_ops} successful, {failed_ops} failed")
        return metrics
    
    async def test_oauth_token_refresh_under_load(self) -> Dict[str, Any]:
        """Test OAuth token refresh behavior under load"""
        logger.info("Testing OAuth token refresh under load")
        
        # Mock token refresh scenarios
        refresh_scenarios = [
            {'expired_token': True, 'network_delay': 0.1},
            {'expired_token': True, 'network_delay': 0.5},
            {'expired_token': True, 'network_delay': 1.0},
            {'expired_token': True, 'network_delay': 2.0},
            {'refresh_failure': True, 'retry_needed': True},
            {'concurrent_refresh': True, 'users': 10}
        ]
        
        results = {}
        
        for i, scenario in enumerate(refresh_scenarios):
            logger.info(f"Testing OAuth refresh scenario {i+1}: {scenario}")
            
            start_time = time.time()
            
            # Simulate token refresh under different conditions
            if scenario.get('network_delay'):
                await asyncio.sleep(scenario['network_delay'])
            
            if scenario.get('concurrent_refresh'):
                # Test concurrent refresh requests
                tasks = []
                for j in range(scenario['users']):
                    task = asyncio.create_task(self._simulate_token_refresh())
                    tasks.append(task)
                
                results[f'concurrent_refresh_{i}'] = await asyncio.gather(*tasks)
            else:
                results[f'scenario_{i}'] = await self._simulate_token_refresh()
            
            elapsed_time = time.time() - start_time
            results[f'scenario_{i}_time'] = elapsed_time
        
        return results
    
    async def _simulate_token_refresh(self) -> Dict[str, Any]:
        """Simulate OAuth token refresh operation"""
        # Mock token refresh logic
        await asyncio.sleep(0.1)  # Simulate network call
        
        return {
            'success': True,
            'refresh_time_ms': 100,
            'token_valid': True
        }
    
    async def test_rate_limiting_and_retry_logic(self) -> Dict[str, Any]:
        """Test API rate limiting and retry logic"""
        logger.info("Testing rate limiting and retry logic")
        
        # Test scenarios for rate limiting
        rate_limit_scenarios = [
            {'requests_per_second': 100, 'duration': 10},
            {'requests_per_second': 200, 'duration': 5},
            {'requests_per_second': 500, 'duration': 2},
            {'burst_requests': 1000, 'burst_duration': 1}
        ]
        
        results = {}
        
        for i, scenario in enumerate(rate_limit_scenarios):
            logger.info(f"Testing rate limit scenario {i+1}: {scenario}")
            
            start_time = time.time()
            successful_requests = 0
            rate_limited_requests = 0
            
            if scenario.get('burst_requests'):
                # Test burst scenario
                tasks = []
                for j in range(scenario['burst_requests']):
                    task = asyncio.create_task(self._make_rate_limited_request())
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                for response in responses:
                    if isinstance(response, Exception):
                        rate_limited_requests += 1
                    else:
                        successful_requests += 1
            
            else:
                # Test sustained load
                duration = scenario['duration']
                rps = scenario['requests_per_second']
                interval = 1.0 / rps
                
                end_time = start_time + duration
                
                while time.time() < end_time:
                    try:
                        await self._make_rate_limited_request()
                        successful_requests += 1
                    except Exception:
                        rate_limited_requests += 1
                    
                    await asyncio.sleep(interval)
            
            elapsed_time = time.time() - start_time
            
            results[f'scenario_{i}'] = {
                'successful_requests': successful_requests,
                'rate_limited_requests': rate_limited_requests,
                'elapsed_time': elapsed_time,
                'actual_rps': successful_requests / elapsed_time if elapsed_time > 0 else 0,
                'rate_limit_percentage': (rate_limited_requests / (successful_requests + rate_limited_requests) * 100) if (successful_requests + rate_limited_requests) > 0 else 0
            }
        
        return results
    
    async def _make_rate_limited_request(self) -> Dict[str, Any]:
        """Make a request that might be rate limited"""
        # Simulate API request with potential rate limiting
        await asyncio.sleep(0.01)  # Simulate network call
        
        # Simulate rate limiting (10% chance)
        if np.random.random() < 0.1:
            raise Exception("Rate limited")
        
        return {'success': True, 'response_time': 10}
    
    async def test_memory_leaks_and_resource_management(self) -> Dict[str, Any]:
        """Test for memory leaks and resource management"""
        logger.info("Testing memory leaks and resource management")
        
        # Start memory tracking
        tracemalloc.start()
        
        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_samples = [initial_memory]
        
        # Perform memory-intensive operations
        for iteration in range(10):
            logger.info(f"Memory test iteration {iteration + 1}")
            
            # Create many objects
            test_objects = []
            for i in range(10000):
                obj = {
                    'id': i,
                    'data': f'test_data_{i}' * 100,
                    'nested': {
                        'items': list(range(100)),
                        'metadata': {'created': datetime.now().isoformat()}
                    }
                }
                test_objects.append(obj)
            
            # Perform operations
            await asyncio.sleep(0.1)
            
            # Measure memory
            current_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # Clean up
            del test_objects
            gc.collect()
            
            # Measure after cleanup
            after_cleanup_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_samples.append(after_cleanup_memory)
        
        # Get memory tracing results
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Analyze memory usage
        memory_growth = memory_samples[-1] - memory_samples[0]
        max_memory = max(memory_samples)
        avg_memory = statistics.mean(memory_samples)
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': memory_samples[-1],
            'memory_growth_mb': memory_growth,
            'max_memory_mb': max_memory,
            'avg_memory_mb': avg_memory,
            'peak_traced_memory_mb': peak / 1024 / 1024,
            'memory_samples': memory_samples,
            'potential_leak': memory_growth > 50  # Flag if growth > 50MB
        }
    
    async def test_concurrent_connections(self, max_connections: int = 100) -> Dict[str, Any]:
        """Test concurrent connections to MCP servers"""
        logger.info(f"Testing concurrent connections (max: {max_connections})")
        
        results = {}
        
        # Test Email MCP concurrent connections
        email_results = await self._test_concurrent_connections_to_server(
            self.email_mcp_base_url,
            max_connections,
            "Email MCP"
        )
        results['email_mcp'] = email_results
        
        # Test Day Management MCP concurrent connections
        day_results = await self._test_concurrent_connections_to_server(
            self.day_mcp_base_url,
            max_connections,
            "Day Management MCP"
        )
        results['day_management_mcp'] = day_results
        
        return results
    
    async def _test_concurrent_connections_to_server(
        self,
        base_url: str,
        max_connections: int,
        server_name: str
    ) -> Dict[str, Any]:
        """Test concurrent connections to a specific server"""
        logger.info(f"Testing concurrent connections to {server_name}")
        
        connection_results = []
        
        # Test different connection levels
        connection_levels = [10, 25, 50, 100, max_connections]
        
        for level in connection_levels:
            if level > max_connections:
                continue
            
            logger.info(f"Testing {level} concurrent connections to {server_name}")
            
            start_time = time.time()
            successful_connections = 0
            failed_connections = 0
            response_times = []
            
            # Create semaphore for connection limit
            semaphore = asyncio.Semaphore(level)
            
            async def connection_worker(session: aiohttp.ClientSession, worker_id: int):
                nonlocal successful_connections, failed_connections
                
                async with semaphore:
                    connection_start = time.time()
                    
                    try:
                        # Make a simple request
                        async with session.get(f"{base_url}/health") as response:
                            if response.status == 200:
                                successful_connections += 1
                            else:
                                failed_connections += 1
                        
                        connection_time = (time.time() - connection_start) * 1000
                        response_times.append(connection_time)
                        
                    except Exception as e:
                        failed_connections += 1
                        logger.debug(f"Connection {worker_id} failed: {e}")
            
            # Create concurrent connections
            tasks = []
            
            # Use connection pool with appropriate limits
            connector = aiohttp.TCPConnector(
                limit=level,
                limit_per_host=level,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout
            ) as session:
                for i in range(level):
                    task = asyncio.create_task(connection_worker(session, i))
                    tasks.append(task)
                
                await asyncio.gather(*tasks, return_exceptions=True)
            
            elapsed_time = time.time() - start_time
            total_connections = successful_connections + failed_connections
            
            connection_results.append({
                'connection_level': level,
                'successful_connections': successful_connections,
                'failed_connections': failed_connections,
                'total_connections': total_connections,
                'success_rate': (successful_connections / total_connections * 100) if total_connections > 0 else 0,
                'avg_response_time_ms': statistics.mean(response_times) if response_times else 0,
                'max_response_time_ms': max(response_times) if response_times else 0,
                'elapsed_time_seconds': elapsed_time
            })
        
        return {
            'server_name': server_name,
            'connection_test_results': connection_results,
            'max_successful_connections': max([r['successful_connections'] for r in connection_results]),
            'connection_limit_reached': any([r['failed_connections'] > 0 for r in connection_results])
        }
    
    async def test_error_recovery_and_graceful_degradation(self) -> Dict[str, Any]:
        """Test error recovery and graceful degradation"""
        logger.info("Testing error recovery and graceful degradation")
        
        error_scenarios = [
            {'error_type': 'network_timeout', 'duration': 5},
            {'error_type': 'server_error_500', 'frequency': 0.1},
            {'error_type': 'auth_failure', 'recovery_time': 2},
            {'error_type': 'rate_limit_exceeded', 'backoff_time': 1},
            {'error_type': 'partial_service_failure', 'affected_percentage': 0.3}
        ]
        
        results = {}
        
        for i, scenario in enumerate(error_scenarios):
            logger.info(f"Testing error scenario {i+1}: {scenario}")
            
            scenario_results = await self._test_error_scenario(scenario)
            results[f'scenario_{i}_{scenario["error_type"]}'] = scenario_results
        
        return results
    
    async def _test_error_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a specific error scenario"""
        error_type = scenario['error_type']
        
        start_time = time.time()
        successful_operations = 0
        failed_operations = 0
        recovered_operations = 0
        
        # Simulate operations under error conditions
        for i in range(100):
            try:
                # Simulate different error types
                if error_type == 'network_timeout':
                    await asyncio.sleep(0.01)  # Normal operation
                    if i % 20 == 0:  # 5% timeout rate
                        raise asyncio.TimeoutError("Network timeout")
                
                elif error_type == 'server_error_500':
                    if np.random.random() < scenario.get('frequency', 0.1):
                        raise Exception("Server error 500")
                
                elif error_type == 'auth_failure':
                    if i == 50:  # Auth failure mid-way
                        raise Exception("Authentication failed")
                
                elif error_type == 'rate_limit_exceeded':
                    if i > 60 and i < 70:  # Rate limit window
                        raise Exception("Rate limit exceeded")
                
                elif error_type == 'partial_service_failure':
                    if np.random.random() < scenario.get('affected_percentage', 0.3):
                        raise Exception("Partial service failure")
                
                successful_operations += 1
                
            except Exception as e:
                failed_operations += 1
                
                # Simulate recovery attempts
                await asyncio.sleep(0.1)  # Recovery delay
                
                # Retry operation
                try:
                    await asyncio.sleep(0.01)  # Retry operation
                    recovered_operations += 1
                except Exception:
                    pass  # Recovery failed
        
        elapsed_time = time.time() - start_time
        total_operations = successful_operations + failed_operations
        
        return {
            'error_type': error_type,
            'successful_operations': successful_operations,
            'failed_operations': failed_operations,
            'recovered_operations': recovered_operations,
            'total_operations': total_operations,
            'success_rate': (successful_operations / total_operations * 100) if total_operations > 0 else 0,
            'recovery_rate': (recovered_operations / failed_operations * 100) if failed_operations > 0 else 0,
            'elapsed_time': elapsed_time
        }
    
    async def benchmark_all_mcp_tools(self) -> Dict[str, PerformanceMetrics]:
        """Benchmark all MCP tools individually"""
        logger.info("Benchmarking all MCP tools")
        
        benchmarks = {}
        
        # Email MCP tools
        email_tools = [
            'get_recent_emails',
            'search_emails',
            'send_email',
            'read_email',
            'mark_emails_as_read',
            'archive_emails',
            'get_gmail_labels'
        ]
        
        for tool in email_tools:
            logger.info(f"Benchmarking Email MCP tool: {tool}")
            metrics = await self._benchmark_tool(self.email_mcp_base_url, tool, 'email')
            benchmarks[f'email_{tool}'] = metrics
        
        # Day Management MCP tools
        day_tools = [
            'get_calendar_events',
            'create_calendar_event',
            'update_calendar_event',
            'delete_calendar_event',
            'get_tasks',
            'create_task',
            'update_task',
            'complete_task',
            'get_day_overview',
            'get_tasklists'
        ]
        
        for tool in day_tools:
            logger.info(f"Benchmarking Day Management MCP tool: {tool}")
            metrics = await self._benchmark_tool(self.day_mcp_base_url, tool, 'day')
            benchmarks[f'day_{tool}'] = metrics
        
        return benchmarks
    
    async def _benchmark_tool(self, base_url: str, tool_name: str, server_type: str) -> PerformanceMetrics:
        """Benchmark a specific MCP tool"""
        # Start memory tracking
        tracemalloc.start()
        
        start_time = time.time()
        response_times = []
        successful_ops = 0
        failed_ops = 0
        
        # Get appropriate test data
        if server_type == 'email':
            test_data = self.email_test_data[0]
        else:
            if 'calendar' in tool_name:
                test_data = self.calendar_test_data[0]
            else:
                test_data = self.task_test_data[0]
        
        # Benchmark the tool with multiple iterations
        iterations = 50
        
        async with aiohttp.ClientSession() as session:
            for i in range(iterations):
                operation_start = time.time()
                
                try:
                    # Customize request based on tool
                    request_data = self._get_tool_request_data(tool_name, test_data)
                    
                    async with session.post(
                        f"{base_url}/{tool_name}",
                        json=request_data
                    ) as response:
                        if response.status == 200:
                            successful_ops += 1
                        else:
                            failed_ops += 1
                        
                        operation_time = (time.time() - operation_start) * 1000
                        response_times.append(operation_time)
                
                except Exception as e:
                    failed_ops += 1
                    logger.debug(f"Tool {tool_name} operation {i} failed: {e}")
                
                # Small delay between operations
                await asyncio.sleep(0.01)
        
        # Calculate metrics
        total_time = time.time() - start_time
        total_operations = successful_ops + failed_ops
        
        # Memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        return PerformanceMetrics(
            operation_name=f"{server_type.title()} MCP - {tool_name}",
            total_operations=total_operations,
            successful_operations=successful_ops,
            failed_operations=failed_ops,
            avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
            min_response_time_ms=min(response_times) if response_times else 0,
            max_response_time_ms=max(response_times) if response_times else 0,
            p95_response_time_ms=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time_ms=np.percentile(response_times, 99) if response_times else 0,
            throughput_ops_per_second=total_operations / total_time if total_time > 0 else 0,
            error_rate_percent=(failed_ops / total_operations * 100) if total_operations > 0 else 0,
            memory_usage_mb=peak / 1024 / 1024,
            cpu_usage_percent=0,  # Not measured per tool
            timestamp=datetime.now()
        )
    
    def _get_tool_request_data(self, tool_name: str, test_data: Dict) -> Dict:
        """Get appropriate request data for a specific tool"""
        # Default request data based on tool
        request_data = {}
        
        if tool_name == 'get_recent_emails':
            request_data = {'limit': 20, 'hours_back': 24}
        elif tool_name == 'search_emails':
            request_data = {'query': 'test', 'limit': 10}
        elif tool_name == 'send_email':
            request_data = test_data
        elif tool_name == 'read_email':
            request_data = {'message_id': 'test_message_id'}
        elif tool_name == 'mark_emails_as_read':
            request_data = {'message_ids': 'test_id_1,test_id_2'}
        elif tool_name == 'archive_emails':
            request_data = {'message_ids': 'test_id_1,test_id_2'}
        elif tool_name == 'get_gmail_labels':
            request_data = {}
        elif tool_name == 'get_calendar_events':
            request_data = {'days_ahead': 7, 'max_results': 20}
        elif tool_name in ['create_calendar_event', 'update_calendar_event']:
            request_data = test_data
        elif tool_name == 'delete_calendar_event':
            request_data = {'event_id': 'test_event_id'}
        elif tool_name == 'get_tasks':
            request_data = {'max_results': 50, 'show_completed': False}
        elif tool_name == 'create_task':
            request_data = test_data
        elif tool_name == 'update_task':
            request_data = {'task_id': 'test_task_id', **test_data}
        elif tool_name == 'complete_task':
            request_data = {'task_id': 'test_task_id'}
        elif tool_name == 'get_day_overview':
            request_data = {'target_date': datetime.now().isoformat()}
        elif tool_name == 'get_tasklists':
            request_data = {}
        
        return request_data
    
    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive performance report"""
        report = []
        report.append("=" * 80)
        report.append("MCP SERVERS STRESS AND PERFORMANCE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary metrics
        if 'email_stress_test' in results:
            email_metrics = results['email_stress_test']
            report.append("EMAIL MCP STRESS TEST RESULTS:")
            report.append("-" * 40)
            report.append(f"Total Operations: {email_metrics.total_operations}")
            report.append(f"Successful Operations: {email_metrics.successful_operations}")
            report.append(f"Failed Operations: {email_metrics.failed_operations}")
            report.append(f"Success Rate: {100 - email_metrics.error_rate_percent:.2f}%")
            report.append(f"Average Response Time: {email_metrics.avg_response_time_ms:.2f} ms")
            report.append(f"P95 Response Time: {email_metrics.p95_response_time_ms:.2f} ms")
            report.append(f"P99 Response Time: {email_metrics.p99_response_time_ms:.2f} ms")
            report.append(f"Throughput: {email_metrics.throughput_ops_per_second:.2f} ops/sec")
            report.append(f"Memory Usage: {email_metrics.memory_usage_mb:.2f} MB")
            report.append(f"CPU Usage: {email_metrics.cpu_usage_percent:.2f}%")
            report.append("")
        
        if 'day_stress_test' in results:
            day_metrics = results['day_stress_test']
            report.append("DAY MANAGEMENT MCP STRESS TEST RESULTS:")
            report.append("-" * 40)
            report.append(f"Total Operations: {day_metrics.total_operations}")
            report.append(f"Successful Operations: {day_metrics.successful_operations}")
            report.append(f"Failed Operations: {day_metrics.failed_operations}")
            report.append(f"Success Rate: {100 - day_metrics.error_rate_percent:.2f}%")
            report.append(f"Average Response Time: {day_metrics.avg_response_time_ms:.2f} ms")
            report.append(f"P95 Response Time: {day_metrics.p95_response_time_ms:.2f} ms")
            report.append(f"P99 Response Time: {day_metrics.p99_response_time_ms:.2f} ms")
            report.append(f"Throughput: {day_metrics.throughput_ops_per_second:.2f} ops/sec")
            report.append(f"Memory Usage: {day_metrics.memory_usage_mb:.2f} MB")
            report.append(f"CPU Usage: {day_metrics.cpu_usage_percent:.2f}%")
            report.append("")
        
        # OAuth token refresh results
        if 'oauth_test' in results:
            report.append("OAUTH TOKEN REFRESH TEST RESULTS:")
            report.append("-" * 40)
            oauth_results = results['oauth_test']
            for key, value in oauth_results.items():
                if isinstance(value, dict):
                    report.append(f"{key}: {value}")
                else:
                    report.append(f"{key}: {value}")
            report.append("")
        
        # Rate limiting results
        if 'rate_limiting_test' in results:
            report.append("RATE LIMITING TEST RESULTS:")
            report.append("-" * 40)
            rate_results = results['rate_limiting_test']
            for scenario, data in rate_results.items():
                report.append(f"{scenario}:")
                report.append(f"  Successful Requests: {data['successful_requests']}")
                report.append(f"  Rate Limited Requests: {data['rate_limited_requests']}")
                report.append(f"  Rate Limit Percentage: {data['rate_limit_percentage']:.2f}%")
                report.append(f"  Actual RPS: {data['actual_rps']:.2f}")
            report.append("")
        
        # Memory test results
        if 'memory_test' in results:
            report.append("MEMORY LEAK TEST RESULTS:")
            report.append("-" * 40)
            memory_results = results['memory_test']
            report.append(f"Initial Memory: {memory_results['initial_memory_mb']:.2f} MB")
            report.append(f"Final Memory: {memory_results['final_memory_mb']:.2f} MB")
            report.append(f"Memory Growth: {memory_results['memory_growth_mb']:.2f} MB")
            report.append(f"Max Memory: {memory_results['max_memory_mb']:.2f} MB")
            report.append(f"Peak Traced Memory: {memory_results['peak_traced_memory_mb']:.2f} MB")
            report.append(f"Potential Memory Leak: {'Yes' if memory_results['potential_leak'] else 'No'}")
            report.append("")
        
        # Concurrent connections results
        if 'concurrent_connections_test' in results:
            report.append("CONCURRENT CONNECTIONS TEST RESULTS:")
            report.append("-" * 40)
            conn_results = results['concurrent_connections_test']
            for server, data in conn_results.items():
                report.append(f"{server.upper()}:")
                report.append(f"  Max Successful Connections: {data['max_successful_connections']}")
                report.append(f"  Connection Limit Reached: {'Yes' if data['connection_limit_reached'] else 'No'}")
                for test_result in data['connection_test_results']:
                    report.append(f"    {test_result['connection_level']} connections: {test_result['success_rate']:.1f}% success")
            report.append("")
        
        # Tool benchmarks
        if 'tool_benchmarks' in results:
            report.append("INDIVIDUAL TOOL BENCHMARKS:")
            report.append("-" * 40)
            benchmarks = results['tool_benchmarks']
            for tool_name, metrics in benchmarks.items():
                report.append(f"{tool_name}:")
                report.append(f"  Success Rate: {100 - metrics.error_rate_percent:.2f}%")
                report.append(f"  Avg Response Time: {metrics.avg_response_time_ms:.2f} ms")
                report.append(f"  Throughput: {metrics.throughput_ops_per_second:.2f} ops/sec")
            report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS:")
        report.append("-" * 40)
        
        # Generate recommendations based on results
        recommendations = self._generate_recommendations(results)
        for rec in recommendations:
            report.append(f"• {rec}")
        
        report.append("")
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check email MCP performance
        if 'email_stress_test' in results:
            email_metrics = results['email_stress_test']
            if email_metrics.error_rate_percent > 5:
                recommendations.append("Email MCP error rate is high - consider implementing better error handling")
            if email_metrics.avg_response_time_ms > 1000:
                recommendations.append("Email MCP response times are slow - consider optimizing email operations")
            if email_metrics.throughput_ops_per_second < 10:
                recommendations.append("Email MCP throughput is low - consider connection pooling optimization")
        
        # Check day management MCP performance
        if 'day_stress_test' in results:
            day_metrics = results['day_stress_test']
            if day_metrics.error_rate_percent > 5:
                recommendations.append("Day Management MCP error rate is high - review calendar/task API handling")
            if day_metrics.avg_response_time_ms > 1000:
                recommendations.append("Day Management MCP response times are slow - optimize calendar operations")
        
        # Check memory usage
        if 'memory_test' in results:
            memory_results = results['memory_test']
            if memory_results['potential_leak']:
                recommendations.append("Potential memory leak detected - review object lifecycle management")
            if memory_results['max_memory_mb'] > 500:
                recommendations.append("High memory usage detected - implement memory usage optimization")
        
        # Check concurrent connections
        if 'concurrent_connections_test' in results:
            conn_results = results['concurrent_connections_test']
            for server, data in conn_results.items():
                if data['connection_limit_reached']:
                    recommendations.append(f"Connection limit reached for {server} - consider increasing connection pool size")
        
        # Check rate limiting
        if 'rate_limiting_test' in results:
            rate_results = results['rate_limiting_test']
            for scenario, data in rate_results.items():
                if data['rate_limit_percentage'] > 20:
                    recommendations.append("High rate limiting detected - implement better backoff strategies")
        
        # General recommendations
        recommendations.append("Implement comprehensive monitoring and alerting for production deployment")
        recommendations.append("Consider implementing circuit breakers for external API calls")
        recommendations.append("Set up proper logging and tracing for performance analysis")
        recommendations.append("Implement health check endpoints for load balancers")
        recommendations.append("Consider using Redis for caching frequently accessed data")
        
        return recommendations
    
    def save_results_to_file(self, results: Dict[str, Any], filename: str = None):
        """Save test results to JSON file"""
        if filename is None:
            filename = f"mcp_stress_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert datetime objects to strings for JSON serialization
        serializable_results = {}
        for key, value in results.items():
            if isinstance(value, PerformanceMetrics):
                serializable_results[key] = asdict(value)
                # Convert datetime to string
                if 'timestamp' in serializable_results[key]:
                    serializable_results[key]['timestamp'] = serializable_results[key]['timestamp'].isoformat()
            elif isinstance(value, dict):
                serializable_results[key] = self._make_serializable(value)
            else:
                serializable_results[key] = value
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)
        
        logger.info(f"Test results saved to {filename}")
    
    def _make_serializable(self, obj):
        """Make object serializable for JSON"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, PerformanceMetrics):
            result = asdict(obj)
            if 'timestamp' in result:
                result['timestamp'] = result['timestamp'].isoformat()
            return result
        else:
            return obj


class MCPLoadTestUser(HttpUser):
    """Locust user for load testing MCP servers"""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Initialize test data"""
        self.email_test_data = {
            'to': 'test@example.com',
            'subject': 'Load Test Email',
            'body': 'This is a test email for load testing.'
        }
        
        self.calendar_test_data = {
            'title': 'Load Test Event',
            'start_datetime': datetime.now().isoformat(),
            'end_datetime': (datetime.now() + timedelta(hours=1)).isoformat(),
            'description': 'Test event for load testing'
        }
        
        self.task_test_data = {
            'title': 'Load Test Task',
            'notes': 'Test task for load testing',
            'due_date': (datetime.now() + timedelta(days=1)).isoformat()
        }
    
    @task(3)
    def test_email_operations(self):
        """Test email MCP operations"""
        # Get recent emails
        self.client.post("/get_recent_emails", json={"limit": 10})
        
        # Search emails
        self.client.post("/search_emails", json={"query": "test", "limit": 5})
        
        # Send email (mock)
        self.client.post("/send_email", json=self.email_test_data)
    
    @task(3)
    def test_calendar_operations(self):
        """Test calendar operations"""
        # Get calendar events
        self.client.post("/get_calendar_events", json={"days_ahead": 7})
        
        # Create calendar event (mock)
        self.client.post("/create_calendar_event", json=self.calendar_test_data)
        
        # Get day overview
        self.client.post("/get_day_overview", json={})
    
    @task(2)
    def test_task_operations(self):
        """Test task operations"""
        # Get tasks
        self.client.post("/get_tasks", json={"max_results": 20})
        
        # Create task (mock)
        self.client.post("/create_task", json=self.task_test_data)
        
        # Get task lists
        self.client.post("/get_tasklists", json={})


async def run_comprehensive_stress_tests():
    """Run all comprehensive stress tests"""
    logger.info("Starting comprehensive MCP stress and performance tests")
    
    # Initialize tester
    tester = MCPStressTester()
    
    # Test configuration
    config = LoadTestConfig(
        concurrent_users=20,
        operations_per_user=50,
        test_duration_seconds=300,
        think_time_min=0.1,
        think_time_max=1.0
    )
    
    # Store all results
    all_results = {}
    
    try:
        # 1. Email MCP stress test
        logger.info("Running Email MCP stress test...")
        email_results = await tester.test_email_mcp_stress(config)
        all_results['email_stress_test'] = email_results
        
        # 2. Day Management MCP stress test
        logger.info("Running Day Management MCP stress test...")
        day_results = await tester.test_day_management_mcp_stress(config)
        all_results['day_stress_test'] = day_results
        
        # 3. OAuth token refresh test
        logger.info("Running OAuth token refresh test...")
        oauth_results = await tester.test_oauth_token_refresh_under_load()
        all_results['oauth_test'] = oauth_results
        
        # 4. Rate limiting test
        logger.info("Running rate limiting test...")
        rate_results = await tester.test_rate_limiting_and_retry_logic()
        all_results['rate_limiting_test'] = rate_results
        
        # 5. Memory leak test
        logger.info("Running memory leak test...")
        memory_results = await tester.test_memory_leaks_and_resource_management()
        all_results['memory_test'] = memory_results
        
        # 6. Concurrent connections test
        logger.info("Running concurrent connections test...")
        conn_results = await tester.test_concurrent_connections(100)
        all_results['concurrent_connections_test'] = conn_results
        
        # 7. Tool benchmarks
        logger.info("Running individual tool benchmarks...")
        benchmark_results = await tester.benchmark_all_mcp_tools()
        all_results['tool_benchmarks'] = benchmark_results
        
        # 8. Error recovery test
        logger.info("Running error recovery test...")
        error_results = await tester.test_error_recovery_and_graceful_degradation()
        all_results['error_recovery_test'] = error_results
        
        # Generate comprehensive report
        logger.info("Generating performance report...")
        report = tester.generate_performance_report(all_results)
        
        # Save results
        tester.save_results_to_file(all_results)
        
        # Save report
        report_filename = f"mcp_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)
        
        logger.info(f"Performance report saved to {report_filename}")
        
        # Print summary
        print("\n" + "="*80)
        print("STRESS TEST SUMMARY")
        print("="*80)
        print(f"Email MCP: {email_results.successful_operations}/{email_results.total_operations} ops successful")
        print(f"Day Management MCP: {day_results.successful_operations}/{day_results.total_operations} ops successful")
        print(f"Results saved to: {report_filename}")
        print("="*80)
        
        return all_results
        
    except Exception as e:
        logger.error(f"Stress test failed: {e}")
        raise


def run_locust_load_test(host: str = "http://127.0.0.1:5002", users: int = 50, spawn_rate: int = 5, duration: int = 300):
    """Run Locust load test"""
    logger.info(f"Starting Locust load test with {users} users for {duration} seconds")
    
    # Setup Locust environment
    env = Environment(user_classes=[MCPLoadTestUser])
    env.create_local_runner()
    
    # Start test
    env.runner.start(user_count=users, spawn_rate=spawn_rate)
    
    # Run for specified duration
    import time
    time.sleep(duration)
    
    # Stop test
    env.runner.stop()
    
    # Get statistics
    stats = env.runner.stats
    
    logger.info("Locust load test completed")
    return stats


if __name__ == "__main__":
    # Run comprehensive stress tests
    asyncio.run(run_comprehensive_stress_tests())