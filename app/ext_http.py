from __future__ import annotations
"""Shared external HTTP helper with conservative retries + jitter.

Simple exponential backoff (cap 5 tries) with jitter; only 5xx/timeouts retried.
"""
import os, random, time
from typing import Optional, Dict, Any
import requests

TIMEOUT = int(os.getenv("EXTERNAL_REQUEST_TIMEOUT_SEC", "20"))
BACKOFF_MAX = int(os.getenv("EXTERNAL_BACKOFF_MAX_SEC", "60"))


def get(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> requests.Response:
    tries = 0
    last_exc = None
    while True:
        tries += 1
        try:
            r = requests.get(url, params=params, headers=headers, timeout=TIMEOUT)
            if r.status_code >= 500:
                raise requests.HTTPError(f"{r.status_code} upstream error", response=r)
            return r
        except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
            last_exc = e
            if tries >= 5:
                if isinstance(e, requests.HTTPError) and getattr(e, "response", None):
                    return e.response  # surface last response
                raise
            delay = min((2 ** min(tries, 6)) + random.uniform(0, 1.0), BACKOFF_MAX)
            time.sleep(delay)
