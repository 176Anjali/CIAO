import json
import subprocess
from pathlib import Path


class UMLGenerator:

    def __init__(
        self,
        graph_path,
        output_dir,
        plantuml_jar,
    ):
        self.graph_path = Path(graph_path)
        self.output_dir = Path(output_dir)
        self.plantuml_jar = Path(plantuml_jar)

        self.graph = {}
        self.nodes = []
        self.edges = []

        self.files = []
        self.classes = []
        self.methods = []

    # =========================================================
    # LOAD GRAPH
    # =========================================================

    def load_graph(self):

        if not self.graph_path.exists():
            raise FileNotFoundError(
                f"Knowledge graph not found: {self.graph_path}"
            )

        with open(
            self.graph_path,
            "r",
            encoding="utf-8"
        ) as f:
            self.graph = json.load(f)

        self._normalize_graph()

    # =========================================================
    # NORMALIZE GRAPH
    # =========================================================

    def _normalize_graph(self):

        raw_nodes = self.graph.get("nodes", [])

        self.nodes = []

        if isinstance(raw_nodes, list):

            for node in raw_nodes:

                if isinstance(node, str):
                    self.nodes.append({"id": node})
                    continue

                if not isinstance(node, dict):
                    continue

                node_id = (
                    node.get("id")
                    or node.get("node")
                    or node.get("name")
                )

                if node_id:

                    normalized = dict(node)
                    normalized["id"] = str(node_id)

                    self.nodes.append(normalized)

        elif isinstance(raw_nodes, dict):

            for node_id, attributes in raw_nodes.items():

                node = {
                    "id": str(node_id)
                }

                if isinstance(attributes, dict):
                    node.update(attributes)

                node["id"] = str(node_id)

                self.nodes.append(node)

        # -----------------------------------------------------

        raw_edges = self.graph.get("edges", [])

        self.edges = []

        if isinstance(raw_edges, list):

            for edge in raw_edges:

                if not isinstance(edge, dict):
                    continue

                source = (
                    edge.get("source")
                    or edge.get("from")
                    or edge.get("u")
                )

                target = (
                    edge.get("target")
                    or edge.get("to")
                    or edge.get("v")
                )

                relation = (
                    edge.get("relation")
                    or edge.get("relationship")
                    or edge.get("type")
                )

                if source and target and relation:

                    self.edges.append(
                        {
                            "source": str(source),
                            "target": str(target),
                            "relation": str(relation),
                        }
                    )

        self._classify_nodes()

    # =========================================================
    # NODE HELPERS
    # =========================================================

    @staticmethod
    def node_type(node_id):

        node_id = str(node_id)

        if ":" not in node_id:
            return ""

        return node_id.split(":", 1)[0]

    @staticmethod
    def node_value(node_id):

        node_id = str(node_id)

        if ":" not in node_id:
            return node_id

        return node_id.split(":", 1)[1]

    @staticmethod
    def windows_filename(path_text):

        path_text = str(path_text)
        path_text = path_text.replace("/", "\\")

        return path_text.rsplit("\\", 1)[-1]

    # =========================================================
    # CLASSIFY NODES
    # =========================================================

    def _classify_nodes(self):

        self.files = []
        self.classes = []
        self.methods = []

        for node in self.nodes:

            node_id = str(node["id"])

            node_type = (
                node.get("type")
                or self.node_type(node_id)
            )

            if node_type == "file":
                self.files.append(node_id)

            elif node_type == "class":
                self.classes.append(node_id)

            elif node_type == "method":
                self.methods.append(node_id)

    # =========================================================
    # METHOD LOOKUP
    # =========================================================

    def methods_for_class(self, class_node):

        class_name = self.node_value(class_node)

        prefix = class_name + "."

        result = []

        for method_node in self.methods:

            method_symbol = self.node_value(method_node)

            if method_symbol.startswith(prefix):

                method_name = method_symbol[len(prefix):]

                result.append(method_name)

        return result

    # =========================================================
    # GENERATE PLANTUML
    # =========================================================

    def generate_puml(self):

        lines = []

        lines.append("@startuml")
        lines.append("title CIAO Generated Software Architecture")
        lines.append("allowmixing")
        lines.append("skinparam shadowing false")
        lines.append("skinparam componentStyle rectangle")
        lines.append("")

        file_aliases = {}
        class_aliases = {}

        # =====================================================
        # FILE COMPONENTS
        # =====================================================

        for index, file_node in enumerate(
            self.files,
            start=1
        ):

            alias = f"F{index}"

            label = self.windows_filename(
                self.node_value(file_node)
            )

            file_aliases[file_node] = alias

            lines.append(
                f'component "{label}" as {alias}'
            )

        lines.append("")

        # =====================================================
        # CLASSES
        # =====================================================

        for index, class_node in enumerate(
            self.classes,
            start=1
        ):

            alias = f"C{index}"

            label = self.node_value(class_node)

            class_aliases[class_node] = alias

            methods = self.methods_for_class(
                class_node
            )

            if methods:

                lines.append(
                    f'class "{label}" as {alias} {{'
                )

                for method_name in methods:

                    lines.append(
                        f"    +{method_name}()"
                    )

                lines.append("}")

            else:

                lines.append(
                    f'class "{label}" as {alias}'
                )

        lines.append("")

        # =====================================================
        # ARCHITECTURE RELATIONSHIPS
        # =====================================================

        generated_relationships = set()

        for edge in self.edges:

            source = edge["source"]
            target = edge["target"]
            relation = edge["relation"]

            # -------------------------------------------------
            # FILE IMPORTS FILE
            # -------------------------------------------------

            if (
                relation == "IMPORTS_FILE"
                and source in file_aliases
                and target in file_aliases
            ):

                relationship = (
                    file_aliases[source],
                    file_aliases[target],
                    "imports"
                )

                if relationship not in generated_relationships:

                    lines.append(
                        f"{file_aliases[source]} "
                        f"..> "
                        f"{file_aliases[target]} "
                        f": imports"
                    )

                    generated_relationships.add(
                        relationship
                    )

            # -------------------------------------------------
            # FILE DEFINES CLASS
            # -------------------------------------------------

            elif (
                relation == "DEFINES"
                and source in file_aliases
                and target in class_aliases
            ):

                relationship = (
                    file_aliases[source],
                    class_aliases[target],
                    "defines"
                )

                if relationship not in generated_relationships:

                    lines.append(
                        f"{file_aliases[source]} "
                        f"..> "
                        f"{class_aliases[target]} "
                        f": defines"
                    )

                    generated_relationships.add(
                        relationship
                    )

            # -------------------------------------------------
            # FILE CALLS METHOD
            # -------------------------------------------------

            elif (
                relation == "CALLS"
                and source in file_aliases
                and target.startswith("method:")
            ):

                method_symbol = self.node_value(target)

                if "." not in method_symbol:
                    continue

                class_name, method_name = (
                    method_symbol.rsplit(".", 1)
                )

                class_node = (
                    "class:" + class_name
                )

                if class_node not in class_aliases:
                    continue

                relationship = (
                    file_aliases[source],
                    class_aliases[class_node],
                    f"calls:{method_name}"
                )

                if relationship not in generated_relationships:

                    lines.append(
                        f"{file_aliases[source]} "
                        f"--> "
                        f"{class_aliases[class_node]} "
                        f": calls {method_name}()"
                    )

                    generated_relationships.add(
                        relationship
                    )

            # -------------------------------------------------
            # VARIABLE INSTANCE OF CLASS
            # -------------------------------------------------

            elif (
                relation == "INSTANCE_OF"
                and source.startswith("variable:")
                and target in class_aliases
            ):

                variable_value = self.node_value(source)

                if ":" not in variable_value:
                    continue

                source_file = variable_value.rsplit(
                    ":",
                    1
                )[0]

                file_node = (
                    "file:" + source_file
                )

                if file_node not in file_aliases:
                    continue

                relationship = (
                    file_aliases[file_node],
                    class_aliases[target],
                    "creates"
                )

                if relationship not in generated_relationships:

                    lines.append(
                        f"{file_aliases[file_node]} "
                        f"--> "
                        f"{class_aliases[target]} "
                        f": creates instance"
                    )

                    generated_relationships.add(
                        relationship
                    )

        lines.append("")
        lines.append("@enduml")

        return "\n".join(lines)

    # =========================================================
    # SAVE PUML
    # =========================================================

    def save_puml(self, content):

        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        output_path = (
            self.output_dir / "architecture.puml"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
            newline="\n"
        ) as f:

            f.write(content)

        return output_path

    # =========================================================
    # RENDER PNG
    # =========================================================

    def render_png(self, puml_path):

        if not self.plantuml_jar.exists():

            raise FileNotFoundError(
                f"PlantUML JAR not found: "
                f"{self.plantuml_jar}"
            )

        command = [
            "java",
            "-jar",
            str(self.plantuml_jar),
            "-tpng",
            str(puml_path),
        ]

        print("\nRunning PlantUML:")
        print(" ".join(command))

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print(result.stderr)

        if result.returncode != 0:

            raise RuntimeError(
                "PlantUML failed with "
                f"exit code {result.returncode}"
            )

        png_path = puml_path.with_suffix(".png")

        if not png_path.exists():

            raise RuntimeError(
                "PlantUML finished but "
                "architecture.png was not generated."
            )

        return png_path

    # =========================================================
    # MAIN GENERATION
    # =========================================================

    def generate(self):

        print("\n" + "=" * 70)
        print("CIAO UML GENERATION")
        print("=" * 70)

        self.load_graph()

        print("\n[PASS] Knowledge graph loaded.")
        print(f"[INFO] Files: {len(self.files)}")
        print(f"[INFO] Classes: {len(self.classes)}")
        print(f"[INFO] Methods: {len(self.methods)}")

        print("\n[INFO] File nodes:")

        for node in self.files:
            print(f"       {repr(node)}")

        print("\n[INFO] Class nodes:")

        for node in self.classes:
            print(f"       {repr(node)}")

        content = self.generate_puml()

        puml_path = self.save_puml(content)

        print("\n[PASS] PlantUML source generated.")
        print(f"[PASS] {puml_path}")

        print("\n" + "-" * 70)
        print("GENERATED PLANTUML")
        print("-" * 70)
        print(content)
        print("-" * 70)

        png_path = self.render_png(
            puml_path
        )

        print("\n[PASS] UML image generated.")
        print(f"[PASS] {png_path}")

        print("\n" + "=" * 70)
        print("UML GENERATION STATUS")
        print("=" * 70)
        print("SUCCESS: Architecture UML generated.")

        return {
            "puml": str(puml_path),
            "png": str(png_path),
        }