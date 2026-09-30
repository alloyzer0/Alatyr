"""Small disposable reference model for the application-data research branch.

This module is intentionally not the Alatyr API. Its purpose is to make the
protocol questions executable before choosing a production language.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


TypeId = str
PersistentId = str
MISSING = object()


class AlatyrError(Exception):
    """Base error for the reference model."""


class InvalidHandle(AlatyrError):
    pass


class UnknownType(AlatyrError):
    pass


class UnknownField(AlatyrError):
    pass


class SchemaMismatch(AlatyrError):
    pass


class MissingReference(AlatyrError):
    pass


class CorruptData(AlatyrError):
    pass


@dataclass(frozen=True)
class ObjectHandle:
    slot: int
    generation: int


@dataclass
class _Slot:
    generation: int = 1
    persistent_id: PersistentId | None = None
    type_id: TypeId | None = None
    alive: bool = False


class ObjectStore:
    """Generational runtime handles with a separate persistent identity."""

    def __init__(self) -> None:
        self._slots: list[_Slot] = []
        self._by_persistent: dict[PersistentId, ObjectHandle] = {}

    def create(self, type_id: TypeId, persistent_id: PersistentId) -> ObjectHandle:
        if persistent_id in self._by_persistent:
            raise AlatyrError(f"duplicate persistent id: {persistent_id}")

        for slot_index, slot in enumerate(self._slots):
            if not slot.alive:
                slot.alive = True
                slot.type_id = type_id
                slot.persistent_id = persistent_id
                handle = ObjectHandle(slot_index, slot.generation)
                self._by_persistent[persistent_id] = handle
                return handle

        slot_index = len(self._slots)
        self._slots.append(_Slot(persistent_id=persistent_id, type_id=type_id, alive=True))
        handle = ObjectHandle(slot_index, 1)
        self._by_persistent[persistent_id] = handle
        return handle

    def _slot(self, handle: ObjectHandle) -> _Slot:
        if handle.slot < 0 or handle.slot >= len(self._slots):
            raise InvalidHandle(f"invalid slot: {handle}")
        slot = self._slots[handle.slot]
        if not slot.alive or slot.generation != handle.generation:
            raise InvalidHandle(f"stale handle: {handle}")
        return slot

    def is_alive(self, handle: ObjectHandle) -> bool:
        try:
            self._slot(handle)
        except InvalidHandle:
            return False
        return True

    def describe(self, handle: ObjectHandle) -> tuple[TypeId, PersistentId]:
        slot = self._slot(handle)
        assert slot.type_id is not None and slot.persistent_id is not None
        return slot.type_id, slot.persistent_id

    def handle_for(self, persistent_id: PersistentId) -> ObjectHandle | None:
        handle = self._by_persistent.get(persistent_id)
        if handle is None or not self.is_alive(handle):
            return None
        return handle

    def destroy(self, handle: ObjectHandle) -> None:
        slot = self._slot(handle)
        assert slot.persistent_id is not None
        self._by_persistent.pop(slot.persistent_id, None)
        slot.persistent_id = None
        slot.type_id = None
        slot.alive = False
        slot.generation += 1


@dataclass(frozen=True)
class FieldDesc:
    field_id: str
    value_type: str
    required: bool = False
    default: Any = MISSING


@dataclass(frozen=True)
class Migration:
    from_version: int
    to_version: int
    rename: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TypeDesc:
    type_id: TypeId
    version: int
    fields: tuple[FieldDesc, ...]
    migrations: tuple[Migration, ...] = ()
    allow_dynamic_fields: bool = False

    def field_map(self) -> dict[str, FieldDesc]:
        return {field.field_id: field for field in self.fields}


class SchemaRegistry:
    def __init__(self) -> None:
        self._types: dict[TypeId, dict[int, TypeDesc]] = {}

    def register(self, desc: TypeDesc) -> None:
        versions = self._types.setdefault(desc.type_id, {})
        if desc.version in versions:
            raise AlatyrError(f"duplicate schema: {desc.type_id}@{desc.version}")
        versions[desc.version] = desc

    def latest(self, type_id: TypeId) -> TypeDesc:
        try:
            return max(self._types[type_id].values(), key=lambda desc: desc.version)
        except KeyError as exc:
            raise UnknownType(type_id) from exc

    def version(self, type_id: TypeId, number: int) -> TypeDesc:
        try:
            return self._types[type_id][number]
        except KeyError as exc:
            raise SchemaMismatch(f"missing schema: {type_id}@{number}") from exc

    def migrate(self, type_id: TypeId, source_version: int, payload: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        target = self.latest(type_id)
        current_version = source_version
        result = dict(payload)

        while current_version < target.version:
            current = self.version(type_id, current_version)
            next_versions = [
                desc
                for desc in self._types[type_id].values()
                if desc.version > current_version
            ]
            if not next_versions:
                raise SchemaMismatch(f"cannot migrate {type_id}@{current_version}")
            next_desc = min(next_versions, key=lambda desc: desc.version)
            migration = next(
                (item for item in next_desc.migrations if item.from_version == current.version and item.to_version == next_desc.version),
                None,
            )
            if migration is None:
                raise SchemaMismatch(f"missing migration: {type_id}@{current.version}->{next_desc.version}")
            for old_name, new_name in migration.rename.items():
                if old_name in result:
                    result[new_name] = result.pop(old_name)
            current_version = next_desc.version

        if current_version > target.version:
            raise SchemaMismatch(f"downgrade is unsupported: {type_id}@{source_version}")

        fields = target.field_map()
        if not target.allow_dynamic_fields:
            unknown = set(result) - set(fields)
            if unknown:
                raise UnknownField(f"unknown fields for {type_id}: {sorted(unknown)}")

        for field_desc in target.fields:
            if field_desc.field_id not in result and field_desc.default is not MISSING:
                result[field_desc.field_id] = field_desc.default
            if field_desc.required and field_desc.field_id not in result:
                raise SchemaMismatch(f"missing required field: {type_id}.{field_desc.field_id}")

        return target.version, result


class PropertyStore:
    def __init__(self, objects: ObjectStore) -> None:
        self._objects = objects
        self._values: dict[ObjectHandle, dict[str, Any]] = {}

    def set(self, handle: ObjectHandle, field_id: str, value: Any) -> None:
        self._objects._slot(handle)
        self._values.setdefault(handle, {})[field_id] = value

    def get(self, handle: ObjectHandle, field_id: str) -> Any:
        self._objects._slot(handle)
        return self._values[handle][field_id]

    def snapshot(self, handle: ObjectHandle) -> dict[str, Any]:
        self._objects._slot(handle)
        return dict(self._values.get(handle, {}))

    def remove(self, handle: ObjectHandle) -> None:
        self._values.pop(handle, None)


class ComponentStore:
    """Reference component store; layout is intentionally replaceable."""

    def __init__(self, objects: ObjectStore) -> None:
        self._objects = objects
        self._values: dict[str, dict[ObjectHandle, Any]] = {}

    def attach(self, handle: ObjectHandle, component_type: str, value: Any) -> None:
        self._objects._slot(handle)
        self._values.setdefault(component_type, {})[handle] = value

    def get(self, handle: ObjectHandle, component_type: str) -> Any:
        self._objects._slot(handle)
        return self._values[component_type][handle]

    def detach(self, handle: ObjectHandle, component_type: str) -> None:
        self._values.get(component_type, {}).pop(handle, None)

    def query(self, component_types: Iterable[str]) -> list[ObjectHandle]:
        required = list(component_types)
        if not required:
            return []
        candidates = set(self._values.get(required[0], {}))
        for component_type in required[1:]:
            candidates.intersection_update(self._values.get(component_type, {}))
        return sorted(candidates, key=lambda handle: (handle.slot, handle.generation))

    def remove_entity(self, handle: ObjectHandle) -> None:
        for values in self._values.values():
            values.pop(handle, None)


class ObjectCentricComponentStore:
    """Alternative layout with the same access semantics as ComponentStore."""

    def __init__(self, objects: ObjectStore) -> None:
        self._objects = objects
        self._values: dict[ObjectHandle, dict[str, Any]] = {}

    def attach(self, handle: ObjectHandle, component_type: str, value: Any) -> None:
        self._objects._slot(handle)
        self._values.setdefault(handle, {})[component_type] = value

    def get(self, handle: ObjectHandle, component_type: str) -> Any:
        self._objects._slot(handle)
        return self._values[handle][component_type]

    def detach(self, handle: ObjectHandle, component_type: str) -> None:
        values = self._values.get(handle)
        if values is None:
            return
        values.pop(component_type, None)
        if not values:
            self._values.pop(handle, None)

    def query(self, component_types: Iterable[str]) -> list[ObjectHandle]:
        required = set(component_types)
        if not required:
            return []
        return sorted(
            [
                handle
                for handle, values in self._values.items()
                if required.issubset(values)
            ],
            key=lambda handle: (handle.slot, handle.generation),
        )

    def remove_entity(self, handle: ObjectHandle) -> None:
        self._values.pop(handle, None)


class World:
    """Candidate lifecycle coordinator for the reference model."""

    def __init__(self) -> None:
        self.objects = ObjectStore()
        self.properties = PropertyStore(self.objects)
        self.components = ComponentStore(self.objects)

    def destroy(self, handle: ObjectHandle) -> None:
        self.properties.remove(handle)
        self.components.remove_entity(handle)
        self.objects.destroy(handle)


@dataclass(frozen=True)
class Envelope:
    type_id: TypeId
    schema_version: int
    persistent_id: PersistentId
    payload: dict[str, Any]
    external_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "type_id": self.type_id,
            "schema_version": self.schema_version,
            "persistent_id": self.persistent_id,
            "payload": self.payload,
            "external_references": list(self.external_references),
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Envelope":
        required = {"type_id", "schema_version", "persistent_id", "payload"}
        missing = required - set(raw)
        if missing or not isinstance(raw.get("payload"), dict):
            raise CorruptData(f"invalid envelope, missing={sorted(missing)}")
        return cls(
            type_id=raw["type_id"],
            schema_version=raw["schema_version"],
            persistent_id=raw["persistent_id"],
            payload=dict(raw["payload"]),
            external_references=tuple(raw.get("external_references", [])),
        )


@dataclass(frozen=True)
class OpaqueObject:
    envelope: Envelope


@dataclass(frozen=True)
class LoadResult:
    handle: ObjectHandle | None = None
    opaque: OpaqueObject | None = None


class PersistenceService:
    def __init__(self, objects: ObjectStore, properties: PropertyStore, schemas: SchemaRegistry) -> None:
        self.objects = objects
        self.properties = properties
        self.schemas = schemas

    def save(self, handle: ObjectHandle) -> Envelope:
        type_id, persistent_id = self.objects.describe(handle)
        schema = self.schemas.latest(type_id)
        _, payload = self.schemas.migrate(type_id, schema.version, self.properties.snapshot(handle))
        return Envelope(type_id, schema.version, persistent_id, payload)

    def load(self, envelope: Envelope) -> LoadResult:
        try:
            latest_version, payload = self.schemas.migrate(
                envelope.type_id,
                envelope.schema_version,
                envelope.payload,
            )
        except UnknownType:
            return LoadResult(opaque=OpaqueObject(envelope))

        handle = self.objects.create(envelope.type_id, envelope.persistent_id)
        for field_id, value in payload.items():
            self.properties.set(handle, field_id, value)
        assert latest_version == self.schemas.latest(envelope.type_id).version
        return LoadResult(handle=handle)


@dataclass(frozen=True)
class Reference:
    kind: str
    target: PersistentId


class ReferenceResolver:
    def __init__(self, objects: ObjectStore) -> None:
        self.objects = objects

    def resolve(self, reference: Reference) -> ObjectHandle | None:
        handle = self.objects.handle_for(reference.target)
        if handle is not None:
            return handle
        if reference.kind == "strong":
            raise MissingReference(reference.target)
        return None
