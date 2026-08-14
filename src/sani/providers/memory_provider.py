"""Abstract Interface for Replaceable Memory Storage (Commandment 8)."""

from abc import ABC, abstractmethod
from sani.models import MemoryItem


class MemoryProvider(ABC):
    """Abstract memory storage contract (SQLite, Vector DB, Graph DB)."""

    @abstractmethod
    def store_memory(self, item: MemoryItem) -> str:
        """Store a new memory item and return its ID."""
        pass

    @abstractmethod
    def get_memory(self, memory_id: str) -> MemoryItem | None:
        """Retrieve memory item by ID."""
        pass

    @abstractmethod
    def search_memories(self, owner_id: str, query: str = "", memory_type: str | None = None) -> list[MemoryItem]:
        """Search memories scoped to a specific owner ID."""
        pass

    @abstractmethod
    def update_memory(self, memory_id: str, content: str, confidence: float = 1.0) -> bool:
        """Update existing memory content."""
        pass

    @abstractmethod
    def supersede_memory(self, old_memory_id: str, new_memory_id: str) -> bool:
        """Mark an old memory item as superseded by a newer memory item."""
        pass
