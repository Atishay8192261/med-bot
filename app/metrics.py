"""Lightweight in-process metrics counters exposed at /metrics.

Provides counter helpers used by external source clients and fallback merge logic.
Thread-safety: simple GIL-protected increments (no heavy concurrency expected here).
"""

from __future__ import annotations
import time
from typing import Dict, Tuple

_COUNTERS: Dict[Tuple[str, Tuple[Tuple[str,str], ...]], int] = {}
_START = time.time()

def _key(name: str, labels: Dict[str,str] | None = None):
	if not labels:
		return (name, tuple())
	return (name, tuple(sorted(labels.items())))

def inc(name: str, labels: Dict[str,str] | None = None, value: int = 1):
	k = _key(name, labels)
	_COUNTERS[k] = _COUNTERS.get(k, 0) + value

# Backwards compatibility alias
def incr(name: str, labels: Dict[str,str] | None = None, value: int = 1):  # pragma: no cover
	inc(name, labels, value)

def cache_hit(source: str, layer: str):
	inc("cache_hit_total", {"source": source, "layer": layer})

def cache_miss(source: str):
	inc("cache_miss_total", {"source": source})

def external_call(source: str):
	inc("external_call_total", {"source": source})

def external_success(source: str):
	inc("external_success_total", {"source": source})

def external_error(source: str):
	inc("external_error_total", {"source": source})

def fallback_fill(source: str, bucket: str):
	inc("fallback_fill_total", {"source": source, "bucket": bucket})

def snapshot() -> str:
	lines = []
	for (name, labels), value in sorted(_COUNTERS.items()):
		if labels:
			label_txt = ",".join(f"{k}=\"{v}\"" for k,v in labels)
			lines.append(f"{name}{{{label_txt}}} {value}")
		else:
			lines.append(f"{name} {value}")
	# gauge
	lines.append(f"app_uptime_seconds {int(time.time() - _START)}")
	return "\n".join(lines) + "\n"

def render_prometheus():  # used by /metrics endpoint
	return snapshot()

def reset():  # test helper
	_COUNTERS.clear()
	global _START
	_START = time.time()

__all__ = [
	"cache_hit","cache_miss","external_call","external_success","external_error","fallback_fill","render_prometheus","reset","incr"
]
