#!/usr/bin/env python3
"""Show current configuration from config.yml"""

import sys
from pathlib import Path

# Add scripts directory to path to import lib modules
scripts_dir = Path(__file__).resolve().parent
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from lib.config import load_config

def main():
    try:
        config = load_config()
        print(f"\n📋 Current Configuration")
        print("=" * 50)
        print(f"Ontology version:  {config.ontology_version}")
        print(f"Shapes version:    {config.shapes_version}")
        print(f"Examples version:  {config.examples_version}")
        print(f"Codelists version: {config.codelists_version}")
        print(f"Build version:     {config.build_version}")
        print("\n📁 Example Paths")
        print("=" * 50)
        print(f"Ontology: {config.get_ontology_path('digitalWastePassport.ttl')}")
        print(f"Shapes:   {config.get_shapes_path('digital-waste-passport.shacl.ttl')}")
        print(f"Build:    {config.get_build_path('digitalWastePassport.schema.json')}")
        print("\n🔗 GitHub Repository")
        print("=" * 50)
        print(f"Owner:  {config.repository['owner']}")
        print(f"Repo:   {config.repository['name']}")
        print(f"Branch: {config.repository['branch']}")
        print("\n✨ Generation Artifacts")
        print("=" * 50)
        artifacts = config.get_generation_artifacts()
        if not artifacts:
            print("  (none)")

        conv_shacl_to_json = config.get_conversion_shacl_to_json()
        conv_shacl_to_context = config.get_conversion_shacl_to_context()
        conv_json_to_ts = config.get_conversion_json_to_ts()

        for artifact in artifacts:
            name = (artifact or {}).get("name", "(unnamed)")
            print(f"\n  • {name}")

            # Resolve via conversion configs
            shacl_s = (conv_shacl_to_json or {}).get(name) or {}
            ctx_s = (conv_shacl_to_context or {}).get(name) or {}
            ts_s = (conv_json_to_ts or {}).get(name) or {}

            # Show everything that is expected to be generated for this artifact
            # (faithful to config.yml): schema output, TS output, and optional context output.
            if shacl_s:
                print(f"     shacl:  {shacl_s.get('input', 'N/A')}")
                print(f"     schema: {shacl_s.get('output', 'N/A')}")
                if shacl_s.get("naming"):
                    print(f"     naming: {shacl_s.get('naming')}")
                # When naming=context, this is the context file used during schema generation
                if shacl_s.get("context"):
                    print(f"     schema-context: {shacl_s.get('context')}")

            if ctx_s:
                print(f"     context: {ctx_s.get('output', 'N/A')}")

            if ts_s:
                print(f"     ts:     {ts_s.get('output', 'N/A')}")
                if ts_s.get("source"):
                    print(f"     banner-source: {ts_s.get('source')}")
            if not shacl_s and not ts_s and not ctx_s:
                print("     (no matching conversion scenario found)")

        conversions = config.get_conversion_json_to_ts()
        print("\n🔁 Conversion: JSON Schema → TypeScript")
        print("=" * 50)
        if not conversions:
            print("  (none)")
        else:
            for key in sorted(conversions.keys()):
                scenario = conversions.get(key) or {}
                print(f"\n  • {key}")
                print(f"     name:   {scenario.get('name', 'N/A')}")
                print(f"     input:  {scenario.get('input', 'N/A')}")
                print(f"     output: {scenario.get('output', 'N/A')}")
                if scenario.get("source"):
                    print(f"     source: {scenario.get('source')}")

        shacl_to_json = config.get_conversion_shacl_to_json()
        print("\n🔁 Conversion: SHACL → JSON Schema")
        print("=" * 50)
        if not shacl_to_json:
            print("  (none)")
        else:
            for key in sorted(shacl_to_json.keys()):
                scenario = shacl_to_json.get(key) or {}
                print(f"\n  • {key}")
                print(f"     name:   {scenario.get('name', 'N/A')}")
                print(f"     input:  {scenario.get('input', 'N/A')}")
                print(f"     output: {scenario.get('output', 'N/A')}")
                if scenario.get("naming"):
                    print(f"     naming: {scenario.get('naming')}")
                if scenario.get("context"):
                    print(f"     context: {scenario.get('context')}")

        shacl_to_context = config.get_conversion_shacl_to_context()
        print("\n🔁 Conversion: SHACL → JSON-LD Context")
        print("=" * 50)
        if not shacl_to_context:
            print("  (none)")
        else:
            for key in sorted(shacl_to_context.keys()):
                scenario = shacl_to_context.get(key) or {}
                print(f"\n  • {key}")
                print(f"     name:   {scenario.get('name', 'N/A')}")
                print(f"     input:  {scenario.get('input', 'N/A')}")
                print(f"     output: {scenario.get('output', 'N/A')}")

        print("\n🧪 Validation")
        print("=" * 50)

        owl_cfg = config.get_owl_validation_config() or {}
        print("\n  OWL")
        ontology_glob = f"{config.paths.get('ontology', 'ontology')}/{config.ontology_version}/*.ttl"
        codelists_glob = f"{config.paths.get('codelists', 'codelists')}/{config.codelists_version}/**/*.ttl"
        include_codelists = owl_cfg.get("include_codelists", "N/A")

        print(f"     inputs:            auto ({ontology_glob})")
        if include_codelists is True:
            print(f"     inputs+codelists:  auto ({codelists_glob})")
        print(f"     reasoner:          {owl_cfg.get('reasoner', 'N/A')}")
        print(f"     profile:           {owl_cfg.get('profile', 'N/A')}")
        print(f"     include_codelists: {include_codelists}")

        shacl_scenarios = config.get_validation_shacl_scenarios() or {}
        print("\n  SHACL Scenarios")
        if not shacl_scenarios:
            print("     (none)")
        else:
            for key in sorted(shacl_scenarios.keys()):
                scenario = shacl_scenarios.get(key) or {}
                print(f"\n     • {key}")
                print(f"        name:        {scenario.get('name', 'N/A')}")
                print(f"        description: {scenario.get('description', 'N/A')}")
                print(f"        data:        {scenario.get('data', 'N/A')}")
                print(f"        shapes:      {scenario.get('shapes', 'N/A')}")
                print(f"        format:      {scenario.get('format', 'N/A')}")
                # Keep faithful to config.yml: print extras even if empty string
                if "extras" in scenario:
                    print(f"        extras:      {scenario.get('extras')}")
        print()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
