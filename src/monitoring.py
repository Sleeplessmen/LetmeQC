"""Monitoring and Metrics for LetmeQC"""
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class MetricCounter:
    """Simple counter metric"""
    name: str
    value: int = 0
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def increment(self, by: int = 1):
        """Increment the counter"""
        self.value += by
    
    def reset(self):
        """Reset the counter"""
        self.value = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Prometheus"""
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
            "tags": self.tags
        }


@dataclass
class MetricTimer:
    """Timer metric for tracking durations"""
    name: str
    total_time: float = 0.0
    call_count: int = 0
    min_time: float = float('inf')
    max_time: float = 0.0
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def record(self, duration: float):
        """Record a duration"""
        self.total_time += duration
        self.call_count += 1
        self.min_time = min(self.min_time, duration)
        self.max_time = max(self.max_time, duration)
    
    def average(self) -> float:
        """Get average duration"""
        return self.total_time / self.call_count if self.call_count > 0 else 0.0
    
    def reset(self):
        """Reset the timer"""
        self.total_time = 0.0
        self.call_count = 0
        self.min_time = float('inf')
        self.max_time = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "total_time": self.total_time,
            "call_count": self.call_count,
            "average_time": self.average(),
            "min_time": self.min_time if self.min_time != float('inf') else 0.0,
            "max_time": self.max_time,
            "description": self.description,
            "tags": self.tags
        }


@dataclass
class MetricGauge:
    """Gauge metric for tracking values"""
    name: str
    value: float = 0.0
    description: str = ""
    tags: Dict[str, str] = field(default_factory=dict)
    
    def set(self, value: float):
        """Set the gauge value"""
        self.value = value
    
    def increment(self, by: float = 1.0):
        """Increment the gauge"""
        self.value += by
    
    def decrement(self, by: float = 1.0):
        """Decrement the gauge"""
        self.value -= by
    
    def reset(self):
        """Reset the gauge"""
        self.value = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "value": self.value,
            "description": self.description,
            "tags": self.tags
        }


class MetricsRegistry:
    """Registry for all metrics"""
    
    def __init__(self):
        self.counters: Dict[str, MetricCounter] = {}
        self.timers: Dict[str, MetricTimer] = {}
        self.gauges: Dict[str, MetricGauge] = {}
    
    def get_counter(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None) -> MetricCounter:
        """Get or create a counter"""
        if name not in self.counters:
            self.counters[name] = MetricCounter(name=name, description=description, tags=tags or {})
        return self.counters[name]
    
    def get_timer(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None) -> MetricTimer:
        """Get or create a timer"""
        if name not in self.timers:
            self.timers[name] = MetricTimer(name=name, description=description, tags=tags or {})
        return self.timers[name]
    
    def get_gauge(self, name: str, description: str = "", tags: Optional[Dict[str, str]] = None) -> MetricGauge:
        """Get or create a gauge"""
        if name not in self.gauges:
            self.gauges[name] = MetricGauge(name=name, description=description, tags=tags or {})
        return self.gauges[name]
    
    def reset_all(self):
        """Reset all metrics"""
        for counter in self.counters.values():
            counter.reset()
        for timer in self.timers.values():
            timer.reset()
        for gauge in self.gauges.values():
            gauge.reset()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics as dictionary"""
        return {
            "counters": {name: counter.to_dict() for name, counter in self.counters.items()},
            "timers": {name: timer.to_dict() for name, timer in self.timers.items()},
            "gauges": {name: gauge.to_dict() for name, gauge in self.gauges.items()},
            "timestamp": datetime.now().isoformat()
        }


# Global metrics registry
metrics = MetricsRegistry()


# Pre-defined metrics
def get_metrics():
    """Get the global metrics registry"""
    return metrics


# Common metrics
REQUEST_COUNTER = metrics.get_counter("http_requests_total", "Total HTTP requests", {"type": "counter"})
REQUEST_TIMER = metrics.get_timer("http_request_duration_seconds", "HTTP request duration")
ERROR_COUNTER = metrics.get_counter("http_errors_total", "Total HTTP errors", {"type": "counter"})
QC_ERRORS_COUNTER = metrics.get_counter("qc_errors_total", "Total QC errors found", {"type": "counter"})
QC_CHECKS_COUNTER = metrics.get_counter("qc_checks_total", "Total QC checks performed", {"type": "counter"})
JOB_PROCESSED_COUNTER = metrics.get_counter("jobs_processed_total", "Total jobs processed", {"type": "counter"})
JOB_FAILED_COUNTER = metrics.get_counter("jobs_failed_total", "Total jobs failed QC", {"type": "counter"})
JOB_PASSED_COUNTER = metrics.get_counter("jobs_passed_total", "Total jobs passed QC", {"type": "counter"})
ISSUES_CREATED_COUNTER = metrics.get_counter("issues_created_total", "Total issues created in CVAT", {"type": "counter"})


@contextmanager
def timed_operation(metric: MetricTimer, **tags):
    """Context manager for timing operations"""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start_time
        metric.record(duration)


