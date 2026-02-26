"""Tree-sitter based C/C++ file processing function.

This module provides a function similar to ClangAnalyzer._process_translation_unit
but uses tree-sitter parsed trees instead of Clang's libclang API.
"""

from typing import Optional, List
from tree_sitter import Node, Tree
from cldk.analysis.commons.treesitter.treesitter_cpp import TreeSitterCpp
from orchard.helpers.perched import get_nodes_of_type, get_nodes_of_multiple_types

# Import the C models from CLDK
from cldk.models.c import (
    CTranslationUnit,
    CFunction,
    CCallSite,
    CInclude,
    CppClass,
    CVariable,
    CParameter,
    StorageClass,
)

# Initialize tree-sitter C++ parser

tree_sitter_cpp = TreeSitterCpp()



def process_parsed_file(tree: Tree, translation_unit: CTranslationUnit) -> CTranslationUnit:
    """Process a tree-sitter parsed C/C++ file and extract information.
    
    This function is analogous to ClangAnalyzer._process_translation_unit but works
    with tree-sitter parsed trees instead of Clang cursors.
    
    Args:
        tree: Tree-sitter parsed tree of the source file
        file_path: Path to the source file being analyzed
        is_header: Whether this is a header file
        
    Returns:
        CTranslationUnit: Processed translation unit with functions, includes, and classes
    """
    
    for node in get_nodes_of_type(tree, "function_definition"):
        func = extract_function_from_node(node)
        if func:
            translation_unit.functions[func.name] = func

    for node in get_nodes_of_type(tree, "preproc_include"):
        include = process_inclusion_from_node(node)
        if include:
            translation_unit.includes.append(include)

    for node in get_nodes_of_multiple_types(tree, ("class_specifier", "struct_specifier")):
        node_class = process_class_from_node(node)
        if node_class:
            translation_unit.classes.append(node_class)
    
    return translation_unit


def process_inclusion_from_node(node: Node) -> Optional[CInclude]:
    """Extract include directive information from a tree-sitter node.
    
    Args:
        node: Tree-sitter node representing a preproc_include
        
    Returns:
        CInclude: Include information with name, system/local flag, and line number
    """
    # Get the include path from the node
    include_name = None
    is_system_include = False

    # TODO use orchard for this
    for child in node.children:
        if child.type == "system_lib_string":
            # System include: #include <header.h>
            include_name = child.text.decode('utf-8').strip('<>')
            is_system_include = True
            break
        elif child.type == "string_literal":
            # Local include: #include "header.h"
            include_name = child.text.decode('utf-8').strip('"')
            is_system_include = False
            break
    
    if not include_name:
        return None
    
    # Get the full text of the include directive
    full_text = node.text.decode('utf-8')
    
    return CInclude(
        name=include_name,
        is_system=is_system_include,
        line_number=node.start_point[0] + 1,  # tree-sitter uses 0-based line numbers
        full_text=full_text
    )


