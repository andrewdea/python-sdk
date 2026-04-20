"""
High-level Python API for C++ code analysis.

This module provides a convenient interface for analyzing C++ projects,
extracting symbols, building call graphs, and querying code structure.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import networkx as nx

import clang_callgraph
import json
from cldk.analysis import AnalysisLevel
from cldk.models.c import (
    CppApplication,
    CppTranslationUnit,
    CppFunction,
    CppVariable,
    CppRecord,
    CppEnum,
    CppTypedef,
    CppMacro,
    CppCallGraphEdge,
    CppNamespace,
    CppRecordKind,
    VariableFilter,
)
from cldk.analysis.c.process_parsed_file_treesitter import tree_sitter_cpp, process_class_from_node
from orchard.helpers.perched import get_nodes_of_type, get_nodes_of_multiple_types
import sys
import os


# the backend uses: symbols | callgraph
_ANALYSIS_MAP = {
    AnalysisLevel.symbol_table: "symbols",
    AnalysisLevel.call_graph: "callgraph",
    AnalysisLevel.program_dependency_graph: "callgraph",  # not supported, default to callgraph
    AnalysisLevel.system_dependency_graph: "callgraph",  # not supported, default to callgraph
}


def path_is_within_certain_directories(
    path: str, project_root: str, names_to_check_for: list[str] = ["test"]
):
    parts = path[len(project_root) :].split(os.sep)
    for name in names_to_check_for:
        if name in parts:
            return True
    return False


def remove_test_files(source_files: list[str], project_root: str) -> list[str]:
    return [
        f
        for f in source_files
        if not path_is_within_certain_directories(f, project_root)
    ]


def remove_files_in_dirs(source_files, project_root: str, dirs: list[str]) -> list[str]:
    return [
        f
        for f in source_files
        if not path_is_within_certain_directories(f, project_root, dirs)
    ]


def find_includes(project_root: str, with_subdirs: bool = True) -> list[str]:
    project_root_path = Path(project_root)
    include_path = project_root_path / "include"
    all_includes: list[str] = []

    # Add the include directory itself first
    if include_path.exists() and include_path.is_dir():
        all_includes.append(str(include_path))

    # Then add all subdirectories
    if with_subdirs:
        for p in include_path.rglob("*"):
            if p.is_dir():
                all_includes.append(str(p))
    return all_includes


# TEMP right now we're using this function here
# eventually we'll want to integrate upstream directly into CallGraphAnalyzer.analyze
def safe_analyze(
    analyzer: clang_callgraph.CallGraphAnalyzer,
    source_files: list[str],
    compilation_db_path: str,
    project_root: str,
    mode: Optional[str] = None,
    file_filters: list[str] = [],
    extra_args: list[str] = [],
):
    print(f"From: `safe_analyze` in cpp_analysis.py; line number: 85; ")
    include_dirs = find_includes(project_root)

    source_files = remove_files_in_dirs(
        source_files, project_root, ["test", "build", "CMakeFiles", "performance"]
    )
    extra_args.extend([f"-I{d}" for d in include_dirs])
    all_args = {
        "source_files": source_files,
        "compilation_db_path": compilation_db_path,
        "file_filters": file_filters,
        "extra_args": extra_args,
        # "mode": mode
    }
    if mode is not None:
        all_args["mode"] = mode

    # TEMP: on macOS, we need extra args, and we seemingly cannot set the
    # compilation_db_path arg
    # TODO investigate the root cause of this and fix it
    print(
        f"From: `safe_analyze` in utils.py; line number: 55; compilation_db_path : {compilation_db_path}"
    )
    if sys.platform == "darwin":
        all_args["extra_args"] = extra_args + [
            # "-std=c++17",
            "-resource-dir",
            "/opt/homebrew/Cellar/llvm@18/18.1.8/lib/clang/18",
            "-isysroot",
            "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk",
            "-I/opt/homebrew/opt/llvm@18/include",
        ]
        # all_args.pop("file_filters")
        all_args.pop("compilation_db_path")

    print(
        f"From: `safe_analyze` in utils.py; line number: 68; all_args : \n{json.dumps(all_args, indent=4)}"
    )
    result = analyzer.analyze(**all_args)
    return result


def enhance_analysis(app: CppApplication) -> CppApplication:

    # add classes, if they're not already there
    for tu in app.translation_units:
        if len(tu.classes) > 0:
            continue
        tree = tree_sitter_cpp.parse_file(tu.file_path)
        for node in get_nodes_of_multiple_types(
            tree, ("class_specifier", "struct_specifier")
        ):
            node_class = process_class_from_node(node, file_path=tu.file_path)
            if node_class:
                tu.classes.append(node_class)
    return app


class CppAnalysis:
    """High-level interface for C++ code analysis."""

    def __init__(
        self,
        project_dir: Union[Path, str],
        compilation_db_path: Optional[Union[Path, str]] = None,
        extra_compiler_args: Optional[List[str]] = None,
        analysis_level: AnalysisLevel = AnalysisLevel.symbol_table,
    ):
        """Initialize the C++ analysis backend.

        Args:
            project_dir: Path to the C++ project directory.
            compilation_db_path: Optional path to compilation database directory.
                If not provided, defaults to project_dir/build if it exists.
        """
        if not isinstance(project_dir, Path):
            project_dir = Path(project_dir)

        self.project_dir = project_dir
        self.analyzer = clang_callgraph.CallGraphAnalyzer()
        self._symbol_db = None

        # Initialize the application model
        self.cpp_application: CppApplication = self._init_application(
            compilation_db_path, extra_compiler_args or [], analysis_level
        )
        self.cpp_application = enhance_analysis(self.cpp_application)

    def _init_application(
        self,
        compilation_db_path: Optional[Union[Path, str]] = None,
        extra_compiler_args: List[str] = [],
        analysis_level: AnalysisLevel = AnalysisLevel.symbol_table,
    ) -> CppApplication:
        """Construct the C++ application model from project sources.

        Args:
            project_dir: Path to the project directory.
            compilation_db_path: Optional path to compilation database directory.

        Returns:
            CppApplication: Pydantic application model.
        """
        # NOTE it's important that when they're passed to `analyze`, all Path variables
        # are resolved (ie they show the full absolute path rather than relative)
        project_dir_str = str(self.project_dir.resolve())

        # Find all C++ source files
        source_files = []
        for ext in ["*.cpp", "*.cc", "*.cxx", "*.c"]:
            source_files.extend([str(f.resolve()) for f in self.project_dir.rglob(ext)])

        if not source_files:
            raise ValueError(f"No C++ source files found in {self.project_dir}")

        # Determine compilation database path
        if compilation_db_path is not None:
            # Use provided path
            if not isinstance(compilation_db_path, Path):
                compilation_db_path = Path(compilation_db_path)
            compilation_db = (
                str(compilation_db_path) if compilation_db_path.exists() else ""
            )
        else:
            # Default to project_dir/build if it exists
            build_dir = self.project_dir / "build"
            compilation_db = str(build_dir) if build_dir.exists() else ""

        include_dirs = find_includes(project_dir_str)

        extra_compiler_args.extend([f"-I{d}" for d in include_dirs])
        # Run analysis
        safe_analyze(
            self.analyzer,
            source_files=source_files,
            extra_args=extra_compiler_args,
            compilation_db_path=compilation_db,
            project_root=project_dir_str,
            mode=self._get_analysis_level(analysis_level),
        )
        # Get the tree-based application model (pybind11 object)
        app_pybind = self.analyzer.get_application_model()
        self._symbol_db = self.analyzer.get_symbol_db()

        # Convert to Pydantic model
        return CppApplication.from_pybind(app_pybind)

    def get_cpp_application(self) -> CppApplication:
        """Return the C++ application object.

        Returns:
            CppApplication: Pydantic application model.
        """
        return self.cpp_application

    def get_imports(self) -> List[str]:
        """Return all include/import statements in the project.

        Returns:
            List of included file paths.
        """
        imports = []
        for tu in self.cpp_application.translation_units:
            for inc in tu.includes:
                imports.append(inc.included_file)
        return list(set(imports))  # Remove duplicates

    def get_variables(
        self, filter: Optional[VariableFilter] = None
    ) -> List[CppVariable]:
        """Return all variables discovered across the project.

        Args:
            filter: Optional filters (e.g., file_name, is_global, is_const)

        Returns:
            List of CppVariable objects.
        """
        variables = []

        for tu in self.cpp_application.translation_units:
            # globals
            for var in tu.global_variables:
                if not filter or self._matches_variable_filter(var, filter):
                    variables.append(var)

            # namespaces
            for ns in tu.namespaces:
                variables.extend(
                    self._collect_namespace_variables_with_filter(ns, filter)
                )

        return variables

    def _matches_variable_filter(self, var: CppVariable, f: VariableFilter) -> bool:
        if f.usr and var.usr != f.usr:
            return False

        if f.name and f.name not in var.name:
            return False

        if f.file_name and f.file_name not in var.location.file:
            return False

        if f.type and f.type not in var.type:
            return False

        # Boolean checks
        for attr in ["is_global", "is_const", "is_static", "is_constexpr"]:
            value = getattr(f, attr)
            if value is not None and getattr(var, attr) != value:
                return False

        return True

    def _collect_namespace_variables_with_filter(
        self,
        ns: CppNamespace,
        filter: Optional[VariableFilter],
    ) -> List[CppVariable]:
        """Recursively collect variables from a namespace."""
        variables = []

        for var in ns.variables:
            if not filter or self._matches_variable_filter(var, filter):
                variables.append(var)

        for child_ns in ns.namespaces:
            variables.extend(
                self._collect_namespace_variables_with_filter(child_ns, filter)
            )

        return variables

    def get_application_view(self) -> CppApplication:
        """Return the application view of the C++ project.

        Returns:
            CppApplication: Application model summarizing translation units.
        """
        return self.cpp_application

    def get_symbol_table(self) -> Dict[str, CppTranslationUnit]:
        """Return a symbol table view keyed by file path.

        Returns:
            Dictionary mapping file paths to Pydantic translation units.
        """
        return {tu.file_path: tu for tu in self.cpp_application.translation_units}

    def get_compilation_units(self) -> List[CppTranslationUnit]:
        """Return all compilation units parsed from C++ sources.

        Returns:
            List of Pydantic CppTranslationUnit objects.
        """
        return self.cpp_application.translation_units

    def get_call_graph(self) -> nx.DiGraph:
        """Return the call graph of the C++ code.

        Returns:
            networkx.DiGraph: Call graph with functions as nodes and calls as edges.
        """
        G = nx.DiGraph()

        for edge in self.cpp_application.call_graph_edges:
            G.add_node(edge.caller_usr, name=edge.caller_name)
            G.add_node(edge.callee_usr, name=edge.callee_name)

            G.add_edge(
                edge.caller_usr,
                edge.callee_usr,
                kind=edge.kind,
                file=edge.caller_file,
                line=edge.call_site_line,
            )

        return G

    def get_call_graph_edges(self) -> List[CppCallGraphEdge]:
        """Return the call graph edges of the C++ code.

        Returns:
            List of Pydantic CppCallGraphEdge objects connecting callers to callees.
        """
        return self.cpp_application.call_graph_edges

    def get_call_graph_json(self) -> str:
        """Return the call graph serialized as JSON.

        Returns:
            str: Call graph encoded as JSON.
        """
        import json

        edges_data = []
        for edge in self.cpp_application.call_graph_edges:
            edges_data.append(
                {
                    "caller": edge.caller_name,
                    "caller_usr": edge.caller_usr,
                    "caller_file": edge.caller_file,
                    "caller_line": edge.caller_line,
                    "call_site_line": edge.call_site_line,
                    "callee": edge.callee_name,
                    "callee_usr": edge.callee_usr,
                    "callee_file": edge.callee_file,
                    "callee_line": edge.callee_line,
                    "kind": str(edge.kind),
                    "is_from_macro": edge.is_from_macro,
                    "macro_name": edge.macro_name,
                }
            )

        return json.dumps({"edges": edges_data}, indent=2)

    def get_callers(self, function: CppFunction) -> Dict[str, List[CppCallGraphEdge]]:
        """Return callers of a function.

        Args:
            function: Target Pydantic function.

        Returns:
            Dictionary mapping caller USRs to lists of Pydantic call edges.
        """
        callers = {}
        for edge in self.cpp_application.call_graph_edges:
            if edge.callee_usr == function.usr:
                if edge.caller_usr not in callers:
                    callers[edge.caller_usr] = []
                callers[edge.caller_usr].append(edge)
        return callers

    def get_callees(self, function: CppFunction) -> Dict[str, List[CppCallGraphEdge]]:
        """Return callees of a function.

        Args:
            function: Source Pydantic function.

        Returns:
            Dictionary mapping callee USRs to lists of Pydantic call edges.
        """
        callees = {}
        for edge in self.cpp_application.call_graph_edges:
            if edge.caller_usr == function.usr:
                if edge.callee_usr not in callees:
                    callees[edge.callee_usr] = []
                callees[edge.callee_usr].append(edge)
        return callees

    def get_callers_list(self, function: CppFunction) -> List[CppCallGraphEdge]:
        return [
            edge
            for edge in self.cpp_application.call_graph_edges
            if edge.callee_usr == function.usr
        ]

    def get_callees_list(self, function: CppFunction) -> List[CppCallGraphEdge]:
        return [
            edge
            for edge in self.cpp_application.call_graph_edges
            if edge.caller_usr == function.usr
        ]

    def find_references(self, usr: str) -> List[CppCallGraphEdge]:
        return [
            edge
            for edge in self.cpp_application.call_graph_edges
            if edge.caller_usr == usr or edge.callee_usr == usr
        ]

    def get_transitive_callees(self, function: CppFunction) -> set[str]:
        visited = set()
        stack = [function.usr]

        while stack:
            current = stack.pop()

            for edge in self.cpp_application.call_graph_edges:
                if edge.caller_usr == current:
                    callee = edge.callee_usr
                    if callee not in visited:
                        visited.add(callee)
                        stack.append(callee)

        return visited

    def get_transitive_callers(self, function: CppFunction) -> set[str]:
        visited = set()
        stack = [function.usr]

        while stack:
            current = stack.pop()

            for edge in self.cpp_application.call_graph_edges:
                if edge.callee_usr == current:
                    caller = edge.caller_usr
                    if caller not in visited:
                        visited.add(caller)
                        stack.append(caller)

        return visited

    def get_functions(self) -> Dict[str, CppFunction]:
        """Return all functions in the project.

        Returns:
            Dictionary mapping function USRs to Pydantic CppFunction objects.
        """
        functions = {}

        for tu in self.cpp_application.translation_units:
            # Top-level functions
            for func in tu.functions:
                # Deduplicate by USR - prefer definitions over declarations
                if func.usr not in functions or func.is_definition:
                    functions[func.usr] = func

            # Functions in namespaces
            for ns in tu.namespaces:
                ns_funcs = self._collect_namespace_functions(ns)
                for usr, func in ns_funcs.items():
                    if usr not in functions or func.is_definition:
                        functions[usr] = func

            # Methods in records
            for record in tu.records:
                rec_funcs = self._collect_record_methods(record)
                for usr, func in rec_funcs.items():
                    if usr not in functions or func.is_definition:
                        functions[usr] = func

        return functions

    def find_functions(
        self,
        name: Optional[str] = None,
        file_name: Optional[str] = None,
    ) -> List[CppFunction]:
        functions = self.get_functions().values()

        results = list(functions)

        if name:
            results = [f for f in results if name in f.name]

        if file_name:
            results = [f for f in results if file_name in f.location.file]

        return results

    def get_function_by_usr(self, usr: str) -> Optional[CppFunction]:
        functions = self.get_functions()
        return functions.get(usr)

    def _collect_namespace_functions(self, ns: CppNamespace) -> Dict[str, CppFunction]:
        """Recursively collect functions from a namespace."""
        functions = {}
        for func in ns.functions:
            functions[func.usr] = func
        for child_ns in ns.namespaces:
            functions.update(self._collect_namespace_functions(child_ns))
        for record in ns.records:
            functions.update(self._collect_record_methods(record))
        return functions

    def _collect_record_methods(self, record: CppRecord) -> Dict[str, CppFunction]:
        """Recursively collect methods from a record."""
        functions = {}
        for method in record.methods:
            functions[method.usr] = method
        for nested in record.nested_records:
            functions.update(self._collect_record_methods(nested))
        return functions

    def get_records(self) -> List[CppRecord]:
        """Return all record types (classes, structs, unions) in the project.

        Returns:
            List of Pydantic CppRecord objects.
        """
        records_by_usr = {}

        for tu in self.cpp_application.translation_units:
            for record in tu.records:
                # Deduplicate by USR - prefer definitions over declarations
                if record.usr not in records_by_usr or record.is_definition:
                    records_by_usr[record.usr] = record

            for ns in tu.namespaces:
                for record in self._collect_namespace_records(ns):
                    if record.usr not in records_by_usr or record.is_definition:
                        records_by_usr[record.usr] = record

        return list(records_by_usr.values())

    def get_record_by_usr(self, usr: str) -> Optional[CppRecord]:
        for record in self.get_records():
            if record.usr == usr:
                return record
        return None

    def _collect_namespace_records(self, ns: CppNamespace) -> List[CppRecord]:
        """Recursively collect records from a namespace."""
        records = []
        records.extend(ns.records)
        for child_ns in ns.namespaces:
            records.extend(self._collect_namespace_records(child_ns))
        return records

    def get_function(
        self, function_name: str, file_name: Optional[str] = None
    ) -> Union[CppFunction, List[CppFunction]]:
        """Return a function object.

        Args:
            function_name: Function name (can be qualified).
            file_name: Optional file name to narrow search.

        Returns:
            Pydantic CppFunction or list of CppFunction objects matching the query.
        """
        functions = self.get_functions()
        matches = []

        for usr, func in functions.items():
            if function_name in func.name:
                if file_name is None or file_name in func.location.file:
                    matches.append(func)

        if len(matches) == 1:
            return matches[0]
        return matches

    def get_cpp_file(self, file_name: str) -> Optional[str]:
        """Return a C++ file path by name.

        Args:
            file_name: File name (can be partial).

        Returns:
            Full file path or None if not found.
        """
        for tu in self.cpp_application.translation_units:
            if file_name in tu.file_path:
                return tu.file_path
        return None

    def get_cpp_compilation_unit(self, file_path: str) -> Optional[CppTranslationUnit]:
        """Return the compilation unit for a C++ source file.

        Args:
            file_path: Path to a C++ source file (can be partial).

        Returns:
            Pydantic CppTranslationUnit object or None if not found.
        """
        for tu in self.cpp_application.translation_units:
            if file_path in tu.file_path:
                return tu
        return None

    def get_functions_in_file(self, file_name: str) -> List[CppFunction]:
        """Return all functions in a given file.

        Args:
            file_name: File name (can be partial).

        Returns:
            List of Pydantic CppFunction objects.
        """
        functions = []
        tu = self.get_cpp_compilation_unit(file_name)

        if tu:
            functions.extend(tu.functions)
            for ns in tu.namespaces:
                functions.extend(self._collect_namespace_functions(ns).values())
            for record in tu.records:
                functions.extend(self._collect_record_methods(record).values())

        return functions

    def get_macros(self) -> List[CppMacro]:
        """Return all macros in the project.

        Returns:
            List of Pydantic CppMacro objects.
        """
        macros_by_usr = {}
        for tu in self.cpp_application.translation_units:
            for macro in tu.macros:
                # Deduplicate by USR - macros don't have is_definition
                # so we just keep the first occurrence
                if macro.usr not in macros_by_usr:
                    macros_by_usr[macro.usr] = macro

        return list(macros_by_usr.values())

    def get_macros_in_file(self, file_name: str) -> Optional[List[CppMacro]]:
        """Return all macros in the given file.

        Args:
            file_name: File name (can be partial).

        Returns:
            List of Pydantic CppMacro objects or None if file not found.
        """
        tu = self.get_cpp_compilation_unit(file_name)
        return tu.macros if tu else None

    def get_typedefs(self) -> List[CppTypedef]:
        """Return typedef declarations across the project.

        Returns:
            List of Pydantic CppTypedef objects.
        """
        typedefs_by_usr = {}
        for tu in self.cpp_application.translation_units:
            for typedef in tu.typedefs:
                # Deduplicate by USR - prefer definitions over declarations
                if typedef.usr not in typedefs_by_usr or typedef.is_definition:
                    typedefs_by_usr[typedef.usr] = typedef

            for ns in tu.namespaces:
                for typedef in self._collect_namespace_typedefs(ns):
                    if typedef.usr not in typedefs_by_usr or typedef.is_definition:
                        typedefs_by_usr[typedef.usr] = typedef

        return list(typedefs_by_usr.values())

    def _collect_namespace_typedefs(self, ns: CppNamespace) -> List[CppTypedef]:
        """Recursively collect typedefs from a namespace."""
        typedefs = []
        typedefs.extend(ns.typedefs)
        for child_ns in ns.namespaces:
            typedefs.extend(self._collect_namespace_typedefs(child_ns))
        return typedefs

    def get_typedefs_in_file(self, file_name: str) -> Optional[List[CppTypedef]]:
        """Return typedef declarations in a file.

        Args:
            file_name: File name (can be partial).

        Returns:
            List of Pydantic CppTypedef objects or None if file not found.
        """
        tu = self.get_cpp_compilation_unit(file_name)
        if not tu:
            return None

        typedefs = list(tu.typedefs)
        for ns in tu.namespaces:
            typedefs.extend(self._collect_namespace_typedefs(ns))
        return typedefs

    def get_structs(self) -> List[CppRecord]:
        """Return struct/union declarations across the project.

        Returns:
            List of Pydantic CppRecord objects with kind Struct or Union.
        """
        records = self.get_records()
        return [
            r for r in records if r.kind in [CppRecordKind.STRUCT, CppRecordKind.UNION]
        ]

    def get_structs_in_file(self, file_name: str) -> Optional[List[CppRecord]]:
        """Return struct/union declarations in a file.

        Args:
            file_name: File name (can be partial).

        Returns:
            List of Pydantic CppRecord objects or None if file not found.
        """
        tu = self.get_cpp_compilation_unit(file_name)
        if not tu:
            return None

        structs = [
            r
            for r in tu.records
            if r.kind in [CppRecordKind.STRUCT, CppRecordKind.UNION]
        ]

        for ns in tu.namespaces:
            records = self._collect_namespace_records(ns)
            structs.extend(
                [
                    r
                    for r in records
                    if r.kind in [CppRecordKind.STRUCT, CppRecordKind.UNION]
                ]
            )

        return structs

    def get_enums(self) -> List[CppEnum]:
        """Return enum declarations across the project.

        Returns:
            List of Pydantic CppEnum objects.
        """
        enums_by_usr = {}
        for tu in self.cpp_application.translation_units:
            for enum in tu.enums:
                # Deduplicate by USR - prefer definitions over declarations
                if enum.usr not in enums_by_usr or enum.is_definition:
                    enums_by_usr[enum.usr] = enum

            for ns in tu.namespaces:
                for enum in self._collect_namespace_enums(ns):
                    if enum.usr not in enums_by_usr or enum.is_definition:
                        enums_by_usr[enum.usr] = enum

        return list(enums_by_usr.values())

    def _collect_namespace_enums(self, ns: CppNamespace) -> List[CppEnum]:
        """Recursively collect enums from a namespace."""
        enums = []
        enums.extend(ns.enums)
        for child_ns in ns.namespaces:
            enums.extend(self._collect_namespace_enums(child_ns))
        return enums

    def get_enums_in_file(self, file_name: str) -> Optional[List[CppEnum]]:
        """Return enum declarations in a file.

        Args:
            file_name: File name (can be partial).

        Returns:
            List of Pydantic CppEnum objects or None if file not found.
        """
        tu = self.get_cpp_compilation_unit(file_name)
        if not tu:
            return None

        enums = list(tu.enums)
        for ns in tu.namespaces:
            enums.extend(self._collect_namespace_enums(ns))
        return enums

    def get_globals(self, file_name: str) -> Optional[List[CppVariable]]:
        """Return global variable declarations in a file.

        Args:
            file_name: File name (can be partial).

        Returns:
            List of Pydantic CppVariable objects or None if file not found.
        """
        tu = self.get_cpp_compilation_unit(file_name)
        return tu.global_variables if tu else None

    def get_file_dependency_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()

        for tu in self.cpp_application.translation_units:
            G.add_node(tu.file_path)

            for inc in tu.includes:
                if not inc.is_system:
                    G.add_edge(tu.file_path, inc.included_file)

        return G

    def _get_analysis_level(self, analysis_level: AnalysisLevel) -> str:
        return _ANALYSIS_MAP[analysis_level]
