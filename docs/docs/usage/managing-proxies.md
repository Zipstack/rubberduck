# Managing Proxies

Learn how to control, configure, and monitor your LLM proxy instances in Rubberduck.

## Proxy Lifecycle Management

### Starting Proxies

**From the Proxies Page:**
1. Navigate to the **Proxies** page
2. Find your proxy in the list
3. Click the **"Start"** button (green play icon)

**Automatic Startup:**
- Running proxies are automatically restarted when Rubberduck restarts
- Proxy states are saved and restored from the database

**Startup Process:**
- Port binding and availability check
- Provider connection validation
- Cache initialization
- Logging system activation

### Stopping Proxies

**Graceful Stop:**
- Click the **"Stop"** button (red stop icon)
- Waits for in-flight requests to complete
- Safely closes all connections
- Preserves cache data

**Force Stop:**
- Available through the **"Actions"** menu
- Immediately terminates the proxy
- Use only when graceful stop fails

### Proxy Status Indicators

**Running** (Green dot)
- Proxy is active and accepting requests
- Port is bound and listening
- Ready to forward requests to providers

**Stopped** (Gray dot)  
- Proxy is inactive
- Port is released
- No requests are being processed

**Starting** (Yellow dot)
- Proxy is in the process of starting up
- Port binding in progress
- Temporary state during startup

**Error** (Red dot)
- Proxy failed to start or encountered an error
- Check logs for specific error messages
- Common causes: port conflicts, provider issues

## Configuration Management

### Basic Configuration

**Edit Proxy Settings:**
1. Click the **"Configure"** button (gear icon) on any proxy
2. Modify available settings:
   - Proxy name and description
   - Port assignment
   - Provider-specific settings

**Configuration Options:**
- **Name**: Update the display name
- **Description**: Modify the proxy description
- **Port**: Change the listening port (requires restart)
- **Tags**: Add organizational tags

### Advanced Configuration

**Failure Simulation:**
Access through the **"Actions"** menu → **"Failure Settings"**

**Timeout Configuration:**
- Set custom timeout values
- Configure delay injection
- Enable indefinite hang simulation

**Error Injection:**
- Configure HTTP error codes (400, 429, 500)
- Set individual failure rates per error type
- Enable/disable error simulation

**Rate Limiting:**
- Set requests per minute limits
- Configure burst allowances
- Customize rate limit responses

**IP Filtering:**
- Configure allow/block lists
- Support for CIDR notation
- Wildcard pattern matching

**Response Delay:**
- Simulate realistic LLM response times for cached responses
- Configure minimum and maximum delay ranges (0-30 seconds)
- Cache-only mode: Apply delays only to cache hits (recommended)
- All-requests mode: Apply delays to both cached and non-cached responses
- Non-blocking implementation maintains system performance

### Cache Management

**Cache Settings:**
- View cache hit/miss statistics
- Configure cache TTL settings
- Enable/disable caching per proxy

**Cache Operations:**
- **Invalidate Cache**: Clear all cached responses for this proxy
- **Cache Statistics**: View detailed cache performance metrics
- **Cache Size**: Monitor cache storage usage

**Cache Invalidation:**
1. Go to the **"Actions"** menu
2. Select **"Clear Cache"**
3. Confirm the operation
4. Cache is immediately cleared for this proxy only

## Monitoring and Analytics

### Real-time Metrics

**Per-Proxy Statistics:**
- Current requests per minute (RPM)
- Average response latency
- Cache hit rate percentage
- Error rate tracking

**Live Updates:**
- Metrics refresh automatically every few seconds
- Real-time status changes
- Live request counting

### Request Monitoring

**Recent Activity:**
- Last 10 requests shown per proxy
- Request timestamps and response codes
- Quick status overview

**Detailed Logs:**
- Access full request logs via the **Logs** page
- Filter by specific proxy
- Export logs for analysis

### Performance Analytics

