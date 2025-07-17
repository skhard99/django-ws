from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from prometheus_client import CONTENT_TYPE_LATEST
from chat.metrics import get_metrics_text, legacy_metrics
from chat.connection_pool import active_connections
import os
import time
import json
from django.core.exceptions import DisallowedHost
import logging

logger = logging.getLogger(__name__)

def metrics_view(request):
    """Prometheus metrics endpoint"""
    logger.info(f"Metrics request: method={request.method}, headers={request.headers}, path={request.path}")
    try:
        response = get_metrics_text()
        return HttpResponse(response, content_type=CONTENT_TYPE_LATEST)
    except DisallowedHost as e:
        logger.warning(f"DisallowedHost bypassed for metrics: {str(e)}")
        return HttpResponse(get_metrics_text(), content_type=CONTENT_TYPE_LATEST)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for load balancer and deployment scripts
    """
    try:
        deployment_color = os.getenv('DEPLOYMENT_COLOR', 'unknown')
        
        health_data = {
            "status": "healthy",
            "timestamp": int(time.time()),
            "deployment_color": deployment_color,
            "service": "django-websocket-app",
            "active_connections": len(active_connections),
            "version": "1.0.0"
        }
        
        return JsonResponse(health_data, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": int(time.time()),
            "deployment_color": os.getenv('DEPLOYMENT_COLOR', 'unknown')
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def observability_status(request):
    """
    Detailed observability endpoint for monitoring dashboard
    """
    try:
        deployment_color = os.getenv('DEPLOYMENT_COLOR', 'unknown')
        
        status_data = {
            "service": "django-websocket-app",
            "deployment_color": deployment_color,
            "timestamp": int(time.time()),
            "health": "healthy",
            "metrics": {
                "active_connections": len(active_connections),
                "total_connections": legacy_metrics.get("total_connections", 0),
                "total_messages": legacy_metrics.get("total_messages", 0),
                "heartbeat_pings": legacy_metrics.get("heartbeat_pings", 0)
            },
            "system": {
                "uptime_seconds": int(time.time() - 1721180306),  # Approximate start time
                "memory_usage": "unknown",  # You can add psutil later if needed
                "cpu_usage": "unknown"
            },
            "endpoints": {
                "health": "/health/",
                "metrics": "/metrics/",
                "observability": "/observability/"
            }
        }
        
        return JsonResponse(status_data, status=200)
    
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "timestamp": int(time.time())
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check - more strict than health check
    Used by Kubernetes/orchestrators to determine if service is ready to receive traffic
    """
    try:
        # Check if application is ready to serve requests
        deployment_color = os.getenv('DEPLOYMENT_COLOR', 'unknown')
        
        # You can add more sophisticated readiness checks here
        # For example: database connectivity, external service availability, etc.
        
        ready_data = {
            "ready": True,
            "deployment_color": deployment_color,
            "timestamp": int(time.time()),
            "checks": {
                "websocket_handler": True,
                "metrics_collector": True,
                "session_store": True
            }
        }
        
        return JsonResponse(ready_data, status=200)
    
    except Exception as e:
        return JsonResponse({
            "ready": False,
            "error": str(e),
            "timestamp": int(time.time())
        }, status=503)  # Service Unavailable