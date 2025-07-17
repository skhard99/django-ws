"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from chat.views import metrics_view, health_check, observability_status, readiness_check

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Observability endpoints
    path('metrics/', metrics_view, name='metrics'),           # Prometheus metrics
    path('health/', health_check, name='health'),             # Health check
    path('ready/', readiness_check, name='readiness'),        # Readiness check
    path('observability/', observability_status, name='observability'),  # Detailed status
    
    # Legacy endpoint (keep for backward compatibility)
    # path('metrics', metrics_view, name='metrics_legacy'),     # Without trailing slash
]