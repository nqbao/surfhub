from typing import Optional


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


class InsufficientFundsError(SurfhubError):
    """Raised when the API returns an insufficient funds, credits, or quota error."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(message)


_INSUFFICIENT_FUNDS_KEYWORDS = [
    "insufficient funds",
    "insufficient balance",
    "insufficient credits",
    "insufficientbalance",
    "quota exceeded",
    "exceeded your quota",
    "out of credits",
    "no_more_credits",
    "credits exhausted",
    "quota limit",
    "payment required",
    "billing error",
    "billing required",
    "run out of",
    "daily limit",
    "dailylimit",
    "account suspended",
    "account-suspended",
    "recharge",
    "budget exceeded",
    "plan limit",
]


def is_insufficient_funds(status_code: int, body: str) -> bool:
    if status_code == 402:
        return True
    if status_code in (403, 429, 432):
        body_lower = body.lower()
        return any(kw in body_lower for kw in _INSUFFICIENT_FUNDS_KEYWORDS)
    return False


def check_insufficient_funds(message: str, status_code: Optional[int] = None):
    if status_code == 402:
        raise InsufficientFundsError(message, status_code=status_code)
    msg_lower = message.lower()
    if any(kw in msg_lower for kw in _INSUFFICIENT_FUNDS_KEYWORDS):
        raise InsufficientFundsError(message, status_code=status_code)


def raise_for_insufficient_funds(resp):
    if is_insufficient_funds(resp.status_code, resp.text):
        raise InsufficientFundsError(
            f"Insufficient funds or quota exceeded (status {resp.status_code})",
            status_code=resp.status_code,
        )
