from opt_data.util.ratelimit import TokenBucket


def test_token_bucket_refill_and_acquire() -> None:
    fake_time = [0.0]

    def now() -> float:
        return fake_time[0]

    tb = TokenBucket.create(capacity=2, refill_per_minute=60, time_fn=now)
    assert tb.try_acquire()  # 1 -> left 1
    assert tb.try_acquire()  # 2 -> left 0
    assert not tb.try_acquire()  # no token

    # advance 1 second, 1 token should refill (60/min -> 1/sec)
    fake_time[0] += 1.0
    assert tb.try_acquire()  # token available again
