#!/usr/bin/env python3
"""
Shared HTTP client with retry logic and user-agent rotation.

Provides a configured requests.Session with:
- Exponential backoff retry (configurable max_retries, backoff_factor)
- User-agent rotation from a pool of realistic browser user-agents
- Configurable timeout
- Proper logging of retries
- Handles: Timeout, ConnectionError, SSLError, HTTP 5xx with retries
- Does NOT retry on 403 or 404

Usage:
    from utils.http_client import create_http_client

    client = create_http_client(max_retries=3, backoff_factor=2.0)
    response = client.get("https://example.com", timeout=30)
"""

import logging
import random
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Pool of realistic browser user-agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# Default foodlaw-ai user-agent for identification
FOODLAW_USER_AGENT = "foodlaw-ai/1.0 (https://github.com/supplemental-pl/foodlaw-ai; prawo zywnosciowe PL/EU)"


def _get_random_user_agent() -> str:
    """Return a randomly selected user-agent string from the pool."""
    return random.choice(USER_AGENTS)


class RetrySession(requests.Session):
    """A requests.Session subclass that rotates user-agent per request if configured."""

    def __init__(self, user_agent_rotate: bool = True, default_timeout: int = 30):
        super().__init__()
        self._user_agent_rotate = user_agent_rotate
        self._default_timeout = default_timeout

    def request(self, method, url, **kwargs):
        """Override request to inject user-agent rotation and default timeout."""
        if self._user_agent_rotate:
            if "headers" not in kwargs:
                kwargs["headers"] = {}
            if "User-Agent" not in kwargs["headers"]:
                kwargs["headers"]["User-Agent"] = _get_random_user_agent()

        if "timeout" not in kwargs:
            kwargs["timeout"] = self._default_timeout

        return super().request(method, url, **kwargs)


class RetryWithLogging(Retry):
    """Custom Retry class that logs retry attempts."""

    def increment(self, method=None, url=None, response=None, error=None,
                  _pool=None, _stacktrace=None):
        if error:
            logger.warning(
                "Retry due to error: %s %s - %s (retries left: %d)",
                method, url, str(error), self.total - 1
            )
        elif response:
            logger.warning(
                "Retry due to HTTP %d: %s %s (retries left: %d)",
                response.status, method, url, self.total - 1
            )
        return super().increment(
            method=method, url=url, response=response, error=error,
            _pool=_pool, _stacktrace=_stacktrace
        )


def create_http_client(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    user_agent_rotate: bool = True,
    timeout: int = 30,
) -> requests.Session:
    """
    Create a configured HTTP client session with retry logic and user-agent rotation.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Exponential backoff factor in seconds (default: 2.0).
            Delays will be: backoff_factor * (2 ** (retry_number - 1))
            e.g., with factor=2.0: 2s, 4s, 8s
        user_agent_rotate: If True, rotate user-agents per request from a pool
            of realistic browser user-agents. If False, use the foodlaw-ai
            identification user-agent.
        timeout: Default request timeout in seconds (default: 30)

    Returns:
        Configured requests.Session with retry logic mounted for http/https.

    Example:
        client = create_http_client(max_retries=3, backoff_factor=2.0)
        response = client.get("https://example.com")
    """
    session = RetrySession(
        user_agent_rotate=user_agent_rotate,
        default_timeout=timeout,
    )

    if not user_agent_rotate:
        session.headers["User-Agent"] = FOODLAW_USER_AGENT

    # Configure retry strategy
    # Retry on 500, 502, 503, 504 but NOT on 403 or 404
    retry_strategy = RetryWithLogging(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "HEAD", "OPTIONS", "POST"],
        raise_on_status=False,
    )

    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    logger.debug(
        "Created HTTP client: max_retries=%d, backoff_factor=%.1f, "
        "user_agent_rotate=%s, timeout=%d",
        max_retries, backoff_factor, user_agent_rotate, timeout,
    )

    return session
