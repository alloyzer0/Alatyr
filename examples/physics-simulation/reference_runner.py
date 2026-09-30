"""Disposable physics adapter harness for Alatyr protocol vectors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VECTOR_DIR = ROOT / "test-vectors" / "physics-simulation"


class PhysicsReference:
    def __init__(self) -> None:
        self.objects: dict[str, dict[str, dict[str, float]]] = {}
        self.handles: dict[str, tuple[int, int]] = {}
        self.slots: list[tuple[int, str | None]] = []
        self.solver_indices: dict[str, int] = {}

    def create(self, persistent_id: str, components: dict[str, dict[str, float]] | None = None) -> None:
        for slot, (generation, current) in enumerate(self.slots):
            if current is None:
                self.slots[slot] = (generation, persistent_id)
                self.handles[persistent_id] = (slot, generation)
                break
        else:
            slot = len(self.slots)
            self.slots.append((1, persistent_id))
            self.handles[persistent_id] = (slot, 1)
        self.objects[persistent_id] = dict(components or {})

    def destroy(self, persistent_id: str) -> None:
        handle = self.handles.pop(persistent_id)
        slot, generation = handle
        current_generation, current_id = self.slots[slot]
        assert current_generation == generation and current_id == persistent_id
        self.slots[slot] = (generation + 1, None)
        self.objects.pop(persistent_id)
        self.solver_indices.pop(persistent_id, None)

    def attach(self, persistent_id: str, component: str, value: dict[str, float]) -> None:
        self.objects[persistent_id][component] = dict(value)

    def detach(self, persistent_id: str, component: str) -> None:
        self.objects[persistent_id].pop(component, None)

    def query(self, required: list[str]) -> list[str]:
        return [
            persistent_id
            for persistent_id, components in self.objects.items()
            if all(component in components for component in required)
        ]

    def integrate(self, dt: float) -> None:
        for components in self.objects.values():
            transform = components.get("Transform")
            velocity = components.get("Velocity")
            if transform is None or velocity is None:
                continue
            transform["x"] += velocity.get("x", 0) * dt
            transform["y"] += velocity.get("y", 0) * dt

    def bind_solver_index(self, persistent_id: str, solver_index: int) -> None:
        self.solver_indices[persistent_id] = solver_index


def run_batch_query(vector: dict[str, Any]) -> None:
    world = PhysicsReference()
    for obj in vector["objects"]:
        world.create(obj["persistent_id"], obj["components"])
    operations = vector["operations"]
    before = world.query(operations[0]["requires"])
    world.integrate(operations[1]["dt"])
    expected = vector["expected"]
    assert before == expected["query_ids"]
    for persistent_id, transform in expected["transforms"].items():
        assert world.objects[persistent_id]["Transform"] == transform
    assert world.objects["body-003"]["Transform"] == {"x": 5, "y": 5}


def run_component_removal(vector: dict[str, Any]) -> None:
    world = PhysicsReference()
    for obj in vector["objects"]:
        world.create(obj["persistent_id"], obj["components"])
    first, detach, second = vector["operations"]
    before = world.query(first["requires"])
    world.detach(detach["persistent_id"], detach["component"])
    after = world.query(second["requires"])
    assert before == vector["expected"]["before"]
    assert after == vector["expected"]["after"]


def run_solver_lifecycle(vector: dict[str, Any]) -> None:
    world = PhysicsReference()
    old_handle = None
    new_handle = None
    for operation in vector["operations"]:
        op = operation["op"]
        if op == "create":
            world.create(operation["persistent_id"])
            if old_handle is None:
                old_handle = world.handles[operation["persistent_id"]]
            else:
                new_handle = world.handles[operation["persistent_id"]]
        elif op == "bind_solver_index":
            world.bind_solver_index(operation["persistent_id"], operation["solver_index"])
        elif op == "destroy":
            world.destroy(operation["persistent_id"])
    assert old_handle != new_handle
    assert old_handle[0] == new_handle[0]
    assert old_handle[1] != new_handle[1]
    assert vector["expected"]["body-002_may_reuse_solver_index"] is True


RUNNERS = {
    "batch-query-and-update": run_batch_query,
    "component-removal-changes-query": run_component_removal,
    "solver-index-is-not-object-identity": run_solver_lifecycle,
}


def main() -> None:
    for path in sorted(VECTOR_DIR.glob("*.json")):
        vector = json.loads(path.read_text())
        RUNNERS[vector["case"]](vector)
        print(f"PASS {path.name}")


if __name__ == "__main__":
    main()
