import pytest
import time
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from main import app
from models import LogEntry, Proxy, User
from logging_middleware import logging_middleware, log_proxy_request
from database import SessionLocal


class TestLoggingMiddleware:
    """Test logging middleware functionality."""
    
    def test_generate_prompt_hash(self):
        """Test prompt hash generation."""
        request_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        hash1 = logging_middleware.generate_prompt_hash(request_data)
        hash2 = logging_middleware.generate_prompt_hash(request_data)
        
        # Same data should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Should be 16 characters
        
        # Different data should produce different hash
        different_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "Goodbye"}]
        }
        hash3 = logging_middleware.generate_prompt_hash(different_data)
        assert hash1 != hash3
    
    def test_generate_prompt_hash_empty_data(self):
        """Test hash generation with empty data."""
        hash_result = logging_middleware.generate_prompt_hash({})
        assert hash_result == ""
        
        hash_result = logging_middleware.generate_prompt_hash(None)
        assert hash_result == ""
    
    @pytest.mark.asyncio
    async def test_log_proxy_request(self):
        """Test logging proxy requests."""
        # Create mock request and response
        mock_request = MagicMock()
        mock_request.client.host = "192.168.1.100"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        request_data = {"model": "gpt-4", "messages": [{"role": "user", "content": "test"}]}
        start_time = time.time() - 0.1  # 100ms ago
        
        # This will actually create a log entry in the database
        await log_proxy_request(
            proxy_id=1,
            request=mock_request,
            response=mock_response,
            start_time=start_time,
            cache_hit=True,
            failure_type=None,
            request_data=request_data
        )
        
        # Verify log entry was created
        db = SessionLocal()
        try:
            log_entry = db.query(LogEntry).filter(LogEntry.proxy_id == 1).first()
            assert log_entry is not None
            assert log_entry.ip_address == "192.168.1.100"
            assert log_entry.status_code == 200
            assert log_entry.cache_hit is True
            assert log_entry.latency > 0  # Should have some latency
            assert log_entry.prompt_hash is not None
            assert len(log_entry.prompt_hash) == 16
        finally:
            # Clean up
            if log_entry:
                db.delete(log_entry)
                db.commit()
            db.close()


