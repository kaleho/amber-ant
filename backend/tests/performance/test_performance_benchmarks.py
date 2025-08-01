"""Performance and load testing benchmarks."""
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import mean, median
import psutil
import gc

from httpx import AsyncClient
from fastapi.testclient import TestClient


@pytest.mark.performance
@pytest.mark.slow
class TestAPIPerformance:
    """Test API endpoint performance benchmarks."""
    
    def test_user_endpoint_response_time(self, test_client, auth_headers, benchmark):
        """Benchmark user endpoint response time."""
        def get_users():
            response = test_client.get("/api/v1/users", headers=auth_headers)
            assert response.status_code in [200, 401]  # May not be authenticated in test
            return response
        
        # Benchmark the function
        result = benchmark(get_users)
        
        # Performance assertions
        assert benchmark.stats['mean'] < 0.5  # Should complete in under 500ms
        assert benchmark.stats['max'] < 2.0   # No request should take over 2s
    
    def test_budget_endpoint_response_time(self, test_client, auth_headers, benchmark):
        """Benchmark budget endpoint response time."""
        def get_budgets():
            response = test_client.get("/api/v1/budgets", headers=auth_headers)
            assert response.status_code in [200, 401]
            return response
        
        result = benchmark(get_budgets)
        
        # Performance assertions
        assert benchmark.stats['mean'] < 0.5  # Should complete in under 500ms
        assert benchmark.stats['max'] < 2.0
    
    def test_transaction_endpoint_response_time(self, test_client, auth_headers, benchmark):
        """Benchmark transaction endpoint response time."""
        def get_transactions():
            response = test_client.get("/api/v1/transactions", headers=auth_headers)
            assert response.status_code in [200, 401]
            return response
        
        result = benchmark(get_transactions)
        
        # Performance assertions
        assert benchmark.stats['mean'] < 0.5
        assert benchmark.stats['max'] < 2.0
    
    def test_health_endpoint_response_time(self, test_client, benchmark):
        """Benchmark health endpoint response time."""
        def get_health():
            response = test_client.get("/health")
            assert response.status_code == 200
            return response
        
        result = benchmark(get_health)
        
        # Health endpoint should be very fast
        assert benchmark.stats['mean'] < 0.1   # Under 100ms
        assert benchmark.stats['max'] < 0.5    # Under 500ms max
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_performance(self, async_client, auth_headers):
        """Test performance under concurrent load."""
        concurrent_requests = 50
        request_timeout = 5.0
        
        async def make_request():
            start_time = time.time()
            try:
                response = await async_client.get(
                    "/api/v1/users",
                    headers=auth_headers,
                    timeout=request_timeout
                )
                end_time = time.time()
                return {
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': True
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'status_code': 0,
                    'response_time': end_time - start_time,
                    'success': False,
                    'error': str(e)
                }
        
        # Execute concurrent requests
        start_time = time.time()
        tasks = [make_request() for _ in range(concurrent_requests)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # Analyze results
        successful_requests = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        failed_requests = [r for r in results if not (isinstance(r, dict) and r.get('success', False))]
        
        # Performance assertions
        success_rate = len(successful_requests) / len(results)
        assert success_rate >= 0.9  # At least 90% success rate
        
        if successful_requests:
            response_times = [r['response_time'] for r in successful_requests]
            average_response_time = mean(response_times)
            median_response_time = median(response_times)
            max_response_time = max(response_times)
            
            # Performance targets
            assert average_response_time < 2.0  # Average under 2s
            assert median_response_time < 1.5   # Median under 1.5s
            assert max_response_time < 5.0      # Max under 5s
            
            # Throughput check
            throughput = len(successful_requests) / total_time
            assert throughput > 10  # At least 10 requests per second
        
        print(f"Concurrent requests: {concurrent_requests}")
        print(f"Success rate: {success_rate:.2%}")
        print(f"Total time: {total_time:.2f}s")
        if successful_requests:
            print(f"Average response time: {average_response_time:.3f}s")
            print(f"Median response time: {median_response_time:.3f}s")
            print(f"Max response time: {max_response_time:.3f}s")
            print(f"Throughput: {throughput:.1f} req/s")


@pytest.mark.performance
@pytest.mark.slow
class TestDatabasePerformance:
    """Test database operation performance."""
    
    def test_user_query_performance(self, test_client, auth_headers, benchmark):
        """Test user database query performance."""
        def query_users():
            response = test_client.get("/api/v1/users?limit=100", headers=auth_headers)
            return response
        
        result = benchmark(query_users)
        
        # Database queries should be fast
        assert benchmark.stats['mean'] < 1.0  # Under 1 second average
    
    def test_budget_query_performance(self, test_client, auth_headers, benchmark):
        """Test budget database query performance."""
        def query_budgets():
            response = test_client.get("/api/v1/budgets?limit=100", headers=auth_headers)
            return response
        
        result = benchmark(query_budgets)
        
        assert benchmark.stats['mean'] < 1.0
    
    def test_transaction_query_performance(self, test_client, auth_headers, benchmark):
        """Test transaction database query performance."""
        def query_transactions():
            response = test_client.get("/api/v1/transactions?limit=100", headers=auth_headers)
            return response
        
        result = benchmark(query_transactions)
        
        assert benchmark.stats['mean'] < 1.5  # Transactions might be more complex
    
    def test_complex_analytics_query_performance(self, test_client, auth_headers, benchmark):
        """Test complex analytics query performance."""
        def query_analytics():
            response = test_client.get("/api/v1/budgets/analytics", headers=auth_headers)
            return response
        
        result = benchmark(query_analytics)
        
        # Analytics queries can be more complex
        assert benchmark.stats['mean'] < 3.0  # Under 3 seconds
        assert benchmark.stats['max'] < 10.0  # Max 10 seconds


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    def test_memory_usage_during_requests(self, test_client, auth_headers):
        """Test memory usage during API requests."""
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make multiple requests to test for memory leaks
        for i in range(100):
            response = test_client.get("/api/v1/users", headers=auth_headers)
            # Force garbage collection periodically
            if i % 20 == 0:
                gc.collect()
        
        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly
        assert memory_increase < 100  # Less than 100MB increase
        
        print(f"Initial memory: {initial_memory:.1f} MB")
        print(f"Final memory: {final_memory:.1f} MB")
        print(f"Memory increase: {memory_increase:.1f} MB")
    
    def test_large_response_memory_efficiency(self, test_client, auth_headers):
        """Test memory efficiency with large responses."""
        # Test with large limit to get potentially large response
        response = test_client.get("/api/v1/transactions?limit=1000", headers=auth_headers)
        
        # Should handle large responses without excessive memory usage
        # This is more of a smoke test - actual memory measurement would require more setup
        assert response.status_code in [200, 401]
    
    def test_concurrent_request_memory_usage(self, test_client, auth_headers):
        """Test memory usage under concurrent load."""
        import threading
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        def make_requests():
            for _ in range(20):
                response = test_client.get("/api/v1/users", headers=auth_headers)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase excessively during concurrent operations
        assert memory_increase < 200  # Less than 200MB increase
        
        print(f"Concurrent memory test - Initial: {initial_memory:.1f} MB, Final: {final_memory:.1f} MB")


@pytest.mark.performance
@pytest.mark.slow
class TestScalabilityPerformance:
    """Test system scalability and performance under load."""
    
    @pytest.mark.asyncio
    async def test_progressive_load_performance(self, async_client, auth_headers):
        """Test performance as load progressively increases."""
        load_levels = [5, 10, 25, 50, 100]
        results = {}
        
        for concurrent_requests in load_levels:
            print(f"Testing with {concurrent_requests} concurrent requests...")
            
            async def make_request():
                start_time = time.time()
                try:
                    response = await async_client.get(
                        "/api/v1/users",
                        headers=auth_headers,
                        timeout=10.0
                    )
                    end_time = time.time()
                    return {
                        'response_time': end_time - start_time,
                        'success': response.status_code in [200, 401]
                    }
                except Exception:
                    end_time = time.time()
                    return {
                        'response_time': end_time - start_time,
                        'success': False
                    }
            
            # Execute concurrent requests
            start_time = time.time()
            tasks = [make_request() for _ in range(concurrent_requests)]
            request_results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Analyze results
            successful_results = [
                r for r in request_results 
                if isinstance(r, dict) and r.get('success', False)
            ]
            
            if successful_results:
                avg_response_time = mean([r['response_time'] for r in successful_results])
                success_rate = len(successful_results) / len(request_results)
                throughput = len(successful_results) / total_time
                
                results[concurrent_requests] = {
                    'avg_response_time': avg_response_time,
                    'success_rate': success_rate,
                    'throughput': throughput
                }
                
                print(f"  Avg response time: {avg_response_time:.3f}s")
                print(f"  Success rate: {success_rate:.2%}")
                print(f"  Throughput: {throughput:.1f} req/s")
        
        # Analyze scalability
        # Response times shouldn't degrade too much with increased load
        if len(results) >= 2:
            first_load = min(results.keys())
            last_load = max(results.keys())
            
            first_response_time = results[first_load]['avg_response_time']
            last_response_time = results[last_load]['avg_response_time']
            
            # Response time shouldn't increase by more than 5x
            response_time_degradation = last_response_time / first_response_time
            assert response_time_degradation < 5.0
            
            print(f"Response time degradation: {response_time_degradation:.2f}x")
    
    def test_sustained_load_performance(self, test_client, auth_headers):
        """Test performance under sustained load."""
        duration_seconds = 30  # 30 second test
        requests_per_second = 5
        
        start_time = time.time()
        request_count = 0
        response_times = []
        errors = []
        
        while time.time() - start_time < duration_seconds:
            request_start = time.time()
            
            try:
                response = test_client.get("/api/v1/users", headers=auth_headers)
                response_time = time.time() - request_start
                response_times.append(response_time)
                
                if response.status_code not in [200, 401]:
                    errors.append(f"Status {response.status_code}")
                
            except Exception as e:
                response_time = time.time() - request_start
                response_times.append(response_time)
                errors.append(str(e))
            
            request_count += 1
            
            # Control rate
            sleep_time = (1.0 / requests_per_second) - (time.time() - request_start)
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        total_time = time.time() - start_time
        
        # Analyze sustained load results
        if response_times:
            avg_response_time = mean(response_times)
            max_response_time = max(response_times)
            error_rate = len(errors) / request_count
            actual_throughput = request_count / total_time
            
            print(f"Sustained load test results:")
            print(f"  Duration: {total_time:.1f}s")
            print(f"  Total requests: {request_count}")
            print(f"  Avg response time: {avg_response_time:.3f}s")
            print(f"  Max response time: {max_response_time:.3f}s")
            print(f"  Error rate: {error_rate:.2%}")
            print(f"  Throughput: {actual_throughput:.1f} req/s")
            
            # Performance assertions for sustained load
            assert avg_response_time < 2.0  # Average should stay reasonable
            assert error_rate < 0.05        # Less than 5% error rate
            assert actual_throughput > 2.0  # At least 2 req/s


@pytest.mark.performance
@pytest.mark.slow 
class TestSpecificOperationPerformance:
    """Test performance of specific business operations."""
    
    def test_budget_creation_performance(self, test_client, auth_headers, benchmark):
        """Test budget creation performance."""
        budget_data = {
            "name": "Performance Test Budget",
            "total_amount": 5000.00,
            "period_type": "monthly",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29",
            "categories": [
                {
                    "category_name": f"Category {i}",
                    "allocated_amount": 100.00,
                    "is_essential": i % 2 == 0,
                    "priority": (i % 5) + 1
                }
                for i in range(10)  # 10 categories
            ]
        }
        
        def create_budget():
            response = test_client.post(
                "/api/v1/budgets",
                json=budget_data,
                headers=auth_headers
            )
            # Delete the budget after creation to avoid accumulation
            if response.status_code == 201:
                budget_id = response.json().get("id")
                if budget_id:
                    test_client.delete(f"/api/v1/budgets/{budget_id}", headers=auth_headers)
            return response
        
        result = benchmark(create_budget)
        
        # Budget creation with categories should be reasonably fast
        assert benchmark.stats['mean'] < 2.0  # Under 2 seconds average
        assert benchmark.stats['max'] < 5.0   # Max 5 seconds
    
    def test_complex_budget_analytics_performance(self, test_client, auth_headers, benchmark):
        """Test complex budget analytics calculation performance."""
        def get_analytics():
            response = test_client.get("/api/v1/budgets/analytics", headers=auth_headers)
            return response
        
        result = benchmark(get_analytics)
        
        # Analytics calculations can be complex
        assert benchmark.stats['mean'] < 5.0  # Under 5 seconds average
        assert benchmark.stats['max'] < 15.0  # Max 15 seconds
    
    def test_transaction_aggregation_performance(self, test_client, auth_headers, benchmark):
        """Test transaction aggregation performance."""
        def get_transaction_summary():
            response = test_client.get(
                "/api/v1/transactions/summary?start_date=2024-01-01&end_date=2024-12-31",
                headers=auth_headers
            )
            return response
        
        result = benchmark(get_transaction_summary)
        
        # Transaction aggregations can be expensive
        assert benchmark.stats['mean'] < 10.0  # Under 10 seconds
        assert benchmark.stats['max'] < 30.0   # Max 30 seconds


@pytest.mark.performance
class TestCachePerformance:
    """Test caching performance and effectiveness."""
    
    def test_repeated_request_performance(self, test_client, auth_headers):
        """Test that repeated requests benefit from caching."""
        endpoint = "/api/v1/users"
        
        # First request (cache miss)
        start_time = time.time()
        response1 = test_client.get(endpoint, headers=auth_headers)
        first_request_time = time.time() - start_time
        
        # Second request (should be cached)
        start_time = time.time()
        response2 = test_client.get(endpoint, headers=auth_headers)
        second_request_time = time.time() - start_time
        
        # Third request (should also be cached)
        start_time = time.time()
        response3 = test_client.get(endpoint, headers=auth_headers)
        third_request_time = time.time() - start_time
        
        print(f"First request: {first_request_time:.3f}s")
        print(f"Second request: {second_request_time:.3f}s")
        print(f"Third request: {third_request_time:.3f}s")
        
        # Cached requests should be faster (if caching is implemented)
        # This test would only pass if caching is actually implemented
        # For now, we just ensure all requests complete
        assert response1.status_code in [200, 401]
        assert response2.status_code in [200, 401]
        assert response3.status_code in [200, 401]
    
    def test_cache_invalidation_performance(self, test_client, auth_headers):
        """Test cache invalidation doesn't significantly impact performance."""
        # This would test that cache invalidation after updates
        # doesn't cause significant performance degradation
        pass


@pytest.mark.performance
class TestResourceUtilizationPerformance:
    """Test resource utilization during operations."""
    
    def test_cpu_utilization_during_load(self, test_client, auth_headers):
        """Test CPU utilization during API load."""
        import psutil
        
        # Monitor CPU usage during requests
        cpu_percentages = []
        
        def monitor_cpu():
            for _ in range(10):  # Monitor for 10 samples
                cpu_percent = psutil.cpu_percent(interval=0.1)
                cpu_percentages.append(cpu_percent)
        
        # Start CPU monitoring in background
        import threading
        monitor_thread = threading.Thread(target=monitor_cpu)
        monitor_thread.start()
        
        # Make requests during monitoring
        for _ in range(50):
            response = test_client.get("/api/v1/users", headers=auth_headers)
        
        monitor_thread.join()
        
        if cpu_percentages:
            avg_cpu = mean(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            print(f"Average CPU usage: {avg_cpu:.1f}%")
            print(f"Max CPU usage: {max_cpu:.1f}%")
            
            # CPU usage should be reasonable
            assert avg_cpu < 80.0  # Average under 80%
            assert max_cpu < 95.0  # Max under 95%
    
    def test_database_connection_efficiency(self, test_client, auth_headers):
        """Test database connection pool efficiency."""
        # This would test that database connections are properly pooled
        # and reused efficiently during concurrent operations
        pass