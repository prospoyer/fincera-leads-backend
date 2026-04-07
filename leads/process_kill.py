"""Terminate a Unix process group (Railway / Linux)."""

from __future__ import annotations

import errno
import os
import signal
import time


def terminate_process_group(pgid: int, *, grace_sec: float = 5.0) -> None:
    """
    Send SIGTERM to every process in the group, wait, then SIGKILL if needed.
    pgid is the process group id (session leader pid from Popen(..., start_new_session=True)).
    No-op if pgid is missing or invalid; ignores ESRCH if already exited.
    """
    if not pgid or pgid <= 0:
        return

    try:
        os.kill(-pgid, signal.SIGTERM)
    except OSError as e:
        if e.errno == errno.ESRCH:
            return
        raise

    deadline = time.monotonic() + grace_sec
    while time.monotonic() < deadline:
        try:
            os.kill(-pgid, 0)
        except OSError as e:
            if e.errno == errno.ESRCH:
                return
            raise
        time.sleep(0.15)

    try:
        os.kill(-pgid, signal.SIGKILL)
    except OSError as e:
        if e.errno == errno.ESRCH:
            return
        raise
