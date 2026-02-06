"""Common utilities for CLI commands."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import which as shutil_which
from typing import List, Optional

try:
    from .config import load_config
except ImportError:
    # Fallback if config module not available yet
    load_config = None


def which(cmd: str) -> Optional[str]:
    """Check if a command is available in PATH.
    
    Args:
        cmd: Command name to search for
        
    Returns:
        Full path to command if found, None otherwise
    """
    return shutil_which(cmd)


def split_csv(value: str) -> List[str]:
    """Split a comma-separated string into a list of non-empty parts.
    
    Args:
        value: Comma-separated string
        
    Returns:
        List of stripped non-empty strings
    """
    return [part.strip() for part in value.split(",") if part.strip()]


def print_err(msg: str) -> None:
    """Print message to stderr.
    
    Args:
        msg: Message to print
    """
    print(msg, file=sys.stderr)


def run_command(cmd: List[str], quiet: bool = False) -> int:
    """Run a command and capture its output.
    
    Args:
        cmd: Command and arguments as list
        quiet: If True, suppress stdout (stderr is always shown)
        
    Returns:
        Command exit code
    """
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        check=False,
    )
    if not quiet and result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        # Keep stderr always visible
        print_err(result.stderr.rstrip("\n"))
    return result.returncode


def get_workspace_root() -> Path:
    """Get the workspace root directory from .env file.
    
    Returns:
        Path to workspace root
        
    Raises:
        FileNotFoundError: If .env file not found
        EnvironmentError: If WORKSPACE_ROOT is not set in .env
    """
    from dotenv import load_dotenv
    import os
    
    # Find .env file (search upward from current directory)
    env_file = None
    current = Path.cwd()
    for _ in range(10):
        candidate = current / '.env'
        if candidate.exists():
            env_file = candidate
            break
        parent = current.parent
        if parent == current:
            break
        current = parent
    
    if env_file is None:
        raise FileNotFoundError(
            ".env file not found.\n"
            f"Create .env file in project root based on .env.example"
        )
    
    # Load .env file
    load_dotenv(env_file)
    
    # Check WORKSPACE_ROOT is defined
    if 'WORKSPACE_ROOT' not in os.environ:
        raise EnvironmentError(
            f"WORKSPACE_ROOT not defined in {env_file}\n"
            "Add: WORKSPACE_ROOT=/path/to/workspace"
        )
    
    workspace = Path(os.environ['WORKSPACE_ROOT']).resolve()
    
    if not workspace.exists():
        raise FileNotFoundError(
            f"WORKSPACE_ROOT points to non-existent directory: {workspace}"
        )
    
    return workspace


def iter_ontology_files(include_codelists: bool = False) -> List[Path]:
    """Iterate over ontology TTL files in the workspace.
    
    Args:
        include_codelists: If True, include files from codelists/v*/
        
    Returns:
        List of Path objects to TTL files
    """
    workspace_root = get_workspace_root()
    config = load_config()
    
    ontology_dir = workspace_root / config.paths['ontology'] / config.ontology_version
    codelists_dir = workspace_root / config.paths['codelists'] / config.codelists_version if include_codelists else None
    
    candidates: List[Path] = []
    
    # Look for ontology files
    if ontology_dir.exists():
        for ttl_file in sorted(ontology_dir.glob("*.ttl")):
            candidates.append(ttl_file)
    
    # Include codelists if requested
    if include_codelists and codelists_dir and codelists_dir.exists():
        for ttl_file in sorted(codelists_dir.rglob("*.ttl")):
            candidates.append(ttl_file)
    
    return candidates
