"""Prometheus metrics for real-time monitoring."""

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response


# Create custom registry
registry = CollectorRegistry()

# ============================================
# Request Metrics
# ============================================

REQUEST_COUNT = Counter(
    'resolveai_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'resolveai_request_latency_seconds',
    'Request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

# ============================================
# Business Metrics
# ============================================

INTENT_CLASSIFICATION = Counter(
    'resolveai_intent_classification_total',
    'Total intent classifications',
    ['intent', 'language'],
    registry=registry
)

RESOLUTION_COUNT = Counter(
    'resolveai_resolutions_total',
    'Total resolved conversations',
    registry=registry
)

ESCALATION_COUNT = Counter(
    'resolveai_escalations_total',
    'Total number of escalations',
    ['intent', 'reason'],
    registry=registry
)

ACTIVE_CONVERSATIONS = Gauge(
    'resolveai_active_conversations',
    'Number of active conversations',
    registry=registry
)

# ============================================
# LLM Metrics
# ============================================

LLM_CALL_DURATION = Histogram(
    'resolveai_llm_call_duration_seconds',
    'LLM API call duration',
    ['operation'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

LLM_CALLS_TOTAL = Counter(
    'resolveai_llm_calls_total',
    'Total LLM API calls',
    ['operation', 'status'],
    registry=registry
)

# ============================================
# Cache Metrics
# ============================================

CACHE_HITS = Counter(
    'resolveai_cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=registry
)

CACHE_MISSES = Counter(
    'resolveai_cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=registry
)

# ============================================
# Node Performance Metrics
# ============================================

NODE_EXECUTION_TIME = Histogram(
    'resolveai_node_execution_seconds',
    'Node execution time in seconds',
    ['node_name'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry
)

# ============================================
# Application Info
# ============================================

APP_INFO = Info(
    'resolveai_app',
    'Application information',
    registry=registry
)

APP_INFO.info({
    'version': '1.0.0',
    'service': 'resolveai-api',
})


def metrics_endpoint() -> Response:
    """FastAPI endpoint for Prometheus metrics.
    
    Returns:
        Response with Prometheus metrics in text format.
    """
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )
