#!/usr/bin/env python
"""
Markdown wiki generator for Turtle ontologies in the `ontology/v*/` directory.

Requirements:
    pip install -r requirements.txt

Usage:
    python scripts/generate-wiki.py [--ontology-dir ontology] [--output-dir wiki] [--include-codelists]

Produces:
    - wiki/index.md global summary
    - wiki/<ontology-name>/README.md details (Classes, Object properties, Data properties)

Features:
    - Extracts rdfs:label (multi-language) and rdfs:comment
    - Fallback to localName when label is missing
    - Domains and ranges of properties
    - Subclasses
    - Handling of duplicates and stable ordering

Limitations:
    - Does not process complex axioms (OWL restrictions) yet.
    - Codelists are included only if --include-codelists is passed.
"""
import argparse
import os
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from urllib.parse import quote
import rdflib
from rdflib import RDF, RDFS, OWL
try:
    from graphviz import Digraph  # type: ignore
except ImportError:  # pragma: no cover
    Digraph = None  # type: ignore

# Namespaces comunes
SKOS = rdflib.Namespace("http://www.w3.org/2004/02/skos/core#")
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")

LOGGER = logging.getLogger("generate-wiki")

def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')
    LOGGER.debug("Logging initialized in DEBUG mode")

def slug(uri: rdflib.term.Identifier) -> str:
    s = str(uri)
    if '#' in s:
        s = s.split('#')[-1]
    else:
        s = s.rstrip('/').split('/')[-1]
    return "".join(c if c.isalnum() else '-' for c in s).strip('-').lower()

def local_name(uri: rdflib.term.Identifier) -> str:
    s = str(uri)
    if '#' in s:
        return s.split('#')[-1]
    return s.rstrip('/').split('/')[-1]

def get_labels(g: rdflib.Graph, subject) -> Dict[str, List[str]]:
    labels: Dict[str, List[str]] = {}
    for p in [RDFS.label, SKOS.prefLabel]:
        for lbl in g.objects(subject, p):
            lang = getattr(lbl, 'language', None) or 'und'
            labels.setdefault(lang, []).append(str(lbl))
    return labels

def get_comments(g: rdflib.Graph, subject) -> Dict[str, List[str]]:
    comments: Dict[str, List[str]] = {}
    for c in g.objects(subject, RDFS.comment):
        lang = getattr(c, 'language', None) or 'und'
        comments.setdefault(lang, []).append(str(c))
    return comments

def format_multilang(d: Dict[str, List[str]]) -> str:
    if not d:
        return ''
    lines = []
    # Priorizar es, en, und
    order = sorted(d.keys(), key=lambda k: (k != 'es', k != 'en', k))
    for lang in order:
        values = sorted(set(d[lang]))
        for v in values:
            lines.append(f"- ({lang}) {v}")
    return '\n'.join(lines)

def extract_entities(g: rdflib.Graph, rdf_type) -> List[rdflib.term.Identifier]:
    return sorted(set(g.subjects(RDF.type, rdf_type)), key=lambda u: str(u))

def _normalize_artifact_key(stem: str) -> str:
    """Normalizes file names to an ontology key.

    Supports conventions such as:
    - <OntologyName>Shapes.ttl
    - <ontology>.shacl.ttl
    - <ontology>.context.jsonld
    """
    key = stem
    # Strip common suffixes (order matters)
    for suffix in (".shacl", "-shacl", "_shacl", ".context", "-context", "_context"):
        if key.endswith(suffix):
            key = key[: -len(suffix)]
    if key.endswith("Shapes"):
        key = key[: -len("Shapes")]
    return key


def build_index_row(
    name: str,
    classes: int,
    obj_props: int,
    data_props: int,
    shapes: Optional[int] = None,
    contexts: Optional[int] = None,
) -> str:
    cols: List[str] = [name, str(classes), str(obj_props), str(data_props)]
    if shapes is not None:
        cols.append(str(shapes))
    if contexts is not None:
        cols.append(str(contexts))
    return "| " + " | ".join(cols) + " |"

def extract_metadata(g: rdflib.Graph) -> Dict[str, List[str]]:
    """Extracts simple metadata from the graph (title, description, creator, contributor, version, date, imports).
    Tries multiple standard properties (DC, DCTERMS, OWL) for each field.
    """
    DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
    DCT = rdflib.Namespace('http://purl.org/dc/terms/')
    METADATA_PREDICATES = {
        'title': [DCT.title, DC.title],
        'description': [DCT.description, DC.description],
        'creator': [DCT.creator, DC.creator],
        'contributor': [DCT.contributor, DC.contributor],
        'date': [DCT.date, DC.date],
        'version': [OWL.versionInfo],
        'imports': [OWL.imports],
    }
    # Find the ontology node
    ontology_nodes = list(g.subjects(RDF.type, OWL.Ontology))
    meta: Dict[str, List[str]] = {}
    for ont in ontology_nodes:
        for key, preds in METADATA_PREDICATES.items():
            for p in preds:
                for o in g.objects(ont, p):
                    meta.setdefault(key, []).append(str(o))
    return meta


def md_table_cell(text: Optional[str]) -> str:
    """Escape text for safe inclusion inside a Markdown table cell.

    - Escapes pipe characters so they don't split columns.
    - Converts newlines to <br> so multiline comments don't break the table.
    """
    if not text:
        return ""
    value = str(text).replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("|", "\\|")
    value = "<br>".join(line.strip() for line in value.split("\n"))
    return value.strip()


