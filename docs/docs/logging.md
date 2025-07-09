# Logging & Monitoring

Rubberduck provides comprehensive logging and monitoring capabilities to track proxy performance, analyze usage patterns, and troubleshoot issues. Learn how to effectively monitor your LLM proxy infrastructure.

## Overview

The logging system captures detailed information about every request processed by your proxies, providing insights into:

- **Request Patterns**: API usage trends and traffic patterns
- **Performance Metrics**: Latency, throughput, and response times
- **Error Analysis**: Failure rates and error categorization
- **Cache Effectiveness**: Hit rates and performance improvements
- **Provider Behavior**: Upstream service performance

## Accessing Logs

### Logs Dashboard

Navigate to the **Logs** page from the main sidebar to access the centralized logging dashboard.

The logs dashboard provides:
- **Real-time log streaming** with automatic updates
- **Advanced filtering** by proxy, status, date range
- **Search functionality** across log messages
- **Export capabilities** for further analysis

### Log Entry Structure

Each log entry contains comprehensive request information:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "proxy_id": "openai-proxy-8001",
  "proxy_name": "Production OpenAI",
  "provider": "openai",
  "method": "POST",
  "path": "/v1/chat/completions",
  "status_code": 200,
  "latency_ms": 1234.56,
  "request_size_bytes": 256,
  "response_size_bytes": 1024,
  "cache_hit": true,
  "user_agent": "openai-python/1.3.0",
  "client_ip": "192.168.1.100",
  "model": "gpt-4",
  "tokens_used": 150,
  "error_message": null
}
```

## Filtering and Searching

### Advanced Filters

**Time Range Filtering:**
- Last hour, day, week, month
- Custom date/time ranges
- Real-time vs. historical data

**Proxy Filtering:**
- Filter by specific proxy instances
- Group by provider type
- Multi-proxy selection

**Status Code Filtering:**
- Successful requests (2xx)
- Client errors (4xx)
- Server errors (5xx)
- Specific status codes

**Performance Filtering:**
- Latency thresholds
- Cache hit/miss status
- Request size ranges

### Search Functionality

**Text Search:**
- Search across log messages
- Model name filtering
- User agent patterns
- IP address lookup

**Advanced Query Syntax:**
```
# Search for specific model
model:gpt-4

# Find high latency requests
latency:>2000

# Cache miss requests
cache:false

# Error messages containing timeout
error:timeout

