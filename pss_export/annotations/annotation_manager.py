import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, List, Protocol, Optional

class ExportStrategy(Protocol):
    def format_node(self, valid_records: List[Dict[str, Any]]) -> Any: ...

class AnnotationManager:
    """A completely format-agnostic AnnotationManager driven by a generic YAML schema."""

    def __init__(self, yaml_filepath: Optional[Path] = None):
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._strategies: Dict[str, ExportStrategy] = {}
        self.load_from_yaml(yaml_filepath)

    def load_from_yaml(self, yaml_filepath: Optional[Path] = None):
        """Loads and parses data configurations dynamically."""
        if yaml_filepath is None:
            yaml_filepath = Path(__file__).with_name("annotation_registry.yaml")

        if not yaml_filepath.exists():
            print(f"Warning: Annotation mapping config not found at '{yaml_filepath}'. Running empty.")
            return

        with open(yaml_filepath, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)

        # GENERIC INGEST: Store the whole metadata payload dictionary as-is
        for prefix, meta in config.get("databases", {}).items():
            self._registry[prefix.lower()] = meta
            # Ensure a canonical prefix exists fallback
            if "canonical_prefix" not in self._registry[prefix.lower()]:
                self._registry[prefix.lower()]["canonical_prefix"] = prefix.lower()

    def register_export_strategy(self, format_name: str, strategy: ExportStrategy):
        """Hooks up a format strategy engine to the translation dispatch loop."""
        self._strategies[format_name.strip().lower()] = strategy

    def process_node(self, target_format: str, db_references: List[str]) -> Tuple[Any, List[str]]:
        """Processes raw references and routes elements to selected target format strategy."""
        fmt = target_format.strip().lower()
        if fmt not in self._strategies:
            raise ValueError(f"Unsupported format: '{target_format}'. Targets: {list(self._strategies.keys())}")

        valid_records: List[Dict[str, Any]] = []
        invalid_refs: List[str] = []

        for ref in db_references:
            if ":" not in ref:
                invalid_refs.append(ref)
                continue

            prefix, local_id = ref.split(":", 1)
            prefix_clean = prefix.strip().lower()

            if prefix_clean not in self._registry:
                invalid_refs.append(ref)
                continue

            # Create an intermediate record tracking the matched ID context
            record = self._registry[prefix_clean].copy()
            record["local_id"] = local_id.strip()
            valid_records.append(record)

        return self._strategies[fmt].format_node(valid_records), invalid_refs

# Instantiate the shared registry engine instance
annotation_manager = AnnotationManager()