def generate_readme(
    g: rdflib.Graph,
    ontology_file: Path,
    rich: bool = False,
    mermaid: bool = False,
    source_href: Optional[str] = None,
) -> str:
    classes = extract_entities(g, OWL.Class)
    obj_props = extract_entities(g, OWL.ObjectProperty)
    data_props = extract_entities(g, OWL.DatatypeProperty)

    lines: List[str] = []
    if not rich:
        lines.append(f"# Ontology: {ontology_file.name}")
        lines.append("")
        if source_href:
            display_path = str(ontology_file).replace("\\", "/")
            lines.append(f"Source: [{display_path}]({source_href})")
        else:
            lines.append(f"Source: `{ontology_file}`")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- Classes: {len(classes)}")
        lines.append(f"- Object Properties: {len(obj_props)}")
        lines.append(f"- Data Properties: {len(data_props)}")
        lines.append("")
    else:
        meta = extract_metadata(g)
        pretty_name = ontology_file.stem
        lines.append(f"# {pretty_name} Ontology")
        lines.append("")
        # Use a bullet list to guarantee line breaks across Markdown renderers.
        if 'title' in meta:
            lines.append(f"- **Title:** {meta['title'][0]}")
        if 'description' in meta:
            lines.append(f"- **Description:** {meta['description'][0]}")
        if 'creator' in meta:
            creators = ', '.join(meta['creator'])
            lines.append(f"- **Creator:** {creators}")
        if 'contributor' in meta:
            contributors = ', '.join(meta['contributor'])
            lines.append(f"- **Contributor:** {contributors}")
        if 'date' in meta:
            lines.append(f"- **Date:** {meta['date'][0]}")
        if 'version' in meta:
            lines.append(f"- **Version:** {meta['version'][0]}")
        if 'imports' in meta:
            lines.append(f"- **Imports:** {', '.join(meta['imports'])}")
        if source_href:
            display_path = str(ontology_file).replace("\\", "/")
            lines.append(f"- **Link to ontology:** [{display_path}]({source_href})")
        else:
            lines.append("- **Link to ontology:** " + str(ontology_file))
        lines.append("")
        # Mermaid class diagram
        if mermaid:
            lines.append("```mermaid")
            lines.append("classDiagram")
            # Simple attributes from datatype properties (domain -> property -> range)
            # Collect datatype properties per class
            dt_by_class: Dict[str, List[Tuple[str,str]]] = {}
            for dp in data_props:
                domains = list(g.objects(dp, RDFS.domain))
                ranges = list(g.objects(dp, RDFS.range))
                if not domains:
                    continue
                rng_text = ranges[0] if ranges else ''
                for d in domains:
                    cname = local_name(d)
                    dt_by_class.setdefault(cname, []).append((local_name(dp), local_name(rng_text) if rng_text else ''))
            # Class declarations
            for c in classes:
                cname = local_name(c)
                lines.append(f"   class {cname}{{")
                for (prop, rng) in dt_by_class.get(cname, []):
                    rng_disp = rng if rng else ''
                    lines.append(f"       {prop} {rng_disp}")
                lines.append("   }")
            # Object property relations
            for op in obj_props:
                pname = local_name(op)
                domains = list(g.objects(op, RDFS.domain))
                ranges = list(g.objects(op, RDFS.range))
                for d in domains:
                    for r in ranges:
                        lines.append(f"   {local_name(d)} --> {local_name(r)} : {pname}")
            # Subclass relations
            for c in classes:
                for sc in g.objects(c, RDFS.subClassOf):
                    if (sc, RDF.type, OWL.Class) in g or isinstance(sc, rdflib.term.URIRef):
                        lines.append(f"   {local_name(c)} --|> {local_name(sc)}")
            lines.append("```")
            lines.append("")

    if rich:
        # Rich tables similar to user example
        if classes:
            lines.append("## Classes")
            lines.append("\n|Name|Description|Datatype properties|Object properties|Subclass of|")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for c in classes:
                cname = local_name(c)
                comments = get_comments(g, c)
                desc = comments.get('es') or comments.get('en') or comments.get('und') or ['']
                desc_txt = md_table_cell(desc[0])
                # Datatype props for this class
                dt_props = []
                for dp in data_props:
                    if (dp, RDF.type, OWL.DatatypeProperty) in g:
                        for d in g.objects(dp, RDFS.domain):
                            if local_name(d) == cname:
                                dt_props.append(f"[{local_name(dp)}](#{local_name(dp)})")
                # Object props for this class (as domain)
                op_props = []
                for op in obj_props:
                    for d in g.objects(op, RDFS.domain):
                        if local_name(d) == cname:
                            op_props.append(f"[{local_name(op)}](#{local_name(op)})")
                subclass_of = []
                for sc in g.objects(c, RDFS.subClassOf):
                    subclass_of.append(local_name(sc))
                # Single-line classes table
                lines.append(f"|<span id=\"{cname}\">{cname}</span>|{desc_txt}|{', '.join(dt_props)}|{', '.join(op_props)}|{', '.join(subclass_of)}|")
        if data_props:
            lines.append("\n## Data Properties\n")
            lines.append("|Name|Description|Domain|Range|Subproperty of|")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for dp in data_props:
                pname = local_name(dp)
                comments = get_comments(g, dp)
                desc = comments.get('es') or comments.get('en') or comments.get('und') or ['']
                desc_txt = md_table_cell(desc[0])
                domains = [f"[{local_name(d)}](#{local_name(d)})" for d in g.objects(dp, RDFS.domain)]
                ranges = [local_name(r) for r in g.objects(dp, RDFS.range)]
                subprops = [local_name(sp) for sp in g.objects(dp, RDFS.subPropertyOf)]
                lines.append(f"|<span id=\"{pname}\">{pname}</span>|{desc_txt}|{', '.join(domains)}|{', '.join(ranges)}|{', '.join(subprops)}|")
        if obj_props:
            lines.append("\n## Object Properties\n")
            lines.append("|Name|Descriptions|Domain|Range|Subproperty of|")
            lines.append("| :--- | :--- | :--- | :--- | :--- |")
            for op in obj_props:
                pname = local_name(op)
                comments = get_comments(g, op)
                desc = comments.get('es') or comments.get('en') or comments.get('und') or ['']
                desc_txt = md_table_cell(' '.join(desc))
                domains = [f"[{local_name(d)}](#{local_name(d)})" for d in g.objects(op, RDFS.domain)]
                ranges = [f"[{local_name(r)}](#{local_name(r)})" for r in g.objects(op, RDFS.range)]
                subprops = [local_name(sp) for sp in g.objects(op, RDFS.subPropertyOf)]
                lines.append(f"|<span id=\"{pname}\">{pname}</span>|{desc_txt}|{', '.join(domains)}|{', '.join(ranges)}|{', '.join(subprops)}|")
    else:
        if classes:
            lines.append("## Classes")
            lines.append("")
            for c in classes:
                cname = local_name(c)
                labels = get_labels(g, c)
                comments = get_comments(g, c)
                subclasses = [local_name(o) for o in g.objects(c, RDFS.subClassOf)]
                lines.append(f"### {cname}")
                lines.append("")
                if labels:
                    lines.append("**Labels:**")
                    lines.append(format_multilang(labels))
                if comments:
                    lines.append("**Comments:**")
                    lines.append(format_multilang(comments))
                if subclasses:
                    lines.append("**SubClassOf:** " + ", ".join(subclasses))
                lines.append("")

    # In rich mode we already render tables for properties; avoid duplicating the basic sections.
    if not rich:
        if obj_props:
            lines.append("## Object Properties")
            lines.append("")
            for p in obj_props:
                pname = local_name(p)
                labels = get_labels(g, p)
                comments = get_comments(g, p)
                domains = [local_name(o) for o in g.objects(p, RDFS.domain)]
                ranges = [local_name(o) for o in g.objects(p, RDFS.range)]
                lines.append(f"### {pname}")
                lines.append("")
                if labels:
                    lines.append("**Labels:**")
                    lines.append(format_multilang(labels))
                if comments:
                    lines.append("**Comments:**")
                    lines.append(format_multilang(comments))
                if domains:
                    lines.append("**Domain:** " + ", ".join(domains))
                if ranges:
                    lines.append("**Range:** " + ", ".join(ranges))
                lines.append("")

        if data_props:
            lines.append("## Data Properties")
            lines.append("")
            for p in data_props:
                pname = local_name(p)
                labels = get_labels(g, p)
                comments = get_comments(g, p)
                domains = [local_name(o) for o in g.objects(p, RDFS.domain)]
                ranges = [local_name(o) for o in g.objects(p, RDFS.range)]
                lines.append(f"### {pname}")
                lines.append("")
                if labels:
                    lines.append("**Labels:**")
                    lines.append(format_multilang(labels))
                if comments:
                    lines.append("**Comments:**")
                    lines.append(format_multilang(comments))
                if domains:
                    lines.append("**Domain:** " + ", ".join(domains))
                if ranges:
                    lines.append("**Range:** " + ", ".join(ranges))
                lines.append("")

    return '\n'.join(lines) + '\n'