**Response Time Tracking:**
- Average, minimum, and maximum latency
- Percentile breakdowns (p95, p99)
- Latency trends over time

**Throughput Monitoring:**
- Requests per minute trends
- Peak usage identification
- Capacity planning insights

**Error Analysis:**
- Error rate trends
- Error type breakdown
- Failure pattern identification

## Bulk Operations

### Multi-Proxy Management

**Selecting Multiple Proxies:**
- Use checkboxes to select multiple proxies
- Bulk action menu appears when proxies are selected

**Bulk Actions:**
- **Start All**: Start multiple stopped proxies
- **Stop All**: Gracefully stop multiple running proxies
- **Restart All**: Restart selected proxies
- **Clear Caches**: Invalidate caches for selected proxies

### Filtering and Search

**Search Functionality:**
- Search proxies by name or description
- Real-time filtering as you type
- Case-insensitive matching

**Status Filtering:**
- Filter by proxy status (All, Running, Stopped)
- Quick status overview
- Simplified management view

**Provider Filtering:**
- Filter by provider type
- Group similar proxies
- Provider-specific management

## Proxy Actions Menu

### Available Actions

**Configuration Actions:**
- **Configure**: Edit basic proxy settings
- **Failure Settings**: Configure failure simulation
- **Advanced Settings**: Access detailed configuration

**Management Actions:**
- **Restart**: Restart the proxy instance
- **Force Stop**: Immediately terminate proxy
- **Duplicate**: Create a copy with similar settings

**Data Actions:**
- **Clear Cache**: Invalidate all cached responses
- **Export Logs**: Download logs for this proxy
- **View Statistics**: Detailed analytics view

**Maintenance Actions:**
- **Health Check**: Test provider connectivity
- **Reset Configuration**: Restore default settings
- **Delete**: Permanently remove the proxy

### Confirmation Dialogs

**Destructive Actions:**
- Delete proxy confirmation
- Cache clearing confirmation
- Force stop warnings

**Safety Measures:**
- Running proxies cannot be deleted
- Cache clearing is logged
- Configuration changes require confirmation

## Troubleshooting

### Common Issues

**Proxy Won't Start:**
- Check for port conflicts
- Verify provider API keys
- Review error logs for specific issues

**High Latency:**
- Check provider response times
- Verify network connectivity
- Consider geographical proximity to providers

**Cache Issues:**
- Monitor cache hit rates
- Check cache storage limits
- Verify request normalization

### Diagnostic Tools

**Health Checks:**
- Built-in connectivity testing
- Provider API validation
- Network diagnostics

**Log Analysis:**
- Detailed error logging
- Request/response tracking
- Performance monitoring

**Metrics Dashboard:**
- Real-time performance indicators
- Historical trend analysis
- Comparative analytics

## Best Practices

### Operational Management

**Naming and Organization:**
- Use consistent naming conventions
- Group related proxies logically
- Document proxy purposes clearly

**Resource Management:**
- Monitor resource usage regularly
- Scale proxy instances based on demand
- Balance load across multiple proxies

**Security Practices:**
- Regularly rotate API keys
- Monitor for unusual activity
- Implement proper access controls

### Performance Optimization

**Cache Strategy:**
- Monitor cache hit rates
- Optimize cache invalidation timing
- Balance storage vs. performance

**Request Distribution:**
- Load balance across provider regions
- Use multiple proxies for redundancy
- Implement failover strategies

**Monitoring Setup:**
- Set up alerting for critical metrics
- Regular performance reviews
- Capacity planning based on trends

## Next Steps

After mastering proxy management:

1. **[Learn to use proxies in applications](/usage/using-proxies)** - Integrate with your code
2. **[Explore advanced monitoring](/logging)** - Deep dive into analytics
3. **Configure failure simulation** - Test resilience
4. **[Set up provider-specific features](/providers/overview)** - Optimize for each provider

---

Need help with a specific provider? Check our [Provider-Specific Notes](/providers/overview) for detailed configuration guides.