# Combine filters
model:claude-3 AND status:429 AND latency:>1000
```

## Real-time Monitoring

### Live Log Stream

The logs dashboard provides real-time updates with:
- **Auto-refresh**: Configurable refresh intervals (5s, 10s, 30s, 1m)
- **Live indicators**: New log entries highlighted
- **Scroll behavior**: Automatic scrolling for latest entries
- **Pause/resume**: Control live streaming

### Dashboard Metrics

**Real-time Statistics:**
- Requests per minute (RPM)
- Average response latency
- Error rate percentage
- Cache hit rate
- Active proxy count

**Visual Indicators:**
- Color-coded status (green=healthy, yellow=warning, red=error)
- Trend arrows (increasing/decreasing metrics)
- Threshold alerts for abnormal behavior

## Performance Analytics

### Latency Analysis

**Response Time Metrics:**
- Average, median, 95th, 99th percentiles
- Latency distribution histograms
- Trend analysis over time
- Provider comparison

**Performance Insights:**
```
Proxy: OpenAI Production (localhost:8001)
┌─────────────────┬──────────┐
│ Metric          │ Value    │
├─────────────────┼──────────┤
│ Avg Latency     │ 1,234ms  │
│ P95 Latency     │ 2,456ms  │
│ P99 Latency     │ 3,789ms  │
│ Cache Hit Rate  │ 78.3%    │
│ Error Rate      │ 2.1%     │
└─────────────────┴──────────┘
```

### Throughput Monitoring

**Traffic Patterns:**
- Requests per minute/hour/day
- Peak usage identification
- Traffic distribution across proxies
- Seasonal patterns and trends

**Capacity Planning:**
- Historical usage growth
- Projected capacity needs
- Resource utilization trends
- Scaling recommendations

### Cache Performance

**Cache Effectiveness:**
- Hit rate percentages by proxy
- Cache size and storage usage
- Most/least cached content patterns
- Cache invalidation frequency

**Optimization Insights:**
- Identify cacheable request patterns
- TTL optimization recommendations
- Storage efficiency metrics
- Performance improvement quantification

## Error Analysis & Troubleshooting

### Error Categorization

**HTTP Status Codes:**
- **2xx Success**: Normal operations
- **4xx Client Errors**: Authentication, rate limits, invalid requests
- **5xx Server Errors**: Provider issues, proxy failures
- **Timeouts**: Network or processing delays

**Provider-Specific Errors:**
- Rate limiting patterns by provider
- Authentication failure analysis
- Model availability issues
- Regional service disruptions

### Error Pattern Analysis

**Common Error Patterns:**
```
Top Errors (Last 24 Hours):
1. 429 Rate Limit Exceeded     - 45 occurrences
2. 401 Authentication Failed   - 12 occurrences  
3. 500 Internal Server Error   - 8 occurrences
4. Timeout                     - 6 occurrences
5. 404 Model Not Found        - 3 occurrences
```

**Diagnostic Information:**
- Error frequency and timing
- Affected proxy instances
- Client IP patterns
- Request characteristics leading to errors

### Troubleshooting Workflow

**1. Identify Issues:**
- Monitor error rate spikes
- Check latency degradation
- Observe cache hit rate drops
- Review unusual traffic patterns

**2. Analyze Root Causes:**
- Filter logs by error type
- Examine request patterns
- Check provider status
- Review proxy configuration

**3. Implement Solutions:**
- Adjust rate limiting
- Update authentication
- Modify cache settings
- Scale proxy instances

## Export and Integration

### Log Export Options

**Export Formats:**
- **JSON**: Complete log data with all fields
- **CSV**: Tabular format for spreadsheet analysis
- **JSONL**: Line-delimited JSON for streaming
- **Raw Text**: Human-readable format

**Export Filtering:**
- Apply same filters as dashboard
- Date range selection
- Specific proxy inclusion
- Field selection for reduced size

**Example Export Commands:**
```bash
# Export last 24 hours of OpenAI proxy logs
curl "http://localhost:9000/api/logs/export?proxy=openai-8001&format=json&hours=24" > openai_logs.json

# Export errors only
curl "http://localhost:9000/api/logs/export?status=4xx,5xx&format=csv" > errors.csv

# Export cache miss events
curl "http://localhost:9000/api/logs/export?cache=false&format=jsonl" > cache_misses.jsonl
```

### External Integrations

**Monitoring Systems:**
- **Prometheus**: Metrics endpoint for time-series data
- **Grafana**: Dashboard creation and alerting
- **DataDog**: Cloud-based monitoring integration
- **New Relic**: Application performance monitoring

**Log Aggregation:**
- **ELK Stack**: Elasticsearch, Logstash, Kibana integration
- **Splunk**: Enterprise log analysis
- **CloudWatch**: AWS native logging
- **Google Cloud Logging**: GCP integration

**Sample Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rubberduck'
    static_configs:
      - targets: ['localhost:9000']
    metrics_path: '/api/metrics'
    scrape_interval: 15s
```

## Alerting and Notifications

### Built-in Alerting

**Threshold-Based Alerts:**
- High error rate (greater than 5% failures)
- Elevated latency (greater than 3s average)
- Low cache hit rate (less than 50%)
- Proxy downtime detection

**Alert Channels:**
- Email notifications
- Webhook integrations
- Slack/Teams messaging
- SMS alerts (via third-party)

### Custom Alert Rules

**Configuration Example:**
```json
{
  "alerts": [
    {
      "name": "High Error Rate",
      "condition": "error_rate > 0.05",
      "window": "5m",
      "channels": ["email", "slack"]
    },
    {
      "name": "Latency Spike",
      "condition": "avg_latency > 3000",
      "window": "2m", 
      "channels": ["webhook"]
    }
  ]
}
```

**Alert Management:**
- Alert history and acknowledgment
- Escalation policies
- Maintenance windows
- Alert suppression rules

## Log Retention and Storage

### Retention Policies

**Default Retention:**
- **Debug Logs**: 7 days
- **Request Logs**: 30 days  
- **Error Logs**: 90 days
- **Summary Metrics**: 1 year

**Configurable Retention:**
```json
{
  "log_retention": {
    "debug": "7d",
    "requests": "30d", 
    "errors": "90d",
    "metrics": "365d"
  }
}
```

