from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Callable, Iterator, Optional, TypeVar


F = TypeVar("F", bound=Callable[..., Any])

try:  # pragma: no cover - optional dependency
    import langsmith as _langsmith  # type: ignore
    from langsmith import traceable as _langsmith_traceable  # type: ignore
    from langsmith.wrappers import wrap_openai as _wrap_openai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    _langsmith = None
    _langsmith_traceable = None
    _wrap_openai = None


def is_langsmith_available() -> bool:
    return _langsmith is not None and _langsmith_traceable is not None


def is_tracing_enabled() -> bool:
    value = str(os.getenv("LANGSMITH_TRACING", "")).strip().lower()
    return value in {"1", "true", "yes", "on"}


def traceable(*args: Any, **kwargs: Any):
    if _langsmith_traceable is None:
        if args and callable(args[0]) and len(args) == 1 and not kwargs:
            return args[0]

        def decorator(func: F) -> F:
            return func

        return decorator

    return _langsmith_traceable(*args, **kwargs)


def wrap_openai_client(client: Any) -> Any:
    if _wrap_openai is None or not is_tracing_enabled():
        return client
    try:
        return _wrap_openai(client)
    except Exception:
        return client


@contextmanager
def trace_run(
    name: str,
    run_type: str = "chain",
    *,
    inputs: Optional[dict[str, Any]] = None,
    metadata: Optional[dict[str, Any]] = None,
    project_name: Optional[str] = None,
) -> Iterator[Any]:
    if _langsmith is None or not is_tracing_enabled():
        yield None
        return

    kwargs: dict[str, Any] = {}
    if project_name:
        kwargs["project_name"] = project_name
    if inputs is not None:
        kwargs["inputs"] = inputs
    if metadata is not None:
        kwargs["metadata"] = metadata

    with _langsmith.trace(name, run_type, **kwargs) as run_tree:
        yield run_tree


def finish_trace(run_tree: Any, *, outputs: Optional[dict[str, Any]] = None, error: Optional[BaseException] = None) -> None:
    if run_tree is None:
        return
    try:
        if error is not None:
            run_tree.end(error=str(error))
        else:
            run_tree.end(outputs=outputs or {})
    except Exception:
        return
