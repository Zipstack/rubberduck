# Advanced Topics

Explore advanced configuration options, deployment strategies, and optimization techniques for Rubberduck. This guide covers topics for experienced users looking to maximize the capabilities of their LLM proxy infrastructure.

## Failure Simulation

Rubberduck's failure simulation capabilities allow you to test the resilience of your applications against various failure scenarios. This feature is essential for building robust LLM-dependent applications.

### Timeout Simulation

**Configuration Options:**
- **Delay Injection**: Add artificial delays to responses
- **Timeout Thresholds**: Configure request timeout limits
- **Hang Simulation**: Simulate indefinite request hanging

**Implementation Example:**
```json
{
  "timeout_config": {
    "enabled": true,
    "delay_ms": 5000,
    "timeout_rate": 0.1,
    "hang_rate": 0.02
  }
}
```

**Use Cases:**
- Test application timeout handling
- Validate retry logic implementation
- Simulate network latency issues
- Stress test connection pooling

### HTTP Error Injection

**Supported Error Types:**
- **400 Bad Request**: Invalid request format simulation
- **401 Unauthorized**: Authentication failure testing
- **429 Rate Limited**: Rate limiting behavior testing
- **500 Internal Server Error**: Provider outage simulation
- **503 Service Unavailable**: Temporary service disruption

**Configuration per Error Type:**
```json
{
  "error_injection": {
    "400_rate": 0.05,
    "401_rate": 0.02,
    "429_rate": 0.15,
    "500_rate": 0.03,
    "503_rate": 0.01
  }
}
```

**Testing Scenarios:**
- API key rotation testing
- Rate limit handling validation
- Circuit breaker implementation testing
- Graceful degradation verification

### Rate Limiting Simulation

**Rate Limit Configuration:**
```json
{
  "rate_limiting": {
    "requests_per_minute": 60,
    "burst_allowance": 10,
    "rate_limit_response": {
      "status_code": 429,
      "headers": {
        "Retry-After": "60",
        "X-RateLimit-Remaining": "0"
      }
    }
  }
}
```

**Advanced Features:**
- **Sliding Window**: More accurate rate limiting
- **Per-Client Limits**: IP-based or header-based limiting
- **Burst Handling**: Allow temporary spikes within limits
- **Custom Responses**: Configure rate limit response format

### IP Filtering and Access Control

**Allow/Block Lists:**
```json
{
  "ip_filtering": {
    "mode": "allowlist",
    "allowed_ips": [
      "192.168.1.0/24",
      "10.0.0.0/8",
      "172.16.0.0/12"
    ],
    "blocked_ips": [
      "192.168.1.100",
      "10.0.0.50"
    ]
  }
}
```

**Pattern Matching:**
- **CIDR Notation**: Subnet-based filtering
- **Wildcard Patterns**: Flexible IP matching
- **Geographic Filtering**: Country/region-based access
- **Dynamic Updates**: Runtime filter modifications

## Caching Strategies

### Cache Key Normalization

**Request Normalization:**
```python
def normalize_request(request_data):
    """Normalize request for consistent caching."""
    normalized = {
        "model": request_data.get("model"),
        "messages": request_data.get("messages", []),
        "temperature": round(request_data.get("temperature", 0), 2),
        "max_tokens": request_data.get("max_tokens")
    }
    
    # Remove non-deterministic fields
    normalized.pop("stream", None)
    normalized.pop("user", None)
    
    return json.dumps(normalized, sort_keys=True)
```

**Cache Key Generation:**
```python
import hashlib

def generate_cache_key(normalized_request):
    """Generate SHA-256 cache key."""
    return hashlib.sha256(
        normalized_request.encode('utf-8')
    ).hexdigest()
```

### Cache TTL Optimization

**Dynamic TTL Configuration:**
```json
{
  "cache_ttl": {
    "default": 3600,
    "by_model": {
      "gpt-4": 7200,
      "claude-3-sonnet": 3600,
      "gpt-3.5-turbo": 1800
    },
    "by_request_type": {
      "completion": 3600,
      "chat": 1800,
      "embedding": 86400
    }
  }
}
```

**Adaptive TTL:**
- **Usage-Based**: Longer TTL for frequently accessed content
- **Model-Specific**: Different TTL for different model types
- **Content-Based**: TTL based on response characteristics
- **Time-Based**: Shorter TTL during peak hours

### Cache Invalidation Strategies

