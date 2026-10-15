"""Custom Exception Hierarchy for LetmeQC"""
from typing import Any, Dict, Optional


class LetmeQCException(Exception):
    """Base exception for all LetmeQC errors"""
    
    def __init__(self, message: str = "", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ConfigurationError(LetmeQCException):
    """Raised when configuration is invalid or missing"""
    pass


class CVATAPIError(LetmeQCException):
    """Raised when CVAT API operations fail"""
    
    def __init__(self, message: str = "", status_code: Optional[int] = None, 
                 response: Optional[Dict[str, Any]] = None):
        super().__init__(message, {"status_code": status_code, "response": response})
        self.status_code = status_code
        self.response = response


class QCValidationError(LetmeQCException):
    """Raised when QC validation fails"""
    
    def __init__(self, message: str = "", errors: Optional[list] = None):
        super().__init__(message, {"error_count": len(errors) if errors else 0})
        self.errors = errors or []


class ParseError(LetmeQCException):
    """Raised when parsing CVAT JSON fails"""
    pass


class AuthenticationError(LetmeQCException):
    """Raised when authentication fails"""
    pass


class WebhookError(LetmeQCException):
    """Raised when webhook processing fails"""
    pass


class HealthCheckError(LetmeQCException):
    """Raised when health check fails"""
    pass


# HTTP Status Code to Exception mapping
HTTP_EXCEPTIONS = {
    400: {"exception": ConfigurationError, "message": "Bad Request"},
    401: {"exception": AuthenticationError, "message": "Unauthorized"},
    403: {"exception": AuthenticationError, "message": "Forbidden"},
    404: {"exception": CVATAPIError, "message": "Not Found"},
    422: {"exception": ConfigurationError, "message": "Unprocessable Entity"},
    429: {"exception": CVATAPIError, "message": "Too Many Requests"},
    500: {"exception": CVATAPIError, "message": "Internal Server Error"},
    502: {"exception": CVATAPIError, "message": "Bad Gateway"},
    503: {"exception": CVATAPIError, "message": "Service Unavailable"},
    504: {"exception": CVATAPIError, "message": "Gateway Timeout"},
}


def get_exception_from_status_code(status_code: int, message: str = "") -> LetmeQCException:
    """Get appropriate exception from HTTP status code"""
    info = HTTP_EXCEPTIONS.get(status_code, HTTP_EXCEPTIONS[500])
    return info["exception"](message or info["message"])


class RequestContext:
    """Context for request tracing and correlation"""
    
    def __init__(self, request_id: Optional[str] = None, correlation_id: Optional[str] = None,
                 user_agent: Optional[str] = None, ip_address: Optional[str] = None):
        self.request_id = request_id
        self.correlation_id = correlation_id
        self.user_agent = user_agent
        self.ip_address = ip_address
        self._metadata: Dict[str, Any] = {}
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the context"""
        self._metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata from the context"""
        return self._metadata.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "user_agent": self.user_agent,
            "ip_address": self.ip_address,
            "metadata": self._metadata
        }


# Global request context (thread-local storage would be better, but for simplicity)
_current_context: Optional[RequestContext] = None


def get_current_context() -> Optional[RequestContext]:
    """Get the current request context"""
    return _current_context


def set_current_context(context: RequestContext):
    """Set the current request context"""
    global _current_context
    _current_context = context


def clear_current_context():
    """Clear the current request context"""
    global _current_context
    _current_context = None
