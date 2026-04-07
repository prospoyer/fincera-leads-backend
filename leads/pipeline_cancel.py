"""Cancellation helpers for long-running pipeline subprocesses."""


def make_cancel_check(run_id):
    """
    Returns a callable for use inside pipeline stages. True means stop work.
    Checks cancel_requested (set by API) or status no longer running.
    """
    if run_id is None:

        def never() -> bool:
            return False

        return never

    def check() -> bool:
        from .models import PipelineRun

        try:
            r = PipelineRun.objects.only("status", "cancel_requested").get(pk=run_id)
            return bool(r.cancel_requested) or r.status != "running"
        except PipelineRun.DoesNotExist:
            return True

    return check
