"""
Yurtle Standard Namespaces
==========================

Predefined RDF namespaces for common Yurtle patterns.
These can be customized or extended for specific domains.

License: MIT
"""

from rdflib import Namespace

# Core Yurtle namespace
YURTLE = Namespace("https://yurtle.dev/schema/")

# Project management namespace
PM = Namespace("https://yurtle.dev/pm/")

# Being/agent namespace
BEING = Namespace("https://yurtle.dev/being/")

# Voyage/journey namespace
VOYAGE = Namespace("https://yurtle.dev/voyage/")

# Knowledge/learning namespace
KNOWLEDGE = Namespace("https://yurtle.dev/knowledge/")

# Provenance namespace (for tracking source files)
PROVENANCE = Namespace("https://yurtle.dev/provenance/")

# All namespaces as a dict for easy binding
STANDARD_NAMESPACES = {
    'yurtle': YURTLE,
    'pm': PM,
    'being': BEING,
    'voyage': VOYAGE,
    'knowledge': KNOWLEDGE,
    'prov': PROVENANCE,
}


def bind_standard_namespaces(graph):
    """
    Bind all standard Yurtle namespaces to a graph.

    Args:
        graph: RDFlib Graph to bind namespaces to
    """
    from rdflib.namespace import RDF, RDFS, XSD

    for prefix, ns in STANDARD_NAMESPACES.items():
        graph.bind(prefix, ns)

    # Also bind standard RDF namespaces
    graph.bind('rdf', RDF)
    graph.bind('rdfs', RDFS)
    graph.bind('xsd', XSD)
