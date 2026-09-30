"""Temporary, language-neutral-ish protocol vector runner.

This is a research harness, not Alatyr's production implementation. It is
intentionally small and exists to expose missing protocol semantics before a
Rust/Zig/C++ implementation is selected.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VECTOR_DIR = ROOT / "test-vectors" / "application-data"


def field_map(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {field["id"]: field for field in schema.get("fields", [])}


def apply_defaults(payload: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    for field in schema.get("fields", []):
        if field["id"] not in result and "default" in field:
            result[field["id"]] = copy.deepcopy(field["default"])
    return result


def run_roundtrip(vector: dict[str, Any]) -> None:
    schema = vector["schemas"][0]
    object_data: dict[str, Any] = {}
    saved: dict[str, Any] | None = None

    for operation in vector["operations"]:
        op = operation["op"]
        if op == "create":
            object_data = {
                "type_id": operation["type_id"],
                "schema_version": schema["version"],
                "persistent_id": operation["persistent_id"],
                "payload": {},
            }
        elif op == "set":
            object_data["payload"][operation["field"]] = operation["value"]
        elif op == "save":
            saved = copy.deepcopy(object_data)
        elif op == "load":
            object_data = copy.deepcopy(saved)
            object_data["payload"] = apply_defaults(object_data["payload"], schema)
        else:
            raise ValueError(f"unsupported roundtrip operation: {op}")

    expected = vector["expected"]
    assert object_data["type_id"] == expected["loaded_type_id"]
    assert object_data["schema_version"] == expected["loaded_schema_version"]
    assert object_data["persistent_id"] == expected["loaded_persistent_id"]
    assert object_data["payload"] == expected["fields"]


def migrate_payload(payload: dict[str, Any], source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    for migration in target.get("migrations", []):
        if migration["from"] == source["version"] and migration["to"] == target["version"]:
            for old_name, new_name in migration.get("rename", {}).items():
                if old_name in result:
                    result[new_name] = result.pop(old_name)
    return apply_defaults(result, target)


def run_migration(vector: dict[str, Any]) -> None:
    source, target = vector["schemas"]
    input_data = vector["input"]
    migrated = migrate_payload(input_data["payload"], source, target)
    repeated = migrate_payload(migrated, target, target)
    expected = vector["expected"]
    assert target["version"] == expected["schema_version"]
    assert migrated == expected["payload"]
    assert repeated == migrated


def run_unknown_type(vector: dict[str, Any]) -> None:
    input_data = vector["input"]
    preserved = copy.deepcopy(input_data)
    expected = vector["expected"]
    assert expected["result"] == "opaque-preserved"
    assert preserved["type_id"] == expected["type_id"]
    assert preserved["schema_version"] == expected["schema_version"]
    assert preserved["payload"] == input_data["payload"]


def run_references(vector: dict[str, Any]) -> None:
    objects: dict[str, dict[str, Any]] = {}
    reference: str | None = None
    document_survives = False

    for operation in vector["operations"]:
        op = operation["op"]
        if op == "create":
            objects[operation["persistent_id"]] = {"type_id": operation["type_id"]}
        elif op == "set-reference":
            reference = operation["to"]
        elif op == "destroy":
            objects.pop(operation["persistent_id"], None)
        elif op == "resolve-reference":
            document_survives = operation["from"] in objects
            assert reference not in objects
        else:
            raise ValueError(f"unsupported reference operation: {op}")

    expected = vector["expected"]
    assert expected["reference_result"] == "missing-reference"
    assert document_survives == expected["document_survives"]


RUNNERS = {
    "application-data-roundtrip": run_roundtrip,
    "field-rename-and-default-migration": run_migration,
    "unknown-type-preservation": run_unknown_type,
    "reference-and-deletion-semantics": run_references,
}


def main() -> None:
    files = sorted(VECTOR_DIR.glob("*.json"))
    for path in files:
        vector = json.loads(path.read_text())
        RUNNERS[vector["case"]](vector)
        print(f"PASS {path.name}")


if __name__ == "__main__":
    main()
