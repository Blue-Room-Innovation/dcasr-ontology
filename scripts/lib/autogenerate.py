#!/usr/bin/env python3
"""
TypeScript Generator from SHACL Shapes
=======================================

Orchestrates the generation of TypeScript type definitions from SHACL shapes.

This script is a convenience wrapper that chains two scripts:
1. shacl-to-jsonschema.py: SHACL → JSON Schema
2. jsonschema-to-typescript.py: JSON Schema → TypeScript

Usage:
    python autogenerate.py
    python autogenerate.py --verbose

Output:
    - build/digitalWastePassport.schema.json
    - build/digitalMarpolWastePassport.schema.json
    - build/digitalWastePassport.ts
    - build/digitalMarpolWastePassport.ts

Requirements:
    - Python 3.8+ with rdflib (for SHACL conversion)
    - Node.js 18+ with json-schema-to-typescript (for TS generation)

See also:
    - scripts/shacl-to-jsonschema.py (step 1)
    - scripts/jsonschema-to-typescript.py (step 2)

Author: Blue Room Innovation
Date: 2026-01-13
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any

# Import config and utils with proper error handling
try:
    from .config import load_config
    from .utils import get_workspace_root
except ImportError:
    # Fallback: add parent to path and import directly
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.config import load_config
    from lib.utils import get_workspace_root

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TypeScriptGenerator:
    """Orchestrates TypeScript generation from SHACL shapes."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.workspace_root = get_workspace_root()
        self.config = load_config()
        self.build_dir = self.workspace_root / self.config.paths['build'] / self.config.build_version
        self.shapes_dir = self.workspace_root / self.config.paths['shapes'] / self.config.shapes_version
        self.scripts_dir = self.workspace_root / self.config.paths['scripts']
        
        # Load shape configurations from config.yml
        self.shape_configs = self.config.get_generation_artifacts()
    
    def run(self) -> bool:
        """Execute the full generation pipeline."""
        logger.info("🚀 Starting TypeScript generation pipeline...")
        
        # Ensure build directory exists
        self.build_dir.mkdir(exist_ok=True)
        
        success = True
        
        # Resolve each artifact configuration into concrete paths
        resolved_items: List[Dict[str, Any]] = []
        for item in self.shape_configs:
            resolved = self._resolve_artifact(item)
            if not resolved:
                success = False
                continue
            resolved_items.append(resolved)

        # Process each resolved item
        for config in resolved_items:
            logger.info(f"\n📦 Processing {config['name']}...")
            
            # Step 1: SHACL → JSON Schema
            if not self._run_shacl_to_jsonschema(config):
                logger.error(f"Failed to generate JSON Schema for {config['name']}")
                success = False
                continue
            
            # Step 2: JSON Schema → TypeScript
            if not self._run_jsonschema_to_typescript(config):
                logger.error(f"Failed to generate TypeScript for {config['name']}")
                success = False
                continue
            
            logger.info(f"✅ Generated {Path(config['ts_output']).name}")
        
        if success:
            logger.info("\n🎉 All TypeScript definitions generated successfully!")
            self._print_output_summary(resolved_items)
        else:
            logger.error("\n❌ Some generations failed. Check the logs above.")
        
        return success
    
    def _resolve_artifact(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Resolve a generation artifact into concrete file paths.

        Expected format: {name: <id>} where <id> maps to:
        - conversion.shacl_to_json.<id>
        - conversion.json_to_ts.<id>
        """
        name = (item or {}).get("name")
        if not name:
            logger.error("Generation artifact is missing 'name'")
            return None

        shacl_to_json = self.config.get_conversion_shacl_to_json()
        json_to_ts = self.config.get_conversion_json_to_ts()

        shacl_scenario = (shacl_to_json or {}).get(name)
        ts_scenario = (json_to_ts or {}).get(name)

        if not shacl_scenario:
            logger.error(f"No conversion.shacl_to_json scenario found for '{name}'")
            return None
        if not ts_scenario:
            logger.error(f"No conversion.json_to_ts scenario found for '{name}'")
            return None

        shacl_input = shacl_scenario.get("input")
        shacl_output = shacl_scenario.get("output")
        ts_input = ts_scenario.get("input")
        ts_output = ts_scenario.get("output")

        if not shacl_input or not shacl_output:
            logger.error(f"conversion.shacl_to_json.{name} missing input/output")
            return None
        if not ts_input or not ts_output:
            logger.error(f"conversion.json_to_ts.{name} missing input/output")
            return None

        resolved = {
            "name": name,
            "shacl_input": str(self.workspace_root / Path(str(shacl_input))),
            "shacl_output": str(self.workspace_root / Path(str(shacl_output))),
            "ts_input": str(self.workspace_root / Path(str(ts_input))),
            "ts_output": str(self.workspace_root / Path(str(ts_output))),
            "source": ts_scenario.get("source") or shacl_input,
        }

        naming = shacl_scenario.get("naming")
        context = shacl_scenario.get("context")
        if naming:
            resolved["naming"] = naming
        if context:
            resolved["context"] = context

        return resolved

    def _run_shacl_to_jsonschema(self, config: Dict[str, Any]) -> bool:
        """Run shacl-to-jsonschema.py script."""
        shape_file = Path(str(config["shacl_input"]))
        json_schema_file = Path(str(config["shacl_output"]))
        
        logger.info(f"  Step 1/2: SHACL → JSON Schema")
        
        json_schema_file.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(self.scripts_dir / "lib" / "shacl_to_jsonschema.py"),
            "--input",
            str(shape_file),
            "--output",
            str(json_schema_file),
        ]

        naming = config.get("naming") or "curie"
        if naming:
            cmd.extend(["--naming", str(naming)])

        context = config.get("context")
        if naming == "context" and context:
            context_path = Path(str(context))
            if not context_path.is_absolute():
                context_path = self.workspace_root / context_path
            cmd.extend(["--context", str(context_path)])
        
        if self.verbose:
            cmd.append("--verbose")
        
        return self._run_command(cmd)
    
    def _run_jsonschema_to_typescript(self, config: Dict[str, Any]) -> bool:
        """Run jsonschema-to-typescript.py script."""
        json_schema_file = Path(str(config["ts_input"]))
        typescript_file = Path(str(config["ts_output"]))
        
        logger.info(f"  Step 2/2: JSON Schema → TypeScript")
        
        cmd = [
            sys.executable,
            str(self.scripts_dir / "lib" / "jsonschema_to_typescript.py"),
            "--input", str(json_schema_file),
            "--output", str(typescript_file),
            "--source",
            str(config.get("source") or ""),
        ]

        # Ensure output dir exists
        typescript_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.verbose:
            cmd.append("--verbose")
        
        return self._run_command(cmd)
    
    def _run_command(self, cmd: List[str]) -> bool:
        """Run a command and return success status."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False  # Don't raise on non-zero exit
            )
            
            if self.verbose and result.stdout:
                print(result.stdout)
            
            # Exit code 0 or 2 (warnings) are acceptable
            if result.returncode not in [0, 2]:
                if result.stderr:
                    logger.error(result.stderr)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to run command: {e}")
            return False
    
    def _print_output_summary(self, resolved_items: List[Dict[str, Any]]):
        """Print summary of generated files."""
        logger.info("\n📄 Generated files:")
        for config in resolved_items:
            json_file = Path(str(config["shacl_output"]))
            ts_file = Path(str(config["ts_output"]))
            
            if json_file.exists():
                logger.info(f"  - {json_file.relative_to(self.workspace_root)}")
            if ts_file.exists():
                logger.info(f"  - {ts_file.relative_to(self.workspace_root)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate TypeScript definitions from SHACL shapes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script orchestrates a two-step pipeline:
  1. SHACL → JSON Schema (using shacl-to-jsonschema.py)
  2. JSON Schema → TypeScript (using jsonschema-to-typescript.py)

Versions are configured in config.yml. Current settings will be used automatically.

You can also run each script independently if needed with explicit paths.

Examples:
  python autogenerate.py
  python autogenerate.py --verbose
        """
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    generator = TypeScriptGenerator(verbose=args.verbose)
    success = generator.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
