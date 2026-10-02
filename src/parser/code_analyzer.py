import ast
import os
import json


class CodeAnalyzer:
    def __init__(self, repository_path):
        self.repository_path = repository_path
        self.symbol_index = {}
        self.ignored_calls = {
            "print",
            "open",
            "len",
            "range",
            "str",
            "list",
            "dict",
            "set",
            "sum",
            "cast",
            "isinstance",
            "getattr",
            "setattr",
            "staticmethod",
            "classmethod",
            "super",
            "append",
            "extend",
            "items",
            "keys",
            "get",
            "join",
            "strip",
            "startswith",
            "endswith",
            "encode",
            "decode",
            "sleep"
        }

    def analyze_file(self, file_path):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
            source_code = file.read()

        try:
            tree = ast.parse(source_code)
        except SyntaxError:
            return None

        result = {
            "file": file_path,
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": [],
            "calls": [],
            "inheritance": []
        }

        for node in ast.walk(tree):

            # Classes
            if isinstance(node, ast.ClassDef):

                class_info = {
                    "name": node.name,
                    "bases": [
                        self._get_name(base)
                        for base in node.bases
                    ]
                }

                result["classes"].append(class_info)

                # Inheritance relationships
                for base in node.bases:
                    result["inheritance"].append({
                        "child": node.name,
                        "parent": self._get_name(base)
                    })

                # Class methods
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        result["methods"].append({
                            "class": node.name,
                            "name": child.name
                        })

            # Top-level functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):

                # Check whether this function belongs to a class
                inside_class = False

                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        if node in parent.body:
                            inside_class = True
                            break

                if not inside_class:
                    result["functions"].append(node.name)

            # Imports
            elif isinstance(node, ast.Import):

                for alias in node.names:
                    result["imports"].append(alias.name)

            elif isinstance(node, ast.ImportFrom):

                if node.module:
                    result["imports"].append(node.module)

            # Function / method calls
            elif isinstance(node, ast.Call):

                function_name = self._get_name(node.func)

                if (
                    function_name
                    and function_name not in self.ignored_calls
                ):
                    result["calls"].append(function_name)

        result["calls"] = sorted(set(result["calls"]))

        return result

    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id

        if isinstance(node, ast.Attribute):
            return node.attr

        return "Unknown"

    def analyze_repository(self):
        results = []

        for root, _, files in os.walk(self.repository_path):

            # Ignore unnecessary folders
            if any(
                ignored in root
                for ignored in [
                    ".git",
                    ".history",
                    "__pycache__",
                    "venv",
                    ".venv",
                    "node_modules"
                ]
            ):
                continue

            for file in files:

                if file.endswith(".py"):

                    file_path = os.path.join(root, file)

                    analysis = self.analyze_file(file_path)

                    if analysis:
                        results.append(analysis)

                        # Build symbol index
                        for class_info in analysis["classes"]:
                            class_name = class_info["name"]
                            self.symbol_index[class_name] = file_path

                        for function_name in analysis["functions"]:
                            self.symbol_index[function_name] = file_path

                        for method in analysis["methods"]:
                            method_name = f"{method['class']}.{method['name']}"
                            self.symbol_index[method_name] = file_path

        return results

    def save_results(self, output_path):

        results = self.analyze_repository()

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(
                results,
                file,
                indent=4
            )

        return results