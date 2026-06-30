from collections import Counter
import logging
from threading import Lock
from time import perf_counter
import traceback
from uuid import uuid4

from fastapi import Request, Response

from app.db.session import SessionLocal
from app.services.observability_service import record_error_event, record_request_log

logger = logging.getLogger(__name__)
_lock = Lock()
_request_count: Counter[str] = Counter()
_request_latency_ms: Counter[str] = Counter()


async def metrics_middleware(request: Request, call_next):
    start = perf_counter()
    request_id = request.headers.get("x-request-id") or str(uuid4())
    request.state.request_id = request_id
    response = None
    captured_error = None

    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        captured_error = exc
        raise
    finally:
        duration_ms = int((perf_counter() - start) * 1000)
        status_code = response.status_code if response else 500
        key = f"{request.method} {request.url.path} {status_code}"

        with _lock:
            _request_count[key] += 1
            _request_latency_ms[key] += duration_ms

        if response:
            response.headers["X-Process-Time-Ms"] = str(duration_ms)
            response.headers["X-Request-ID"] = request_id

        _persist_observability(request, request_id, status_code, duration_ms, captured_error)


def _persist_observability(
    request: Request,
    request_id: str,
    status_code: int,
    duration_ms: int,
    captured_error: Exception | None,
) -> None:
    if request.url.path == "/metrics":
        return

    db = SessionLocal()
    try:
        user_id = getattr(request.state, "user_id", None)
        error_message = str(captured_error) if captured_error else None
        request_log = record_request_log(
            db,
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            latency_ms=duration_ms,
            user_id=user_id,
            api_key_prefix=getattr(request.state, "api_key_prefix", None),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            error=error_message,
        )
        db.flush()

        if captured_error or status_code >= 500:
            record_error_event(
                db,
                request_log_id=request_log.id,
                user_id=user_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                error_type=type(captured_error).__name__ if captured_error else "HTTPError",
                message=error_message or f"HTTP {status_code}",
                stack=traceback.format_exc() if captured_error else None,
            )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.debug("Skipping observability persistence: %s", exc)
    finally:
        db.close()


def render_metrics() -> Response:
    lines = [
        "# HELP wefindbest_http_requests_total Total HTTP requests.",
        "# TYPE wefindbest_http_requests_total counter",
    ]

    with _lock:
        for key, count in sorted(_request_count.items()):
            method, path, status = key.split(" ", 2)
            lines.append(
                'wefindbest_http_requests_total{'
                f'method="{method}",path="{path}",status="{status}"'
                f"}} {count}"
            )

        lines.extend(
            [
                "# HELP wefindbest_http_request_latency_ms_total Total request latency in milliseconds.",
                "# TYPE wefindbest_http_request_latency_ms_total counter",
            ]
        )
        for key, latency in sorted(_request_latency_ms.items()):
            method, path, status = key.split(" ", 2)
            lines.append(
                'wefindbest_http_request_latency_ms_total{'
                f'method="{method}",path="{path}",status="{status}"'
                f"}} {latency}"
            )

    return Response("\n".join(lines) + "\n", media_type="text/plain")
