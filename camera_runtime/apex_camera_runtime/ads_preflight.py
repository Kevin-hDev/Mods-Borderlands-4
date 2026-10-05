"""One bounded, read-only compatibility job owned by the shared ADS bridge."""
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from .ads_feedback import exception_kind, native_failure_kind, native_status_code

# The shared budget starts on the elected mod's first enabled third-person preparation.
TIMEOUT_SECONDS = 30.0


class Preflight:
    def __init__(self, verify, log):
        self._verify, self._log = verify, log
        self.future = None
        self._failed = self._reported = False
        self._started = None
        self._finished = None
        self.failure = self.error_kind = None
        self.native_reason = None
        self.native_status = None

    def _run(self):
        started = perf_counter()
        try:
            status = self._verify()
        finally:
            # Include a delayed worker start, but not late polling of a result already ready.
            self._finished = perf_counter()
        return status, (self._finished - started) * 1000

    def start(self):
        if self.future is not None or self._failed:
            return
        self._started = perf_counter()
        try:
            executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="camera-compat")
            try:
                self.future = executor.submit(self._run)
            finally:
                # No more jobs: drain this bounded file read, then retire the worker immediately.
                # The Future keeps its result; Python also joins registered workers at shutdown.
                executor.shutdown(wait=False)
        except Exception as error:
            self._failed = True
            self.failure, self.error_kind = "worker_exception", exception_kind(error)

    def result(self):
        self.start()
        elapsed = (perf_counter() - self._started) * 1000
        if not self._failed and not self.future.done():
            if elapsed < TIMEOUT_SECONDS * 1000:
                return None
            # A running native read cannot be interrupted; abandon its result and never install late.
            self.future.cancel()
            self._failed, self.failure = True, "verification_timeout"
        try:
            status, _ = (1, elapsed) if self._failed else self.future.result()
            if self._finished is not None:
                elapsed = (self._finished - self._started) * 1000
            if not self._failed and elapsed >= TIMEOUT_SECONDS * 1000:
                self._failed, self.failure = True, "verification_timeout"
            ready = not self._failed and type(status) is int and status == 0
            if not ready and self.failure is None:
                self.failure = "verification_refused"
                self.native_status = status
                self.native_reason = native_failure_kind(status)
        except Exception as error:
            ready = False
            self._failed = True
            self.failure, self.error_kind = "verification_exception", exception_kind(error)
        if not self._reported:
            self._reported = True
            # SDK logging stays on the caller, never in the disk worker.
            self._log(f"aiming compatibility {'ready' if ready else 'refused'}; "
                      f"background verification elapsed_ms={elapsed:.0f} "
                      f"reason={self.native_reason or self.failure or 'verified'} "
                      f"native_status={'none' if self.native_status is None else native_status_code(self.native_status)} "
                      f"error_type={self.error_kind or 'none'}")
        return ready
