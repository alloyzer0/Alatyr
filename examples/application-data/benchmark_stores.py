"""Exploratory comparison of the two reference component layouts.

Numbers are machine- and interpreter-dependent. They are evidence for the
research branch only; they must not be treated as Alatyr performance claims.
"""

from __future__ import annotations

import time
import tracemalloc

from reference_model import ComponentStore, ObjectCentricComponentStore, ObjectStore


def measure(store_type: type, count: int = 10_000) -> dict[str, float | int]:
    tracemalloc.start()
    started = time.perf_counter()
    objects = ObjectStore()
    store = store_type(objects)
    handles = [objects.create("example.Task", f"task-{index}") for index in range(count)]
    created = time.perf_counter()

    for handle in handles:
        store.attach(handle, "Tag", "task")
        store.attach(handle, "Counter", 1)
    attached = time.perf_counter()
    matches = store.query(["Tag", "Counter"])
    queried = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "objects": count,
        "matches": len(matches),
        "create_ms": (created - started) * 1000,
        "attach_ms": (attached - created) * 1000,
        "query_ms": (queried - attached) * 1000,
        "peak_kib": peak / 1024,
        "current_kib": current / 1024,
    }


def main() -> None:
    for name, store_type in (
        ("component-centric", ComponentStore),
        ("object-centric", ObjectCentricComponentStore),
    ):
        result = measure(store_type)
        print(name)
        for key, value in result.items():
            print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")


if __name__ == "__main__":
    main()