**Manual Invalidation:**
```python
# Invalidate specific cache entry
cache.invalidate(cache_key)

# Invalidate by pattern
cache.invalidate_pattern("gpt-4:*")

# Clear entire proxy cache
cache.clear_all()
```

**Automatic Invalidation:**
- **TTL Expiration**: Natural cache expiration
- **Model Updates**: Invalidate on provider model changes
- **Error Thresholds**: Clear cache on high error rates
- **Memory Pressure**: LRU eviction policies

## Request Processing Pipeline

### Custom Middleware Development

**Middleware Interface:**
```python
class CustomMiddleware:
    def __init__(self, config):
        self.config = config
    
    async def process_request(self, request):
        """Process incoming request."""
        # Add custom headers
        request.headers["X-Custom-Header"] = "value"
        return request
    
    async def process_response(self, response):
        """Process outgoing response."""
        # Add response timing
        response.headers["X-Processing-Time"] = self.get_processing_time()
        return response
```

**Pipeline Configuration:**
```json
{
  "middleware_pipeline": [
    "authentication",
    "rate_limiting", 
    "request_validation",
    "caching",
    "failure_simulation",
    "provider_forwarding",
    "response_processing",
    "logging"
  ]
}
```

### Request Transformation

**Header Manipulation:**
```python
def transform_headers(headers, provider):
    """Transform headers for provider compatibility."""
    if provider == "azure-openai":
        headers["api-version"] = "2024-02-01"
    elif provider == "anthropic":
        headers["anthropic-version"] = "2023-06-01"
    
    return headers
```

**Payload Transformation:**
```python
def transform_payload(payload, provider, model):
    """Transform request payload for provider format."""
    if provider == "anthropic" and "messages" in payload:
        # Convert OpenAI format to Anthropic format
        return convert_openai_to_anthropic(payload)
    
    return payload
```

### Response Processing

**Response Normalization:**
```python
def normalize_response(response, provider):
    """Normalize provider response to common format."""
    if provider == "anthropic":
        return convert_anthropic_to_openai(response)
    elif provider == "azure-openai":
        return convert_azure_to_openai(response)
    
    return response
```

**Error Handling:**
```python
def handle_provider_error(error, provider):
    """Convert provider-specific errors to standard format."""
    error_mappings = {
        "anthropic": {
            "rate_limit_error": {"status": 429, "type": "rate_limit"},
            "invalid_request_error": {"status": 400, "type": "invalid_request"}
        }
    }
    
    return error_mappings.get(provider, {}).get(error.type, error)
```

## Deployment Architectures

### Single Instance Deployment

**Basic Setup:**
```yaml
# docker-compose.yml
version: '3.8'
services:
  rubberduck:
    image: rubberduck:latest
    ports:
      - "9000:9000"
      - "5173:5173"
    environment:
      - DATABASE_URL=sqlite:///app/data/rubberduck.db
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

**Advantages:**
- Simple deployment and management
- Minimal resource requirements
- Quick setup and testing
- Suitable for development environments

**Limitations:**
- Single point of failure
- Limited scalability
- Resource constraints
- No high availability

### High Availability Deployment

**Load Balanced Setup:**
```yaml
# docker-compose.ha.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - rubberduck-1
      - rubberduck-2
  
  rubberduck-1:
    image: rubberduck:latest
    environment:
      - NODE_ID=node-1
      - DATABASE_URL=postgresql://user:pass@postgres:5432/rubberduck
      - REDIS_URL=redis://redis:6379
  
  rubberduck-2:
    image: rubberduck:latest
    environment:
      - NODE_ID=node-2
      - DATABASE_URL=postgresql://user:pass@postgres:5432/rubberduck
      - REDIS_URL=redis://redis:6379
  
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: rubberduck
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**Load Balancer Configuration:**
```nginx
upstream rubberduck_backend {
    server rubberduck-1:9000;
    server rubberduck-2:9000;
}

server {
    listen 80;
    location / {
        proxy_pass http://rubberduck_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Cloud Deployment

**AWS ECS Configuration:**
```json
{
  "family": "rubberduck",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "rubberduck",
      "image": "your-account.dkr.ecr.region.amazonaws.com/rubberduck:latest",
      "portMappings": [
        {"containerPort": 9000, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "DATABASE_URL", "value": "postgresql://..."},
        {"name": "REDIS_URL", "value": "redis://..."}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/rubberduck",
          "awslogs-region": "us-east-1"
        }
      }
    }
  ]
}
```

**Kubernetes Deployment:**
```yaml
# k8s-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rubberduck
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rubberduck
  template:
    metadata:
      labels:
        app: rubberduck
    spec:
      containers:
      - name: rubberduck
        image: rubberduck:latest
        ports:
        - containerPort: 9000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: rubberduck-secrets
              key: database-url
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: rubberduck-service
spec:
  selector:
    app: rubberduck
  ports:
  - port: 80
    targetPort: 9000
  type: LoadBalancer
