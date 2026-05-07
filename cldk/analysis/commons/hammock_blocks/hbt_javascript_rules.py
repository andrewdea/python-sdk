from tree_sitter import Language, Parser, Tree, Node, Point
from cldk.analysis.commons.hammock_blocks.hb_definition import (
    TSHammockBlock,
    TSHBRelation,
)
from typing import List, Optional, Tuple, Dict
from functools import wraps
from cldk.analysis.commons.hammock_blocks.hbt_dispatcher import ts_node_overload
import os


class JavaScriptTSHBParsingRules:
    """
    Tree-sitter parsing rules for JavaScript code, using the TSHammockBlock and Relation class.
    Supports ES6+, including modules, classes, arrow functions, async/await, and more.
    """

    def __init__(
        self,
        source_code_dir_list,
        src_file_to_dir_map,
        artifact_dir=None,
        exclude_self=True,
    ):
        self.supported_block_type = {
            "if_statement",
            "switch_statement",
            "for_statement",
            "for_in_statement",
            "for_of_statement",
            "while_statement",
            "do_statement",
            "try_statement",
            "function_declaration",
            "arrow_function",
            "function_expression",
            "generator_function_declaration",
            "method_definition",
            "class_declaration",
        }
        self.exclude_self = exclude_self
        self.src_file_to_dir_map = src_file_to_dir_map

    @ts_node_overload
    def parse_ts_node(
        self, node: Node, block_map: Dict, source_file: str
    ) -> TSHammockBlock:
        """Entry point for parsing - dispatches to registered handlers"""
        pass  # Body is replaced by per module dispatcher

    def _parse_default(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Fallback for unhandled node types"""
        # print(f"[JS DEFAULT] Parsing unhandled node type: {node.type}")
        return None, []

    @parse_ts_node.register("program")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript program (top-level node)"""
        print(f"[JS] Dispatched to parse_program for node: {node.type}")
        print(f"[JS] Program at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        project_base = self.src_file_to_dir_map["project_base"]
        relative_path = source_file.replace(project_base + os.sep, "")
        basename_no_ext = os.path.splitext(relative_path)[0]
        basename_no_ext = basename_no_ext.replace(os.sep, ".")
        hammock_block.project_full_qualifier = basename_no_ext

        source_dir = self.src_file_to_dir_map[source_file]
        relative_path = source_file.replace(source_dir + os.sep, "")
        basename_no_ext = os.path.splitext(relative_path)[0]
        basename_no_ext = basename_no_ext.replace(os.sep, ".")
        hammock_block.block_full_qualifier = basename_no_ext

        return hammock_block, []

    @parse_ts_node.register("import_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript ES6 import statement"""
        print(f"[JS] Dispatched to parse_import_statement for node: {node.type}")
        print(f"[JS] Import statement at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        # Extract the source module
        source_node = node.child_by_field_name("source")
        if source_node and source_node.type == "string":
            module_name = source_node.text.decode("utf-8").strip("\"'")
            hammock_block.imported_packages.append(module_name)

        return hammock_block, []

    @parse_ts_node.register("export_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript ES6 export statement"""
        print(f"[JS] Dispatched to parse_export_statement for node: {node.type}")
        print(f"[JS] Export statement at line {node.start_point.row + 1}")
        # Exports don't create hammock blocks, just track what's exported
        return None, []

    @parse_ts_node.register("comment")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript comment"""
        print(f"[JS] Dispatched to parse_comment for node: {node.type}")
        print(f"[JS] Comment at line {node.start_point.row + 1}")
        comment = node.text.decode("utf-8")
        current_parent = node.parent
        while current_parent and (current_parent.id not in block_map):
            current_parent = current_parent.parent
        if current_parent and current_parent.id in block_map:
            block_map[current_parent.id].comments.append(comment)
        return None, []

    @parse_ts_node.register("call_expression")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript function call"""
        print(f"[JS] Dispatched to parse_call_expression for node: {node.type}")
        print(f"[JS] Call expression at line {node.start_point.row + 1}")
        function_node = node.child_by_field_name("function")
        if function_node:
            full_call = function_node.text.decode("utf-8")
            current_parent = node.parent
            while current_parent and (current_parent.id not in block_map):
                current_parent = current_parent.parent
            if current_parent and current_parent.id in block_map:
                block_map[current_parent.id].local_callsites.append(
                    [function_node, full_call]
                )
        return None, []

    @parse_ts_node.register("new_expression")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript constructor call (new expression)"""
        print(f"[JS] Dispatched to parse_new_expression for node: {node.type}")
        print(f"[JS] New expression at line {node.start_point.row + 1}")
        constructor_node = node.child_by_field_name("constructor")
        if constructor_node:
            full_call = constructor_node.text.decode("utf-8")
            current_parent = node.parent
            while current_parent and (current_parent.id not in block_map):
                current_parent = current_parent.parent
            if current_parent and current_parent.id in block_map:
                block_map[current_parent.id].local_callsites.append(
                    [constructor_node, f"new {full_call}"]
                )
        return None, []

    @parse_ts_node.register("class_declaration")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript class declaration"""
        print(f"[JS] Dispatched to parse_class_declaration for node: {node.type}")
        print(f"[JS] Class declaration at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        name_node = node.child_by_field_name("name")
        if name_node and name_node.type == "identifier":
            hammock_block.local_identifiers.append(name_node.text.decode("utf-8"))

        # Handle class heritage (extends)
        heritage_node = node.child_by_field_name("heritage")
        if heritage_node:
            for child in heritage_node.named_children:
                if child.type == "identifier":
                    print(
                        f"[JS] Found superclass identifier: {child.text.decode('utf-8')}"
                    )
                    hammock_block.local_identifiers.append(child.text.decode("utf-8"))

        current_parent = node.parent
        while current_parent:
            if current_parent.id in block_map and len(
                block_map[current_parent.id].block_full_qualifier
            ):
                break
            current_parent = current_parent.parent

        if current_parent and current_parent.id in block_map:
            hammock_block.block_full_qualifier = (
                block_map[current_parent.id].block_full_qualifier
                + "."
                + name_node.text.decode("utf-8")
                if name_node
                else ""
            )
            hammock_block.project_full_qualifier = (
                block_map[current_parent.id].project_full_qualifier
                + "."
                + name_node.text.decode("utf-8")
                if name_node
                else ""
            )

        return hammock_block, []

    @parse_ts_node.register("function_declaration")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript function declaration"""
        print(f"[JS] Dispatched to parse_function_declaration for node: {node.type}")
        print(f"[JS] Function declaration at line {node.start_point.row + 1}")
        return self._parse_function_like(node, block_map, source_file)

    @parse_ts_node.register("arrow_function")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript arrow function"""
        print(f"[JS] Dispatched to parse_arrow_function for node: {node.type}")
        print(f"[JS] Arrow function at line {node.start_point.row + 1}")
        return self._parse_function_like(node, block_map, source_file, is_arrow=True)

    @parse_ts_node.register("function_expression")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript function expression"""
        print(f"[JS] Dispatched to parse_function_expression for node: {node.type}")
        print(f"[JS] Function expression at line {node.start_point.row + 1}")
        return self._parse_function_like(node, block_map, source_file)

    @parse_ts_node.register("generator_function_declaration")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript generator function"""
        print(f"[JS] Dispatched to parse_generator_function for node: {node.type}")
        print(f"[JS] Generator function at line {node.start_point.row + 1}")
        return self._parse_function_like(node, block_map, source_file)

    @parse_ts_node.register("method_definition")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript method definition (in class)"""
        print(f"[JS] Dispatched to parse_method_definition for node: {node.type}")
        print(f"[JS] Method definition at line {node.start_point.row + 1}")
        return self._parse_function_like(node, block_map, source_file)

    def _parse_function_like(
        self, node: Node, block_map: Dict, source_file: str, is_arrow: bool = False
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Helper to parse function-like constructs"""
        hammock_block = self._base_block_builder(node)

        # Get function name
        name_node = node.child_by_field_name("name")
        if name_node and name_node.type == "identifier":
            hammock_block.local_identifiers.append(name_node.text.decode("utf-8"))
        elif is_arrow:
            # Arrow functions might not have names, try to infer from context
            if node.parent and node.parent.type == "variable_declarator":
                var_name = node.parent.child_by_field_name("name")
                if var_name:
                    hammock_block.local_identifiers.append(
                        var_name.text.decode("utf-8")
                    )

        # Get parameters
        parameters_node = node.child_by_field_name("parameters")
        if parameters_node:
            for param in parameters_node.named_children:
                if param.type == "identifier":
                    if param.text.decode("utf-8") != "self" or not self.exclude_self:
                        hammock_block.local_variables.append(param.text.decode("utf-8"))
                elif param.type == "rest_pattern":
                    # Handle rest parameters (...args)
                    rest_id = param.child_by_field_name("name")
                    if rest_id:
                        hammock_block.local_variables.append(
                            rest_id.text.decode("utf-8")
                        )
                elif param.type in ["object_pattern", "array_pattern"]:
                    # Handle destructured parameters
                    identifiers, variables, strings = (
                        self._find_identifiers_locals_strings_in_subtree(param)
                    )
                    hammock_block.local_variables.extend(variables)

        # Build full qualifier
        current_parent = node.parent
        while current_parent:
            if current_parent.id in block_map and len(
                block_map[current_parent.id].block_full_qualifier
            ):
                break
            current_parent = current_parent.parent

        if current_parent and current_parent.id in block_map:
            func_name = name_node.text.decode("utf-8") if name_node else "anonymous"
            hammock_block.block_full_qualifier = (
                block_map[current_parent.id].block_full_qualifier + "." + func_name
            )
            hammock_block.project_full_qualifier = (
                block_map[current_parent.id].project_full_qualifier + "." + func_name
            )

        return hammock_block, []

    @parse_ts_node.register("return_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript return statement"""
        print(f"[JS] Dispatched to parse_return_statement for node: {node.type}")
        print(f"[JS] Return statement at line {node.start_point.row + 1}")

        identifiers, variables, strings = (
            self._find_identifiers_locals_strings_in_subtree(node)
        )
        current_parent = node.parent
        while current_parent:
            if current_parent.id in block_map and len(
                block_map[current_parent.id].block_full_qualifier
            ):
                break
            current_parent = current_parent.parent

        if current_parent and current_parent.id in block_map:
            hammock_block = block_map[current_parent.id]
            hammock_block.local_identifiers.extend(identifiers)
            hammock_block.local_variables.extend(variables)
            hammock_block.string_literals.extend(strings)

        return None, []

    @parse_ts_node.register("expression_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript expression statement"""
        print(f"[JS] Dispatched to parse_expression_statement for node: {node.type}")
        print(f"[JS] Expression statement at line {node.start_point.row + 1}")

        # Only parse expression statements at module level or directly in function/class bodies
        if node.parent and (
            node.parent.type == "program"
            or node.parent.type == "statement_block"
            and node.parent.parent
            and node.parent.parent.type
            in [
                "function_declaration",
                "arrow_function",
                "function_expression",
                "method_definition",
                "class_declaration",
            ]
        ):
            hammock_block = self._base_block_builder(node)

            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(node)
            )
            hammock_block.local_identifiers.extend(identifiers)
            hammock_block.local_variables.extend(variables)
            hammock_block.string_literals.extend(strings)
            return hammock_block, []
        else:
            print(
                f"[JS] Skipping expression_statement not at appropriate level: {node.type}"
            )
            return None, []

    @parse_ts_node.register("variable_declaration")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript variable declaration (var/let/const)"""
        print(f"[JS] Dispatched to parse_variable_declaration for node: {node.type}")
        print(f"[JS] Variable declaration at line {node.start_point.row + 1}")

        identifiers, variables, strings = (
            self._find_identifiers_locals_strings_in_subtree(node)
        )
        current_parent = node.parent
        while current_parent and (current_parent.id not in block_map):
            current_parent = current_parent.parent

        if current_parent and current_parent.id in block_map:
            hammock_block = block_map[current_parent.id]
            hammock_block.local_identifiers.extend(identifiers)
            hammock_block.local_variables.extend(variables)
            hammock_block.string_literals.extend(strings)

        return None, []

    @parse_ts_node.register("if_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript if statement"""
        print(f"[JS] Dispatched to parse_if_statement for node: {node.type}")
        print(f"[JS] If statement at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)
        additional_blocks_list = []

        # Parse condition and consequence
        condition_node = node.child_by_field_name("condition")
        consequence_node = node.child_by_field_name("consequence")

        if condition_node and consequence_node:
            print(f"[JS] IF clause at line {condition_node.start_point.row + 1}")
            if_consequence_child_block = self._base_block_builder(consequence_node)
            if_consequence_child_block.start_point = condition_node.start_point
            if_consequence_child_block.end_point = consequence_node.end_point
            if_consequence_child_block.block_type = "if_clause"

            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(condition_node)
            )
            if_consequence_child_block.local_identifiers.extend(identifiers)
            if_consequence_child_block.local_variables.extend(variables)
            if_consequence_child_block.string_literals.extend(strings)

            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(consequence_node)
            )
            if_consequence_child_block.local_identifiers.extend(identifiers)
            if_consequence_child_block.local_variables.extend(variables)
            if_consequence_child_block.string_literals.extend(strings)

            hammock_block.children.append(if_consequence_child_block)
            hammock_block.children_ids.append(if_consequence_child_block.block_id)
            if_consequence_child_block.parent = hammock_block
            assert if_consequence_child_block.block_id not in block_map
            block_map[if_consequence_child_block.block_id] = if_consequence_child_block
            additional_blocks_list.append(if_consequence_child_block)

        # Parse alternative (else/else if)
        alternative_node = node.child_by_field_name("alternative")
        if alternative_node:
            if alternative_node.type == "if_statement":
                # This is an else-if, handle recursively
                print(
                    f"[JS] Else-if clause at line {alternative_node.start_point.row + 1}"
                )
                elif_block, elif_additional = self.parse_ts_node(
                    alternative_node, block_map, source_file
                )
                if elif_block:
                    elif_block.block_type = "elif_clause"
                    hammock_block.children.append(elif_block)
                    hammock_block.children_ids.append(elif_block.block_id)
                    elif_block.parent = hammock_block
                    additional_blocks_list.append(elif_block)
                    additional_blocks_list.extend(elif_additional)
            else:
                # This is an else clause
                print(
                    f"[JS] Else clause at line {alternative_node.start_point.row + 1}"
                )
                else_consequence_child_block = self._base_block_builder(
                    alternative_node
                )
                else_consequence_child_block.block_type = "else_clause"

                identifiers, variables, strings = (
                    self._find_identifiers_locals_strings_in_subtree(alternative_node)
                )
                else_consequence_child_block.local_identifiers.extend(identifiers)
                else_consequence_child_block.local_variables.extend(variables)
                else_consequence_child_block.string_literals.extend(strings)

                hammock_block.children.append(else_consequence_child_block)
                hammock_block.children_ids.append(else_consequence_child_block.block_id)
                else_consequence_child_block.parent = hammock_block
                assert else_consequence_child_block.block_id not in block_map
                block_map[else_consequence_child_block.block_id] = (
                    else_consequence_child_block
                )
                additional_blocks_list.append(else_consequence_child_block)

        return hammock_block, additional_blocks_list

    @parse_ts_node.register("switch_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript switch statement"""
        print(f"[JS] Dispatched to parse_switch_statement for node: {node.type}")
        print(f"[JS] Switch statement at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)
        additional_blocks_list = []

        # Parse switch value
        value_node = node.child_by_field_name("value")
        if value_node:
            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(value_node)
            )
            hammock_block.local_identifiers.extend(identifiers)
            hammock_block.local_variables.extend(variables)
            hammock_block.string_literals.extend(strings)

        # Parse switch body (cases)
        body_node = node.child_by_field_name("body")
        if body_node:
            for child in body_node.named_children:
                if child.type in ["switch_case", "switch_default"]:
                    print(f"[JS] {child.type} at line {child.start_point.row + 1}")
                    case_child_block = self._base_block_builder(child)

                    identifiers, variables, strings = (
                        self._find_identifiers_locals_strings_in_subtree(child)
                    )
                    case_child_block.local_identifiers.extend(identifiers)
                    case_child_block.local_variables.extend(variables)
                    case_child_block.string_literals.extend(strings)

                    assert case_child_block.block_id not in block_map
                    block_map[case_child_block.block_id] = case_child_block
                    hammock_block.children_ids.append(case_child_block.block_id)
                    hammock_block.children.append(case_child_block)
                    case_child_block.parent = hammock_block
                    additional_blocks_list.append(case_child_block)

        return hammock_block, additional_blocks_list

    @parse_ts_node.register("for_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript for loop"""
        print(f"[JS] Dispatched to parse_for_statement for node: {node.type}")
        print(f"[JS] For loop at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        # Parse initializer, condition, increment
        initializer_node = node.child_by_field_name("initializer")
        condition_node = node.child_by_field_name("condition")
        increment_node = node.child_by_field_name("increment")
        body_node = node.child_by_field_name("body")

        for part_node in [initializer_node, condition_node, increment_node, body_node]:
            if part_node:
                identifiers, variables, strings = (
                    self._find_identifiers_locals_strings_in_subtree(part_node)
                )
                hammock_block.local_identifiers.extend(identifiers)
                hammock_block.local_variables.extend(variables)
                hammock_block.string_literals.extend(strings)

        return hammock_block, []

    @parse_ts_node.register("for_in_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript for...in loop"""
        print(f"[JS] Dispatched to parse_for_in_statement for node: {node.type}")
        print(f"[JS] For-in loop at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        left_node = node.child_by_field_name("left")
        right_node = node.child_by_field_name("right")
        body_node = node.child_by_field_name("body")

        for part_node in [left_node, right_node, body_node]:
            if part_node:
                identifiers, variables, strings = (
                    self._find_identifiers_locals_strings_in_subtree(part_node)
                )
                hammock_block.local_identifiers.extend(identifiers)
                hammock_block.local_variables.extend(variables)
                hammock_block.string_literals.extend(strings)

        return hammock_block, []

    @parse_ts_node.register("for_of_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript for...of loop"""
        print(f"[JS] Dispatched to parse_for_of_statement for node: {node.type}")
        print(f"[JS] For-of loop at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        left_node = node.child_by_field_name("left")
        right_node = node.child_by_field_name("right")
        body_node = node.child_by_field_name("body")

        for part_node in [left_node, right_node, body_node]:
            if part_node:
                identifiers, variables, strings = (
                    self._find_identifiers_locals_strings_in_subtree(part_node)
                )
                hammock_block.local_identifiers.extend(identifiers)
                hammock_block.local_variables.extend(variables)
                hammock_block.string_literals.extend(strings)

        return hammock_block, []

    @parse_ts_node.register("while_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript while loop"""
        print(f"[JS] Dispatched to parse_while_statement for node: {node.type}")
        print(f"[JS] While loop at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        condition_node = node.child_by_field_name("condition")
        body_node = node.child_by_field_name("body")

        for part_node in [condition_node, body_node]:
            if part_node:
                identifiers, variables, strings = (
                    self._find_identifiers_locals_strings_in_subtree(part_node)
                )
                hammock_block.local_identifiers.extend(identifiers)
                hammock_block.local_variables.extend(variables)
                hammock_block.string_literals.extend(strings)

        return hammock_block, []

    @parse_ts_node.register("do_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript do-while loop"""
        print(f"[JS] Dispatched to parse_do_statement for node: {node.type}")
        print(f"[JS] Do-while loop at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)

        body_node = node.child_by_field_name("body")
        condition_node = node.child_by_field_name("condition")

        for part_node in [body_node, condition_node]:
            if part_node:
                identifiers, variables, strings = (
                    self._find_identifiers_locals_strings_in_subtree(part_node)
                )
                hammock_block.local_identifiers.extend(identifiers)
                hammock_block.local_variables.extend(variables)
                hammock_block.string_literals.extend(strings)

        return hammock_block, []

    @parse_ts_node.register("try_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript try-catch-finally statement"""
        print(f"[JS] Dispatched to parse_try_statement for node: {node.type}")
        print(f"[JS] Try-catch block at line {node.start_point.row + 1}")
        hammock_block = self._base_block_builder(node)
        additional_blocks_list = []

        # Parse try block
        try_node = node.child_by_field_name("body")
        if try_node:
            try_child_block = self._base_block_builder(try_node)
            try_child_block.start_point = hammock_block.start_point
            try_child_block.block_type = "try_clause"

            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(try_node)
            )
            try_child_block.local_identifiers.extend(identifiers)
            try_child_block.local_variables.extend(variables)
            try_child_block.string_literals.extend(strings)

            hammock_block.children_ids.append(try_child_block.block_id)
            assert try_child_block.block_id not in block_map
            block_map[try_child_block.block_id] = try_child_block
            hammock_block.children.append(try_child_block)
            try_child_block.parent = hammock_block
            additional_blocks_list.append(try_child_block)

        # Parse catch clause
        handler_node = node.child_by_field_name("handler")
        if handler_node and handler_node.type == "catch_clause":
            print(f"[JS] Catch clause at line {handler_node.start_point.row + 1}")
            catch_child_block = self._base_block_builder(handler_node)

            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(handler_node)
            )
            catch_child_block.local_identifiers.extend(identifiers)
            catch_child_block.local_variables.extend(variables)
            catch_child_block.string_literals.extend(strings)

            assert catch_child_block.block_id not in block_map
            block_map[catch_child_block.block_id] = catch_child_block
            hammock_block.children_ids.append(catch_child_block.block_id)
            hammock_block.children.append(catch_child_block)
            catch_child_block.parent = hammock_block
            additional_blocks_list.append(catch_child_block)

        # Parse finally clause
        finalizer_node = node.child_by_field_name("finalizer")
        if finalizer_node and finalizer_node.type == "finally_clause":
            print(f"[JS] Finally clause at line {finalizer_node.start_point.row + 1}")
            finally_child_block = self._base_block_builder(finalizer_node)

            identifiers, variables, strings = (
                self._find_identifiers_locals_strings_in_subtree(finalizer_node)
            )
            finally_child_block.local_identifiers.extend(identifiers)
            finally_child_block.local_variables.extend(variables)
            finally_child_block.string_literals.extend(strings)

            assert finally_child_block.block_id not in block_map
            block_map[finally_child_block.block_id] = finally_child_block
            hammock_block.children.append(finally_child_block)
            hammock_block.children_ids.append(finally_child_block.block_id)
            finally_child_block.parent = hammock_block
            additional_blocks_list.append(finally_child_block)

        return hammock_block, additional_blocks_list

    @parse_ts_node.register("throw_statement")
    def parse_ts_node_impl(
        self, node: Node, block_map: Dict, source_file: str
    ) -> Tuple[Optional[TSHammockBlock], List[TSHammockBlock]]:
        """Parse JavaScript throw statement"""
        print(f"[JS] Dispatched to parse_throw_statement for node: {node.type}")
        print(f"[JS] Throw statement at line {node.start_point.row + 1}")
        return None, []

    def _base_block_builder(self, node: Node) -> TSHammockBlock:
        """Basic builder for TSHammockBlock"""
        block_id = node.id
        block_type = node.type
        start_point = node.start_point
        end_point = node.end_point
        children_ids = [child.id for child in node.named_children]
        hammock_block = TSHammockBlock(
            block_id=block_id,
            block_full_qualifier="",
            block_type=block_type,
            start_point=start_point,
            end_point=end_point,
            children_ids=children_ids,
        )
        return hammock_block

    def _find_identifiers_locals_strings_in_subtree(
        self, node: Node, exclude_nested_blocks: bool = True
    ) -> tuple:
        """Walk the subtree with optional exclusion of nested statement blocks."""
        if not node:
            return [], [], []

        identifiers = []
        variables = []
        strings = []
        stack = [node]
        visited = set()

        # Get exclude types from registered types
        exclude_types = set()
        if exclude_nested_blocks:
            registered_types = self.parse_ts_node.get_registered_types()
            exclude_types = registered_types & self.supported_block_type

        while stack:
            current_node = stack.pop()
            if current_node.id in visited:
                continue
            visited.add(current_node.id)

            # Process current node based on its type
            if current_node.type == "string":
                strings.append(current_node.text.decode("utf-8"))
                continue
            elif current_node.type == "template_string":
                # Handle template literals
                strings.append(current_node.text.decode("utf-8"))
                continue
            elif current_node.type == "member_expression":
                # Handle property access (obj.prop)
                if (
                    current_node.parent
                    and current_node.parent.type == "call_expression"
                ):
                    # This is a method call
                    identifiers.append(current_node.text.decode("utf-8"))
                else:
                    # This is property access
                    variables.append(current_node.text.decode("utf-8"))
                continue
            elif current_node.type == "identifier":
                if self._is_method_or_class_name(current_node):
                    identifiers.append(current_node.text.decode("utf-8"))
                else:
                    variables.append(current_node.text.decode("utf-8"))
                continue
            elif current_node.type == "property_identifier":
                # Property names in object literals or member expressions
                variables.append(current_node.text.decode("utf-8"))
                continue

            # Add children to stack, but SKIP nested statement blocks
            for child in current_node.named_children:
                if child.id not in visited:
                    if (
                        exclude_nested_blocks
                        and child.type in exclude_types
                        and child != node
                    ):
                        print(
                            f"[JS] Skipping nested {child.type} at line {child.start_point.row + 1}"
                        )
                        continue
                    stack.append(child)

        # Remove duplicates while preserving order
        identifiers = list(dict.fromkeys(identifiers))
        variables = list(dict.fromkeys(variables))
        strings = list(dict.fromkeys(strings))
        return identifiers, variables, strings

    def _is_method_or_class_name(self, node: Node) -> bool:
        """Check if the identifier is likely a method or class name based on its parent type."""
        parent = node.parent
        grandparent = parent.parent if parent else None

        if not parent:
            return False

        # Function/class declarations
        if parent.type in [
            "function_declaration",
            "arrow_function",
            "function_expression",
            "generator_function_declaration",
            "method_definition",
            "class_declaration",
        ]:
            return True

        # Function calls
        if parent.type in ["call_expression", "new_expression"]:
            return True

        # Member expressions that are being called
        if (
            parent.type == "member_expression"
            and grandparent
            and grandparent.type == "call_expression"
        ):
            return True

        return False

    def _post_process_hammock_blocks(self, pdg: dict, block_map):
        """Post-process hammock blocks to merge consecutive statements and clean up"""
        # 1. Merge consecutive straightline blocks into a single hammock block
        basic_block_bookkeeping = {}
        for hammock_block in pdg["hammock_blocks"]:
            if hammock_block.block_type == "expression_statement":
                assert hammock_block.parent is not None
                parent_block_id = hammock_block.parent.block_id
                if parent_block_id not in basic_block_bookkeeping:
                    basic_block_bookkeeping[parent_block_id] = []
                basic_block_bookkeeping[parent_block_id].append(
                    [
                        hammock_block.block_id,
                        hammock_block.start_point,
                        hammock_block.end_point,
                    ]
                )

        # Merge the consecutive straightline blocks
        for parent_block_id, blocks in basic_block_bookkeeping.items():
            if len(blocks) < 2:
                continue
            blocks.sort(key=lambda x: x[1].row)
            merged_bookkeeping = []
            current_group = [[blocks[0][0], blocks[0][1], blocks[0][2]]]
            for i in range(1, len(blocks)):
                current_row_end = blocks[i - 1][2].row
                next_row = blocks[i][1].row
                if next_row == current_row_end + 1:
                    current_group.append([blocks[i][0], blocks[i][1], blocks[i][2]])
                else:
                    merged_bookkeeping.append(current_group)
                    current_group = [[blocks[i][0], blocks[i][1], blocks[i][2]]]
            merged_bookkeeping.append(current_group)
            self._merge_consecutive_expression_statement_helper(
                merged_bookkeeping, pdg, block_map
            )

        # 2. Ensure unique identifiers, strings, and variables
        for hammock_block in pdg["hammock_blocks"]:
            hammock_block.local_identifiers = list(set(hammock_block.local_identifiers))
            hammock_block.string_literals = list(set(hammock_block.string_literals))
            hammock_block.local_variables = list(set(hammock_block.local_variables))

        # 3. Move callsites from if-statement to if-clause hammock blocks
        for hammock_block in pdg["hammock_blocks"]:
            if hammock_block.block_type == "if_statement":
                if_clause = None
                for child in hammock_block.children:
                    if child.block_type == "if_clause":
                        if if_clause is None:
                            if_clause = child
                        else:
                            raise RuntimeError(
                                f"Multiple if_clause blocks found in if_statement {hammock_block.block_id}"
                            )
                if if_clause:
                    for callsite in hammock_block.local_callsites:
                        if_clause.local_callsites.append(callsite)
                    hammock_block.local_callsites = []

    def _merge_consecutive_expression_statement_helper(
        self, merged_bookkeeping, pdg, block_map
    ):
        """Helper to merge consecutive expression statements"""
        for group in merged_bookkeeping:
            if len(group) < 2:
                continue
            else:
                removal_list = []
                anchor_block_id = group[0][0]
                anchor_block = block_map[anchor_block_id]
                for i in range(1, len(group)):
                    next_block_id = group[i][0]
                    next_block = block_map[next_block_id]

                    # Merge the next block into the anchor block
                    anchor_block.end_point = next_block.end_point
                    anchor_block.local_identifiers.extend(next_block.local_identifiers)
                    anchor_block.local_variables.extend(next_block.local_variables)
                    anchor_block.string_literals.extend(next_block.string_literals)
                    anchor_block.comments.extend(next_block.comments)
                    anchor_block.discard_children_ids.extend(
                        next_block.discard_children_ids
                    )
                    assert next_block.children_ids == []
                    anchor_block.relations.extend(next_block.relations)
                    anchor_block.imported_packages.extend(next_block.imported_packages)
