"""Analyze C/C++ code using Clang's Python bindings.

This module provides a thin wrapper around libclang to parse translation
units, extract functions, variables, includes, and call sites, and produce
CLDK C models. It attempts to locate libclang on macOS and Linux.
"""

import os
import platform
from pathlib import Path
from typing import List, Optional
from cldk.analysis.c.process_parsed_file_treesitter import process_parsed_file
from cldk.models.c import CFunction, CCallSite, CTranslationUnit
from cldk.analysis.commons.treesitter.treesitter_cpp import TreeSitterCpp
import logging

from cldk.models.c.models import CInclude, CParameter, CppClass, CVariable, StorageClass

from clang.cindex import Config
from clang.cindex import Index, TranslationUnit, CursorKind, TypeKind, CompilationDatabase

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class ClangAnalyzer:
    """Analyze C/C++ code using Clang's Python bindings.

    This analyzer creates a Clang index, optionally uses a compilation
    database for compile flags, and walks the AST to build CLDK models.
    """
    # TODO figure out the most appropriate place to put these constants
    c_extensions = {".c"}
    c_header_extensions = {".h"}
    cpp_extensions = {".cpp", ".cxx", ".cc", ".c++", ".C"}
    cpp_header_extensions = {".h", ".hpp", ".hxx"}
    all_cpp_extensions = c_extensions | c_header_extensions | cpp_extensions | cpp_header_extensions



    def __init__(self, compilation_database_path: Optional[Path] = None):
        """Initialize the analyzer and libclang configuration.

        Args:
            compilation_database_path (Path | None): Optional path to a
                compilation database (compile_commands.json directory).
        """
        Config.set_library_file(self.__find_libclang())

        self.index = Index.create()
        self.compilation_database = None
        # TODO: Implement compilation database for C/C++ projects so that we can get compile arguments for each file
        # and parse them correctly. This is useful for projects with complex build systems.
        if compilation_database_path:
            self.compilation_database = CompilationDatabase.fromDirectory(str(compilation_database_path))

    def __find_libclang(self) -> str:
        """Locate the libclang library on the system.

        Returns:
            str: Absolute path to the libclang shared library.

        Raises:
            RuntimeError: If the operating system is unsupported or libclang
                cannot be found. Error message includes installation hints.
        """

        system = platform.system()

        load_dotenv()
        llvm_path = os.getenv("LLVM_PATH")
        if llvm_path is not None:
            if os.path.exists(llvm_path):
                logger.info(f"Found libclang at: {llvm_path}")
                return llvm_path
            else:
                logger.warn(f"Environment variable LLVM_PATH is set to non-existent path: {llvm_path}")

        if system == "Darwin":
            possible_paths = [
                # Apple Silicon, specific version:
                "/opt/homebrew/opt/llvm@18/lib/libclang.dylib",
                # Apple Silicon, generic:
                "/opt/homebrew/opt/llvm/lib/libclang.dylib",
                # Intel Mac:
                "/usr/local/opt/llvm/lib/libclang.dylib",
                "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/lib/libclang.dylib",
            ]

            install_instructions = "Install LLVM using: brew install llvm@18"

        # On Linux, we check various common installation paths
        elif system == "Linux":
            lib_paths = [Path("/usr/lib"), Path("/usr/lib64")]
            possible_paths = [str(p) for base in lib_paths if base.exists() for p in base.rglob("libclang*.so.17*")]
            logger.debug(f"Candidate libclang paths: {possible_paths}")
            install_instructions = "Install libclang development package using your system's package manager"
        else:
            raise RuntimeError(f"Unsupported operating system: {system}")

        # Check each possible path and return the first one that exists
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found libclang at: {path}")
                return path
        # TODO ideally find a way to ensure that the found library is of the right
        # version (llvm *18*!)

        # If no library is found, provide clear installation instructions
        raise RuntimeError(f"Could not find libclang library. \n" f"Please ensure LLVM is installed:\n{install_instructions}")

    def analyze_file(self, file_path: Path) -> CTranslationUnit:
        """Analyze a single C/C++ source file using Clang.

        Args:
            file_path (Path): Path to the source file to analyze.

        Returns:
            CTranslationUnit: Parsed translation unit model with functions and includes.
        """

        # Get compilation arguments if available
        compile_args = self._get_compile_args(file_path)
        is_header = file_path.suffix in self.cpp_header_extensions

        # Initialize our translation unit model
        translation_unit = CTranslationUnit(
            file_path=str(file_path),
            is_header=is_header,
        )
        # Parse the file with Clang, or, if that fails, tree-sitter
        try:
            tu = self.index.parse(
            str(file_path),
            args=compile_args,
            options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            if not is_header
            else TranslationUnit.PARSE_INCOMPLETE,
            )
            # Process all cursors in the translation unit
            translation_unit = self._process_translation_unit(tu.cursor, translation_unit)
        except Exception as e:
            logger.warn(e)
            parsed_file = TreeSitterCpp().parse_file(file_path)
            translation_unit = process_parsed_file(parsed_file, translation_unit)


        return translation_unit

    def _process_translation_unit(self, cursor, translation_unit: CTranslationUnit) -> CTranslationUnit:
        """Process all declarations in a translation unit.

        Args:
            cursor: Root cursor of the translation unit.
            translation_unit (CTranslationUnit): Model to

        Returns:
            CTranslationUnit: the processed translation unit
        """

        for child in cursor.get_children():
            if child.location.file and str(child.location.file) != translation_unit.file_path:
                # Skip declarations from included files
                continue

            elif child.kind == CursorKind.FUNCTION_DECL:
                func = self._extract_function(child)
                translation_unit.functions[func.name] = func

            elif child.kind == CursorKind.INCLUSION_DIRECTIVE:
                include = self._process_inclusion(child)
                translation_unit.includes.append(include)

            elif child.kind == CursorKind.CLASS_DECL:
                clazz = self._process_class(child)
                translation_unit.classes.append(clazz)
        return translation_unit

    def _process_inclusion(self, cursor):
        """Process an include directive and capture metadata.

        Args:
            cursor: Cursor pointing to an inclusion directive.

        Returns:
            CInclude: Include info with name, system/local flag, line number, and full text.

        Notes:
            C/C++ include forms:
            - System includes: #include <header.h>
            - Local includes: #include "header.h"
        """
        include_name = cursor.displayname
        include_location = cursor.location

        # Get the full text of the include directive
        tokens = list(cursor.get_tokens())
        full_text = " ".join(token.spelling for token in tokens)

        # Determine if this is a system include or local include
        is_system_include = False
        if tokens:
            # Look at the actual tokens to see if it uses <> or ""
            for token in tokens:
                if token.spelling == "<":
                    is_system_include = True
                    break

        # Store more detailed information about the include
        # include_info = {"name": include_name, "is_system": is_system_include, "line_number": include_location.line, "full_text": full_text}
        return CInclude(name=include_name, is_system=is_system_include, line_number=include_location.line, full_text=full_text)

    def _extract_parameter(self, param) -> CParameter:
        """Extract parameter info, including a best-effort default value.

        In C++, parameters can have default values, but token streams are
        generators and must be consumed carefully.

        Args:
            param: Cursor for the parameter.

        Returns:
            CParameter: Parameter model with name, type, and optional default.
        """
        default_value = None
        try:
            tokens = list(param.get_tokens())
            if tokens:
                default_value = tokens[0].spelling
        except Exception as e:
            logger.error(f"Warning: Could not extract default value for parameter {param.spelling}: {e}")

        return CParameter(name=param.spelling or f"placeholder_arg_{param.type.spelling.replace(' ', '_')}", type=param.type.spelling, default_value=default_value)

    def _extract_variable(self, cursor) -> CVariable:
        """Extract detailed variable information from a cursor.

        Args:
            cursor: Cursor for the variable declaration.

        Returns:
            CVariable: Variable model with qualifiers and source span.
        """
        return CVariable(
            name=cursor.spelling,
            type=cursor.type.spelling,
            is_static=cursor.storage_class == StorageClass.STATIC,
            is_extern=cursor.storage_class == StorageClass.EXTERN,
            is_const=cursor.type.is_const_qualified(),
            is_volatile=cursor.type.is_volatile_qualified(),
            start_line=cursor.extent.start.line,
            end_line=cursor.extent.end.line,
        )

    def _extract_function_body(self, cursor) -> str:
        """Extract a function's body as a string.

        Args:
            cursor: Cursor to the function.

        Returns:
            str: Function body text, or an empty string if unavailable.
        """
        if not cursor.is_definition():
            return ""

        try:
            tokens = list(cursor.get_tokens())
            try:
                body_start = next(i for i, t in enumerate(tokens) if t.spelling == "{")
            except Exception:
                return ""

            brace = 0
            body = []
            for token in tokens[body_start:]:
                if token.spelling == "{":
                    brace += 1
                elif token.spelling == "}":
                    brace -= 1
                body.append(token.spelling)
                if brace == 0:
                    break

            body_str = " ".join(body)

            if brace != 0:
                logging.warning(f"Unbalanced braces in function body: {cursor.spelling}")

            return body_str

        except Exception as e:
            logging.error(f"Error extracting function body: {e}")
            return ""

    def _extract_function(self, cursor) -> CFunction:
        """Extract detailed function information from a cursor.

        Args:
            cursor: Cursor for a function declaration/definition.

        Returns:
            CFunction: Function model including signature, body, calls, and locals.
        """

        # Get storage class
        storage_class = None
        for token in cursor.get_tokens():
            if token.spelling in {"static", "extern"}:
                storage_class = StorageClass(token.spelling)
                break

        # Get function parameters
        parameters = []
        for param in cursor.get_arguments():
            parameters.append(self._extract_parameter(param))

        # Collect call sites and local variables
        call_sites = []
        local_vars = []
        if cursor.is_definition():
            for child in cursor.walk_preorder():
                if child.kind == CursorKind.CALL_EXPR:
                    call_sites.append(self._extract_call_site(child))
                elif child.kind == CursorKind.VAR_DECL:
                    local_vars.append(self._extract_variable(child))

        # Get function body if this is a definition
        body = self._extract_function_body(cursor)
        return CFunction(
            name=cursor.spelling,
            return_type=cursor.result_type.spelling,
            parameters=parameters,
            storage_class=storage_class,
            is_inline="inline" in cursor.get_tokens(),
            is_variadic=cursor.type.is_function_variadic(),
            body=body,
            comment=cursor.brief_comment or "",
            call_sites=call_sites,
            local_variables=local_vars,
            start_line=cursor.extent.start.line,
            end_line=cursor.extent.end.line,
        )

    def _extract_call_site(self, cursor) -> CCallSite:
        """Extract information about a function call.

        Args:
            cursor: Cursor pointing to a call expression.

        Returns:
            CCallSite: Call site model with callee name, arg types, and span.
        """

        # Determine if this is an indirect call (through function pointer)
        is_indirect = cursor.referenced is None and cursor.type.kind == TypeKind.FUNCTIONPROTO

        # Get argument types
        arg_types = []
        for arg in cursor.get_arguments():
            arg_types.append(arg.type.spelling)

        return CCallSite(
            function_name=cursor.spelling,
            argument_types=arg_types,
            is_indirect_call=is_indirect,
            return_type=cursor.type.get_result().spelling,
            start_line=cursor.extent.start.line,
            start_column=cursor.extent.start.column,
            end_line=cursor.extent.end.line,
            end_column=cursor.extent.end.column,
        )

    def _get_compile_args(self, file_path: Path) -> List[str]:
        """Get compilation arguments for a file.

        Args:
            file_path (Path): Source file path.

        Returns:
            list[str]: Compiler arguments for parsing.
        """
        if not self.compilation_database:
            return ["-x", "c++", "-std=c++17"]

        commands = self.compilation_database.getCompileCommands(str(file_path))
        if commands:
            cmd = commands[0]
            return [arg for arg in cmd.arguments[1:] if arg != str(file_path)]
        return ["-x", "c++", "-std=c++17"]

    def _process_class(self, cursor) -> CppClass:
        """Extract detailed class information from a cursor.

        Args:
            cursor: Cursor for a class declaration/definition.

        Returns:
            CppClass: Class model including fields, methods, constructors and inner classes.
        """

        parent_classes = self._get_base_classes(cursor)

        fields = []
        methods = []
        inner_classes = []
        constructors = []
        destructor = None
        for c in cursor.get_children():
            if c.kind == CursorKind.FIELD_DECL:
                fields.append(self._extract_variable(c))

            elif c.kind == CursorKind.CXX_METHOD:
                methods.append(self._extract_function(c))

            elif c.kind == CursorKind.CLASS_DECL:
                # might want to do it for structs too
                inner_classes.append(self._process_class(c))

            elif c.kind == CursorKind.CONSTRUCTOR:
                constructors.append(self._extract_function(c))

            elif c.kind == CursorKind.DESTRUCTOR:
                destructor = self._extract_function(c)

        return CppClass(
            name=cursor.spelling,
            members=fields,
            methods=methods,
            parents=parent_classes,
            inner_classes=inner_classes,
            constructors=constructors,
            destructor=destructor,
            start_line=cursor.extent.start.line,
            end_line=cursor.extent.end.line,
        )

    def _get_base_classes(self, cursor) -> List[str]:
        """Extract the parent classes for the current class cursor.

        Args:
            cursor: Cursor for a class declaration/definition.

        Returns:
            List[str]: parent class names.
        """
        bases = []
        for c in cursor.get_children():
            if c.kind == CursorKind.CXX_BASE_SPECIFIER:
                base = c.get_definition() or c.referenced
                if base:
                    bases.append(base.spelling)

        return bases
