import unittest

from api.resilience import CircuitBreaker, CircuitOpenError, SlidingWindowLimiter


class ResilienceTests(unittest.TestCase):
    def test_sliding_window_limiter_rejects_after_limit_and_reports_retry(self):
        now = [100.0]
        limiter = SlidingWindowLimiter(limit=2, window_seconds=60, clock=lambda: now[0])

        self.assertTrue(limiter.allow("user-1"))
        self.assertTrue(limiter.allow("user-1"))
        self.assertFalse(limiter.allow("user-1"))
        self.assertGreaterEqual(limiter.retry_after("user-1"), 1)

        now[0] = 161.0
        self.assertTrue(limiter.allow("user-1"))

    def test_circuit_breaker_opens_after_failures_and_recovers(self):
        now = [100.0]
        breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=30, clock=lambda: now[0])

        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("one")))
        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("two")))
        self.assertEqual(breaker.state, "open")
        with self.assertRaises(CircuitOpenError):
            breaker.call(lambda: "blocked")

        now[0] = 131.0
        self.assertEqual(breaker.call(lambda: "recovered"), "recovered")
        self.assertEqual(breaker.state, "closed")


if __name__ == "__main__":
    unittest.main()
