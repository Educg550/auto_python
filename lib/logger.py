"""
Shared logging and progress utilities for all scripts.

Usage
-----
    from lib.logger import get_logger, progress, track

    log = get_logger(__name__)

    log.debug("verbose detail")
    log.info("all good")
    log.warning("heads up")
    log.error("something failed")
    log.critical("fatal problem")

    # Indeterminate spinner (unknown total)
    with progress() as p:
        task = p.add_task("Fetching…", total=None)
        for item in items:
            do_work(item)
            p.advance(task)

    # Known total
    with progress() as p:
        task = p.add_task("Processing", total=len(items))
        for item in items:
            do_work(item)
            p.advance(task)

    # Convenience iterator (wraps track())
    for item in track(items, description="Processing"):
        do_work(item)
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from contextlib import contextmanager
from typing import Any, Iterator

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    track as _rich_track,
)
from rich.theme import Theme

# ---------------------------------------------------------------------------
# Console
# ---------------------------------------------------------------------------

_THEME = Theme(
    {
        "logging.level.debug": "dim cyan",
        "logging.level.info": "bold green",
        "logging.level.warning": "bold yellow",
        "logging.level.error": "bold red",
        "logging.level.critical": "bold white on red",
    }
)

console = Console(theme=_THEME, highlight=True)

# ---------------------------------------------------------------------------
# Logger factory
# ---------------------------------------------------------------------------


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """Return a named logger wired to Rich's colorful handler.

    Calling this multiple times with the same *name* returns the same logger
    without adding duplicate handlers.

    Args:
        name:  Usually ``__name__`` of the calling module.
        level: Minimum log level. Defaults to ``logging.DEBUG``.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    handler = RichHandler(
        console=console,
        show_time=True,
        show_level=True,
        show_path=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        markup=True,
    )
    handler.setLevel(level)

    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False

    return logger


# ---------------------------------------------------------------------------
# Progress / spinner
# ---------------------------------------------------------------------------


@contextmanager
def progress(
    *,
    transient: bool = False,
    spinner: str = "dots",
) -> Iterator[Progress]:
    """Context manager that yields a :class:`rich.progress.Progress` instance.

    Args:
        transient: If *True* the progress display is erased after completion.
        spinner:   Name of the spinner animation (see ``rich.spinner``).

    Example::

        with progress() as p:
            task = p.add_task("Downloading…", total=100)
            for chunk in stream:
                process(chunk)
                p.advance(task)
    """
    with Progress(
        SpinnerColumn(spinner),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=transient,
    ) as p:
        yield p


def track(
    iterable: Iterable[Any],
    description: str = "Working…",
    total: int | None = None,
) -> Iterable[Any]:
    """Wrap *iterable* with a Rich progress bar.

    A thin convenience wrapper around :func:`rich.progress.track` that feeds
    through the shared console so the output stays consistent with
    :func:`get_logger`.

    Args:
        iterable:    The sequence to iterate over.
        description: Label shown next to the progress bar.
        total:       Override the total count (useful for generators).

    Returns:
        An iterable that yields the same items as *iterable*.
    """
    return _rich_track(
        iterable,
        description=description,
        total=total,
        console=console,
    )
