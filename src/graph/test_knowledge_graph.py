import os
import sys


# ==========================================================
# PATH SETUP
# ==========================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

GRAPH_DIRECTORY = os.path.dirname(
    os.path.abspath(__file__)
)

PARSER_DIRECTORY = os.path.abspath(
    os.path.join(
        GRAPH_DIRECTORY,
        "..",
        "parser"
    )
)


sys.path.insert(
    0,
    PROJECT_ROOT
)

sys.path.insert(
    0,
    GRAPH_DIRECTORY
)

sys.path.insert(
    0,
    PARSER_DIRECTORY
)


# ==========================================================
# IMPORT
# ==========================================================

from knowledge_graph import (
    RepositoryKnowledgeGraph
)


# ==========================================================
# TEST REPOSITORY
# ==========================================================

repository_path = os.path.join(
    PROJECT_ROOT,
    "data",
    "test_repo"
)


# ==========================================================
# CREATE GRAPH
# ==========================================================

knowledge_graph = (
    RepositoryKnowledgeGraph(
        repository_path
    )
)


# ==========================================================
# BUILD GRAPH
# ==========================================================

knowledge_graph.analyze_repository()

graph = knowledge_graph.build_graph()


# ==========================================================
# PRINT GRAPH
# ==========================================================

knowledge_graph.print_graph()


# ==========================================================
# STATISTICS
# ==========================================================

print("\n" + "=" * 70)
print("GRAPH STATISTICS")
print("=" * 70)

statistics = knowledge_graph.statistics()

print(
    f"Nodes: {statistics['nodes']}"
)

print(
    f"Edges: {statistics['edges']}"
)

print("\nNode Types:")

for node_type, count in (
    statistics["node_types"].items()
):

    print(
        f"  {node_type}: {count}"
    )

print("\nRelationship Types:")

for relationship, count in (
    statistics["relationship_types"].items()
):

    print(
        f"  {relationship}: {count}"
    )


# ==========================================================
# SAVE
# ==========================================================

output_path = os.path.join(
    PROJECT_ROOT,
    "output",
    "graph",
    "repository_graph.json"
)

knowledge_graph.save_json(
    output_path
)

print(
    f"\nGraph saved to:\n{output_path}"
)


# ==========================================================
# VALIDATION
# ==========================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)


# ----------------------------------------------------------
# Required nodes
# ----------------------------------------------------------

required_nodes = [
    "class:Service",
    "method:Service.process"
]


for node in required_nodes:

    if node in graph:

        print(
            f"[PASS] Node exists: {node}"
        )

    else:

        print(
            f"[FAIL] Node missing: {node}"
        )


# ----------------------------------------------------------
# Find service variable
# ----------------------------------------------------------

service_variable = None

for node, data in graph.nodes(
    data=True
):

    if (
        data.get("type") == "variable"
        and data.get("name") == "service"
    ):

        service_variable = node
        break


if service_variable:

    print(
        "[PASS] Service instance node: "
        f"{service_variable}"
    )

else:

    print(
        "[FAIL] Service instance node missing"
    )


# ----------------------------------------------------------
# INSTANCE_OF
# ----------------------------------------------------------

if service_variable:

    if graph.has_edge(
        service_variable,
        "class:Service"
    ):

        if (
            graph[
                service_variable
            ][
                "class:Service"
            ].get(
                "relationship"
            )
            == "INSTANCE_OF"
        ):

            print(
                "[PASS] "
                "service --INSTANCE_OF--> "
                "Service"
            )

        else:

            print(
                "[FAIL] Wrong INSTANCE_OF relationship"
            )

    else:

        print(
            "[FAIL] Missing INSTANCE_OF relationship"
        )


# ----------------------------------------------------------
# DEFINES
# ----------------------------------------------------------

if graph.has_edge(
    "class:Service",
    "method:Service.process"
):

    if (
        graph[
            "class:Service"
        ][
            "method:Service.process"
        ].get(
            "relationship"
        )
        == "DEFINES"
    ):

        print(
            "[PASS] "
            "Service --DEFINES--> "
            "Service.process"
        )

    else:

        print(
            "[FAIL] Wrong DEFINES relationship"
        )

else:

    print(
        "[FAIL] Missing DEFINES relationship"
    )


# ----------------------------------------------------------
# CALLS
# ----------------------------------------------------------

calls_passed = False

if service_variable:

    if graph.has_edge(
        service_variable,
        "method:Service.process"
    ):

        if (
            graph[
                service_variable
            ][
                "method:Service.process"
            ].get(
                "relationship"
            )
            == "CALLS"
        ):

            calls_passed = True

            print(
                "[PASS] "
                "service --CALLS--> "
                "Service.process"
            )

        else:

            print(
                "[FAIL] Wrong CALLS relationship"
            )

    else:

        print(
            "[FAIL] Missing CALLS relationship"
        )


# ==========================================================
# FINAL STATUS
# ==========================================================

print("\n" + "=" * 70)
print("STEP 6 STATUS")
print("=" * 70)


if (
    "class:Service" in graph
    and
    "method:Service.process" in graph
    and
    service_variable
    and
    graph.has_edge(
        service_variable,
        "class:Service"
    )
    and
    graph.has_edge(
        "class:Service",
        "method:Service.process"
    )
    and
    calls_passed
):

    print(
        "SUCCESS: Step 6 completed."
    )

else:

    print(
        "Step 6 still has unresolved relationships."
    )