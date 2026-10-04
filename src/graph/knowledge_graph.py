import json
import os
import networkx as nx

from code_analyzer import CodeAnalyzer


class RepositoryKnowledgeGraph:

    def __init__(self, repository_path):

        self.repository_path = repository_path
        self.graph = nx.DiGraph()
        self.analysis_results = []

    # ==========================================================
    # ANALYZE
    # ==========================================================

    def analyze_repository(self):

        analyzer = CodeAnalyzer(
            self.repository_path
        )

        self.analysis_results = (
            analyzer.analyze_repository()
        )

        return self.analysis_results

    # ==========================================================
    # NODE
    # ==========================================================

    def add_node(
        self,
        node_id,
        node_type,
        **attributes
    ):

        self.graph.add_node(
            node_id,
            type=node_type,
            **attributes
        )

    # ==========================================================
    # BUILD GRAPH
    # ==========================================================

    def build_graph(self):

        if not self.analysis_results:

            self.analyze_repository()

        # ------------------------------------------------------
        # PASS 1: Create all structural nodes
        # ------------------------------------------------------

        for analysis in self.analysis_results:

            file_path = analysis["file"]

            file_node = f"file:{file_path}"

            self.add_node(
                file_node,
                "file",
                name=os.path.basename(file_path),
                path=file_path
            )

            # --------------------------------------------------
            # Classes
            # --------------------------------------------------

            for class_info in analysis["classes"]:

                class_name = class_info["name"]

                class_node = (
                    f"class:{class_name}"
                )

                self.add_node(
                    class_node,
                    "class",
                    name=class_name,
                    file=file_path
                )

                self.graph.add_edge(
                    file_node,
                    class_node,
                    relationship="DEFINES"
                )

            # --------------------------------------------------
            # Functions
            # --------------------------------------------------

            for function_name in analysis["functions"]:

                function_node = (
                    f"function:{function_name}"
                )

                self.add_node(
                    function_node,
                    "function",
                    name=function_name,
                    file=file_path
                )

                self.graph.add_edge(
                    file_node,
                    function_node,
                    relationship="DEFINES"
                )

            # --------------------------------------------------
            # Methods
            # --------------------------------------------------

            for method in analysis["methods"]:

                class_name = method["class"]
                method_name = method["name"]

                class_node = (
                    f"class:{class_name}"
                )

                method_node = (
                    f"method:{class_name}.{method_name}"
                )

                self.add_node(
                    method_node,
                    "method",
                    name=method_name,
                    class_name=class_name,
                    file=file_path
                )

                self.graph.add_edge(
                    class_node,
                    method_node,
                    relationship="DEFINES"
                )

        # ------------------------------------------------------
        # PASS 2: Relationships and secondary nodes
        # ------------------------------------------------------

        for analysis in self.analysis_results:

            file_path = analysis["file"]

            file_node = f"file:{file_path}"

            # --------------------------------------------------
            # Object instances
            # --------------------------------------------------

            for variable in analysis[
                "resolved_variables"
            ]:

                variable_name = variable["variable"]
                class_name = variable["class"]

                variable_node = (
                    f"variable:"
                    f"{file_path}:"
                    f"{variable_name}"
                )

                class_node = (
                    f"class:{class_name}"
                )

                self.add_node(
                    variable_node,
                    "variable",
                    name=variable_name,
                    file=file_path,
                    class_name=class_name
                )

                if class_node in self.graph:

                    self.graph.add_edge(
                        variable_node,
                        class_node,
                        relationship="INSTANCE_OF"
                    )

            # --------------------------------------------------
            # Inheritance
            # --------------------------------------------------

            for inheritance in analysis[
                "inheritance"
            ]:

                child = inheritance["child"]
                parent = inheritance["parent"]

                child_node = f"class:{child}"
                parent_node = f"class:{parent}"

                if parent_node not in self.graph:

                    self.add_node(
                        parent_node,
                        "external_class",
                        name=parent
                    )

                self.graph.add_edge(
                    child_node,
                    parent_node,
                    relationship="INHERITS"
                )

            # --------------------------------------------------
            # Imports
            # --------------------------------------------------

            for imported_module in analysis["imports"]:

                module_node = (
                    f"module:{imported_module}"
                )

                if module_node not in self.graph:

                    self.add_node(
                        module_node,
                        "module",
                        name=imported_module
                    )

                self.graph.add_edge(
                    file_node,
                    module_node,
                    relationship="IMPORTS"
                )

            # --------------------------------------------------
            # RESOLVED CALLS
            # --------------------------------------------------

            for call in analysis["resolved_calls"]:

                original_call = call[
                    "called_symbol"
                ]

                resolved_symbol = call.get(
                    "resolved_symbol"
                )

                # ----------------------------------------------
                # Direct class/function call
                # ----------------------------------------------

                if not resolved_symbol:

                    if original_call in [
                        node.split(":", 1)[1]
                        for node, data
                        in self.graph.nodes(
                            data=True
                        )
                        if data.get("type")
                        in [
                            "class",
                            "function"
                        ]
                    ]:

                        class_node = (
                            f"class:{original_call}"
                        )

                        function_node = (
                            f"function:{original_call}"
                        )

                        if class_node in self.graph:

                            self.graph.add_edge(
                                file_node,
                                class_node,
                                relationship="CALLS"
                            )

                        elif function_node in self.graph:

                            self.graph.add_edge(
                                file_node,
                                function_node,
                                relationship="CALLS"
                            )

                    continue

                # ----------------------------------------------
                # Object method call
                #
                # Example:
                #
                # service.process
                #
                # resolved:
                #
                # Service.process
                # ----------------------------------------------

                if "." in original_call:

                    receiver, method = (
                        original_call.split(
                            ".",
                            1
                        )
                    )

                    method_node = (
                        f"method:{resolved_symbol}"
                    )

                    variable_node = None

                    # Find receiver variable

                    for variable in analysis[
                        "resolved_variables"
                    ]:

                        if (
                            variable["variable"]
                            == receiver
                        ):

                            variable_node = (
                                f"variable:"
                                f"{file_path}:"
                                f"{receiver}"
                            )

                            break

                    # ------------------------------------------
                    # Variable -> method
                    # ------------------------------------------

                    if (
                        variable_node
                        and method_node in self.graph
                    ):

                        self.graph.add_edge(
                            variable_node,
                            method_node,
                            relationship="CALLS"
                        )

                    # ------------------------------------------
                    # File -> method
                    #
                    # Useful because the current analyzer
                    # does not yet track the enclosing function.
                    # ------------------------------------------

                    if method_node in self.graph:

                        self.graph.add_edge(
                            file_node,
                            method_node,
                            relationship="CALLS"
                        )

        return self.graph

    # ==========================================================
    # STATISTICS
    # ==========================================================

    def statistics(self):

        node_types = {}
        relationship_types = {}

        for _, data in self.graph.nodes(
            data=True
        ):

            node_type = data.get(
                "type",
                "unknown"
            )

            node_types[node_type] = (
                node_types.get(
                    node_type,
                    0
                ) + 1
            )

        for _, _, data in self.graph.edges(
            data=True
        ):

            relationship = data.get(
                "relationship",
                "unknown"
            )

            relationship_types[
                relationship
            ] = (
                relationship_types.get(
                    relationship,
                    0
                ) + 1
            )

        return {
            "nodes":
                self.graph.number_of_nodes(),

            "edges":
                self.graph.number_of_edges(),

            "node_types":
                node_types,

            "relationship_types":
                relationship_types
        }

    # ==========================================================
    # PRINT
    # ==========================================================

    def print_graph(self):

        print("\n" + "=" * 70)
        print("REPOSITORY KNOWLEDGE GRAPH")
        print("=" * 70)

        print(
            f"\nNodes: "
            f"{self.graph.number_of_nodes()}"
        )

        print(
            f"Edges: "
            f"{self.graph.number_of_edges()}"
        )

        print("\nNODES:")

        for node, data in self.graph.nodes(
            data=True
        ):

            print(
                f"  {node}"
                f" [{data.get('type')}]"
            )

        print("\nRELATIONSHIPS:")

        for source, target, data in (
            self.graph.edges(data=True)
        ):

            print(
                f"  {source}"
                f" --{data.get('relationship')}"
                f"--> "
                f"{target}"
            )

    # ==========================================================
    # SAVE JSON
    # ==========================================================

    def save_json(
        self,
        output_path
    ):

        output_directory = os.path.dirname(
            output_path
        )

        if output_directory:

            os.makedirs(
                output_directory,
                exist_ok=True
            )

        graph_data = {

            "nodes": [
                {
                    "id": node,
                    **data
                }
                for node, data
                in self.graph.nodes(
                    data=True
                )
            ],

            "edges": [
                {
                    "source": source,
                    "target": target,
                    **data
                }
                for source, target, data
                in self.graph.edges(
                    data=True
                )
            ]
        }

        with open(
            output_path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                graph_data,
                file,
                indent=4
            )

        return output_path