def extract_function_from_node(node: Node) -> Optional[CFunction]:
    """Extract function information from a tree-sitter node.
    
    Args:
        node: Tree-sitter node representing a function_definition
        file_path: Path to the source file
        
    Returns:
        CFunction: Function model with signature, body, calls, and locals
    """
    # Extract function name
    function_name = None
    return_type = None
    parameters = []
    body = ""
    storage_class = None
    is_inline = False
    
    # Find the function declarator
    declarator = None
    for child in node.children:
        if child.type in ("function_declarator", "pointer_declarator"):
            declarator = child
        elif child.type == "primitive_type" or child.type == "type_identifier":
            return_type = child.text.decode('utf-8')
        elif child.type == "storage_class_specifier":
            storage_text = child.text.decode('utf-8')
            if storage_text in ("static", "extern"):
                storage_class = StorageClass(storage_text)
        elif child.type == "type_qualifier" and child.text.decode('utf-8') == "inline":
            is_inline = True
        elif child.type == "compound_statement":
            body = child.text.decode('utf-8')
    
    # Extract function name and parameters from declarator
    if declarator:
        function_name = get_function_name_from_declarator(declarator)
        parameters = extract_parameters_from_declarator(declarator)
    
    if not function_name:
        return None
    
    # Extract call sites and local variables from function body
    call_sites = []
    local_vars = []
    
    # Find the compound_statement (function body)
    for child in node.children:
        if child.type == "compound_statement":
            call_sites = extract_call_sites_from_body(child)
            local_vars = extract_local_variables_from_body(child)
            break
    
    return CFunction(
        name=function_name,
        return_type=return_type or "void",
        parameters=parameters,
        storage_class=storage_class,
        is_inline=is_inline,
        is_variadic=is_variadic_function(node),
        body=body,
        comment="",  # Tree-sitter doesn't easily extract comments
        call_sites=call_sites,
        local_variables=local_vars,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


def get_function_name_from_declarator(declarator: Node) -> Optional[str]:
    """Extract function name from a function declarator node.
    
    Args:
        declarator: Tree-sitter node representing a function_declarator
        
    Returns:
        str: Function name or None
    """
    for child in declarator.children:
        if child.type == "identifier":
            return child.text.decode('utf-8')
        elif child.type in ("function_declarator", "pointer_declarator"):
            # Recursive case for complex declarators
            name = get_function_name_from_declarator(child)
            if name:
                return name
    return None


def extract_parameters_from_declarator(declarator: Node) -> List[CParameter]:
    """Extract function parameters from a function declarator node.
    
    Args:
        declarator: Tree-sitter node representing a function_declarator
        
    Returns:
        List[CParameter]: List of function parameters
    """
    parameters = []
    
    # Find the parameter_list node
    for child in declarator.children:
        if child.type == "parameter_list":
            for param_child in child.children:
                if param_child.type == "parameter_declaration":
                    param = extract_parameter_from_node(param_child)
                    if param:
                        parameters.append(param)
    
    return parameters


def extract_parameter_from_node(node: Node) -> Optional[CParameter]:
    """Extract parameter information from a parameter_declaration node.
    
    Args:
        node: Tree-sitter node representing a parameter_declaration
        
    Returns:
        CParameter: Parameter model with name and type
    """
    param_type = None
    param_name = None
    
    for child in node.children:
        if child.type in ("primitive_type", "type_identifier"):
            param_type = child.text.decode('utf-8')
        elif child.type == "identifier":
            param_name = child.text.decode('utf-8')
        elif child.type in ("pointer_declarator", "array_declarator"):
            # Handle pointer/array parameters
            if not param_name:
                param_name = get_identifier_from_declarator(child)
    
    if not param_type:
        param_type = "unknown"
    
    if not param_name:
        param_name = f"param_{param_type.replace(' ', '_')}"
    
    return CParameter(
        name=param_name,
        type=param_type,
    )


def get_identifier_from_declarator(node: Node) -> Optional[str]:
    """Recursively extract identifier from a declarator node.
    
    Args:
        node: Tree-sitter declarator node
        
    Returns:
        str: Identifier name or None
    """
    if node.type == "identifier":
        return node.text.decode('utf-8')
    
    for child in node.children:
        result = get_identifier_from_declarator(child)
        if result:
            return result
    
    return None


def is_variadic_function(node: Node) -> bool:
    """Check if a function is variadic (has ... parameter).
    
    Args:
        node: Tree-sitter node representing a function_definition
        
    Returns:
        bool: True if function is variadic
    """
    # Look for variadic_parameter in the parameter list
    for child in node.children:
        if child.type == "function_declarator":
            for param_child in child.children:
                if param_child.type == "parameter_list":
                    for param in param_child.children:
                        if param.type == "variadic_parameter":
                            return True
    return False


def extract_call_sites_from_body(body_node: Node) -> List[CCallSite]:
    """Extract function call sites from a function body.
    
    Args:
        body_node: Tree-sitter node representing the function body
        
    Returns:
        List[CCallSite]: List of call sites found in the body
    """
    call_sites = []
    
    def visit_node(node: Node):
        if node.type == "call_expression":
            call_site = extract_call_site_from_node(node)
            if call_site:
                call_sites.append(call_site)
        
        for child in node.children:
            visit_node(child)
    
    visit_node(body_node)
    return call_sites


def extract_call_site_from_node(node: Node) -> Optional[CCallSite]:
    """Extract call site information from a call_expression node.
    
    Args:
        node: Tree-sitter node representing a call_expression
        
    Returns:
        CCallSite: Call site model with function name and arguments
    """
    function_name = None
    argument_types = []
    
    # Extract function name
    for child in node.children:
        if child.type == "identifier":
            function_name = child.text.decode('utf-8')
        elif child.type == "field_expression":
            # Handle method calls like obj.method()
            function_name = child.text.decode('utf-8')
        elif child.type == "argument_list":
            # Extract argument types (simplified - just count them)
            for arg in child.children:
                if arg.type != "," and arg.type != "(" and arg.type != ")":
                    argument_types.append("unknown")
    
    if not function_name:
        function_name = "unknown"
    
    return CCallSite(
        function_name=function_name,
        argument_types=argument_types,
        is_indirect_call=False,  # Would need more analysis to determine
        return_type="",
        start_line=node.start_point[0] + 1,
        start_column=node.start_point[1] + 1,
        end_line=node.end_point[0] + 1,
        end_column=node.end_point[1] + 1,
    )


def extract_local_variables_from_body(body_node: Node) -> List[CVariable]:
    """Extract local variable declarations from a function body.
    
    Args:
        body_node: Tree-sitter node representing the function body
        
    Returns:
        List[CVariable]: List of local variables
    """
    local_vars = []
    
    def visit_node(node: Node):
        if node.type == "declaration":
            var = extract_variable_from_node(node)
            if var:
                local_vars.append(var)
        
        for child in node.children:
            visit_node(child)
    
    visit_node(body_node)
    return local_vars


def extract_variable_from_node(node: Node) -> Optional[CVariable]:
    """Extract variable information from a declaration node.
    
    Args:
        node: Tree-sitter node representing a declaration
        
    Returns:
        CVariable: Variable model with type and qualifiers
    """
    var_type = None
    var_name = None
    is_static = False
    is_extern = False
    is_const = False
    
    for child in node.children:
        if child.type in ("primitive_type", "type_identifier"):
            var_type = child.text.decode('utf-8')
        elif child.type == "storage_class_specifier":
            storage_text = child.text.decode('utf-8')
            if storage_text == "static":
                is_static = True
            elif storage_text == "extern":
                is_extern = True
        elif child.type == "type_qualifier":
            if child.text.decode('utf-8') == "const":
                is_const = True
        elif child.type == "init_declarator":
            # Extract variable name from init_declarator
            for init_child in child.children:
                if init_child.type == "identifier":
                    var_name = init_child.text.decode('utf-8')
        elif child.type == "identifier":
            var_name = child.text.decode('utf-8')
    
    if not var_name or not var_type:
        return None
    
    return CVariable(
        name=var_name,
        type=var_type,
        is_static=is_static,
        is_extern=is_extern,
        is_const=is_const,
        is_volatile=False,  # Would need additional parsing
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


def process_class_from_node(node: Node) -> Optional[CppClass]:
    """Extract class information from a class_specifier node.
    
    Args:
        node: Tree-sitter node representing a class_specifier
        
    Returns:
        CppClass: Class model with members and methods
    """
    class_name = None
    members = []
    methods = []
    
    # Extract class name
    for child in node.children:
        if child.type == "type_identifier":
            class_name = child.text.decode('utf-8')
        elif child.type == "field_declaration_list":
            # Process class body
            for member in child.children:
                if member.type == "field_declaration":
                    var = extract_variable_from_node(member)
                    if var:
                        members.append(var)
                elif member.type == "function_definition":
                    method = extract_function_from_node(member)
                    if method:
                        methods.append(method)
    
    if not class_name:
        return None
    
    return CppClass(
        name=class_name,
        members=members,
        methods=methods,
        parents=[],  # Would need additional parsing for inheritance
        inner_classes=[],
        constructors=[],
        destructor=None,
        start_line=node.start_point[0] + 1,
        end_line=node.end_point[0] + 1,
    )


# Example usage
if __name__ == "__main__":
    # Example C code
    # sample_code = """
    # #include <stdio.h>
    # #include "myheader.h"
    
    # static int global_var = 42;
    
    # int add(int a, int b) {
    #     int result = a + b;
    #     printf("Result: %d\\n", result);
    #     return result;
    # }
    
    # void process_data(const char* data, ...) {
    #     // Variadic function
    # }
    # """
    example_file = "/Users/andrewjda/LLMs/python-sdk/cldk/analysis/c/example_projects/calc.c"
    # with open(example_file, "r") as f:
    #     sample_code = f.read()
    # Parse the code
    tree = tree_sitter_cpp.parse_file(example_file)
    
    # Process the parsed file
    translation_unit = CTranslationUnit(
            file_path=str(example_file),
            is_header=False,
        )
    translation_unit = process_parsed_file(tree, translation_unit)
    
    # Print results
    print(f"File: {translation_unit.file_path}")
    print(f"Includes: {len(translation_unit.includes)}")
    for inc in translation_unit.includes:
        print(f"  - {inc.name} (system={inc.is_system})")
    
    print(f"Functions: {len(translation_unit.functions)}")
    for func_name, func in translation_unit.functions.items():
        print(f"  - {func.name}({', '.join(p.name for p in func.parameters)})")
        print(f"    Return type: {func.return_type}")
        print(f"    Lines: {func.start_line}-{func.end_line}")
        print(f"    Call sites: {len(func.call_sites)}")
        print(f"    Local vars: {len(func.local_variables)}")
