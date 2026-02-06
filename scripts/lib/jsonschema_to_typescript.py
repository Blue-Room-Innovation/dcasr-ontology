#!/usr/bin/env python3
"""
JSON Schema to TypeScript Converter
====================================

Generates TypeScript type definitions from JSON Schema files.

This script wraps the json-schema-to-typescript Node.js tool, providing
a simple Python interface for generating TypeScript definitions.

Usage:
    python jsonschema-to-typescript.py --input build/digitalWastePassport.schema.json --output build/digitalWastePassport.ts
    python jsonschema-to-typescript.py -i schema.json -o types.ts --banner "Custom banner"

Requirements:
    - Node.js 18+
    - json-schema-to-typescript (installed via npm install)

Author: Blue Room Innovation
Date: 2026-01-13
"""

import argparse
import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Handle both direct execution and package import
try:
    from .utils import get_workspace_root
except ImportError:
    from utils import get_workspace_root

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class JSONSchemaToTypeScriptConverter:
    """Converts JSON Schema files to TypeScript definitions."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.workspace_root = get_workspace_root()
        
    def convert(self, input_file: Path, output_file: Path, banner_comment: str = None) -> bool:
        """Convert a JSON Schema file to TypeScript."""
        
        # Validate input file exists
        if not input_file.exists():
            logger.error(f"Input file not found: {input_file}")
            return False
        
        # Check Node.js is installed
        if not self._check_nodejs():
            return False
        
        # Check json-schema-to-typescript is installed
        if not self._check_json2ts():
            return False
        
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate TypeScript
        logger.info(f"Converting {input_file.name} → {output_file.name}")
        return self._run_json2ts(input_file, output_file, banner_comment)
    
    def _check_nodejs(self) -> bool:
        """Check that Node.js is available."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            node_version = result.stdout.strip()
            logger.debug(f"Node.js {node_version}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("Node.js is not installed or not in PATH")
            logger.error("Install from: https://nodejs.org/")
            return False
    
    def _check_json2ts(self) -> bool:
        """Check that json-schema-to-typescript is installed."""
        json2ts_cmd = self.workspace_root / "node_modules" / "json-schema-to-typescript" / "dist" / "src" / "cli.js"
        
        if not json2ts_cmd.exists():
            logger.error("json-schema-to-typescript not found")
            logger.error("Install with: npm install")
            return False
        
        logger.debug("json-schema-to-typescript found")
        return True
    
    def _run_json2ts(self, input_file: Path, output_file: Path, banner_comment: str = None) -> bool:
        """Run json-schema-to-typescript CLI."""
        json2ts_cmd = self.workspace_root / "node_modules" / "json-schema-to-typescript" / "dist" / "src" / "cli.js"
        
        # Build command
        cmd = [
            "node",
            str(json2ts_cmd),
            str(input_file),
            "--output", str(output_file)
        ]
        
        # Add banner comment if provided
        if banner_comment:
            cmd.extend(["--bannerComment", banner_comment])
        
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=True
            )
            
            if self.verbose and result.stdout:
                print(result.stdout)
            
            # Show relative path if possible, otherwise absolute
            try:
                rel_path = output_file.relative_to(self.workspace_root)
                logger.info(f"✅ Generated {rel_path}")
            except ValueError:
                logger.info(f"✅ Generated {output_file}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to generate TypeScript: {e}")
            if e.stderr:
                logger.error(e.stderr)
            return False
        except FileNotFoundError:
            logger.error("Node.js not found. Make sure it's installed and in PATH.")
            return False
    
    @staticmethod
    def get_default_banner(source_file: str = None) -> str:
        """Get default banner comment for generated TypeScript."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        banner = f"""/**
 * Auto-generated TypeScript definitions from JSON Schema
 * DO NOT EDIT MANUALLY
 * Generated: {timestamp}"""
        
        if source_file:
            banner += f"\n * Source: {source_file}"
        
        banner += "\n */"
        return banner


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert JSON Schema to TypeScript type definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python jsonschema-to-typescript.py -i schema.json -o types.ts
  python jsonschema-to-typescript.py --input build/digitalWastePassport.schema.json --output build/digitalWastePassport.ts
  python jsonschema-to-typescript.py -i schema.json -o types.ts --banner "Custom banner" --verbose
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input JSON Schema file"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output TypeScript file"
    )
    
    parser.add_argument(
        "-b", "--banner",
        help="Custom banner comment for the generated TypeScript file"
    )
    
    parser.add_argument(
        "-s", "--source",
        help="Source file name to include in the default banner (e.g., 'shapes/v0.1/example.ttl')"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Create converter
    converter = JSONSchemaToTypeScriptConverter(verbose=args.verbose)
    
    # Determine banner comment
    banner = args.banner
    if not banner:
        banner = converter.get_default_banner(source_file=args.source)
    
    # Convert files
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    success = converter.convert(input_path, output_path, banner)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
