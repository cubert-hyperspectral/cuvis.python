"""What the polling costs on the worker path: per-result latency and idle CPU.

The worker is the clearest case. `Worker.get_next_result_async` sleeps 100 ms between
checks, so a result that arrives just after a check waits out the rest of the interval;
`register_worker_callback` spins at 1 ms, which is pure CPU with nothing to show for it.
"""

import asyncio
import statistics
import time

import cuvis

cuvis.init(".")
session = cuvis.SessionFile("tests/test_data/test_mesu.cu3s")


def built_worker():
    pc = cuvis.ProcessingContext(session)
    pc.processing_mode = cuvis.ProcessingMode.Raw
    worker = cuvis.Worker(cuvis.WorkerSettings(output_queue_size=8))
    worker.set_processing_context(pc)
    worker.start_processing()
    return worker


def report(label, samples):
    print(
        "{:36} median {:7.2f} ms   mean {:7.2f} ms   max {:7.2f} ms".format(
            label, statistics.median(samples), statistics.mean(samples), max(samples)
        )
    )


async def result_latency(rounds=12):
    """Time from ingesting one frame to the awaited result coming back."""
    worker = built_worker()
    samples = []
    try:
        for _ in range(rounds):
            start = time.perf_counter()
            worker.ingest_session_file(session, frame_selection="0")
            await worker.get_next_result_async(10000)
            samples.append((time.perf_counter() - start) * 1000)
    finally:
        worker.stop_processing()
        worker.drop_all_queued()
        worker.reset_worker_callback()
    return samples


def blocking_latency(rounds=12):
    """The same, straight through the SDK's own blocking wait."""
    worker = built_worker()
    samples = []
    try:
        for _ in range(rounds):
            start = time.perf_counter()
            worker.ingest_session_file(session, frame_selection="0")
            worker.get_next_result(10000)
            samples.append((time.perf_counter() - start) * 1000)
    finally:
        worker.stop_processing()
        worker.drop_all_queued()
    return samples


async def idle_cpu(seconds=8.0):
    """CPU spent by an event loop with one registered callback and nothing to do."""
    worker = built_worker()
    worker.register_worker_callback(lambda result: asyncio.sleep(0))
    cpu, wall = time.process_time(), time.perf_counter()
    await asyncio.sleep(seconds)
    used = 100.0 * (time.process_time() - cpu) / (time.perf_counter() - wall)
    worker.reset_worker_callback()
    worker.stop_processing()
    return used


async def main():
    report("worker result, blocking", blocking_latency())
    report("worker result, awaited", await result_latency())
    print(
        "{:36} {:.1f} % of one core".format(
            "registered callback, idle", await idle_cpu()
        )
    )


asyncio.run(main())
