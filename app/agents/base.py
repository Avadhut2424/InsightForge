from typing import Any, Dict, Protocol
from pydantic import BaseModel, Field

class Task(BaseModel):
    """Represents a unit of work passed to an agent."""
    input_data: Any
    context: Dict[str, Any] = Field(default_factory=dict)

class MemoryStore(BaseModel):
    """
    Simple in-memory store for passing context between agents during a run.
    This is kept simple as requested: in-memory key/value store scoped to a run.
    """
    store: Dict[str, Any] = Field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.store.get(key, default)
        
    def clear(self) -> None:
        self.store.clear()

class Agent(Protocol):
    """Base protocol for all agents."""
    async def run(self, task: Task, memory: MemoryStore) -> Any:
        ...
