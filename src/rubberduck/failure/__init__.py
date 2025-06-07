import json
import random
import asyncio
import ipaddress
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from fastapi import HTTPException, Request

@dataclass
class FailureConfig:
    """Configuration for failure simulation."""
    
    # Timeout configuration
    timeout_enabled: bool = False
    timeout_seconds: Optional[float] = None  # None = indefinite hang
    timeout_rate: float = 0.0  # 0.0 to 1.0 (probability)
    
    # Error injection configuration
    error_injection_enabled: bool = False
    error_rates: Dict[int, float] = None  # {status_code: rate}
    
    # IP filtering configuration
    ip_filtering_enabled: bool = False
    ip_allowlist: List[str] = None  # CIDR blocks or exact IPs
    ip_blocklist: List[str] = None  # CIDR blocks or exact IPs
    
    # Rate limiting configuration
    rate_limiting_enabled: bool = False
    requests_per_minute: int = 60
    
    def __post_init__(self):
        if self.error_rates is None:
            self.error_rates = {}
        if self.ip_allowlist is None:
            self.ip_allowlist = []
        if self.ip_blocklist is None:
            self.ip_blocklist = []
    
    @classmethod
    def from_json(cls, json_str: Optional[str]) -> 'FailureConfig':
        """Create FailureConfig from JSON string."""
        if not json_str:
            return cls()
        
        try:
            data = json.loads(json_str)
            # Convert error_rates keys back to integers (JSON serializes int keys as strings)
            if 'error_rates' in data and data['error_rates']:
                data['error_rates'] = {int(k): v for k, v in data['error_rates'].items()}
            return cls(**data)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing failure config: {e}")
            return cls()
    
    def to_json(self) -> str:
        """Convert FailureConfig to JSON string."""
        return json.dumps({
            "timeout_enabled": self.timeout_enabled,
            "timeout_seconds": self.timeout_seconds,
            "timeout_rate": self.timeout_rate,
            "error_injection_enabled": self.error_injection_enabled,
            "error_rates": self.error_rates,
            "ip_filtering_enabled": self.ip_filtering_enabled,
            "ip_allowlist": self.ip_allowlist,
            "ip_blocklist": self.ip_blocklist,
            "rate_limiting_enabled": self.rate_limiting_enabled,
            "requests_per_minute": self.requests_per_minute
        })