def extract_node_shapes(g: rdflib.Graph) -> List[rdflib.term.Identifier]:
    return sorted(set(g.subjects(RDF.type, SH.NodeShape)), key=lambda u: str(u))

def extract_property_shapes(g: rdflib.Graph, node_shape: rdflib.term.Identifier) -> List[rdflib.term.Identifier]:
    return [ps for ps in g.objects(node_shape, SH.property)]

def node_shape_targets(g: rdflib.Graph, node_shape: rdflib.term.Identifier) -> List[str]:
    targets = []
    for t in g.objects(node_shape, SH.targetClass):
        targets.append(local_name(t))
    # Other possible targets (targetNode, targetSubjectsOf, etc.) could be added here
    return targets

def format_constraint(g: rdflib.Graph, ps: rdflib.term.Identifier) -> Dict[str, str]:
    data: Dict[str, str] = {}
    path = next(g.objects(ps, SH.path), None)
    if path is not None:
        data['path'] = local_name(path)
    dtype = next(g.objects(ps, SH.datatype), None)
    if dtype is not None:
        data['datatype'] = local_name(dtype)
    klass = next(g.objects(ps, SH['class']), None)
    if klass is not None:
        data['class'] = local_name(klass)
    minc = next(g.objects(ps, SH.minCount), None)
    if minc is not None:
        data['min'] = str(minc)
    maxc = next(g.objects(ps, SH.maxCount), None)
    if maxc is not None:
        data['max'] = str(maxc)
    in_list = next(g.objects(ps, SH['in']), None)
    if in_list is not None and isinstance(in_list, rdflib.term.BNode):
        # Recoger elementos RDF list
        items = []
        collection = rdflib.collection.Collection(g, in_list)
        for itm in collection:
            items.append(local_name(itm))
        if items:
            data['in'] = ', '.join(items)
    comments = get_comments(g, ps)
    desc = comments.get('es') or comments.get('en') or comments.get('und') or []
    if desc:
        data['description'] = desc[0]
    return data

