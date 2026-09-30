import unittest

from reference_model import (
    ComponentStore,
    Envelope,
    FieldDesc,
    InvalidHandle,
    Migration,
    MissingReference,
    ObjectStore,
    ObjectCentricComponentStore,
    PersistenceService,
    PropertyStore,
    Reference,
    ReferenceResolver,
    SchemaRegistry,
    TypeDesc,
)


class ReferenceModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.objects = ObjectStore()
        self.properties = PropertyStore(self.objects)
        self.components = ComponentStore(self.objects)
        self.schemas = SchemaRegistry()
        self.persistence = PersistenceService(self.objects, self.properties, self.schemas)

    def test_handle_generation_and_cleanup(self) -> None:
        handle = self.objects.create("example.Task", "task-001")
        self.properties.set(handle, "title", "first")
        self.objects.destroy(handle)
        self.properties.remove(handle)

        self.assertFalse(self.objects.is_alive(handle))
        with self.assertRaises(InvalidHandle):
            self.properties.snapshot(handle)

        replacement = self.objects.create("example.Task", "task-002")
        self.assertEqual(replacement.slot, handle.slot)
        self.assertNotEqual(replacement.generation, handle.generation)

    def test_component_store_is_optional_and_queryable(self) -> None:
        first = self.objects.create("example.Task", "task-001")
        second = self.objects.create("example.Task", "task-002")
        self.components.attach(first, "Tag", "important")
        self.components.attach(first, "Counter", 1)
        self.components.attach(second, "Tag", "normal")

        self.assertEqual(self.components.query(["Tag", "Counter"]), [first])

    def test_alternative_component_layout_has_same_query_semantics(self) -> None:
        first = self.objects.create("example.Task", "task-001")
        second = self.objects.create("example.Task", "task-002")
        store = ObjectCentricComponentStore(self.objects)
        store.attach(first, "Tag", "important")
        store.attach(first, "Counter", 1)
        store.attach(second, "Tag", "normal")
        self.assertEqual(store.query(["Tag", "Counter"]), [first])

    def test_roundtrip_uses_schema_defaults(self) -> None:
        self.schemas.register(
            TypeDesc(
                "example.Project",
                1,
                (
                    FieldDesc("name", "string", required=True),
                    FieldDesc("owner", "string", default="unknown"),
                ),
            )
        )
        handle = self.objects.create("example.Project", "project-001")
        self.properties.set(handle, "name", "Alatyr")
        envelope = self.persistence.save(handle)

        loaded_store = ObjectStore()
        loaded_properties = PropertyStore(loaded_store)
        loaded = PersistenceService(loaded_store, loaded_properties, self.schemas).load(envelope)
        assert loaded.handle is not None
        self.assertEqual(loaded_properties.snapshot(loaded.handle), {"name": "Alatyr", "owner": "unknown"})

    def test_migration_is_repeatable(self) -> None:
        self.schemas.register(
            TypeDesc(
                "example.Task",
                1,
                (FieldDesc("title", "string", required=True), FieldDesc("state", "string", default="todo")),
            )
        )
        self.schemas.register(
            TypeDesc(
                "example.Task",
                2,
                (
                    FieldDesc("title", "string", required=True),
                    FieldDesc("status", "string", default="todo"),
                    FieldDesc("priority", "integer", default=0),
                ),
                migrations=(Migration(1, 2, {"state": "status"}),),
            )
        )
        version, migrated = self.schemas.migrate("example.Task", 1, {"title": "x", "state": "doing"})
        repeated_version, repeated = self.schemas.migrate("example.Task", version, migrated)
        self.assertEqual(version, 2)
        self.assertEqual(repeated_version, version)
        self.assertEqual(repeated, migrated)

    def test_unknown_type_is_opaque(self) -> None:
        envelope = self.persistence.load(
            Envelope("external.Note", 7, "note-001", {"text": "keep"})
        )
        self.assertIsNotNone(envelope.opaque)
        assert envelope.opaque is not None
        self.assertEqual(envelope.opaque.envelope.payload, {"text": "keep"})

    def test_strong_reference_fails_after_destroy(self) -> None:
        target = self.objects.create("example.Task", "task-001")
        resolver = ReferenceResolver(self.objects)
        self.assertEqual(resolver.resolve(Reference("strong", "task-001")), target)
        self.objects.destroy(target)
        with self.assertRaises(MissingReference):
            resolver.resolve(Reference("strong", "task-001"))


if __name__ == "__main__":
    unittest.main()
