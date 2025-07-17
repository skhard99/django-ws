from django.http import HttpResponse
from chat.metrics import get_metrics_text

def metrics_view(request):
    return HttpResponse(get_metrics_text(), content_type="text/plain")