def generate_shapes_md(g: rdflib.Graph, ontology_name: str) -> str:
    node_shapes = extract_node_shapes(g)
    if not node_shapes:
        return "# Shapes\n\n_No NodeShape found in the shapes file._\n"
    lines: List[str] = []
    lines.append(f"# Shapes for {ontology_name}")
    lines.append("")
    lines.append("| Shape | Target Class(es) | Property | Datatype | Class | Min | Max | In | Description |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for ns in node_shapes:
        shape_name = local_name(ns)
        targets = node_shape_targets(g, ns)
        prop_shapes = extract_property_shapes(g, ns)
        if not prop_shapes:
            # Empty row (no property shapes)
            lines.append(f"| {shape_name} | {', '.join(targets)} |  |  |  |  |  |  |  |")
            continue
        for ps in prop_shapes:
            data = format_constraint(g, ps)
            lines.append(
                f"| {shape_name} | {', '.join(targets)} | {data.get('path','')} | {data.get('datatype','')} | {data.get('class','')} | {data.get('min','')} | {data.get('max','')} | {data.get('in','')} | {data.get('description','')} |"
            )
    return '\n'.join(lines) + '\n'

def generate_diagram(g: rdflib.Graph, ontology_file: Path, out_dir: Path, fmt: str = 'png', max_classes: int = 150) -> Optional[Path]:
    """Generate a simple diagram of classes and object properties.

    Rules:
       - One node per OWL class
       - One edge (domain -> range) for each ObjectProperty with defined domain and range
       - If there are more than max_classes classes, abort to avoid unreadable diagrams
    """
    if Digraph is None:
        return None
    classes = extract_entities(g, OWL.Class)
    if len(classes) > max_classes:
        return None
    obj_props = extract_entities(g, OWL.ObjectProperty)
    dot = Digraph(comment=f"Diagrama {ontology_file.stem}")
    dot.attr(rankdir='LR', fontsize='10')
    class_set = set(classes)
    # Add nodes with label (main label or localName)
    for c in classes:
        labels = get_labels(g, c)
        label_txt = labels.get('es') or labels.get('en') or []
        if label_txt:
            title = label_txt[0]
        else:
            title = local_name(c)
        dot.node(local_name(c), title, shape='box')

    for p in obj_props:
        domains = list(g.objects(p, RDFS.domain))
        ranges = list(g.objects(p, RDFS.range))
        if not domains or not ranges:
            continue
        pname = local_name(p)
        for d in domains:
            for r in ranges:
                if d in class_set and r in class_set:
                    dot.edge(local_name(d), local_name(r), label=pname)

    out_path = out_dir / f"diagram.{fmt}"
    try:
        dot.format = fmt
        dot.render(out_path.with_suffix(''), cleanup=True)
        return out_path
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate Markdown wiki from Turtle ontologies.")
    parser.add_argument('--ontology-dir', default='ontology', help='Directory with .ttl files')
    parser.add_argument('--output-dir', default='docs/wiki', help='Output directory for Markdown (typically configured via config.yml wiki.output_dir)')
    parser.add_argument('--include-codelists', action='store_true', help='Include ontologies inside codelists')
    parser.add_argument('--generate-diagrams', action='store_true', help='Generate Graphviz diagrams of classes and object properties')
    parser.add_argument('--diagram-format', default='png', choices=['png','svg'], help='Diagram output format (png|svg)')
    parser.add_argument('--format', choices=['basic','rich'], default='rich', help='README output format per ontology')
    parser.add_argument('--mermaid', action='store_true', default=True, help='Include Mermaid diagram in rich mode')
    parser.add_argument('--diagram-max-classes', type=int, default=150, help='Maximum number of classes to attempt diagram generation')
    parser.add_argument('--include-shapes', action='store_true', help='Process SHACL shapes and generate documentation')
    parser.add_argument('--shapes-dir', default='shapes', help='Directory with shapes .ttl files')
    parser.add_argument('--contexts-dir', default=None, help='Directory with JSON-LD contexts (for #Contexts counter)')
    parser.add_argument('--pages-url', default='', help='Base GitHub Pages URL (used to build navigation links in wiki index)')
    parser.add_argument('--build-version', default='', help='Build version (used to build navigation links in wiki index)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    setup_logging(args.verbose)
    LOGGER.info("Starting wiki generation")

    ontology_dir = Path(args.ontology_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ttl_files: List[Path] = []
    for root, _, files in os.walk(ontology_dir):
        for f in files:
            if f.endswith('.ttl'):
                fp = Path(root) / f
                # argparse convierte '--include-codelists' a atributo 'include_codelists'
                if not args.include_codelists and 'codelists' in fp.parts:
                    continue
                ttl_files.append(fp)

    ttl_files = sorted(ttl_files)

    shapes_graphs: Dict[str, rdflib.Graph] = {}
    if args.include_shapes:
        shapes_dir = Path(args.shapes_dir)
        if shapes_dir.exists():
            for f in shapes_dir.glob('*.ttl'):
                try:
                    sg = rdflib.Graph()
                    sg.parse(str(f), format='turtle')
                    key = _normalize_artifact_key(f.stem)
                    shapes_graphs[key] = sg
                    LOGGER.debug(f"Shapes loaded: {f.name} -> key {key}")
                except Exception as e:
                    LOGGER.warning(f"Could not parse shapes {f}: {e}")
        else:
            LOGGER.warning(f"Shapes directory does not exist: {shapes_dir}")

    contexts_by_ontology: Dict[str, int] = {}
    include_contexts = bool(args.contexts_dir)
    if include_contexts:
        contexts_dir = Path(args.contexts_dir)
        if contexts_dir.exists():
            for f in contexts_dir.glob('*.context.jsonld'):
                key = _normalize_artifact_key(f.stem)
                contexts_by_ontology[key] = contexts_by_ontology.get(key, 0) + 1
                LOGGER.debug(f"Context detected: {f.name} -> key {key}")
        else:
            LOGGER.warning(f"Contexts directory does not exist: {contexts_dir}")

    # Dynamic header construction
    header_cols = ["Ontology", "#Classes", "#ObjProps", "#DataProps"]
    sep_cols = ["-----------", "---------", "-----------", "-----------"]
    if args.include_shapes:
        header_cols.append("#Shapes")
        sep_cols.append("---------")
    if include_contexts:
        header_cols.append("#Contexts")
        sep_cols.append("-----------")

    # Navigation for users browsing the published wiki on GitHub Pages.
    pages_url = (args.pages_url or '').rstrip('/')
    build_version = (args.build_version or '').strip()

    build_root_href = "../../"
    build_version_href = "../"
    if pages_url and build_version:
        build_root_href = f"{pages_url}/build/"
        build_version_href = f"{pages_url}/build/{build_version}/"
    elif pages_url:
        build_root_href = f"{pages_url}/build/"

    index_lines = [
        "# Ontology Index",
        "",
        "## Navigation",
        f"- [Build artifacts (this version)]({build_version_href})",
        f"- [All build versions]({build_root_href})",
        "",
        "| " + " | ".join(header_cols) + " |",
        "| " + " | ".join(sep_cols) + " |",
    ]

    # Collect per-ontology navigation links (built during generation)
    ontology_nav: List[str] = []

    for ttl in ttl_files:
        g = rdflib.Graph()
        g.parse(str(ttl), format='turtle')
        classes = extract_entities(g, OWL.Class)
        obj_props = extract_entities(g, OWL.ObjectProperty)
        data_props = extract_entities(g, OWL.DatatypeProperty)

        name = ttl.stem
        shapes_count: Optional[int] = None
        shape_graph = None
        if args.include_shapes and name in shapes_graphs:
            shape_graph = shapes_graphs[name]
            shapes_count = len(extract_node_shapes(shape_graph))
        
        # When include_shapes is True, always pass a shapes count (0 if missing/failed)
        if args.include_shapes:
            shapes_count = shapes_count if shapes_count is not None else 0

        contexts_count: Optional[int] = None
        if include_contexts:
            contexts_count = contexts_by_ontology.get(name, 0)
        
        index_lines.append(
            build_index_row(
                name,
                len(classes),
                len(obj_props),
                len(data_props),
                shapes_count,
                contexts_count,
            )
        )

        ont_out_dir = out_dir / name
        ont_out_dir.mkdir(parents=True, exist_ok=True)
        source_href: Optional[str] = None
        if pages_url:
            rel_path = str(ttl).replace("\\", "/").lstrip("./").lstrip("/")
            source_href = f"{pages_url}/{quote(rel_path, safe='/')}"

        readme_content = generate_readme(
            g,
            ttl,
            rich=(args.format=='rich'),
            mermaid=args.mermaid,
            source_href=source_href,
        )
        # Optional diagram
        if args.generate_diagrams:
            diagram_path = generate_diagram(
                g,
                ttl,
                ont_out_dir,
                fmt=args.diagram_format,
                max_classes=args.diagram_max_classes
            )
            if diagram_path and args.format != 'rich':
                # Insert diagram reference at the top of the README only in basic mode
                readme_content = readme_content.replace('# Ontology:', f"# Ontology:\n\n![Diagram]({diagram_path.name})\n\nOntology:")
        readme_path = ont_out_dir / 'README.md'
        readme_path.write_text(readme_content, encoding='utf-8')

        # Create per-ontology index.md so folder URLs work on GitHub Pages.
        # The wiki index will link to "<ontology>/".
        (ont_out_dir / 'index.md').write_text(readme_content, encoding='utf-8')

        # Shapes opcionales
        if shape_graph is not None:
            shapes_md = generate_shapes_md(shape_graph, name)
            (ont_out_dir / 'SHAPES.md').write_text(shapes_md, encoding='utf-8')
            LOGGER.debug(f"Shapes documented for {name}")

        # Navigation entry (prefer folder link)
        folder_href = f"{name}/"
        if pages_url and build_version:
            folder_href = f"{pages_url}/build/{build_version}/wiki/{name}/"
        ontology_nav.append(f"- [{name}]({folder_href})")

    if ontology_nav:
        index_lines.extend(
            [
                "",
                "## Ontologies",
                "",
                *ontology_nav,
            ]
        )

    (out_dir / 'index.md').write_text('\n'.join(index_lines) + '\n', encoding='utf-8')
    LOGGER.info(f"Generated wiki for {len(ttl_files)} ontologies in {out_dir}")

if __name__ == '__main__':
    main()
