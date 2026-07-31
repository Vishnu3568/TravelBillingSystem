"""
AMIP Adapter Registry.
Central registry mapping task types and agent names to production domain adapters.
"""
from __future__ import annotations
import threading
from typing import Dict, Any, Optional
from app.services.amip.interfaces.adapter_interfaces import IAdapter, IAdapterRegistry
from app.services.amip.adapters.validation_adapter import ValidationAdapter
from app.services.amip.adapters.learning_adapter import LearningAdapter
from app.services.amip.adapters.knowledge_graph_adapter import KnowledgeGraphAdapter
from app.services.amip.adapters.predictive_adapter import PredictiveAdapter
from app.services.amip.adapters.copilot_adapter import CopilotAdapter
from app.services.amip.adapters.bulk_import_adapter import BulkImportAdapter


class AdapterRegistry(IAdapterRegistry):
    """
    Registry for resolving production domain adapters.
    """

    def __init__(self, register_defaults: bool = True):
        self._adapters: Dict[str, IAdapter] = {}
        self._lock: threading.RLock = threading.RLock()

        if register_defaults:
            self._register_default_adapters()

    def _register_default_adapters(self) -> None:
        """Instantiates and registers default production adapters."""
        val = ValidationAdapter()
        learn = LearningAdapter()
        graph = KnowledgeGraphAdapter()
        pred = PredictiveAdapter()
        copilot = CopilotAdapter()
        bulk = BulkImportAdapter()

        # Register by agent name
        self.register_adapter("ValidationAgent", val)
        self.register_adapter("LearningAgent", learn)
        self.register_adapter("KnowledgeGraphAgent", graph)
        self.register_adapter("GraphAgent", graph)
        self.register_adapter("PredictiveAgent", pred)
        self.register_adapter("CopilotAgent", copilot)
        self.register_adapter("BulkImportAgent", bulk)
        self.register_adapter("DocIntelAgent", bulk)

        # Register by TaskType
        self.register_adapter("DOCUMENT_IMPORT", bulk)
        self.register_adapter("COPILOT_CHAT", copilot)
        self.register_adapter("PREDICTIVE_FORECAST", pred)
        self.register_adapter("GRAPH_QUERY", graph)
        self.register_adapter("REVIEW_CORRECTION", learn)

    def register_adapter(self, key: str, adapter: IAdapter) -> None:
        """Registers an adapter under a specified lookup key (thread-safe)."""
        with self._lock:
            self._adapters[key.upper()] = adapter
            self._adapters[key] = adapter

    def resolve(self, key: str) -> Optional[IAdapter]:
        """Resolves adapter by key or agent name (thread-safe)."""
        with self._lock:
            if not key:
                return None
            return self._adapters.get(key) or self._adapters.get(key.upper())

    def list_adapters(self) -> Dict[str, IAdapter]:
        """Returns shallow copy of registered adapters (thread-safe)."""
        with self._lock:
            return dict(self._adapters)
