# Observability Guide

This document outlines the observability features implemented in the Django WebSocket application.

## Endpoints

### Health Check
- **URL**: `/health/`
- **Method**: GET
- **Purpose**: Basic health check for load balancers and orchestrators
- **Response**: JSON with status, timestamp, deployment color, and active connections count

```json
{
  "status": "healthy",
  "timestamp": 1721180306,
  "deployment_color": "blue",
  "service": "django-websocket-app",
  "active_connections": 42,
  "version": "1.0.0"
}
```

### Readiness Check
- **URL**: `/ready/`
- **Method**: GET
- **Purpose**: More strict readiness check for Kubernetes/orchestrators
- **Response**: JSON with readiness status and component checks

```json
{
  "ready": true,
  "deployment_color": "blue",
  "timestamp": 1721180306,
  "checks": {
    "websocket_handler": true,
    "metrics_collector": true,
    "session_store": true
  }
}
```

### Prometheus Metrics
- **URL**: `/metrics/`
- **Method**: GET
- **Purpose**: Prometheus-compatible metrics endpoint
- **Response**: Plain text metrics in Prometheus format

### Detailed Observability Status
- **URL**: `/observability/`
- **Method**: GET
- **Purpose**: Comprehensive status information for monitoring dashboards
- **Response**: JSON with detailed metrics and system information

## Metrics

### WebSocket Metrics

#### `websocket_connections_total`
- **Type**: Counter
- **Description**: Total number of WebSocket connections established
- **Labels**: `deployment_color`

#### `websocket_connections_active`
- **Type**: Gauge
- **Description**: Number of currently active WebSocket connections
- **Labels**: `deployment_color`

#### `websocket_messages_total`
- **Type**: Counter
- **Description**: Total number of WebSocket messages processed
- **Labels**: `deployment_color`

#### `websocket_heartbeat_pings_total`
- **Type**: Counter
- **Description**: Total number of heartbeat pings sent
- **Labels**: `deployment_color`

#### `websocket_message_processing_duration_seconds`
- **Type**: Histogram
- **Description**: Time spent processing WebSocket messages
- **Labels**: `deployment_color`
- **Buckets**: Default Prometheus histogram buckets

### Application Metrics

#### `application_uptime_seconds`
- **Type**: Gauge
- **Description**: Application uptime in seconds
- **Labels**: `deployment_color`

## Alerting Rules

### Critical Alerts

#### `ApplicationDown`
- **Condition**: `up{job="websocket-app"} == 0`
- **Duration**: 30 seconds
- **Severity**: Critical
- **Description**: Application is not responding to health checks

#### `BothDeploymentsDown`
- **Condition**: `count(up{job="websocket-app"} == 1) == 0`
- **Duration**: 30 seconds
- **Severity**: Critical
- **Description**: Both blue and green deployments are down

### Warning Alerts

#### `NoActiveConnections`
- **Condition**: `websocket_connections_active == 0`
- **Duration**: 60 seconds
- **Severity**: Warning
- **Description**: No active WebSocket connections for more than 60 seconds

#### `TooManyConnections`
- **Condition**: `websocket_connections_active > 4000`
- **Duration**: 30 seconds
- **Severity**: Warning
- **Description**: High number of connections approaching the 5000 limit

#### `SlowMessageProcessing`
- **Condition**: `histogram_quantile(0.95, websocket_message_processing_duration_seconds_bucket) > 1`
- **Duration**: 60 seconds
- **Severity**: Warning
- **Description**: 95th percentile message processing time is above 1 second

#### `HeartbeatPingsFailing`
- **Condition**: `rate(websocket_heartbeat_pings_total[5m]) == 0`
- **Duration**: 2 minutes
- **Severity**: Warning
- **Description**: No heartbeat pings sent in the last 5 minutes

### Info Alerts

#### `ApplicationLongUptime`
- **Condition**: `application_uptime_seconds > 604800`
- **Duration**: 5 minutes
- **Severity**: Info
- **Description**: Application has been running for more than 7 days

#### `UnknownDeploymentColor`
- **Condition**: `websocket_connections_active{deployment_color="unknown"} > 0`
- **Duration**: 60 seconds
- **Severity**: Warning
- **Description**: Connections being handled by deployment with unknown color

## Testing Observability

### Test Health Endpoints
```bash
# Health check
curl http://localhost/health/

# Readiness check
curl http://localhost/ready/

# Detailed observability
curl http://localhost/observability/
```

### Test Metrics
```bash
# Prometheus metrics
curl http://localhost/metrics/

# Check specific metric
curl http://localhost/metrics/ | grep websocket_connections_active
```

### Load Testing
```bash
# Test with multiple connections to generate metrics
# You can use tools like websocat or write a simple script
```

## Grafana Dashboard Queries

### Active Connections
```promql
websocket_connections_active{deployment_color="blue"}
```

### Message Rate
```promql
rate(websocket_messages_total[5m])
```

### Processing Time Percentiles
```promql
histogram_quantile(0.95, websocket_message_processing_duration_seconds_bucket)
```

### Connection Churn
```promql
rate(websocket_connections_total[5m])
```

## Integration with Prometheus

1. Add the following to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'websocket-app'
    static_configs:
      - targets: ['localhost:80']
    scrape_interval: 15s
    metrics_path: /metrics/
```

2. Add the alerting rules from `prometheus_alerts.yml` to your Prometheus configuration.

3. Configure Alertmanager to handle the alerts according to your notification preferences.

## Structured Logging

The application uses structured JSON logging for better observability:

```json
{
  "asctime": "2025-07-17 02:58:26,991",
  "levelname": "INFO",
  "message": "Client connected",
  "session_id": "abc123",
  "resumed": false,
  "count": 0,
  "total_active": 1
}
```

## Monitoring Best Practices

1. **Set up dashboards** in Grafana for real-time monitoring
2. **Configure alerts** based on your SLA requirements
3. **Monitor trends** over time, not just current values
4. **Set up log aggregation** for better troubleshooting
5. **Test your alerting** regularly to ensure it works