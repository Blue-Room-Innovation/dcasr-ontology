#!/usr/bin/env python3
"""Configuration Loader

Loads configuration from config.yml and provides easy access to version numbers,
paths, and other settings.

Usage:
    from lib.config import Config
    
    config = Config.load()
    print(config.ontology_version)  # "v0.1"
    print(config.get_ontology_path("digitalWastePassport.ttl"))  # "ontology/v0.1/digitalWastePassport.ttl"
"""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any


class Config:
    """Configuration manager for ontology repository."""
    
    _instance: Optional[Config] = None
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize config from parsed YAML data."""
        self._data = config_data
        
        # Extract commonly used values
        self.ontology_version: str = config_data.get("ontology_version", "v0.1")
        self.shapes_version: str = config_data.get("shapes_version", "v0.1")
        self.examples_version: str = config_data.get("examples_version", "v0.1")
        self.codelists_version: str = config_data.get("codelists_version", "v0.1")
        self.build_version: str = config_data.get("build_version", "v0.1")
        
        # Paths
        self.paths: Dict[str, str] = config_data.get("paths", {})
        
        # Repository info
        self.repository: Dict[str, str] = config_data.get("repository", {})
        
        # Component configurations
        self.ontologies: List[Dict[str, str]] = config_data.get("ontologies", [])
        self.shapes: List[Dict[str, str]] = config_data.get("shapes", [])
        # Generation artifacts: list of string IDs only.
        # Each ID must exist in conversion.shacl_to_json.<id> and conversion.json_to_ts.<id>
        raw_artifacts = (config_data.get("generation", {}) or {}).get("artifacts", [])
        if raw_artifacts is None:
            raw_artifacts = []
        if not isinstance(raw_artifacts, list):
            raise ValueError(
                "generation.artifacts must be a list of strings (artifact ids). "
                f"Got: {type(raw_artifacts).__name__}"
            )

        normalized: List[Dict[str, Any]] = []
        for item in raw_artifacts:
            if not isinstance(item, str):
                raise ValueError(
                    "generation.artifacts must contain only strings (artifact ids). "
                    f"Found: {type(item).__name__}"
                )
            if item.strip() == "":
                raise ValueError("generation.artifacts contains an empty string")
            normalized.append({"name": item})

        self.generation_artifacts = normalized
        
        # Validation config
        self.validation: Dict[str, Any] = config_data.get("validation", {})
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> Config:
        """Load configuration from YAML file.
        
        Args:
            config_path: Path to config.yml. If None, searches from current directory upwards.
            
        Returns:
            Config instance
        """
        if cls._instance is not None:
            return cls._instance
        
        if config_path is None:
            # Search for config.yml in workspace root
            config_path = cls._find_config_file()
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        cls._instance = cls(config_data)
        return cls._instance
    
    @staticmethod
    def _find_config_file() -> Path:
        """Find config.yml using WORKSPACE_ROOT from .env file."""
        # Import here to avoid circular dependency
        import sys
        from pathlib import Path as P
        
        # Try to import get_workspace_root from utils
        try:
            from .utils import get_workspace_root
        except ImportError:
            # Fallback: add parent to path
            script_dir = P(__file__).parent
            if str(script_dir.parent) not in sys.path:
                sys.path.insert(0, str(script_dir.parent))
            from lib.utils import get_workspace_root
        
        workspace = get_workspace_root()
        config_path = workspace / 'config.yml'
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"config.yml not found in WORKSPACE_ROOT: {workspace}"
            )
        
        return config_path
    
    def get_ontology_path(self, filename: str) -> str:
        """Get versioned path to ontology file.
        
        Args:
            filename: Ontology filename (e.g., "digitalWastePassport.ttl")
            
        Returns:
            Relative path (e.g., "ontology/v0.1/digitalWastePassport.ttl")
        """
        return f"{self.paths['ontology']}/{self.ontology_version}/{filename}"
    
    def get_shapes_path(self, filename: str) -> str:
        """Get versioned path to shapes file."""
        return f"{self.paths['shapes']}/{self.shapes_version}/{filename}"
    
    def get_examples_path(self, filename: str) -> str:
        """Get versioned path to examples file."""
        return f"{self.paths['examples']}/{self.examples_version}/{filename}"
    
    def get_codelists_path(self, filename: str) -> str:
        """Get versioned path to codelists file."""
        return f"{self.paths['codelists']}/{self.codelists_version}/{filename}"
    
    def get_contexts_path(self, filename: str) -> str:
        """Get versioned path to a JSON-LD context file.

        Contexts are treated as build artifacts and live under build/<build_version>/.
        """
        return self.get_build_path(filename)
    
    def get_build_path(self, filename: str) -> str:
        """Get versioned path to build output file."""
        return f"{self.paths['build']}/{self.build_version}/{filename}"
    
    def get_github_raw_url(self, component: str, filename: str) -> str:
        """Get GitHub raw URL for a file.
        
        Args:
            component: Component name (ontology, shapes, examples, codelists, contexts)
            filename: Filename within the component
            
        Returns:
            Full GitHub raw URL
        """
        base = self.repository["base_url"]
        branch = self.repository["branch"]
        
        # Get versioned path based on component
        if component == "ontology":
            path = self.get_ontology_path(filename)
        elif component == "shapes":
            path = self.get_shapes_path(filename)
        elif component == "examples":
            path = self.get_examples_path(filename)
        elif component == "codelists":
            path = self.get_codelists_path(filename)
        elif component == "contexts":
            # Contexts are published under build/<build_version>/
            path = self.get_contexts_path(filename)
        else:
            raise ValueError(f"Unknown component: {component}")
        
        return f"{base}/{branch}/{path}"
    
    def get_ontology_configs(self) -> List[Dict[str, str]]:
        """Get list of ontology configurations."""
        return self.ontologies
    
    def get_shape_configs(self) -> List[Dict[str, str]]:
        """Get list of shape configurations."""
        return self.shapes
    
    def get_generation_artifacts(self) -> List[Dict[str, str]]:
        """Get list of artifacts to generate (SHACL → JSON Schema → TypeScript)."""
        return self.generation_artifacts
    
    def get_validation_examples(self) -> List[Dict[str, str]]:
        """Get list of SHACL validation examples."""
        return self.validation.get("shacl_examples", [])

    def get_validation_shacl_config(self) -> Dict[str, Any]:
        """Get SHACL validation configuration block."""
        return (self.validation.get("shacl", {}) or {})

    def get_validation_shacl_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """Get configured SHACL validation scenarios (validation.shacl.scenarios)."""
        shacl_cfg = self.get_validation_shacl_config()
        return (shacl_cfg.get("scenarios", {}) or {})

    def get_conversion_json_to_ts(self) -> Dict[str, Dict[str, Any]]:
        """Get configured JSON Schema → TypeScript conversion scenarios."""
        return (self._data.get("conversion", {}) or {}).get("json_to_ts", {}) or {}

    def get_conversion_shacl_to_json(self) -> Dict[str, Dict[str, Any]]:
        """Get configured SHACL → JSON Schema conversion scenarios."""
        return (self._data.get("conversion", {}) or {}).get("shacl_to_json", {}) or {}

    def get_conversion_shacl_to_context(self) -> Dict[str, Dict[str, Any]]:
        """Get configured SHACL → JSON-LD Context conversion scenarios."""
        return (self._data.get("conversion", {}) or {}).get("shacl_to_context", {}) or {}
    
    def get_owl_validation_config(self) -> Dict[str, Any]:
        """Get OWL validation configuration."""
        return self.validation.get("owl", {})
    
    def __repr__(self) -> str:
        return (f"Config(ontology={self.ontology_version}, "
                f"shapes={self.shapes_version}, "
                f"codelists={self.codelists_version})")


# Convenience function for quick access
def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration (convenience function)."""
    return Config.load(config_path)


if __name__ == "__main__":
    # Test configuration loading
    config = load_config()
    print(f"Loaded configuration: {config}")
    print(f"\nOntology version: {config.ontology_version}")
    print(f"Shapes version: {config.shapes_version}")
    print(f"Codelists version: {config.codelists_version}")
    print(f"\nOntology path: {config.get_ontology_path('digitalWastePassport.ttl')}")
    print(f"GitHub URL: {config.get_github_raw_url('ontology', 'digitalWastePassport.ttl')}")
    print(f"\nGeneration artifacts: {len(config.get_generation_artifacts())} configured")
