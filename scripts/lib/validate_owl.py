"""OWL ontology validation module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .utils import (
    get_workspace_root,
    iter_ontology_files,
    print_err,
    run_command,
    split_csv,
    which,
)


@dataclass
class OwlConfig:
    """Configuration for OWL validation.
    
    Attributes:
        inputs_csv: Comma-separated list of input TTL files
        include_codelists: Include codelists in auto-discovery
        no_auto: Disable auto-discovery of ontology files
        reasoner: Reasoner to use (HermiT, ELK, or none)
        profile: OWL profile to validate (DL or OWL2)
        build_dir: Directory for build outputs
        merged: Filename for merged ontology output
        output: Filename for reasoned ontology output
        quiet: Suppress informational output
    """

    inputs_csv: str = ""
    include_codelists: bool = False
    no_auto: bool = False
    reasoner: str = "HermiT"
    profile: str = "DL"
    build_dir: Path = Path("build")
    merged: str = "merged-ontology.ttl"
    output: str = "reasoned-ontology.ttl"
    quiet: bool = False


def _get_input_files(config: OwlConfig) -> List[Path]:
    """Get list of input ontology files based on config.
    
    Args:
        config: OWL validation configuration
        
    Returns:
        List of paths to input files
    """
    workspace_root = get_workspace_root()
    input_files: List[Path] = []
    
    if config.inputs_csv:
        input_files = [
            workspace_root / Path(p) for p in split_csv(config.inputs_csv)
        ]
    elif not config.no_auto:
        input_files = iter_ontology_files(
            include_codelists=config.include_codelists
        )
    
    return [p for p in input_files if p.exists()]


def _validate_with_robot(
    input_files: List[Path],
    merged_path: Path,
    reasoned_path: Path,
    config: OwlConfig,
) -> int:
    """Validate ontologies using ROBOT CLI.
    
    Args:
        input_files: List of input ontology files
        merged_path: Path for merged output
        reasoned_path: Path for reasoned output
        config: Validation configuration
        
    Returns:
        Exit code (0 for success)
    """
    robot = which("robot")
    if not robot:
        return -1
    
    if not config.quiet:
        print("[OWL] Usant ROBOT CLI")
    
    # Check for catalog file
    # ----------------------
    # The catalog.xml file (OASIS XML Catalog standard) redirects external URIs 
    # to local files. This is needed because our ontologies have owl:imports with 
    # absolute GitHub URLs (e.g., https://blue-room-innovation.github.io/dcasr-ontology/build/vX.X/.../*.ttl).
    # Without the catalog, ROBOT tries to download from those URLs and fails.
    # The catalog maps those GitHub URIs to local files in codelists/v0.1/
    workspace_root = get_workspace_root()
    catalog_path = workspace_root / "ontology" / "catalog-v001.xml"
    
    # Merge ontologies
    merge_cmd: List[str] = [robot, "merge"]
    if catalog_path.exists():
        merge_cmd += ["--catalog", str(catalog_path)]
    for p in input_files:
        merge_cmd += ["--input", str(p)]
    merge_cmd += ["--output", str(merged_path)]
    
    merge_status = run_command(merge_cmd, quiet=config.quiet)
    if (
        merge_status != 0
        or not merged_path.exists()
        or merged_path.stat().st_size == 0
    ):
        print_err(
            f"[OWL] Merge fallat o sense sortida. "
            f"No existeix '{merged_path}'. Codi: {merge_status}"
        )
        return merge_status
    
    # Validate profile
    profile_cmd = [
        robot,
        "validate-profile",
    ]
    if catalog_path.exists():
        profile_cmd += ["--catalog", str(catalog_path)]
    profile_cmd += [
        "--input",
        str(merged_path),
        "--profile",
        config.profile,
    ]
    profile_status = run_command(profile_cmd, quiet=config.quiet)
    if profile_status != 0:
        print_err(
            f"[OWL] Profile ({config.profile}) amb incidències "
            f"(exit {profile_status})."
        )
    
    # Apply reasoner if requested
    if config.reasoner != "none":
        reason_cmd = [
            robot,
            "reason",
        ]
        if catalog_path.exists():
            reason_cmd += ["--catalog", str(catalog_path)]
        reason_cmd += [
            "--input",
            str(merged_path),
            "--reasoner",
            config.reasoner,
            "--equivalent-classes-allowed",
            "all",
            "--output",
            str(reasoned_path),
        ]
        reason_status = run_command(reason_cmd, quiet=config.quiet)
        if (
            reason_status != 0
            or not reasoned_path.exists()
            or reasoned_path.stat().st_size == 0
        ):
            print_err(
                f"[OWL] Raonament fallat o sense sortida. "
                f"Codi: {reason_status}"
            )
            return reason_status
    
    return 0 if profile_status == 0 else profile_status


def _validate_with_riot(input_files: List[Path], config: OwlConfig) -> int:
    """Validate ontologies using Apache Jena RIOT (syntax only).
    
    Args:
        input_files: List of input ontology files
        config: Validation configuration
        
    Returns:
        Exit code (0 for success)
    """
    riot = which("riot")
    if not riot:
        return -1
    
    if not config.quiet:
        print("[OWL] ROBOT no trobat. Usant Apache Jena RIOT (només sintaxi).")
    
    workspace_root = get_workspace_root()
    for p in input_files:
        if not config.quiet:
            print(f"[RIOT] Validant {p.relative_to(workspace_root).as_posix()}")
        status = run_command([riot, "--validate", str(p)], quiet=config.quiet)
        if status != 0:
            return status
    
    return 0


def validate_owl(config: OwlConfig) -> int:
    """Validate OWL ontologies using available tools.
    
    This function will:
    1. Discover or use specified input ontology files
    2. Merge them using ROBOT (if available)
    3. Validate against specified OWL profile
    4. Apply reasoning (if requested)
    5. Fall back to RIOT for syntax validation if ROBOT unavailable
    
    Args:
        config: OWL validation configuration
        
    Returns:
        Exit code (0 for success, non-zero for errors)
    """
    workspace_root = get_workspace_root()
    
    # Ensure build directory exists
    full_build_dir = workspace_root / config.build_dir
    full_build_dir.mkdir(parents=True, exist_ok=True)
    
    # Get input files
    input_files = _get_input_files(config)
    if not input_files:
        print_err(
            "[OWL] No s'han proporcionat ontologies i l'auto-descobriment "
            "està desactivat o buit."
        )
        return 2
    
    # Print configuration
    if not config.quiet:
        print(f"[OWL] Ontologies ({len(input_files)}):")
        for p in input_files:
            print(f"  - {p.relative_to(workspace_root).as_posix()}")
        print(f"[OWL] Profile  : {config.profile}")
        print(f"[OWL] Reasoner : {config.reasoner}")
        merged_rel = (full_build_dir / config.merged).relative_to(workspace_root)
        output_rel = (full_build_dir / config.output).relative_to(workspace_root)
        print(f"[OWL] Merge out: {merged_rel.as_posix()}")
        print(f"[OWL] Reasoned : {output_rel.as_posix()}")
    
    merged_path = full_build_dir / config.merged
    reasoned_path = full_build_dir / config.output
    
    # Try ROBOT first
    result = _validate_with_robot(
        input_files, merged_path, reasoned_path, config
    )
    if result != -1:
        return result
    
    # Fall back to RIOT
    result = _validate_with_riot(input_files, config)
    if result != -1:
        return result
    
    # No validator found
    print_err(
        "[OWL] No s'ha trobat cap validador. "
        "Instal·la 'robot' o Apache Jena (riot)."
    )
    return 1
