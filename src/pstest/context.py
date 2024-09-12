import contextlib
import resource
import signal
from contextlib import redirect_stdout, nullcontext


class redirect_stdin(contextlib._RedirectStream):
    """Context manager for temporarily receiving stdin from another source."""
    _stream = "stdin"


@contextlib.contextmanager
def timeout(seconds: float):
    def _handler(signum, frame):
        raise TimeoutError("Time Limit Exceeded")
    signal.signal(signal.SIGALRM, _handler)
    signal.setitimer(signal.ITIMER_REAL, seconds)

    try:
        yield
    except TimeoutError:
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


@contextlib.contextmanager
def memory_limit(size: int):
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    resource.setrlimit(resource.RLIMIT_AS, (size, hard))

    try:
        yield
    finally:
        resource.setrlimit(resource.RLIMIT_AS, (soft, hard))
