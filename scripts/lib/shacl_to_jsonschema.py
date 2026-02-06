#!/usr/bin/env python3
"""
SHACL to JSON Schema Converter
================================

Generates a structural JSON Schema projection from SHACL shapes.

This is NOT a semantic conversion - it only captures structural validation
constraints that can be expressed in JSON Schema. SHACL remains the source
of truth for semantic validation.

Usage:
    python shacl-to-jsonschema.py --input shapes/v0.1/digital-waste-passport.shacl.ttl --output build/v0.1/digitalWastePassport.schema.json
    python shacl-to-jsonschema.py --input shapes/v0.1/digital-marpol-waste-passport.shacl.ttl --output build/v0.1/digitalMarpolWastePassport.schema.json

Author: Blue Room Innovation
Date: 2026-01-08
"""

import argparse
import json
import sys
import logging
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import date, datetime, time
from decimal import Decimal
from rdflib import Graph, Namespace, URIRef, Literal, RDF, RDFS, XSD
from rdflib.namespace import SH, OWL
from pathlib import Path
from urllib.parse import urlparse, unquote

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class SHACLToJSONSchemaConverter:
    """Converts SHACL shapes to JSON Schema."""
    
    def __init__(
        self,
        graph: Graph,
        *,
        naming: str = "curie",
        context_path: Optional[Path] = None,
    ):
        self.graph = graph
        self.naming = naming
        self.context_path = context_path
        self.definitions: Dict[str, Any] = {}
        self.warnings: List[str] = []
        self.class_to_shape_map: Dict[str, str] = {}  # Maps class URIs to shape names

        self._iri_to_term: Dict[str, str] = {}
        if self.naming == "context":
            if not self.context_path:
                raise ValueError("naming='context' requires context_path")
            self._iri_to_term = self._load_jsonld_context_inverse(self.context_path)
        
        # XSD to JSON Schema type mapping
        self.xsd_to_json_type = {
            XSD.string: "string",
            XSD.integer: "integer",
            XSD.int: "integer",
            XSD.long: "integer",
            XSD.short: "integer",
            XSD.byte: "integer",
            XSD.decimal: "number",
            XSD.float: "number",
            XSD.double: "number",
            XSD.boolean: "boolean",
            XSD.date: "string",
            XSD.dateTime: "string",
            XSD.time: "string",
            XSD.anyURI: "string",
        }
        
        # XSD to JSON Schema format mapping
        self.xsd_to_json_format = {
            XSD.dateTime: "date-time",
            XSD.date: "date",
            XSD.time: "time",
            XSD.anyURI: "uri",
        }
    
    def convert(self) -> Dict[str, Any]:
        """Main conversion method."""
        logger.info("Starting SHACL to JSON Schema conversion...")
        
        # Find all NodeShapes
        node_shapes = list(self.graph.subjects(RDF.type, SH.NodeShape))
        logger.info(f"Found {len(node_shapes)} NodeShapes")
        
        if not node_shapes:
            logger.warning("No SHACL NodeShapes found in input file")
            return self._create_empty_schema()
        
        # Build mapping from classes to shapes (for sh:class resolution)
        self._build_class_to_shape_map(node_shapes)
        
        # Convert each shape to a JSON Schema definition
        for shape in node_shapes:
            self._convert_node_shape(shape)
        
        # Create the main schema
        schema = self._create_main_schema()
        
        # Log warnings
        if self.warnings:
            logger.warning(f"Conversion completed with {len(self.warnings)} warnings:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        else:
            logger.info("Conversion completed successfully with no warnings")
        
        return schema
    
    def _build_class_to_shape_map(self, node_shapes: List[URIRef]):
        """Build a mapping from targetClass to Shape name for sh:class resolution."""
        for shape in node_shapes:
            target_class = self.graph.value(shape, SH.targetClass)
            if target_class:
                shape_name = self._get_local_name(shape)
                self.class_to_shape_map[str(target_class)] = shape_name
                logger.debug(f"Mapped class {target_class} -> shape {shape_name}")
    
    def _create_empty_schema(self) -> Dict[str, Any]:
        """Create an empty schema when no shapes are found."""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Empty Schema",
            "description": "No SHACL shapes found for conversion",
            "type": "object"
        }
    
    def _create_main_schema(self) -> Dict[str, Any]:
        """Create the main JSON Schema structure."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Generated JSON Schema from SHACL",
            "description": "This schema was automatically generated from SHACL shapes. It provides structural validation only. For semantic validation, use the original SHACL shapes.",
            "$comment": "Auto-generated by shacl-to-jsonschema.py - DO NOT EDIT MANUALLY",
            "$defs": self.definitions
        }
        
        # If there's a main shape, use it as root (expand it rather than just $ref)
        # Look for a shape that represents the main class (heuristic: first shape found)
        if self.definitions:
            first_def = next(iter(self.definitions.keys()))
            # Instead of using $ref at root, copy the first definition to the root
            # This is compatible with json-schema-to-typescript
            first_shape = self.definitions[first_def]
            schema.update({
                "type": first_shape.get("type", "object"),
                "properties": first_shape.get("properties", {}),
                "required": first_shape.get("required", []),
            })
            if "additionalProperties" in first_shape:
                schema["additionalProperties"] = first_shape["additionalProperties"]
            # Preserve composition keywords so downstream tooling (json-schema-to-typescript)
            # can reflect sh:and/sh:or mappings correctly.
            for key in ("allOf", "anyOf", "oneOf", "not"):
                if key in first_shape:
                    schema[key] = first_shape[key]
            if "title" in first_shape:
                schema["title"] = first_shape["title"]
            if "description" in first_shape:
                schema["description"] = first_shape["description"]
        
        return schema
    
    def _convert_node_shape(self, shape: URIRef):
        """Convert a single NodeShape to a JSON Schema definition."""
        shape_name = self._get_local_name(shape)
        logger.info(f"Converting shape: {shape_name}")
        
        definition: Dict[str, Any] = {
            "type": "object",
            "$comment": f"Generated from SHACL shape {shape}"
        }
        
        # Get shape labels and description.
        # IMPORTANT: json-schema-to-typescript uses JSON Schema "title" to name interfaces.
        # We want interface names to match SHACL NodeShape names (local part of the shape IRI)
        # rather than sh:name (human label) or sh:targetClass.
        name = self._get_literal_value(shape, SH.name)
        description = self._get_literal_value(shape, SH.description)

        # Always title by shape name for stable, 1:1 typing.
        definition["title"] = shape_name

        if description:
            definition["description"] = description
        elif name:
            # If there is no explicit description, fall back to sh:name as a description.
            definition["description"] = name
        
        # Process properties
        properties: Dict[str, Any] = {}
        required: List[str] = []
        
        # Add @type property based on sh:targetClass
        target_class = self.graph.value(shape, SH.targetClass)
        if target_class:
            class_name = self._get_local_name(target_class)
            properties["@type"] = {
                "type": "string",
                "const": class_name,
                "description": f"Type identifier for {class_name}"
            }
            required.append("@type")
            logger.debug(f"Added required @type field with value '{class_name}' to {shape_name}")
        
        for prop_shape in self.graph.objects(shape, SH.property):
            prop_name, prop_def, is_required = self._convert_property_shape(prop_shape)
            if prop_name:
                properties[prop_name] = prop_def
                if is_required:
                    required.append(prop_name)

        # Handle node-level sh:or (e.g. constraints like "latitude and longitude both present or both absent")
        shape_or_list = self.graph.value(shape, SH["or"])
        if shape_or_list:
            any_of: List[Dict[str, Any]] = []
            discovered_props: Dict[str, Any] = {}

            for alt_node in self._extract_list_nodes(shape_or_list):
                alt_schema, alt_props = self._convert_node_constraint_node_to_schema(alt_node)
                if alt_schema:
                    any_of.append(alt_schema)
                for name, schema in alt_props.items():
                    # Prefer the most informative schema definition for the property.
                    existing = discovered_props.get(name)
                    if existing is None or (not self._is_informative_property_schema(existing) and self._is_informative_property_schema(schema)):
                        discovered_props[name] = schema

            # Merge discovered properties into the main properties map.
            for name, schema in discovered_props.items():
                existing = properties.get(name)
                if existing is None or (not self._is_informative_property_schema(existing) and self._is_informative_property_schema(schema)):
                    properties[name] = schema

            if any_of:
                definition["anyOf"] = any_of
            else:
                self.warnings.append(f"sh:or found in NodeShape {shape_name} but no convertible alternatives were found")
        
        if properties:
            definition["properties"] = properties
        
        if required:
            definition["required"] = required

        # Handle NodeShape-level sh:and (shape composition) -> JSON Schema allOf
        and_list = self.graph.value(shape, SH["and"])
        if and_list:
            all_of: List[Dict[str, Any]] = []

            for and_node in self._extract_list_nodes(and_list):
                if isinstance(and_node, URIRef):
                    # If this points at another NodeShape, model it as a $ref.
                    ref_name = self._get_local_name(and_node)
                    if ref_name == shape_name:
                        # Avoid self-reference
                        continue
                    all_of.append({"$ref": f"#/$defs/{ref_name}"})
                else:
                    # Inline constraint node (BNode) - best-effort conversion.
                    and_schema, and_props = self._convert_node_constraint_node_to_schema(and_node)
                    for name, schema in and_props.items():
                        existing = properties.get(name)
                        if existing is None or (
                            not self._is_informative_property_schema(existing)
                            and self._is_informative_property_schema(schema)
                        ):
                            properties[name] = schema
                    if and_schema:
                        all_of.append(and_schema)

            if all_of:
                definition["allOf"] = all_of
            else:
                self.warnings.append(
                    f"sh:and found in NodeShape {shape_name} but no convertible members were found"
                )
        
        # Handle sh:closed
        closed = self._get_literal_value(shape, SH.closed)
        if closed and str(closed).lower() == "true":
            definition["additionalProperties"] = False
        
        self.definitions[shape_name] = definition

    def _is_informative_property_schema(self, schema: Any) -> bool:
        """Heuristic: decide whether a property schema carries useful typing/constraints."""
        if not isinstance(schema, dict):
            return False
        informative_keys = {
            "type",
            "$ref",
            "anyOf",
            "oneOf",
            "allOf",
            "enum",
            "format",
            "minimum",
            "maximum",
            "exclusiveMinimum",
            "exclusiveMaximum",
            "pattern",
            "minLength",
            "maxLength",
        }
        return any(k in schema for k in informative_keys)

    def _convert_node_constraint_node_to_schema(self, constraint_node: URIRef) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Convert an inline node constraint (e.g. inside NodeShape sh:or) to JSON Schema.

        Supports a subset needed for structural constraints:
        - sh:property blocks
        - sh:not blocks (recursively)

        Returns (schema, discovered_properties)
        """
        subschemas: List[Dict[str, Any]] = []
        discovered_props: Dict[str, Any] = {}

        # Inline sh:property constraints
        props: Dict[str, Any] = {}
        req: List[str] = []
        for prop_shape in self.graph.objects(constraint_node, SH.property):
            prop_name, prop_def, is_required = self._convert_property_shape(prop_shape)
            if prop_name:
                props[prop_name] = prop_def
                discovered_props[prop_name] = prop_def
                if is_required:
                    req.append(prop_name)

        if props or req:
            obj_schema: Dict[str, Any] = {"type": "object"}
            if props:
                obj_schema["properties"] = props
            if req:
                obj_schema["required"] = req
            subschemas.append(obj_schema)

        # Inline sh:not constraints
        for not_node in self.graph.objects(constraint_node, SH["not"]):
            nested_schema, nested_props = self._convert_node_constraint_node_to_schema(not_node)
            for k, v in nested_props.items():
                # Keep the best schema we can infer.
                existing = discovered_props.get(k)
                if existing is None or (not self._is_informative_property_schema(existing) and self._is_informative_property_schema(v)):
                    discovered_props[k] = v
            if nested_schema:
                subschemas.append({"not": nested_schema})

        if not subschemas:
            return {}, discovered_props
        if len(subschemas) == 1:
            return subschemas[0], discovered_props
        return {"allOf": subschemas}, discovered_props
    
    def _convert_property_shape(self, prop_shape: URIRef) -> tuple[Optional[str], Dict[str, Any], bool]:
        """Convert a property shape to JSON Schema property definition."""
        path = self.graph.value(prop_shape, SH.path)
        if not path:
            self.warnings.append(f"Property shape without sh:path found: {prop_shape}")
            return None, {}, False
        
        prop_name = self._get_property_name(path)
        prop_def: Dict[str, Any] = {}
        
        # Get description
        description = self._get_literal_value(prop_shape, SH.description)
        message = self._get_literal_value(prop_shape, SH.message)
        if description:
            prop_def["description"] = description
        elif message:
            prop_def["description"] = message
        
        # Determine type from sh:datatype, sh:class, sh:node, sh:nodeKind, or sh:or
        datatype = self.graph.value(prop_shape, SH.datatype)
        class_ref = self.graph.value(prop_shape, SH["class"])
        node_kind = self.graph.value(prop_shape, SH.nodeKind)
        or_list = self.graph.value(prop_shape, SH["or"])
        has_value = self.graph.value(prop_shape, SH.hasValue)
        
        if has_value is not None:
            # sh:hasValue -> const
            if isinstance(has_value, URIRef):
                val = self._get_property_name(has_value)
                prop_def["const"] = val
                prop_def["type"] = "string"
            elif isinstance(has_value, Literal):
                val = has_value.toPython()
                # Handle dates/times which are not JSON serializable by default
                if isinstance(val, (date, datetime, time)):
                    val = val.isoformat()
                elif isinstance(val, Decimal):
                    val = float(val)
                
                prop_def["const"] = val
                
                if isinstance(val, bool):
                     prop_def["type"] = "boolean"
                elif isinstance(val, (int, float)):
                     prop_def["type"] = "number"
                else:
                     prop_def["type"] = "string"

        elif or_list:
            # sh:or is an RDF list of alternative constraint shapes.
            # Map it to JSON Schema anyOf.
            any_of: List[Dict[str, Any]] = []
            for alt_node in self._extract_list_nodes(or_list):
                alt_schema = self._convert_inline_constraint_to_schema(alt_node)
                if alt_schema:
                    # Avoid nested anyOf (common when an alternative is sh:nodeKind sh:IRI)
                    if (
                        isinstance(alt_schema, dict)
                        and set(alt_schema.keys()) == {"anyOf"}
                        and isinstance(alt_schema.get("anyOf"), list)
                    ):
                        any_of.extend(alt_schema["anyOf"])
                    else:
                        any_of.append(alt_schema)

            if any_of:
                prop_def["anyOf"] = any_of
            else:
                self.warnings.append(f"sh:or found in {prop_name} but no convertible alternatives were found")
                prop_def["$comment"] = "sh:or present but could not be converted"

        elif datatype:
            json_type = self.xsd_to_json_type.get(datatype, "string")
            prop_def["type"] = json_type

            # Add format if applicable
            json_format = self.xsd_to_json_format.get(datatype)
            if json_format:
                prop_def["format"] = json_format

        elif node_kind:
            prop_def.update(self._nodekind_to_schema(node_kind))

        elif self.graph.value(prop_shape, SH.node):
            # sh:node directly references another shape.
            # NOTE: Some SHACL property shapes include both sh:class and sh:node.
            # For structural typing, sh:node is the most precise link to a NodeShape,
            # so we prefer it over sh:class.
            node_shape = self.graph.value(prop_shape, SH.node)
            shape_name = self._get_local_name(node_shape)
            prop_def["$ref"] = f"#/$defs/{shape_name}"

        elif class_ref:
            # sh:class points to an ontology class. Find the Shape that targets this class.
            class_uri = str(class_ref)
            shape_name = self.class_to_shape_map.get(class_uri)

            if shape_name:
                # Found a shape that targets this class
                prop_def["$ref"] = f"#/$defs/{shape_name}"
            else:
                # No shape found for this class - might be external or missing
                self.warnings.append(
                    f"No shape found with sh:targetClass {class_ref} for property {prop_name}"
                )
                prop_def["$comment"] = f"sh:class {class_ref} - no corresponding shape found"
        
        else:
            # No explicit type - default to allowing any type
            prop_def["$comment"] = "No explicit sh:datatype or sh:class found"
        
        # If the property schema is a $ref, avoid adding sibling keywords.
        # Downstream tools (json-schema-to-typescript) can generate spurious
        # helper interfaces (e.g. PartyShape1) when $ref coexists with description.
        if "$ref" in prop_def and "description" in prop_def:
            desc = prop_def["description"]
            ref = prop_def["$ref"]
            prop_def = {"description": desc, "allOf": [{"$ref": ref}]}

        # Handle cardinality
        min_count = self._get_literal_value(prop_shape, SH.minCount)
        max_count = self._get_literal_value(prop_shape, SH.maxCount)
        
        is_required = False
        if min_count is not None:
            min_count_int = int(min_count)
            if min_count_int >= 1:
                is_required = True
        
        # If maxCount > 1 or minCount > 1, this is an array
        if max_count is not None and int(max_count) > 1:
            array_def = {"type": "array"}
            if "type" in prop_def or "$ref" in prop_def:
                array_def["items"] = {k: v for k, v in prop_def.items() if k != "description"}
            if "description" in prop_def:
                array_def["description"] = prop_def["description"]
            if min_count is not None:
                array_def["minItems"] = int(min_count)
            if max_count is not None:
                array_def["maxItems"] = int(max_count)
            prop_def = array_def
        elif min_count is not None and int(min_count) > 1:
            # minCount > 1 without maxCount also implies array
            array_def = {"type": "array"}
            if "type" in prop_def or "$ref" in prop_def:
                array_def["items"] = {k: v for k, v in prop_def.items() if k != "description"}
            if "description" in prop_def:
                array_def["description"] = prop_def["description"]
            array_def["minItems"] = int(min_count)
            prop_def = array_def
        
        # Handle sh:in (enumeration)
        in_values = list(self.graph.objects(prop_shape, SH["in"]))
        if in_values:
            enum_values = self._extract_list_values(in_values[0])
            if enum_values:
                # If it's an array, add enum to items
                enum_target = prop_def["items"] if prop_def.get("type") == "array" and "items" in prop_def else prop_def

                # Special case: sh:in (true false) on xsd:boolean is redundant.
                # Keeping it can produce noisy TypeScript unions; drop it.
                if enum_target.get("type") == "boolean" and set(enum_values) == {True, False}:
                    pass
                else:
                    enum_target["enum"] = enum_values
        
        # Handle numeric constraints
        min_inclusive = self._get_literal_value(prop_shape, SH.minInclusive)
        max_inclusive = self._get_literal_value(prop_shape, SH.maxInclusive)
        min_exclusive = self._get_literal_value(prop_shape, SH.minExclusive)
        max_exclusive = self._get_literal_value(prop_shape, SH.maxExclusive)
        
        target_def = prop_def
        if prop_def.get("type") == "array" and "items" in prop_def:
            target_def = prop_def["items"]
        
        if min_inclusive is not None:
            target_def["minimum"] = float(min_inclusive)
        if max_inclusive is not None:
            target_def["maximum"] = float(max_inclusive)
        if min_exclusive is not None:
            target_def["exclusiveMinimum"] = float(min_exclusive)
        if max_exclusive is not None:
            target_def["exclusiveMaximum"] = float(max_exclusive)
        
        # Handle string constraints
        min_length = self._get_literal_value(prop_shape, SH.minLength)
        max_length = self._get_literal_value(prop_shape, SH.maxLength)
        pattern = self._get_literal_value(prop_shape, SH.pattern)
        
        if min_length is not None:
            target_def["minLength"] = int(min_length)
        if max_length is not None:
            target_def["maxLength"] = int(max_length)
        if pattern:
            target_def["pattern"] = str(pattern)
        
        # NOTE: sh:or is handled above and mapped to anyOf when possible.
        
        # Handle sh:xone (oneOf)
        xone_constraints = list(self.graph.objects(prop_shape, SH.xone))
        if xone_constraints:
            self.warnings.append(f"sh:xone found in {prop_name} - partial conversion to oneOf")
        
        # Handle sh:and (allOf)
        and_constraints = list(self.graph.objects(prop_shape, SH["and"]))
        if and_constraints:
            self.warnings.append(f"sh:and found in {prop_name} - partial conversion to allOf")
        
        # Handle sh:sparql (not convertible)
        sparql_constraints = list(self.graph.objects(prop_shape, SH.sparql))
        if sparql_constraints:
            self.warnings.append(f"sh:sparql found in {prop_name} - CANNOT be converted to JSON Schema")
            prop_def["$comment"] = (prop_def.get("$comment", "") + " Contains sh:sparql constraint not convertible to JSON Schema").strip()
        
        return prop_name, prop_def, is_required
    
    def _extract_list_values(self, list_node: URIRef) -> List[Any]:
        """Extract values from an RDF list.

        Preserves JSON-compatible native types when possible (e.g., booleans for xsd:boolean)
        to avoid generating incorrect enums like ["true"].
        """
        values = []
        current = list_node
        
        while current != RDF.nil:
            first = self.graph.value(current, RDF.first)
            if first is not None:
                if isinstance(first, URIRef):
                    values.append(str(first))
                elif isinstance(first, Literal):
                    py_value = first.toPython()

                    # Ensure JSON-serializable primitives.
                    if isinstance(py_value, (bool, int, float, str)):
                        values.append(py_value)
                    elif isinstance(py_value, Decimal):
                        values.append(float(py_value))
                    elif isinstance(py_value, (datetime, date, time)):
                        values.append(py_value.isoformat())
                    else:
                        values.append(str(first))
            
            rest = self.graph.value(current, RDF.rest)
            if rest:
                current = rest
            else:
                break
        
        return values

    def _extract_list_nodes(self, list_node: URIRef) -> List[URIRef]:
        """Extract nodes (URIRefs or BNodes) from an RDF list."""
        nodes: List[URIRef] = []
        current = list_node

        while current != RDF.nil:
            first = self.graph.value(current, RDF.first)
            if first is not None:
                nodes.append(first)

            rest = self.graph.value(current, RDF.rest)
            if rest:
                current = rest
            else:
                break

        return nodes

    def _nodekind_to_schema(self, node_kind: URIRef) -> Dict[str, Any]:
        """Map sh:nodeKind to a JSON Schema snippet (best-effort structural mapping)."""
        # SHACL node kinds: sh:IRI, sh:Literal, sh:BlankNode,
        # and the *Or* variants.
        if node_kind == SH.IRI:
            # JSON-LD often represents IRIs either as a string or as an object with @id.
            return {
                "anyOf": [
                    {"type": "string", "format": "uri"},
                    self._jsonld_id_object_schema(),
                ]
            }
        if node_kind == SH.Literal:
            # Without datatype, assume string (structural best-effort)
            return {"type": "string"}
        if node_kind == SH.BlankNode:
            return {"type": "object"}
        if node_kind == SH.BlankNodeOrIRI:
            return {
                "anyOf": [
                    {"type": "object"},
                    {"type": "string", "format": "uri"},
                    self._jsonld_id_object_schema(),
                ]
            }
        if node_kind == SH.IRIOrLiteral:
            return {
                "anyOf": [
                    {"type": "string", "format": "uri"},
                    self._jsonld_id_object_schema(),
                    {"type": "string"},
                ]
            }
        if node_kind == SH.BlankNodeOrLiteral:
            return {"anyOf": [{"type": "object"}, {"type": "string"}]}

        # Unknown / uncommon nodeKind
        return {"$comment": f"Unsupported sh:nodeKind {node_kind}"}

    def _jsonld_id_object_schema(self) -> Dict[str, Any]:
        """Schema for a JSON-LD IRI object like {"@id": "https://..."}."""
        return {
            "type": "object",
            "properties": {
                "@id": {"type": "string", "format": "uri"},
            },
            "required": ["@id"],
            # JSON-LD objects may contain other keys like @type, @context, etc.
            "additionalProperties": True,
        }

    def _convert_inline_constraint_to_schema(self, constraint_node: URIRef) -> Dict[str, Any]:
        """Convert an inline constraint node (e.g., inside sh:or) to JSON Schema."""
        datatype = self.graph.value(constraint_node, SH.datatype)
        class_ref = self.graph.value(constraint_node, SH["class"])
        node_kind = self.graph.value(constraint_node, SH.nodeKind)
        node_shape = self.graph.value(constraint_node, SH.node)

        if datatype:
            schema: Dict[str, Any] = {
                "type": self.xsd_to_json_type.get(datatype, "string")
            }
            json_format = self.xsd_to_json_format.get(datatype)
            if json_format:
                schema["format"] = json_format
            return schema

        if node_kind:
            return self._nodekind_to_schema(node_kind)

        if class_ref:
            class_uri = str(class_ref)
            shape_name = self.class_to_shape_map.get(class_uri)
            if shape_name:
                return {"$ref": f"#/$defs/{shape_name}"}
            return {"$comment": f"sh:class {class_ref} - no corresponding shape found"}

        if node_shape:
            shape_name = self._get_local_name(node_shape)
            return {"$ref": f"#/$defs/{shape_name}"}

        return {}
    
    def _get_property_name(self, path: URIRef) -> str:
        """Get a JSON-friendly property name from a path URI."""
        iri = str(path)

        if self.naming == "local":
            return self._get_local_name(path)

        if self.naming == "context":
            term = self._iri_to_term.get(iri)
            if term:
                return term
            # If not found in context, fall back to local name (best effort).
            return self._get_local_name(path)

        # Default: "curie" naming (stable and collision-resistant)
        local_name = self._get_local_name(path)
        for prefix, namespace in self.graph.namespaces():
            if str(path).startswith(str(namespace)):
                return f"{prefix}:{local_name}"
        return local_name

    def _load_jsonld_context_inverse(self, context_path: Path) -> Dict[str, str]:
        """Load a JSON-LD context file and build an inverse mapping: IRI -> term.

        Supports string term definitions like:
          {"@context": {"schema": "https://schema.org/", "name": "schema:name"}}
        """
        try:
            with context_path.open("r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as e:
            raise ValueError(f"Failed to load JSON-LD context: {context_path} ({e})")

        ctx = doc.get("@context") if isinstance(doc, dict) else None
        if not isinstance(ctx, dict):
            raise ValueError(f"Invalid JSON-LD context document (missing @context): {context_path}")

        # Prefix mappings inside the context
        prefixes: Dict[str, str] = {
            k: v for k, v in ctx.items() if isinstance(k, str) and isinstance(v, str) and v.endswith(('/', '#'))
        }

        def expand(value: str) -> str:
            if value.startswith("http://") or value.startswith("https://"):
                return value
            if ":" in value:
                pfx, suffix = value.split(":", 1)
                base = prefixes.get(pfx)
                if base:
                    return f"{base}{suffix}"
            return value

        iri_to_term: Dict[str, str] = {}
        for term, value in ctx.items():
            if not isinstance(term, str):
                continue
            if not isinstance(value, str):
                continue
            # Skip prefix declarations themselves
            if value.endswith(('/', '#')):
                continue

            iri = expand(value)
            # First term wins to keep deterministic output
            iri_to_term.setdefault(iri, term)

        return iri_to_term
    
    def _get_local_name(self, uri: URIRef) -> str:
        """Extract the local name from a URI."""
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        elif "/" in uri_str:
            return uri_str.split("/")[-1]
        return uri_str
    
    def _get_literal_value(self, subject: URIRef, predicate: URIRef) -> Optional[str]:
        """Get a literal value from the graph."""
        value = self.graph.value(subject, predicate)
        if value:
            return str(value)
        return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert SHACL shapes to JSON Schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python shacl-to-jsonschema.py -i shapes/v0.1/digital-waste-passport.shacl.ttl -o build/v0.1/digitalWastePassport.schema.json
  python shacl-to-jsonschema.py --input shapes/digital-marpol-waste-passport.shacl.ttl --output build/digitalMarpolWastePassport.schema.json
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Input SHACL file (Turtle format)"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Output JSON Schema file"
    )

    parser.add_argument(
        "--naming",
        default="curie",
        choices=["curie", "local", "context"],
        help="Property naming strategy: curie (schema:name), local (name), or context (use term from JSON-LD context).",
    )

    parser.add_argument(
        "--context",
        default=None,
        help="Path to a JSON-LD context file (required when --naming=context).",
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Check input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    # Load SHACL graph (and any owl:imports)
    logger.info(f"Loading SHACL file: {args.input}")
    graph = Graph()
    try:
        graph.parse(args.input, format="turtle")
        logger.info(f"Loaded {len(graph)} triples")

        # Follow owl:imports recursively for local Turtle files.
        input_path_abs = input_path.resolve()

        def resolve_import_path(import_iri: str, base_dir: Path) -> Optional[Path]:
            try:
                parsed = urlparse(import_iri)
                if parsed.scheme in ("http", "https"):
                    return None
                if parsed.scheme == "file":
                    # file:///C:/path or file:/C:/path
                    p = unquote(parsed.path)
                    if p.startswith("/") and len(p) >= 3 and p[2] == ":":
                        p = p[1:]  # strip leading '/' for Windows drive paths
                    return Path(p)
            except Exception:
                pass

            # Treat as a filesystem path (absolute or relative)
            candidate = Path(import_iri)
            if not candidate.is_absolute():
                candidate = base_dir / candidate
            return candidate

        def load_imports_recursive(base_file: Path, visited: Set[Path]):
            base_dir = base_file.parent
            for imported in list(graph.objects(None, OWL.imports)):
                if not isinstance(imported, URIRef):
                    continue
                import_iri = str(imported)
                import_path = resolve_import_path(import_iri, base_dir)
                if not import_path:
                    logger.debug(f"Skipping non-local owl:imports: {import_iri}")
                    continue

                try:
                    import_path_abs = import_path.resolve()
                except Exception:
                    import_path_abs = import_path

                if import_path_abs in visited:
                    continue
                if not import_path_abs.exists():
                    logger.warning(f"owl:imports target not found (skipped): {import_path_abs}")
                    visited.add(import_path_abs)
                    continue

                logger.info(f"Loading owl:imports: {import_path_abs}")
                try:
                    graph.parse(str(import_path_abs), format="turtle")
                    visited.add(import_path_abs)
                except Exception as e:
                    logger.warning(f"Failed to parse owl:imports '{import_path_abs}': {e}")
                    visited.add(import_path_abs)
                    continue

                # Recurse: imported files may themselves declare owl:imports
                load_imports_recursive(import_path_abs, visited)

        load_imports_recursive(input_path_abs, visited={input_path_abs})
        logger.info(f"Graph size after owl:imports: {len(graph)} triples")
    except Exception as e:
        logger.error(f"Failed to parse SHACL file: {e}")
        sys.exit(1)
    
    # Convert
    context_path = Path(args.context) if args.context else None
    try:
        converter = SHACLToJSONSchemaConverter(
            graph,
            naming=args.naming,
            context_path=context_path,
        )
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    schema = converter.convert()
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing JSON Schema to: {args.output}")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    
    logger.info("✅ Conversion complete")
    
    # Exit with warning code if there were warnings
    if converter.warnings:
        sys.exit(2)  # Non-zero exit code to signal warnings


if __name__ == "__main__":
    main()
