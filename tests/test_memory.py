"""Unit tests for SQLiteMemoryStore and owner scoping."""

import pytest
from sani.memory.sqlite_store import SQLiteMemoryStore
from sani.models import MemoryItem


@pytest.fixture
def memory_store(tmp_path) -> SQLiteMemoryStore:
    db_file = tmp_path / "test_sani_memory.db"
    return SQLiteMemoryStore(db_path=db_file)


def test_memory_storage_and_retrieval(memory_store: SQLiteMemoryStore) -> None:
    item = MemoryItem(
        memory_id="m1",
        owner_id="aman_01",
        memory_type="INSTRUCTION",
        content="Prefer dark mode in code editor.",
    )
    memory_store.store_memory(item)

    retrieved = memory_store.get_memory("m1")
    assert retrieved is not None
    assert retrieved.content == "Prefer dark mode in code editor."
    assert retrieved.owner_id == "aman_01"


def test_memory_owner_scoping(memory_store: SQLiteMemoryStore) -> None:
    item_aman = MemoryItem(
        memory_id="m_aman",
        owner_id="aman_01",
        memory_type="PREFERENCE",
        content="Aman's private instruction.",
    )
    item_guest = MemoryItem(
        memory_id="m_guest",
        owner_id="guest_02",
        memory_type="PREFERENCE",
        content="Guest's private instruction.",
    )
    memory_store.store_memory(item_aman)
    memory_store.store_memory(item_guest)

    # Search scoped to Aman
    aman_memories = memory_store.search_memories(owner_id="aman_01")
    assert len(aman_memories) == 1
    assert aman_memories[0].memory_id == "m_aman"

    # Search scoped to Guest
    guest_memories = memory_store.search_memories(owner_id="guest_02")
    assert len(guest_memories) == 1
    assert guest_memories[0].memory_id == "m_guest"


def test_memory_superseding(memory_store: SQLiteMemoryStore) -> None:
    old_item = MemoryItem(
        memory_id="m_old",
        owner_id="aman_01",
        memory_type="FACT",
        content="Current project directory is E:/OldPath",
    )
    new_item = MemoryItem(
        memory_id="m_new",
        owner_id="aman_01",
        memory_type="FACT",
        content="Current project directory is E:/Projects/SANI",
    )
    memory_store.store_memory(old_item)
    memory_store.store_memory(new_item)
    memory_store.supersede_memory(old_memory_id="m_old", new_memory_id="m_new")

    # Search active (non-superseded) memories
    active_memories = memory_store.search_memories(owner_id="aman_01")
    assert len(active_memories) == 1
    assert active_memories[0].memory_id == "m_new"
