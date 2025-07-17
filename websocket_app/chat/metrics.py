from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry
import time
import os

# Create a custom registry for this application
registry = CollectorRegistry()

# Define Prometheus metrics
websocket_connections_total = Counter(
    'websocket_connections_total',
    'Total number of WebSocket connections established',
    ['deployment_color'],
    registry=registry
)

websocket_connections_active = Gauge(
    'websocket_connections_active',
    'Number of currently active WebSocket connections',
    ['deployment_color'],
    registry=registry
)

websocket_messages_total = Counter(
    'websocket_messages_total',
    'Total number of WebSocket messages processed',
    ['deployment_color'],
    registry=registry
)

websocket_heartbeat_pings_total = Counter(
    'websocket_heartbeat_pings_total',
    'Total number of heartbeat pings sent',
    ['deployment_color'],
    registry=registry
)

websocket_message_processing_duration = Histogram(
    'websocket_message_processing_duration_seconds',
    'Time spent processing WebSocket messages',
    ['deployment_color'],
    registry=registry
)

application_uptime_seconds = Gauge(
    'application_uptime_seconds',
    'Application uptime in seconds',
    ['deployment_color'],
    registry=registry
)

# Track application start time
app_start_time = time.time()

# Get deployment color from environment
deployment_color = os.getenv('DEPLOYMENT_COLOR', 'unknown')

def inc_connections():
    """Increment total connections counter"""
    websocket_connections_total.labels(deployment_color=deployment_color).inc()

def set_active_connections(count):
    """Set current active connections count"""
    websocket_connections_active.labels(deployment_color=deployment_color).set(count)

def inc_messages():
    """Increment total messages counter"""
    websocket_messages_total.labels(deployment_color=deployment_color).inc()

def inc_heartbeat_pings():
    """Increment heartbeat pings counter"""
    websocket_heartbeat_pings_total.labels(deployment_color=deployment_color).inc()

def record_message_processing_time(duration):
    """Record message processing time"""
    websocket_message_processing_duration.labels(deployment_color=deployment_color).observe(duration)

def update_uptime():
    """Update application uptime"""
    uptime = time.time() - app_start_time
    application_uptime_seconds.labels(deployment_color=deployment_color).set(uptime)

def get_metrics_text():
    """Generate Prometheus metrics text"""
    # Update uptime before generating metrics
    update_uptime()
    return generate_latest(registry).decode('utf-8')

# Legacy compatibility (keep for now to avoid breaking existing code)
from collections import defaultdict
legacy_metrics = defaultdict(int)

def inc(metric_name, count=1):
    """Legacy function - use specific metric functions instead"""
    legacy_metrics[metric_name] += count
    
    # Map legacy metrics to new Prometheus metrics
    if metric_name == "total_connections":
        inc_connections()
    elif metric_name == "total_messages":
        inc_messages()
    elif metric_name == "heartbeat_pings":
        inc_heartbeat_pings()

def set_value(metric_name, value):
    """Legacy function - use specific metric functions instead"""
    legacy_metrics[metric_name] = value
    
    # Map legacy metrics to new Prometheus metrics
    if metric_name == "connected_users":
        set_active_connections(value)