### Storage Management

**Storage Optimization:**
- Automatic log rotation
- Compression for old logs
- Archival to cold storage
- Cleanup of expired data

**Disk Usage Monitoring:**
- Current storage utilization
- Growth rate tracking
- Capacity planning alerts
- Cleanup recommendations

## Performance Metrics API

### Metrics Endpoints

**Real-time Metrics:**
```bash
# Current proxy status
GET /api/metrics/proxies

# Live performance data
GET /api/metrics/performance?window=5m

# Error rate summary
GET /api/metrics/errors?period=1h
```

**Historical Data:**
```bash
# Latency trends
GET /api/metrics/latency?start=2024-01-01&end=2024-01-31

# Traffic patterns
GET /api/metrics/traffic?groupBy=hour&days=7

# Cache performance
GET /api/metrics/cache?proxy=openai-8001&hours=24
```

### Custom Dashboards

**Dashboard Configuration:**
```json
{
  "dashboard": {
    "name": "OpenAI Performance",
    "widgets": [
      {
        "type": "metric",
        "title": "Response Time",
        "query": "avg_latency",
        "proxy": "openai-8001"
      },
      {
        "type": "chart",
        "title": "Request Volume",
        "query": "request_count",
        "groupBy": "5m"
      }
    ]
  }
}
```

## Best Practices

### Monitoring Strategy

**Proactive Monitoring:**
- Set up alerts before issues occur
- Monitor trends, not just current state
- Track both technical and business metrics
- Regular review of alert thresholds

**Key Metrics to Track:**
1. **Availability**: Proxy uptime and health
2. **Performance**: Latency and throughput
3. **Quality**: Error rates and success ratios
4. **Efficiency**: Cache hit rates and cost optimization
5. **Usage**: Traffic patterns and growth trends

### Log Analysis Workflow

**Daily Monitoring:**
- Check overnight alerts and issues
- Review performance degradations
- Analyze error patterns
- Verify cache effectiveness

**Weekly Reviews:**
- Trend analysis and capacity planning
- Provider performance comparison
- Alert threshold optimization
- Cost and usage optimization

**Monthly Reports:**
- Service level objective (SLO) compliance
- Performance benchmarking
- Capacity planning updates
- Cost analysis and optimization

### Security and Privacy

**Sensitive Data Handling:**
- Never log API keys or credentials
- Mask PII in request/response data
- Secure log storage and access
- Audit log access patterns

**Compliance Considerations:**
- GDPR data retention requirements
- HIPAA logging restrictions
- SOX audit trail requirements
- Industry-specific regulations

## Troubleshooting Common Issues

### High Latency Diagnosis

**Investigation Steps:**
1. **Identify affected proxies**: Filter logs by latency thresholds
2. **Check provider performance**: Compare direct vs. proxy latency
3. **Analyze request patterns**: Look for resource-heavy requests
4. **Review cache behavior**: Check cache hit/miss patterns
5. **Network diagnostics**: Verify connectivity and routing

**Common Causes:**
- Provider API slowdowns
- Cache inefficiency
- Resource contention
- Network connectivity issues

### Error Rate Spikes

**Diagnostic Approach:**
1. **Categorize errors**: Group by status codes and patterns
2. **Timeline analysis**: Identify when issues started
3. **Client analysis**: Check if specific clients affected
4. **Provider status**: Verify upstream service health
5. **Configuration review**: Check recent changes

**Resolution Strategies:**
- Adjust rate limiting configuration
- Update authentication credentials
- Implement retry logic
- Switch to backup providers

### Cache Performance Issues

**Performance Indicators:**
- Decreasing cache hit rates
- Increased average latency
- Higher provider costs
- Unusual cache storage growth

**Optimization Actions:**
- Review cache TTL settings
- Analyze request normalization
- Check cache eviction policies
- Monitor cache storage limits

## Next Steps

After setting up comprehensive monitoring:

1. **Configure automated alerts** - Set up proactive notifications
2. **Implement custom dashboards** - Create tailored monitoring views
3. **Set up external integrations** - Connect to existing monitoring tools
4. **Establish SLOs and SLIs** - Define service level objectives

---

Effective logging and monitoring are essential for maintaining reliable LLM proxy services. Use these tools to ensure optimal performance and quick issue resolution.