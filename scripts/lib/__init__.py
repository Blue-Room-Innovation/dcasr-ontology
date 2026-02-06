"""CLI package for ontology validation and generation tools."""

from .utils import which, split_csv, print_err, run_command
from .validate_owl import validate_owl, OwlConfig
from .validate_shacl import validate_shacl, ShaclConfig

__all__ = [
    "which",
    "split_csv",
    "print_err",
    "run_command",
    "validate_owl",
    "OwlConfig",
    "validate_shacl",
    "ShaclConfig",
]