class FailureSimulator:
    """Handles failure simulation for proxy requests."""
    
    def __init__(self):
        # Track request counts for rate limiting (proxy_id -> {minute: count})
        self.request_counts: Dict[int, Dict[int, int]] = {}
    
    def _is_ip_in_list(self, client_ip: str, ip_list: List[str]) -> bool:
        """Check if client IP is in the given list (supports CIDR and exact matches)."""
        try:
            client_addr = ipaddress.ip_address(client_ip)
            
            for ip_entry in ip_list:
                try:
                    # Try CIDR notation first
                    if '/' in ip_entry:
                        network = ipaddress.ip_network(ip_entry, strict=False)
                        if client_addr in network:
                            return True
                    else:
                        # Exact IP match
                        if client_addr == ipaddress.ip_address(ip_entry):
                            return True
                except ValueError:
                    # Handle wildcards or invalid entries
                    if ip_entry == '*' or ip_entry == client_ip:
                        return True
                        
            return False
            
        except ValueError:
            # Invalid client IP
            return False
    
    def _check_ip_filtering(self, config: FailureConfig, client_ip: str) -> bool:
        """
        Check IP filtering rules.
        
        Returns:
            True if request should be allowed, False if blocked
        """
        if not config.ip_filtering_enabled:
            return True
        
        # If allowlist is specified, IP must be in allowlist
        if config.ip_allowlist:
            if not self._is_ip_in_list(client_ip, config.ip_allowlist):
                return False
        
        # If blocklist is specified, IP must not be in blocklist
        if config.ip_blocklist:
            if self._is_ip_in_list(client_ip, config.ip_blocklist):
                return False
        
        return True
    
    def _check_rate_limiting(self, config: FailureConfig, proxy_id: int) -> bool:
        """
        Check rate limiting.
        
        Returns:
            True if request should be allowed, False if rate limited
        """
        if not config.rate_limiting_enabled:
            return True
        
        import time
        current_minute = int(time.time() // 60)
        
        # Initialize tracking for this proxy if needed
        if proxy_id not in self.request_counts:
            self.request_counts[proxy_id] = {}
        
        # Clean old entries (keep only current minute)
        self.request_counts[proxy_id] = {
            minute: count for minute, count in self.request_counts[proxy_id].items()
            if minute >= current_minute
        }
        
        # Count requests in current minute
        current_count = self.request_counts[proxy_id].get(current_minute, 0)
        
        # Check if rate limit exceeded
        if current_count >= config.requests_per_minute:
            return False
        
        # Increment counter
        self.request_counts[proxy_id][current_minute] = current_count + 1
        return True
    
    async def _simulate_timeout(self, config: FailureConfig) -> None:
        """Simulate timeout by sleeping."""
        if not config.timeout_enabled:
            return
        
        # Check if we should trigger timeout
        if random.random() > config.timeout_rate:
            return
        
        if config.timeout_seconds is None:
            # Indefinite hang - sleep for a very long time
            await asyncio.sleep(3600)  # 1 hour
        else:
            # Fixed delay
            await asyncio.sleep(config.timeout_seconds)
    
    def _simulate_error(self, config: FailureConfig) -> Optional[HTTPException]:
        """Simulate error injection."""
        if not config.error_injection_enabled:
            return None
        
        # Generate a single random value to check against all error rates
        # This ensures we get proper probability distribution
        random_value = random.random()
        
        # Calculate cumulative probability and check each error rate
        cumulative_prob = 0.0
        for status_code, rate in config.error_rates.items():
            cumulative_prob += rate
            if random_value <= cumulative_prob:
                # Simulate this error
                error_messages = {
                    400: "Bad Request - Simulated Error",
                    401: "Unauthorized - Simulated Error",
                    403: "Forbidden - Simulated Error",
                    404: "Not Found - Simulated Error",
                    429: "Too Many Requests - Simulated Error",
                    500: "Internal Server Error - Simulated Error",
                    502: "Bad Gateway - Simulated Error",
                    503: "Service Unavailable - Simulated Error",
                    504: "Gateway Timeout - Simulated Error"
                }
                
                message = error_messages.get(status_code, f"Simulated Error {status_code}")
                return HTTPException(status_code=status_code, detail=message)
        
        return None
    
    async def process_request(
        self, 
        config: FailureConfig, 
        proxy_id: int, 
        request: Request
    ) -> Optional[HTTPException]:
        """
        Process a request through failure simulation.
        
        Args:
            config: Failure simulation configuration
            proxy_id: Proxy instance ID
            request: Incoming request
            
        Returns:
            HTTPException if request should fail, None if should proceed
            
        Raises:
            HTTPException: For simulated failures
        """
        # Get client IP
        client_ip = request.client.host if request.client else "127.0.0.1"
        
        # Check IP filtering
        if not self._check_ip_filtering(config, client_ip):
            return HTTPException(
                status_code=403,
                detail=f"IP {client_ip} is blocked by proxy configuration"
            )
        
        # Check rate limiting
        if not self._check_rate_limiting(config, proxy_id):
            return HTTPException(
                status_code=429,
                detail="Rate limit exceeded"
            )
        
        # Simulate timeout (this will delay the response)
        await self._simulate_timeout(config)
        
        # Simulate error injection
        error = self._simulate_error(config)
        if error:
            return error
        
        return None


# Global failure simulator instance
failure_simulator = FailureSimulator()


def create_default_failure_config() -> FailureConfig:
    """Create a default failure configuration."""
    return FailureConfig(
        timeout_enabled=False,
        timeout_seconds=5.0,
        timeout_rate=0.0,
        error_injection_enabled=False,
        error_rates={
            429: 0.0,  # Too Many Requests
            500: 0.0,  # Internal Server Error
            502: 0.0,  # Bad Gateway
            503: 0.0,  # Service Unavailable
        },
        ip_filtering_enabled=False,
        ip_allowlist=[],
        ip_blocklist=[],
        rate_limiting_enabled=False,
        requests_per_minute=60
    )