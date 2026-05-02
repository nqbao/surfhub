class SurfhubError(Exception):
    """Base exception for all surfhub errors."""
    pass


class ScrapingError(SurfhubError):
    """Raised when a scraping operation fails."""

    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class SerpApiError(SurfhubError):
    """Raised when a SERP API call fails."""

    def __init__(self, message: str, status_code: int = None):
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(SurfhubError):
    """Raised when the target service throttles or blocks the request."""
    pass