class TestLoggingEndpoints:
    """Test logging API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        
        # Create test user and get auth headers
        import time
        import random
        timestamp = int(time.time() * 1000)  # Use milliseconds for more uniqueness
        random_suffix = random.randint(1000, 9999)
        self.user_data = {"email": f"test-logging-{timestamp}-{random_suffix}@example.com", "password": "testpass123"}
        
        # Register user
        register_response = self.client.post("/auth/register", json=self.user_data)
        assert register_response.status_code == 201
        
        # Login to get token
        login_response = self.client.post("/auth/jwt/login", data={
            "username": self.user_data["email"],
            "password": self.user_data["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {token}"}
        
        # Create test proxy
        proxy_data = {
            "name": "test-logging-proxy",
            "provider": "openai",
            "model_name": "gpt-4",
            "description": "Test proxy for logging"
        }
        
        response = self.client.post("/proxies", json=proxy_data, headers=self.headers)
        assert response.status_code == 200
        self.proxy_id = response.json()["id"]
    
    def create_test_logs(self, count=5):
        """Create test log entries."""
        db = SessionLocal()
        try:
            for i in range(count):
                log_entry = LogEntry(
                    proxy_id=self.proxy_id,
                    ip_address=f"192.168.1.{100 + i}",
                    status_code=200 if i < 3 else 429,  # Mix of success and errors
                    latency=50.0 + i * 10,
                    cache_hit=i % 2 == 0,  # Alternate cache hits
                    prompt_hash=f"hash{i:04d}",
                    failure_type="rate_limited" if i >= 3 else None,
                    timestamp=datetime.utcnow() - timedelta(hours=i)
                )
                db.add(log_entry)
            db.commit()
        finally:
            db.close()
    
    def test_get_logs_basic(self):
        """Test basic log retrieval."""
        self.create_test_logs(3)
        
        response = self.client.get("/logs", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "total_count" in data
        assert data["total_count"] >= 3
        assert len(data["logs"]) >= 3
        
        # Check log structure
        log = data["logs"][0]
        required_fields = [
            "id", "timestamp", "proxy_id", "ip_address", "status_code",
            "latency", "cache_hit", "prompt_hash", "failure_type"
        ]
        for field in required_fields:
            assert field in log
    
    def test_get_logs_with_filters(self):
        """Test log retrieval with filters."""
        self.create_test_logs(5)
        
        # Filter by status code
        response = self.client.get("/logs?status_code=429", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        for log in data["logs"]:
            assert log["status_code"] == 429
        
        # Filter by cache hit
        response = self.client.get("/logs?cache_hit=true", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        for log in data["logs"]:
            assert log["cache_hit"] is True
        
        # Filter by failure type
        response = self.client.get("/logs?failure_type=rate_limited", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        for log in data["logs"]:
            assert log["failure_type"] == "rate_limited"
    
    def test_get_logs_date_filtering(self):
        """Test log retrieval with date filters."""
        self.create_test_logs(5)
        
        # Get today's date
        today = datetime.utcnow().strftime("%Y-%m-%d")
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Filter by start date
        response = self.client.get(f"/logs?start_date={yesterday}", headers=self.headers)
        assert response.status_code == 200
        
        # Filter by end date
        response = self.client.get(f"/logs?end_date={today}", headers=self.headers)
        assert response.status_code == 200
        
        # Invalid date format
        response = self.client.get("/logs?start_date=invalid-date", headers=self.headers)
        assert response.status_code == 400
    
    def test_get_logs_pagination(self):
        """Test log pagination."""
        self.create_test_logs(10)
        
        # Get first page
        response = self.client.get("/logs?limit=3&offset=0", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 3
        assert data["limit"] == 3
        assert data["offset"] == 0
        
        # Get second page
        response = self.client.get("/logs?limit=3&offset=3", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 3
    
    def test_export_logs_csv(self):
        """Test CSV export functionality."""
        self.create_test_logs(3)
        
        response = self.client.get("/logs?export=csv", headers=self.headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check CSV content
        csv_content = response.content.decode()
        assert "timestamp,proxy_id,ip_address" in csv_content  # Header
        assert str(self.proxy_id) in csv_content  # Data
    
    def test_export_logs_json(self):
        """Test JSON export functionality."""
        self.create_test_logs(3)
        
        response = self.client.get("/logs?export=json", headers=self.headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")
        
        # Check JSON content
        json_data = json.loads(response.content)
        assert "logs" in json_data
        assert len(json_data["logs"]) >= 3
    
    def test_get_log_stats(self):
        """Test log statistics endpoint."""
        self.create_test_logs(5)
        
        response = self.client.get("/logs/stats", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = [
            "total_requests", "cache_hit_rate", "error_rate", "average_latency",
            "status_code_distribution", "failure_type_distribution", "requests_by_day"
        ]
        for field in required_fields:
            assert field in data
        
        assert data["total_requests"] >= 5
        assert 0 <= data["cache_hit_rate"] <= 100
        assert 0 <= data["error_rate"] <= 100
        assert data["average_latency"] >= 0
    
    def test_get_log_stats_with_proxy_filter(self):
        """Test log statistics with proxy filter."""
        self.create_test_logs(3)
        
        response = self.client.get(f"/logs/stats?proxy_id={self.proxy_id}", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_requests"] >= 3
    
    def test_get_log_stats_empty(self):
        """Test log statistics with no data."""
        response = self.client.get("/logs/stats?days=1", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_requests"] == 0
        assert data["cache_hit_rate"] == 0.0
        assert data["error_rate"] == 0.0
    
    def test_purge_logs(self):
        """Test log purging functionality."""
        self.create_test_logs(5)
        
        # Try without confirmation
        response = self.client.delete("/logs", headers=self.headers)
        assert response.status_code == 400
        assert "confirmation" in response.json()["detail"].lower()
        
        # Purge with confirmation
        response = self.client.delete("/logs?confirm=true", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert "deleted_count" in data
        assert data["deleted_count"] >= 5
        
        # Verify logs were deleted
        response = self.client.get("/logs", headers=self.headers)
        data = response.json()
        assert data["total_count"] == 0
    
    def test_purge_logs_with_filters(self):
        """Test log purging with filters."""
        self.create_test_logs(5)
        
        # Purge logs for specific proxy
        response = self.client.delete(f"/logs?proxy_id={self.proxy_id}&confirm=true", headers=self.headers)
        assert response.status_code == 200
        
        # Purge logs older than 0 days (all logs)
        self.create_test_logs(3)
        response = self.client.delete("/logs?days=0&confirm=true", headers=self.headers)
        assert response.status_code == 200
    
    def test_purge_logs_no_matching_data(self):
        """Test log purging when no data matches criteria."""
        # Test with non-existent proxy (should return 404)
        response = self.client.delete("/logs?proxy_id=99999&confirm=true", headers=self.headers)
        assert response.status_code == 404
        
        # Test with valid filters but no matching data (should return 200 with 0 count)
        response = self.client.delete("/logs?days=1000&confirm=true", headers=self.headers)
        assert response.status_code == 200
        data = response.json()
        assert data["deleted_count"] == 0
    
    def test_logs_user_isolation(self):
        """Test that users can only see their own logs."""
        # Create logs for current user
        self.create_test_logs(3)
        
        # Create another user
        import time
        import random
        timestamp = int(time.time() * 1000)
        random_suffix = random.randint(1000, 9999)
        other_user_data = {"email": f"other-user-{timestamp}-{random_suffix}@example.com", "password": "testpass123"}
        
        register_response = self.client.post("/auth/register", json=other_user_data)
        assert register_response.status_code == 201
        
        login_response = self.client.post("/auth/jwt/login", data={
            "username": other_user_data["email"],
            "password": other_user_data["password"]
        })
        assert login_response.status_code == 200
        other_token = login_response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # Other user should not see our logs
        response = self.client.get("/logs", headers=other_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 0  # No logs for other user


if __name__ == "__main__":
    pytest.main([__file__])