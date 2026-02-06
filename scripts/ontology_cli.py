#!/usr/bin/env python3
"""Ontology CLI

Unifies validation, generation, and conversion tasks for this ontology repository.

Commands:
- validate owl   : validates OWL ontologies using ROBOT or Apache Jena
- validate shacl : validates RDF data against SHACL shapes
- generate types : generates TypeScript types from SHACL shapes (autogenerate)
- generate wiki  : generates wiki documentation from ontologies
- convert json-schema : converts SHACL shapes to JSON Schema
- convert ts     : converts JSON Schema to TypeScript

This CLI delegates to modular components in the cli/ package.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from lib import OwlConfig, ShaclConfig, validate_owl, validate_shacl
from lib.config import load_config
from lib.utils import get_workspace_root


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser for CLI commands.
    
    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        prog="ontology-cli",
        description="Ontology repository CLI - validation, generation, and conversion",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ===== VALIDATE COMMANDS =====
    validate = sub.add_parser("validate", help="Validation commands")
    validate_sub = validate.add_subparsers(dest="validate_cmd", required=True)

    # OWL validation
    owl = validate_sub.add_parser(
        "owl", help="Validate OWL ontologies (ROBOT/RIOT)"
    )
    owl.add_argument(
        "-i",
        "--inputs",
        dest="inputs_csv",
        default="",
        help="CSV list of TTL files",
    )
    owl.add_argument(
        "--include-codelists",
        action="store_true",
        help="Include codelists/v*/ in auto-discovery",
    )
    owl.add_argument(
        "--no-auto", action="store_true", help="Disable auto-discovery"
    )
    owl.add_argument(
        "-r",
        "--reasoner",
        default="HermiT",
        choices=["HermiT", "ELK", "none"],
        help="Reasoner",
    )
    owl.add_argument(
        "-p",
        "--profile",
        default="DL",
        choices=["DL", "OWL2"],
        help="OWL profile",
    )
    owl.add_argument(
        "--build-dir", default=None, help="Build output dir (default: build/<version>)"
    )
    owl.add_argument(
        "-m",
        "--merged",
        default="merged-ontology.ttl",
        help="Merged output filename (in build dir)",
    )
    owl.add_argument(
        "-o",
        "--output",
        default="reasoned-ontology.ttl",
        help="Reasoned output filename (in build dir)",
    )
    owl.add_argument(
        "-q", "--quiet", action="store_true", help="Reduce output"
    )

    # SHACL validation
    shacl = validate_sub.add_parser(
        "shacl", help="Validate data graph against SHACL shapes (pyshacl)"
    )
    shacl.add_argument(
        "scenario",
        nargs="?",
        help="Validation scenario name from config.yml (e.g., 'dwp', 'dmwp'). If not provided, validates all configured scenarios.",
    )
    shacl.add_argument(
        "-d",
        "--data",
        dest="data",
        required=False,
        help="Data graph file (ttl/jsonld) - overrides scenario config",
    )
    shacl.add_argument(
        "-s", 
        "--shapes", 
        dest="shapes", 
        required=False, 
        help="Shapes file (ttl) - overrides scenario config"
    )
    shacl.add_argument(
        "-e",
        "--extras",
        dest="extras_csv",
        required=False,
        help="CSV list of extra ttl files - overrides scenario config",
    )
    shacl.add_argument(
        "-f",
        "--format",
        dest="fmt",
        required=False,
        choices=["human", "text", "turtle", "json-ld"],
        help="Output format - overrides scenario config",
    )
    shacl.add_argument(
        "--list",
        action="store_true",
        help="List all available validation scenarios from config.yml",
    )

    # ===== GENERATE COMMANDS =====
    generate = sub.add_parser("generate", help="Generation commands")
    generate_sub = generate.add_subparsers(dest="generate_cmd", required=True)

    # TypeScript generation (autogenerate)
    gen_types = generate_sub.add_parser(
        "types",
        help="Generate TypeScript types from SHACL shapes (autogenerate pipeline)",
    )
    gen_types.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    # Wiki generation
    gen_wiki = generate_sub.add_parser(
        "wiki", help="Generate wiki documentation from ontologies"
    )
    gen_wiki.add_argument(
        "--ontology-dir",
        default="ontology",
        help="Ontology directory (default: ontology)",
    )
    gen_wiki.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (default: from config.yml wiki.output_dir)",
    )
    gen_wiki.add_argument(
        "--include-codelists",
        action="store_true",
        help="Include codelists in wiki generation",
    )
    gen_wiki.add_argument(
        "--include-shapes",
        action="store_true",
        default=True,
        help="Include shapes count in index (default: True)",
    )
    gen_wiki.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    # Build index generation
    generate_sub.add_parser(
        "build-index",
        help="Generate build/ index.md files for GitHub Pages",
    )

    # ===== CONVERT COMMANDS =====
    convert = sub.add_parser("convert", help="Conversion commands")
    convert_sub = convert.add_subparsers(dest="convert_cmd", required=True)

    # SHACL to JSON Schema
    conv_shacl = convert_sub.add_parser(
        "json-schema", help="Convert SHACL shapes to JSON Schema"
    )
    conv_shacl.add_argument(
        "scenario",
        nargs="?",
        help="Conversion scenario name from config.yml (conversion.shacl_to_json). If not provided, converts all configured scenarios.",
    )
    conv_shacl.add_argument(
        "-i", "--input", required=False, help="Input SHACL shapes file (TTL) - overrides scenario config"
    )
    conv_shacl.add_argument(
        "-o", "--output", required=False, help="Output JSON Schema file - overrides scenario config"
    )
    conv_shacl.add_argument(
        "--list",
        action="store_true",
        help="List all available SHACL->JSON conversion scenarios from config.yml",
    )
    conv_shacl.add_argument(
        "--naming",
        required=False,
        choices=["curie", "local", "context"],
        help="Property naming strategy for generated JSON Schema (overrides scenario config).",
    )
    conv_shacl.add_argument(
        "--context",
        required=False,
        help="JSON-LD context file to use when --naming=context (overrides scenario config).",
    )
    conv_shacl.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    # SHACL to JSON-LD context
    conv_ctx = convert_sub.add_parser(
        "context", help="Generate a JSON-LD context from SHACL shapes"
    )
    conv_ctx.add_argument(
        "scenario",
        nargs="?",
        help="Conversion scenario name from config.yml (conversion.shacl_to_context). If not provided, converts all configured scenarios.",
    )
    conv_ctx.add_argument(
        "-i", "--input", required=False, help="Input SHACL shapes file (TTL) - overrides scenario config"
    )
    conv_ctx.add_argument(
        "-o", "--output", required=False, help="Output JSON-LD context file - overrides scenario config"
    )
    conv_ctx.add_argument(
        "--list",
        action="store_true",
        help="List all available SHACL->JSON-LD-context conversion scenarios from config.yml",
    )
    conv_ctx.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    # JSON Schema to TypeScript
    conv_ts = convert_sub.add_parser(
        "ts", help="Convert JSON Schema to TypeScript"
    )
    conv_ts.add_argument(
        "scenario",
        nargs="?",
        help="Conversion scenario name from config.yml (conversion.json_to_ts). If not provided, converts all configured scenarios.",
    )
    conv_ts.add_argument(
        "-i", "--input", required=False, help="Input JSON Schema file - overrides scenario config"
    )
    conv_ts.add_argument(
        "-o", "--output", required=False, help="Output TypeScript file - overrides scenario config"
    )
    conv_ts.add_argument(
        "-b", "--banner", help="Custom banner comment for TypeScript file"
    )
    conv_ts.add_argument(
        "-s",
        "--source",
        help="Source file name for default banner (e.g., 'shapes/example.ttl')",
    )
    conv_ts.add_argument(
        "--list",
        action="store_true",
        help="List all available JSON->TS conversion scenarios from config.yml",
    )
    conv_ts.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for CLI.
    
    Args:
        argv: Command-line arguments (defaults to sys.argv)
        
    Returns:
        Exit code
    """
    parser = build_parser()
    ns = parser.parse_args(argv)
    
    workspace_root = get_workspace_root()
    config_obj = load_config()

    # ===== VALIDATE COMMANDS =====
    if ns.command == "validate":
        if ns.validate_cmd == "owl":
            # Use versioned build directory if not explicitly specified
            build_dir = ns.build_dir
            if build_dir is None:
                build_dir = f"{config_obj.paths['build']}/{config_obj.build_version}"
            
            config = OwlConfig(
                inputs_csv=ns.inputs_csv,
                include_codelists=ns.include_codelists,
                no_auto=ns.no_auto,
                reasoner=ns.reasoner,
                profile=ns.profile,
                build_dir=Path(build_dir),
                merged=ns.merged,
                output=ns.output,
                quiet=ns.quiet,
            )
            return validate_owl(config)
        
        elif ns.validate_cmd == "shacl":
            # Handle --list flag
            if ns.list:
                scenarios = config_obj._data.get("validation", {}).get("shacl", {}).get("scenarios", {})
                default_scenario = config_obj._data.get("validation", {}).get("shacl", {}).get("default", "")
                
                print("\n📋 Available SHACL Validation Scenarios")
                print("=" * 60)
                if not scenarios:
                    print("❌ No scenarios configured in config.yml")
                    return 1
                
                for key, scenario in scenarios.items():
                    is_default = " (default; informational)" if key == default_scenario else ""
                    print(f"\n🔹 {key}{is_default}")
                    print(f"   Name: {scenario.get('name', 'N/A')}")
                    print(f"   Description: {scenario.get('description', 'N/A')}")
                    print(f"   Data: {scenario.get('data', 'N/A')}")
                    print(f"   Shapes: {scenario.get('shapes', 'N/A')}")
                
                print("\n💡 Usage:")
                print(f"   npm run validate:shacl                # validates all scenarios")
                print(f"   npm run validate:shacl <scenario-name> # validates one scenario")
                print(f"   node docker/docker.js run cli validate shacl <scenario-name>")
                print(f"   node docker/docker.js run cli validate shacl dwp")
                return 0
            
            # Get scenario configuration
            shacl_config = config_obj._data.get("validation", {}).get("shacl", {})
            scenarios = shacl_config.get("scenarios", {})

            # Determine which scenario(s) to run
            has_overrides = any(
                v is not None
                for v in (ns.data, ns.shapes, ns.extras_csv, ns.fmt)
            )
            scenario_name = ns.scenario
            
            # Get values from scenario or arguments
            data_file = ns.data
            shapes_file = ns.shapes
            extras_csv = ns.extras_csv
            fmt = ns.fmt

            # Case 1: specific scenario
            if scenario_name:
                scenario = scenarios.get(scenario_name)
                if not scenario:
                    print(f"❌ ERROR: Scenario '{scenario_name}' not found in config.yml")
                    print(f"Available scenarios: {', '.join(scenarios.keys())}")
                    print("Run 'npm run validate:shacl:list' to see all scenarios")
                    return 1

                print(f"[SHACL] Using scenario '{scenario_name}': {scenario.get('name', 'N/A')}")

                if data_file is None:
                    data_file = scenario.get("data")
                if shapes_file is None:
                    shapes_file = scenario.get("shapes")
                if extras_csv is None:
                    extras_csv = scenario.get("extras", "")
                if fmt is None:
                    fmt = scenario.get("format", "human")

                if data_file is None or shapes_file is None:
                    print("❌ ERROR: Scenario is missing required 'data' or 'shapes' values")
                    return 1

                if extras_csv is None:
                    extras_csv = ""
                if fmt is None:
                    fmt = "human"

                config = ShaclConfig(
                    data_file=workspace_root / Path(data_file),
                    shapes_file=workspace_root / Path(shapes_file),
                    extras_csv=extras_csv,
                    output_format=fmt,
                )
                return validate_shacl(config)

            # Case 2: explicit overrides (single run)
            if has_overrides:
                if data_file is None:
                    print("❌ ERROR: --data is required when using overrides without a scenario")
                    return 1
                if shapes_file is None:
                    print("❌ ERROR: --shapes is required when using overrides without a scenario")
                    return 1
                if extras_csv is None:
                    extras_csv = ""
                if fmt is None:
                    fmt = "human"

                config = ShaclConfig(
                    data_file=workspace_root / Path(data_file),
                    shapes_file=workspace_root / Path(shapes_file),
                    extras_csv=extras_csv,
                    output_format=fmt,
                )
                return validate_shacl(config)

            # Case 3: no scenario and no overrides => validate all scenarios
            if not scenarios:
                print("❌ ERROR: No validation.shacl.scenarios configured in config.yml")
                return 1

            print(f"[SHACL] Validating all scenarios ({len(scenarios)}): {', '.join(sorted(scenarios.keys()))}")

            worst_exit = 0
            for key in sorted(scenarios.keys()):
                scenario = scenarios.get(key) or {}
                data_file = scenario.get("data")
                shapes_file = scenario.get("shapes")
                extras_csv = scenario.get("extras", "")
                fmt = scenario.get("format", "human")

                if not data_file or not shapes_file:
                    print(f"\n[SHACL] ❌ Scenario '{key}' is missing 'data' or 'shapes' in config.yml")
                    worst_exit = max(worst_exit, 1)
                    continue

                print(f"\n[SHACL] === Scenario '{key}': {scenario.get('name', 'N/A')} ===")
                config = ShaclConfig(
                    data_file=workspace_root / Path(data_file),
                    shapes_file=workspace_root / Path(shapes_file),
                    extras_csv=extras_csv or "",
                    output_format=fmt or "human",
                )
                code = validate_shacl(config)
                worst_exit = max(worst_exit, code)

            return worst_exit

    # ===== GENERATE COMMANDS =====
    elif ns.command == "generate":
        if ns.generate_cmd == "types":
            # Import here to avoid unnecessary dependencies
            import subprocess
            autogenerate_script = workspace_root / "scripts" / "lib" / "autogenerate.py"
            cmd = [sys.executable, str(autogenerate_script)]
            if ns.verbose:
                cmd.append("--verbose")
            result = subprocess.run(cmd)
            return result.returncode
        
        elif ns.generate_cmd == "wiki":
            import subprocess
            wiki_script = workspace_root / "scripts" / "lib" / "generate_wiki.py"
            # Construir path de shapes amb la versió del config
            shapes_dir = f"{config_obj.paths['shapes']}/{config_obj.shapes_version}"
            contexts_dir = f"{config_obj.paths['build']}/{config_obj.build_version}"
            wiki_cfg = (config_obj._data.get("wiki", {}) or {})
            output_dir = ns.output_dir
            if not output_dir:
                output_dir = str(wiki_cfg.get("output_dir", "docs/wiki"))
            # Allow templating with build_version
            output_dir = output_dir.replace("{build_version}", str(config_obj.build_version))

            include_codelists = bool(ns.include_codelists) or bool(
                wiki_cfg.get("include_codelists", False)
            )

            cmd = [
                sys.executable,
                str(wiki_script),
                "--ontology-dir", ns.ontology_dir,
                "--output-dir", output_dir,
                "--shapes-dir", shapes_dir,
                "--contexts-dir", contexts_dir,
                "--pages-url", str((config_obj.repository or {}).get("pages_url", "")),
                "--build-version", str(config_obj.build_version),
            ]
            if include_codelists:
                cmd.append("--include-codelists")
            if ns.include_shapes:
                cmd.append("--include-shapes")
            if ns.verbose:
                cmd.append("--verbose")
            result = subprocess.run(cmd)
            return result.returncode

        elif ns.generate_cmd == "build-index":
            from lib.generate_build_index import generate_build_indexes

            return generate_build_indexes(workspace_root)

    # ===== CONVERT COMMANDS =====
    elif ns.command == "convert":
        if ns.convert_cmd == "json-schema":
            import subprocess
            shacl_script = workspace_root / "scripts" / "lib" / "shacl_to_jsonschema.py"
            conversions = config_obj._data.get("conversion", {}).get("shacl_to_json", {})

            # Handle --list
            if getattr(ns, "list", False):
                print("\n📋 Available SHACL → JSON Schema Conversion Scenarios")
                print("=" * 60)
                if not conversions:
                    print("❌ No conversion.shacl_to_json scenarios configured in config.yml")
                    return 1
                for key, scenario in conversions.items():
                    print(f"\n🔹 {key}")
                    print(f"   Name:   {scenario.get('name', 'N/A')}")
                    print(f"   Input:  {scenario.get('input', 'N/A')}")
                    print(f"   Output: {scenario.get('output', 'N/A')}")
                print("\n💡 Usage:")
                print("   npm run generate:json-schema                 # converts all scenarios")
                print("   npm run generate:json-schema <scenario-name> # converts one scenario")
                print("   npm run generate:json-schema -- -i in.ttl -o out.json")
                return 0

            has_overrides = any(v is not None for v in (ns.input, ns.output))
            scenario_name = getattr(ns, "scenario", None)

            # Case 1: specific scenario
            if scenario_name:
                scenario = conversions.get(scenario_name)
                if not scenario:
                    print(f"❌ ERROR: Conversion scenario '{scenario_name}' not found in config.yml")
                    print(f"Available scenarios: {', '.join(sorted(conversions.keys()))}")
                    print("Run 'node docker/docker.js run cli convert json-schema --list' to see all scenarios")
                    return 1

                input_file = ns.input or scenario.get("input")
                output_file = ns.output or scenario.get("output")
                naming = ns.naming or scenario.get("naming") or "curie"
                ctx_file = ns.context or scenario.get("context")

                if not input_file or not output_file:
                    print("❌ ERROR: Scenario is missing required 'input' or 'output' values")
                    return 1

                print(f"[CONVERT:SHACL] Using scenario '{scenario_name}': {scenario.get('name', 'N/A')}")
                cmd = [
                    sys.executable,
                    str(shacl_script),
                    "--input",
                    str(workspace_root / Path(input_file)),
                    "--output",
                    str(workspace_root / Path(output_file)),
                ]
                if naming:
                    cmd.extend(["--naming", naming])
                if naming == "context":
                    if not ctx_file:
                        print("❌ ERROR: naming=context requires a context file (scenario.context or --context)")
                        return 1
                    cmd.extend(["--context", str(workspace_root / Path(ctx_file))])
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                # shacl_to_jsonschema.py uses exit code 2 to signal warnings.
                # Treat warnings as non-fatal at the CLI level.
                return 0 if result.returncode == 2 else result.returncode

            # Case 2: explicit overrides (single run)
            if has_overrides:
                if ns.input is None:
                    print("❌ ERROR: --input is required when using overrides without a scenario")
                    return 1
                if ns.output is None:
                    print("❌ ERROR: --output is required when using overrides without a scenario")
                    return 1

                naming = ns.naming or "curie"
                ctx_file = ns.context

                cmd = [
                    sys.executable,
                    str(shacl_script),
                    "--input",
                    str(workspace_root / Path(ns.input)),
                    "--output",
                    str(workspace_root / Path(ns.output)),
                ]
                cmd.extend(["--naming", naming])
                if naming == "context":
                    if not ctx_file:
                        print("❌ ERROR: naming=context requires --context")
                        return 1
                    cmd.extend(["--context", str(workspace_root / Path(ctx_file))])
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                return 0 if result.returncode == 2 else result.returncode

            # Case 3: no scenario and no overrides => convert all
            if not conversions:
                print("❌ ERROR: No conversion.shacl_to_json scenarios configured in config.yml")
                return 1

            print(
                f"[CONVERT:SHACL] Converting all scenarios ({len(conversions)}): {', '.join(sorted(conversions.keys()))}"
            )

            worst_exit = 0
            for key in sorted(conversions.keys()):
                scenario = conversions.get(key) or {}
                input_file = scenario.get("input")
                output_file = scenario.get("output")
                naming = ns.naming or scenario.get("naming") or "curie"
                ctx_file = ns.context or scenario.get("context")

                if not input_file or not output_file:
                    print(f"\n[CONVERT:SHACL] ❌ Scenario '{key}' is missing 'input' or 'output' in config.yml")
                    worst_exit = max(worst_exit, 1)
                    continue

                print(f"\n[CONVERT:SHACL] === Scenario '{key}': {scenario.get('name', 'N/A')} ===")
                cmd = [
                    sys.executable,
                    str(shacl_script),
                    "--input",
                    str(workspace_root / Path(input_file)),
                    "--output",
                    str(workspace_root / Path(output_file)),
                ]
                if naming:
                    cmd.extend(["--naming", naming])
                if naming == "context":
                    if not ctx_file:
                        print(f"[CONVERT:SHACL] ❌ Scenario '{key}' has naming=context but no context file configured")
                        worst_exit = max(worst_exit, 1)
                        continue
                    cmd.extend(["--context", str(workspace_root / Path(ctx_file))])
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                code = 0 if result.returncode == 2 else result.returncode
                worst_exit = max(worst_exit, code)

            return worst_exit

        elif ns.convert_cmd == "context":
            import subprocess
            ctx_script = workspace_root / "scripts" / "lib" / "shacl_to_jsonld_context.py"
            conversions = config_obj._data.get("conversion", {}).get("shacl_to_context", {})

            if getattr(ns, "list", False):
                print("\n📋 Available SHACL → JSON-LD Context Conversion Scenarios")
                print("=" * 60)
                if not conversions:
                    print("❌ No conversion.shacl_to_context scenarios configured in config.yml")
                    return 1
                for key, scenario in conversions.items():
                    print(f"\n🔹 {key}")
                    print(f"   Name:   {scenario.get('name', 'N/A')}")
                    print(f"   Input:  {scenario.get('input', 'N/A')}")
                    print(f"   Output: {scenario.get('output', 'N/A')}")
                print("\n💡 Usage:")
                print("   npm run convert:context                 # converts all scenarios")
                print("   npm run convert:context <scenario-name> # converts one scenario")
                print("   npm run convert:context -- -i in.ttl -o out.jsonld")
                return 0

            has_overrides = any(v is not None for v in (ns.input, ns.output))
            scenario_name = getattr(ns, "scenario", None)

            if scenario_name:
                scenario = conversions.get(scenario_name)
                if not scenario:
                    print(f"❌ ERROR: Conversion scenario '{scenario_name}' not found in config.yml")
                    print(f"Available scenarios: {', '.join(sorted(conversions.keys()))}")
                    print("Run 'node docker/docker.js run cli convert context --list' to see all scenarios")
                    return 1

                input_file = ns.input or scenario.get("input")
                output_file = ns.output or scenario.get("output")

                if not input_file or not output_file:
                    print("❌ ERROR: Scenario is missing required 'input' or 'output' values")
                    return 1

                print(f"[CONVERT:CONTEXT] Using scenario '{scenario_name}': {scenario.get('name', 'N/A')}")
                cmd = [
                    sys.executable,
                    str(ctx_script),
                    "--input",
                    str(workspace_root / Path(input_file)),
                    "--output",
                    str(workspace_root / Path(output_file)),
                ]
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                return result.returncode

            if has_overrides:
                if ns.input is None:
                    print("❌ ERROR: --input is required when using overrides without a scenario")
                    return 1
                if ns.output is None:
                    print("❌ ERROR: --output is required when using overrides without a scenario")
                    return 1
                cmd = [
                    sys.executable,
                    str(ctx_script),
                    "--input",
                    str(workspace_root / Path(ns.input)),
                    "--output",
                    str(workspace_root / Path(ns.output)),
                ]
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                return result.returncode

            if not conversions:
                print("❌ ERROR: No conversion.shacl_to_context scenarios configured in config.yml")
                return 1

            print(
                f"[CONVERT:CONTEXT] Converting all scenarios ({len(conversions)}): {', '.join(sorted(conversions.keys()))}"
            )
            worst_exit = 0
            for key in sorted(conversions.keys()):
                scenario = conversions.get(key) or {}
                input_file = scenario.get("input")
                output_file = scenario.get("output")
                if not input_file or not output_file:
                    print(f"\n[CONVERT:CONTEXT] ❌ Scenario '{key}' is missing 'input' or 'output' in config.yml")
                    worst_exit = max(worst_exit, 1)
                    continue

                print(f"\n[CONVERT:CONTEXT] === Scenario '{key}': {scenario.get('name', 'N/A')} ===")
                cmd = [
                    sys.executable,
                    str(ctx_script),
                    "--input",
                    str(workspace_root / Path(input_file)),
                    "--output",
                    str(workspace_root / Path(output_file)),
                ]
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                worst_exit = max(worst_exit, result.returncode)

            return worst_exit
        
        elif ns.convert_cmd == "ts":
            import subprocess
            ts_script = workspace_root / "scripts" / "lib" / "jsonschema_to_typescript.py"
            conversions = config_obj._data.get("conversion", {}).get("json_to_ts", {})

            # Handle --list
            if getattr(ns, "list", False):
                print("\n📋 Available JSON Schema → TypeScript Conversion Scenarios")
                print("=" * 60)
                if not conversions:
                    print("❌ No conversion.json_to_ts scenarios configured in config.yml")
                    return 1
                for key, scenario in conversions.items():
                    print(f"\n🔹 {key}")
                    print(f"   Name:   {scenario.get('name', 'N/A')}")
                    print(f"   Input:  {scenario.get('input', 'N/A')}")
                    print(f"   Output: {scenario.get('output', 'N/A')}")
                    if scenario.get("source"):
                        print(f"   Source: {scenario.get('source')}")
                print("\n💡 Usage:")
                print("   npm run convert:ts                 # converts all scenarios")
                print("   npm run convert:ts <scenario-name> # converts one scenario")
                print("   npm run convert:ts -- -i in.json -o out.ts")
                return 0

            has_overrides = any(v is not None for v in (ns.input, ns.output, ns.source, ns.banner))
            scenario_name = getattr(ns, "scenario", None)

            # Case 1: specific scenario
            if scenario_name:
                scenario = conversions.get(scenario_name)
                if not scenario:
                    print(f"❌ ERROR: Conversion scenario '{scenario_name}' not found in config.yml")
                    print(f"Available scenarios: {', '.join(sorted(conversions.keys()))}")
                    print("Run 'node docker/docker.js run cli convert ts --list' to see all scenarios")
                    return 1

                input_file = ns.input or scenario.get("input")
                output_file = ns.output or scenario.get("output")
                source_file = ns.source or scenario.get("source")

                if not input_file or not output_file:
                    print("❌ ERROR: Scenario is missing required 'input' or 'output' values")
                    return 1

                print(f"[CONVERT:TS] Using scenario '{scenario_name}': {scenario.get('name', 'N/A')}")
                cmd = [
                    sys.executable,
                    str(ts_script),
                    "--input",
                    str(workspace_root / Path(input_file)),
                    "--output",
                    str(workspace_root / Path(output_file)),
                ]
                if ns.banner:
                    cmd.extend(["--banner", ns.banner])
                if source_file:
                    cmd.extend(["--source", source_file])
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                return result.returncode

            # Case 2: explicit overrides (single run)
            if has_overrides:
                if ns.input is None:
                    print("❌ ERROR: --input is required when using overrides without a scenario")
                    return 1
                if ns.output is None:
                    print("❌ ERROR: --output is required when using overrides without a scenario")
                    return 1

                cmd = [
                    sys.executable,
                    str(ts_script),
                    "--input",
                    str(workspace_root / Path(ns.input)),
                    "--output",
                    str(workspace_root / Path(ns.output)),
                ]
                if ns.banner:
                    cmd.extend(["--banner", ns.banner])
                if ns.source:
                    cmd.extend(["--source", ns.source])
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                return result.returncode

            # Case 3: no scenario and no overrides => convert all
            if not conversions:
                print("❌ ERROR: No conversion.json_to_ts scenarios configured in config.yml")
                return 1

            print(
                f"[CONVERT:TS] Converting all scenarios ({len(conversions)}): {', '.join(sorted(conversions.keys()))}"
            )

            worst_exit = 0
            for key in sorted(conversions.keys()):
                scenario = conversions.get(key) or {}
                input_file = scenario.get("input")
                output_file = scenario.get("output")
                source_file = scenario.get("source")

                if not input_file or not output_file:
                    print(f"\n[CONVERT:TS] ❌ Scenario '{key}' is missing 'input' or 'output' in config.yml")
                    worst_exit = max(worst_exit, 1)
                    continue

                print(f"\n[CONVERT:TS] === Scenario '{key}': {scenario.get('name', 'N/A')} ===")
                cmd = [
                    sys.executable,
                    str(ts_script),
                    "--input",
                    str(workspace_root / Path(input_file)),
                    "--output",
                    str(workspace_root / Path(output_file)),
                ]
                if ns.banner:
                    cmd.extend(["--banner", ns.banner])
                if source_file:
                    cmd.extend(["--source", source_file])
                if ns.verbose:
                    cmd.append("--verbose")
                result = subprocess.run(cmd)
                worst_exit = max(worst_exit, result.returncode)

            return worst_exit

    print("Unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