def timed(metric_name: str, description: str = "", **tags):
    """Decorator for timing functions"""
    def decorator(func: Callable):
        metric = metrics.get_timer(metric_name, description, tags)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                metric.record(duration)
                return result
            except Exception:
                duration = time.perf_counter() - start_time
                metric.record(duration)
                raise
        
        return wrapper
    return decorator


class HealthCheckResult:
    """Result of a health check"""
    
    def __init__(self, name: str, status: str = "healthy", details: Optional[Dict[str, Any]] = None):
        self.name = name
        self.status = status
        self.details = details or {}
        self.timestamp = datetime.now().isoformat()
    
    def is_healthy(self) -> bool:
        """Check if the component is healthy"""
        return self.status == "healthy"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp
        }


class HealthChecker:
    """Health check manager"""
    
    def __init__(self):
        self.checks: Dict[str, Callable[[], HealthCheckResult]] = {}
    
    def add_check(self, name: str, check_func: Callable[[], HealthCheckResult]):
        """Add a health check"""
        self.checks[name] = check_func
    
    def check_all(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        for name, check_func in self.checks.items():
            try:
                results[name] = check_func()
            except Exception as e:
                results[name] = HealthCheckResult(
                    name=name,
                    status="unhealthy",
                    details={"error": str(e)}
                )
        return results
    
    def is_healthy(self) -> bool:
        """Check if all components are healthy"""
        return all(check.is_healthy() for check in self.checks.values())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get health check summary"""
        results = self.check_all()
        healthy_count = sum(1 for r in results.values() if r.is_healthy())
        total_count = len(results)
        
        return {
            "status": "healthy" if healthy_count == total_count else "degraded",
            "timestamp": datetime.now().isoformat(),
            "checks": {name: result.to_dict() for name, result in results.items()},
            "summary": {
                "healthy": healthy_count,
                "unhealthy": total_count - healthy_count,
                "total": total_count
            }
        }


# Global health checker
health_checker = HealthChecker()


def register_health_check(name: str):
    """Decorator for registering health checks"""
    def decorator(func: Callable[[], HealthCheckResult]):
        health_checker.add_check(name, func)
        return func
    return decorator


# Pre-defined health checks
@register_health_check("cvat_api")
def check_cvat_api() -> HealthCheckResult:
    """Check CVAT API connectivity"""
    from src.config.settings import get_cvat_config
    config = get_cvat_config()
    
    if not config.token:
        return HealthCheckResult(
            name="cvat_api",
            status="unhealthy",
            details={"error": "CVAT_TOKEN not configured"}
        )
    
    # Try to make a simple request
    try:
        import requests
        from src.clients.cvat_client import CVATAPI
        
        api = CVATAPI(
            base_url=config.base_url,
            token=config.token,
            org_slug=config.org_slug,
            timeout=5
        )
        
        # Try to get jobs list (lightweight check)
        response = requests.get(
            f"{config.base_url}/jobs",
            headers=api._get_headers(),
            timeout=5
        )
        
        if response.status_code in [200, 401, 403]:
            return HealthCheckResult(
                name="cvat_api",
                status="healthy",
                details={"api_url": config.base_url, "connected": True}
            )
        else:
            return HealthCheckResult(
                name="cvat_api",
                status="degraded",
                details={"api_url": config.base_url, "status_code": response.status_code}
            )
    except Exception as e:
        return HealthCheckResult(
            name="cvat_api",
            status="unhealthy",
            details={"api_url": config.base_url, "error": str(e)}
        )


@register_health_check("qc_service")
def check_qc_service() -> HealthCheckResult:
    """Check QC service health"""
    from src.config.settings import get_qc_config
    config = get_qc_config()
    
    # Validate config values
    errors = []
    if config.min_box_area < 0:
        errors.append("min_box_area must be positive")
    if config.iou_threshold < 0 or config.iou_threshold > 1:
        errors.append("iou_threshold must be between 0 and 1")
    
    if errors:
        return HealthCheckResult(
            name="qc_service",
            status="unhealthy",
            details={"errors": errors}
        )
    
    return HealthCheckResult(
        name="qc_service",
        status="healthy",
        details={"config_valid": True}
    )


@register_health_check("dependencies")
def check_dependencies() -> HealthCheckResult:
    """Check required dependencies"""
    import importlib
    
    required_modules = [
        "fastapi",
        "uvicorn",
        "requests",
        "pydantic",
        "pydantic_settings",
        "shapely"
    ]
    
    missing = []
    versions = {}
    
    for module in required_modules:
        try:
            mod = importlib.import_module(module)
            versions[module] = getattr(mod, "__version__", "unknown")
        except ImportError:
            missing.append(module)
    
    if missing:
        return HealthCheckResult(
            name="dependencies",
            status="unhealthy",
            details={"missing": missing, "found": versions}
        )
    
    return HealthCheckResult(
        name="dependencies",
        status="healthy",
        details={"versions": versions}
    )


def get_health_summary() -> Dict[str, Any]:
    """Get complete health check summary"""
    return health_checker.get_summary()