```

## Performance Optimization

### Database Optimization

**Connection Pooling:**
```python
# Database configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

**Index Optimization:**
```sql
-- Optimize log queries
CREATE INDEX idx_logs_timestamp ON request_logs(timestamp);
CREATE INDEX idx_logs_proxy_id ON request_logs(proxy_id);
CREATE INDEX idx_logs_status ON request_logs(status_code);

-- Optimize cache queries
CREATE INDEX idx_cache_key ON cache_entries(cache_key);
CREATE INDEX idx_cache_expiry ON cache_entries(expires_at);
```

**Query Optimization:**
```python
# Efficient log retrieval
def get_recent_logs(proxy_id, limit=100):
    return session.query(RequestLog)\
        .filter(RequestLog.proxy_id == proxy_id)\
        .order_by(RequestLog.timestamp.desc())\
        .limit(limit)\
        .all()
```

### Memory Management

**Cache Size Limits:**
```json
{
  "memory_limits": {
    "cache_max_size": "1GB",
    "cache_max_entries": 10000,
    "log_buffer_size": "100MB",
    "response_buffer_size": "10MB"
  }
}
```

**Garbage Collection:**
```python
import gc

class MemoryManager:
    def __init__(self):
        self.gc_threshold = 1000000  # 1MB
        
    def check_memory_usage(self):
        if self.get_memory_usage() > self.gc_threshold:
            gc.collect()
    
    def cleanup_expired_cache(self):
        expired_entries = cache.get_expired_entries()
        for entry in expired_entries:
            cache.delete(entry.key)
```

### Network Optimization

**Connection Pooling:**
```python
import aiohttp

class HTTPClientManager:
    def __init__(self):
        self.connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            keepalive_timeout=300,
            enable_cleanup_closed=True
        )
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=aiohttp.ClientTimeout(total=30)
        )
```

**Request Batching:**
```python
async def batch_requests(requests, batch_size=10):
    """Process requests in batches to optimize throughput."""
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i + batch_size]
        tasks = [process_request(req) for req in batch]
        await asyncio.gather(*tasks)
```

## Security Hardening

### TLS/SSL Configuration

**Nginx TLS Setup:**
```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/ssl/certs/rubberduck.crt;
    ssl_certificate_key /etc/ssl/private/rubberduck.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS;
    ssl_prefer_server_ciphers off;
    
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
}
```

**Certificate Management:**
```bash
# Let's Encrypt with Certbot
certbot --nginx -d your-domain.com

# Automatic renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

### Authentication Hardening

**Session Security:**
```python
SESSION_CONFIG = {
    "secure": True,
    "httponly": True,
    "samesite": "strict",
    "max_age": 3600,
    "secret_key": os.urandom(32)
}
```

**Password Policies:**
```python
import re

def validate_password(password):
    """Enforce strong password policy."""
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain uppercase letters"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain lowercase letters"
    
    if not re.search(r"\d", password):
        return False, "Password must contain numbers"
    
    if not re.search(r"[!@#$%^&*]", password):
        return False, "Password must contain special characters"
    
    return True, "Password meets requirements"
```

### Input Validation

**Request Validation:**
```python
from pydantic import BaseModel, validator

class ChatRequest(BaseModel):
    model: str
    messages: List[dict]
    temperature: float = 0.7
    max_tokens: int = 1000
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if not 1 <= v <= 8192:
            raise ValueError('Max tokens must be between 1 and 8192')
        return v
```

**SQL Injection Prevention:**
```python
# Use parameterized queries
def get_user_logs(user_id, start_date, end_date):
    query = """
        SELECT * FROM request_logs 
        WHERE user_id = %s 
        AND timestamp BETWEEN %s AND %s
    """
    return db.execute(query, (user_id, start_date, end_date))
```

## Monitoring and Observability

### Custom Metrics

**Prometheus Metrics:**
```python
from prometheus_client import Counter, Histogram, Gauge

# Define custom metrics
request_count = Counter('rubberduck_requests_total', 
                       'Total requests processed', 
                       ['proxy_id', 'provider', 'status'])

request_duration = Histogram('rubberduck_request_duration_seconds',
                           'Request duration in seconds',
                           ['proxy_id', 'provider'])

active_proxies = Gauge('rubberduck_active_proxies',
                      'Number of active proxy instances')

# Use in request processing
def process_request(proxy_id, provider):
    start_time = time.time()
    try:
        # Process request
        result = handle_request()
        request_count.labels(proxy_id, provider, 'success').inc()
        return result
    except Exception as e:
        request_count.labels(proxy_id, provider, 'error').inc()
        raise
    finally:
        duration = time.time() - start_time
        request_duration.labels(proxy_id, provider).observe(duration)
```

**Health Check Endpoints:**
```python
@app.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "timestamp": time.time()}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies."""
    checks = {
        "database": check_database_connection(),
        "redis": check_redis_connection(),
        "providers": check_provider_connectivity(),
        "disk_space": check_disk_space(),
        "memory": check_memory_usage()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    return {"status": overall_status, "checks": checks}
```

### Distributed Tracing

**OpenTelemetry Integration:**
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Trace request processing
@tracer.start_as_current_span("process_llm_request")
def process_llm_request(request):
    span = trace.get_current_span()
    span.set_attributes({
        "llm.provider": request.provider,
        "llm.model": request.model,
        "request.size": len(request.payload)
    })
    
    # Process request
    result = forward_to_provider(request)
    
    span.set_attributes({
        "response.status": result.status_code,
        "response.size": len(result.content)
    })
    
    return result
```

## Backup and Recovery

### Automated Backup

**Database Backup:**
```bash
#!/bin/bash
# backup_database.sh

DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/backups/rubberduck"
DB_FILE="/app/data/rubberduck.db"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup SQLite database
sqlite3 $DB_FILE ".backup $BACKUP_DIR/rubberduck_$DATE.db"

# Compress backup
gzip "$BACKUP_DIR/rubberduck_$DATE.db"

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "rubberduck_*.db.gz" -mtime +30 -delete

echo "Backup completed: rubberduck_$DATE.db.gz"
```

**Configuration Backup:**
```python
import json
import os
from datetime import datetime

def backup_configuration():
    """Backup proxy configurations and settings."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_data = {
        "timestamp": timestamp,
        "proxies": export_proxy_configurations(),
        "settings": export_global_settings(),
        "users": export_user_data()
    }
    
    backup_file = f"/backups/config_backup_{timestamp}.json"
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    return backup_file
```

### Disaster Recovery

**Recovery Procedures:**
```bash
#!/bin/bash
# restore_from_backup.sh

BACKUP_FILE=$1
RESTORE_DIR="/app/data"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# Stop services
docker-compose down

# Restore database
gunzip -c "$BACKUP_FILE" > "$RESTORE_DIR/rubberduck.db"

# Restore configuration
python restore_configuration.py "$BACKUP_FILE"

# Start services
docker-compose up -d

echo "Restore completed from $BACKUP_FILE"
```

**Data Migration:**
```python
def migrate_data(source_db, target_db):
    """Migrate data between database versions."""
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)
    
    # Migrate tables
    tables = ['users', 'proxies', 'request_logs', 'cache_entries']
    
    for table in tables:
        # Read from source
        source_data = source_conn.execute(f"SELECT * FROM {table}").fetchall()
        
        # Transform data if needed
        transformed_data = transform_table_data(table, source_data)
        
        # Insert into target
        insert_query = generate_insert_query(table, transformed_data)
        target_conn.executemany(insert_query, transformed_data)
    
    target_conn.commit()
    source_conn.close()
    target_conn.close()
```

## Next Steps

After implementing advanced configurations:

1. **Monitor Performance**: Use metrics and observability tools to track system performance
2. **Optimize Resources**: Fine-tune configuration based on usage patterns
3. **Plan for Scale**: Prepare infrastructure for growth and increased load
4. **Security Review**: Regularly audit security configurations and practices
5. **Disaster Testing**: Regularly test backup and recovery procedures

---

These advanced topics provide the foundation for building a robust, scalable, and secure LLM proxy infrastructure with Rubberduck. Implement these features gradually based on your specific requirements and use cases.