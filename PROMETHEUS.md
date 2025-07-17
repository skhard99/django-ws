# Prometheus & Alerting Setup Guide

## Overview
This guide explains how to set up Prometheus monitoring and alerting for your Django WebSocket application.

## Components

### 1. Prometheus Server
- **Purpose**: Scrapes metrics from your Django app and evaluates alert rules
- **Port**: 9090
- **UI**: http://localhost:9090

### 2. Alertmanager
- **Purpose**: Receives alerts from Prometheus and routes them to destinations
- **Port**: 9093
- **UI**: http://localhost:9093

### 3. Webhook Server
- **Purpose**: Simple test server to receive alerts (for development)
- **Port**: 5001

## File Structure

Create these files in your `websocket_app` directory:

```
websocket_app/
├── prometheus.yml              # Prometheus configuration
├── alertmanager.yml           # Alertmanager configuration
├── prometheus_alerts.yml      # Alert rules (you already have this)
└── docker-compose.yml         # Updated with monitoring services
```

## Setup Steps

### 1. Create Configuration Files

Save the provided `prometheus.yml` and `alertmanager.yml` files in your `websocket_app` directory.

### 2. Update Docker Compose

Replace your existing `docker-compose.yml` with the updated version that includes Prometheus and Alertmanager services.

### 3. Start the Stack

```bash
docker-compose up -d
```

### 4. Verify Setup

1. **Prometheus UI**: http://localhost:9090
   - Go to Status → Targets to see if your Django apps are being scraped
   - Go to Alerts to see your alert rules

2. **Alertmanager UI**: http://localhost:9093
   - View active alerts and silences

3. **Your Django App**: http://localhost
   - The metrics endpoint: http://localhost/metrics/

## Testing Alerts

### Test "No Active Connections" Alert

1. Start your application
2. Wait for more than 60 seconds without any WebSocket connections
3. Check the webhook server logs:
   ```bash
   docker-compose logs webhook-server
   ```

### Test "Application Down" Alert

1. Stop one of your Django containers:
   ```bash
   docker-compose stop web_blue
   ```
2. Wait 30 seconds
3. Check for alerts in Prometheus UI and webhook logs

## Alert Destinations

### Current Setup (Development)
- Alerts go to the webhook server at http://localhost:5001/alerts
- You can see alerts in the webhook server logs

### Production Setup Options

1. **Email Alerts**: Configure SMTP settings in `alertmanager.yml`
2. **Slack Integration**: Add Slack webhook URL
3. **PagerDuty**: Add PagerDuty integration key
4. **Custom Webhook**: Point to your own alert handling service

## Monitoring Your Metrics

### Key Metrics to Watch
- `websocket_connections_active`: Current active connections
- `websocket_connections_total`: Total connections created
- `websocket_messages_total`: Total messages processed
- `websocket_message_processing_duration_seconds`: Message processing time
- `application_uptime_seconds`: Application uptime

### Prometheus Queries Examples

```promql
# Current active connections
websocket_connections_active

# Message processing rate (per second)
rate(websocket_messages_total[5m])

# 95th percentile processing time
histogram_quantile(0.95, websocket_message_processing_duration_seconds_bucket)

# Applications that are down
up{job="websocket-app"} == 0
```

## Alert Rules Explanation

Your `prometheus_alerts.yml` contains these alerts:

1. **NoActiveConnections**: Fires when no WebSocket connections for >60s
2. **ApplicationDown**: Fires when health check fails for >30s
3. **TooManyConnections**: Fires when >4000 connections (approaching 5000 limit)
4. **SlowMessageProcessing**: Fires when 95th percentile processing time >1s
5. **ApplicationLongUptime**: Info alert when app runs >7 days
6. **HeartbeatPingsFailing**: Fires when no heartbeat pings for >2 minutes
7. **BothDeploymentsDown**: Critical alert when both blue/green are down
8. **UnknownDeploymentColor**: Fires when deployment color is unknown

## Troubleshooting

### Common Issues

1. **Targets not being scraped**
   - Check if your Django containers are running
   - Verify the metrics endpoint is accessible: `curl http://localhost:8001/metrics/`

2. **Alerts not firing**
   - Check Prometheus UI → Alerts to see rule evaluation
   - Verify your metrics are being collected

3. **Webhook server not receiving alerts**
   - Check if alertmanager can reach the webhook server
   - Look at alertmanager logs: `docker-compose logs alertmanager`

### Useful Commands

```bash
# Check if metrics endpoint is working
curl http://localhost:8001/metrics/

# Check Prometheus config
docker-compose exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Check alert rules
docker-compose exec prometheus promtool check rules /etc/prometheus/alerts/prometheus_alerts.yml

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# View logs
docker-compose logs prometheus
docker-compose logs alertmanager
docker-compose logs webhook-server
```

## Next Steps

1. **Configure Real Alert Destinations**: Set up email/Slack/PagerDuty in `alertmanager.yml`
2. **Add More Metrics**: Consider adding business metrics to your Django app
3. **Set up Grafana**: For better visualization of metrics
4. **Production Hardening**: Add authentication, TLS, and proper storage retention

## Production Considerations

1. **Persistent Storage**: Use named volumes for Prometheus and Alertmanager data
2. **Backup**: Regularly backup your metrics and alerting configuration
3. **High Availability**: Run multiple Prometheus and Alertmanager instances
4. **Security**: Add authentication and TLS
5. **Retention**: Configure appropriate data retention policies