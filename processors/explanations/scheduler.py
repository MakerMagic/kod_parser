"""Bounded deferred work; transport behavior stays inside each provider."""


def run_deferred_queue(items, step, publish, *, maximum_deferred_cycles):
    deferred = []

    def attempt(item, trigger, after=None):
        step(item, trigger=trigger, after=after)
        publish()
        if item["entry"]["status"] == "provider_failure_deferred":
            deferred.append(item)

    for item in items:
        # Only earlier failures are eligible after this question has completed.
        ready = deferred[:]
        deferred.clear()
        attempt(item, "initial")
        for waiting in ready:
            attempt(waiting, "after_subsequent_question", item["entry"]["identity"])

    # There is no later question for a failure on the last selected item. Drain
    # the remaining queue in at most two explicit, bounded end-of-run sweeps.
    for _ in range(maximum_deferred_cycles):
        if not deferred:
            break
        ready = deferred[:]
        deferred.clear()
        for waiting in ready:
            attempt(waiting, "end_of_run_sweep")
