from collections import defaultdict

metrics = defaultdict(int)

def inc(metric_name, count=1):
    metrics[metric_name] += count

def set_value(metric_name, value):
    metrics[metric_name] = value

def get_metrics_text():
    return "\n".join(f"{k} {v}" for k, v in metrics.items())
