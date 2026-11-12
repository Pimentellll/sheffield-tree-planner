"""Exercise synthetic job bookkeeping through real temporary SQLite stores."""

import os
import tempfile
import threading
import unittest
from pathlib import Path

from probe import ProbeError, Record, Store


class ProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "jobs.sqlite"
        self.store = Store(self.path)
        self.addCleanup(self.store.close)
        self.store.activate("s", 1)

    def accept(
        self,
        job: str,
        request: str | None = None,
        operation: str = "evaluate_layout",
        scenario: str = "s",
        revision: int = 1,
        scope: str = "accepted",
        fingerprint: str = "full",
        payload: str = "input",
        deadline: float | None = None,
    ) -> Record:
        """Accept an opaque synthetic request with deterministic test defaults."""
        return self.store.accept(
            job,
            request or job,
            operation,
            scenario,
            revision,
            scope,
            fingerprint,
            payload,
            deadline,
        )

    def complete(self, job: str, run: str | None = None) -> None:
        """Finish a non-deadline synthetic job without numerical fixtures."""
        self.store.start(job)
        self.store.finish(
            job, "complete", run_id=run or "run-" + job, token="synthetic-token"
        )

    def test_accepted_job_is_persisted_before_work(self) -> None:
        job = self.accept("j1")
        self.assertIsNotNone(job)
        self.assertEqual((job["status"], job["selection_seq"]), ("queued", 1))
        other = Store(self.path)
        try:
            self.assertEqual(other.job("j1"), job)
        finally:
            other.close()

    def test_concurrent_acceptance_serializes_independent_connections(self) -> None:
        barrier = threading.Barrier(8)
        results, errors = [], []
        lock = threading.Lock()

        def submit(i: int) -> None:
            connection = None
            try:
                connection = Store(self.path)
                barrier.wait(timeout=10)
                job = connection.accept(
                    str(i),
                    str(i),
                    "evaluate_layout",
                    "s",
                    1,
                    "accepted",
                    "full",
                    "input",
                )
                with lock:
                    results.append(job)
            except Exception as exc:  # noqa: BLE001
                # Report worker-thread failures on the main test thread.
                with lock:
                    errors.append(exc)
            finally:
                if connection:
                    connection.close()

        threads = [threading.Thread(target=submit, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=20)
        self.assertFalse(any(t.is_alive() for t in threads))
        self.assertEqual(errors, [])
        self.assertEqual(sorted(j["selection_seq"] for j in results), list(range(1, 9)))
        newest = max(results, key=lambda j: j["selection_seq"])
        self.complete(newest["job_id"])
        self.assertEqual(
            self.store.current("s", 1, "accepted", "evaluation")["job_id"],
            newest["job_id"],
        )

    def test_supersession_fail_cancel_slots_and_scope(self) -> None:
        self.accept("old")
        self.store.start("old")
        self.accept("new")
        self.accept("search", operation="search_layouts")
        self.complete("search")
        self.store.finish("old", "complete", run_id="old-run", token="synthetic-token")
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))
        self.store.finish("new", "fail")
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))
        self.assertEqual(
            self.store.current("s", 1, "accepted", "search")["job_id"], "search"
        )
        self.accept("newest")
        self.store.finish("newest", "cancel")
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))
        self.accept("hyp", scope="hypothetical")
        self.complete("hyp")
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))
        self.assertEqual(
            self.store.current("s", 1, "hypothetical", "evaluation")["job_id"], "hyp"
        )
        self.store.activate("s", 2)
        self.assertIsNone(self.store.current("s", 1, "accepted", "search"))
        self.store.activate("another", 1)
        self.assertIsNone(self.store.current("s", 1, "accepted", "search"))
        self.assertEqual(self.store.run("old-run")["source_job_id"], "old")

    def test_idempotency_admission_and_rollback(self) -> None:
        self.store.capacity = 2
        first = self.accept("one", request="request")
        self.accept("other", operation="search_layouts")
        self.assertEqual(self.accept("unused", request="request"), first)
        with self.assertRaises(ProbeError):
            self.accept("other", request="request")
        with self.assertRaises(ProbeError):
            self.accept("conflict", request="request", payload="changed")
        with self.assertRaises(ProbeError):
            self.accept("other", request="different")
        with self.assertRaises(ProbeError):
            self.accept("full")
        self.assertIsNone(self.store.job("full"))
        self.assertEqual(self.store.job("other")["status"], "queued")
        self.store.finish("other", "cancel")
        self.assertEqual(self.accept("next")["selection_seq"], 2)
        self.store.start("one")
        self.store.finish("one", "complete", run_id="unique", token="synthetic-token")
        self.store.start("next")
        with self.assertRaises(ProbeError):
            self.store.finish(
                "next", "complete", run_id="unique", token="synthetic-token"
            )
        self.assertEqual(self.store.job("next")["status"], "running")
        self.assertEqual(self.store.run("unique")["source_job_id"], "one")

    def test_cache_identity_and_original_provenance(self) -> None:
        self.accept("source")
        self.complete("source", "run")
        original = self.store.run("run")
        for i, changes in enumerate(
            (
                {"fingerprint": "wrong"},
                {"revision": 2},
                {"scope": "hypothetical"},
                {"payload": "different"},
                {"scenario": "different"},
                {"operation": "search_layouts"},
            )
        ):
            job = "bad" + str(i)
            self.accept(job, **changes)
            with self.assertRaises(ProbeError):
                self.store.deliver_cached(job, "run")
            self.assertEqual(self.store.job(job)["status"], "queued")
        self.accept("reuse")
        self.store.deliver_cached("reuse", "run")
        delivery = self.store.current("s", 1, "accepted", "evaluation")
        self.assertEqual(
            (
                delivery["job_id"],
                delivery["source_job_id"],
                delivery["run_id"],
                delivery["mode"],
            ),
            ("reuse", "source", "run", "cached"),
        )
        self.assertEqual(self.store.run("run"), original)

    def test_terminal_callbacks_deadline_and_running_limit(self) -> None:
        self.store.running_limit = 1
        self.accept("running", deadline=10)
        self.store.start("running")
        self.accept("queued")
        with self.assertRaises(ProbeError):
            self.store.start("queued")
        with self.assertRaises(ProbeError):
            self.store.finish("running", "expire", now=9)
        self.store.finish("running", "expire", now=10)
        self.assertEqual(self.store.job("running")["error"], "DEADLINE_EXCEEDED")
        self.store.finish("queued", "cancel")
        for job in ("running", "queued"):
            for action in ("complete", "fail", "cancel"):
                self.assertFalse(
                    self.store.finish(
                        job, action, run_id="late", token="synthetic-token"
                    )
                )
            self.assertIsNone(self.store.job(job)["run_id"])
            self.assertEqual(
                self.store.history(job)[-3:],
                ["late:complete", "late:fail", "late:cancel"],
            )
        self.accept("running-cancel")
        self.store.start("running-cancel")
        self.store.finish("running-cancel", "cancel")
        self.assertFalse(
            self.store.finish(
                "running-cancel", "complete", run_id="late", token="synthetic-token"
            )
        )
        self.accept("completed")
        self.complete("completed")
        self.assertFalse(self.store.finish("completed", "fail"))
        self.assertEqual(self.store.job("completed")["status"], "completed")

    def test_completion_at_deadline_cannot_publish_success(self) -> None:
        self.accept("overdue", deadline=10)
        self.store.start("overdue")
        self.store.finish(
            "overdue", "complete", run_id="late-run", token="synthetic-token", now=10
        )
        self.assertEqual(self.store.job("overdue")["status"], "failed")
        self.assertEqual(self.store.job("overdue")["error"], "DEADLINE_EXCEEDED")
        self.assertIsNone(self.store.run("late-run"))
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))

    def test_deadline_delivery_requires_a_finite_clock(self) -> None:
        self.accept("clocked", deadline=10)
        self.store.start("clocked")
        for clock in (None, float("nan"), float("inf"), True, 2**53 + 3):
            with self.subTest(clock=clock), self.assertRaises(ProbeError):
                self.store.finish(
                    "clocked",
                    "complete",
                    run_id="clock-run",
                    token="synthetic-token",
                    now=clock,
                )
            self.assertEqual(self.store.job("clocked")["status"], "running")
            self.assertIsNone(self.store.run("clock-run"))
        self.store.finish(
            "clocked", "complete", run_id="clock-run", token="synthetic-token", now=9
        )
        self.assertEqual(
            self.store.current("s", 1, "accepted", "evaluation")["job_id"], "clocked"
        )

    def test_cache_deadline_preserves_source_and_never_falls_back(self) -> None:
        self.accept("source")
        self.complete("source", "source-run")
        original = self.store.run("source-run")
        self.accept("cached", deadline=10)
        with self.assertRaises(ProbeError):
            self.store.deliver_cached("cached", "source-run")
        self.assertEqual(self.store.job("cached")["status"], "queued")
        self.assertTrue(self.store.deliver_cached("cached", "source-run", now=9))
        self.assertEqual(self.store.job("cached")["mode"], "cached")
        self.accept("expired-cache", deadline=10)
        self.assertFalse(
            self.store.deliver_cached("expired-cache", "source-run", now=10)
        )
        self.assertEqual(self.store.job("expired-cache")["error"], "DEADLINE_EXCEEDED")
        self.assertIsNone(self.store.job("expired-cache")["run_id"])
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))
        self.assertEqual(self.store.run("source-run"), original)

    def test_invalid_identity_deadline_and_limits_do_not_mutate_selection(self) -> None:
        self.assertEqual(self.accept("first")["selection_seq"], 1)
        for revision in (True, 0, -1, 1.5, "1"):
            with self.subTest(revision=revision), self.assertRaises(ProbeError):
                self.accept("invalid", revision=revision)
        for deadline in (float("nan"), float("inf"), True, "soon", 10**10000):
            with (
                self.subTest(deadline_type=type(deadline).__name__),
                self.assertRaises(ProbeError),
            ):
                self.accept("invalid", deadline=deadline)
        for limit in (True, 0, -1, 1.5):
            with self.subTest(limit=limit), self.assertRaises(ProbeError):
                Store(self.path, capacity=limit)
        self.assertIsNone(self.store.job("invalid"))
        self.assertEqual(self.store.history("invalid"), [])
        self.assertEqual(self.accept("next")["selection_seq"], 2)

    def test_lossy_deadline_is_rejected_before_acceptance(self) -> None:
        deadline = 2**53 + 3
        with self.assertRaises(ProbeError):
            self.accept("lossy", deadline=deadline)
        self.assertIsNone(self.store.job("lossy"))
        self.assertEqual(self.accept("next")["selection_seq"], 1)

    def test_exact_large_deadline_preserves_retry_and_delivery_boundaries(self) -> None:
        deadline = 2**53 + 2
        original = self.accept("live", request="stable", deadline=deadline)
        self.assertEqual(original["deadline"], float(deadline))
        self.assertEqual(
            self.accept("retry", request="stable", deadline=deadline), original
        )
        self.store.start("live")
        self.store.finish(
            "live", "complete", run_id="late-run", token="synthetic-token", now=deadline
        )
        self.assertEqual(self.store.job("live")["error"], "DEADLINE_EXCEEDED")
        self.assertIsNone(self.store.run("late-run"))
        self.accept("source")
        self.complete("source", "source-run")
        source = self.store.run("source-run")
        self.accept("cache", deadline=deadline)
        self.assertFalse(self.store.deliver_cached("cache", "source-run", now=deadline))
        self.assertEqual(self.store.job("cache")["error"], "DEADLINE_EXCEEDED")
        self.assertIsNone(self.store.current("s", 1, "accepted", "evaluation"))
        self.assertEqual(self.store.run("source-run"), source)

    def test_explicit_recovery_persists_and_leaves_others(self) -> None:
        self.accept("abandoned")
        self.store.start("abandoned")
        self.accept("waiting", operation="search_layouts")
        self.accept("done", operation="compare_locations")
        self.complete("done")
        self.store.close()
        second = Store(self.path)
        try:
            self.assertEqual(second.job("abandoned")["status"], "running")
            self.assertEqual(second.recover_exclusive_startup(), 1)
        finally:
            second.close()
        third = Store(self.path)
        try:
            self.assertEqual(third.job("abandoned")["error"], "WORKER_INTERRUPTED")
            self.assertEqual(third.job("waiting")["status"], "queued")
            self.assertEqual(third.job("done")["status"], "completed")
            self.assertEqual(
                third.history("abandoned"),
                ["queued", "running", "failed:WORKER_INTERRUPTED"],
            )
            self.assertEqual(third.recover_exclusive_startup(), 0)
        finally:
            third.close()


if __name__ == "__main__":
    unittest.main()
