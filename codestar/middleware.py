"""
Exception logging middleware for production error tracking.

This middleware catches all exceptions and logs full tracebacks to stderr
so they appear in Heroku logs even when DEBUG=False.
"""
import logging
import traceback

logger = logging.getLogger('django.request')


class ExceptionLoggingMiddleware:
    """
    Middleware to log all exceptions with full tracebacks.
    
    This ensures that even when DEBUG=False, all exceptions are logged
    with full tracebacks to stderr, making them visible in Heroku logs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Log exception with full traceback, then re-raise.
        
        This method is called by Django when an exception occurs.
        We log the full traceback, then re-raise so Django's normal
        error handling continues (500 response, etc.).
        """
        logger.exception(
            f"Exception in {request.path}: {type(exception).__name__}: {exception}",
            exc_info=True,
            extra={
                'request': request,
                'path': request.path,
                'method': request.method,
            }
        )
        # Re-raise the exception so Django handles it normally
        return None

