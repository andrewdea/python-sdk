from cldk.analysis.c.process_parsed_file_treesitter import (
    tree_sitter_cpp,
)
from tree_sitter import Node
from typing import Optional

def compute_cyclomatic_complexity(snippet: str) -> int:
    """
    Compute the cyclomatic complexity of a C/C++ code snippet.

    Cyclomatic complexity is calculated as the number of decision points + 1.
    Decision points include: if, else if, for, while, do, switch cases,
    logical operators (&&, ||), ternary operators, and catch blocks.

    Args:
        snippet: A string containing C/C++ code to analyze

    Returns:
        An integer representing the cyclomatic complexity
    """
    # Parse the snippet using tree-sitter
    tree = tree_sitter_cpp.parse(snippet)

    # Decision point node types in C/C++
    decision_nodes = [
        "if_statement",
        "else_clause",
        "for_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
        "case_statement",
        "conditional_expression",  # ternary operator
        "catch_clause",
    ]

    # Count decision points by traversing the tree
    complexity = 1  # Base complexity

    def traverse(node: Node, parent_type: Optional[str] = None):
        nonlocal complexity

        # Skip if_statement nodes that are direct children of else_clause
        # (they represent "else if" and should only be counted once as the else_clause)
        if node.type == "if_statement" and parent_type == "else_clause":
            # Still traverse children, but don't count this if_statement
            for child in node.children:
                traverse(child, node.type)
            return

        # Check if this node is a decision point
        if node.type in decision_nodes:
            complexity += 1

        # Special handling for logical operators
        if node.type == "binary_expression":
            # Check if it"s a logical AND or OR
            for child in node.children:
                if child.type in ["&&", "||"]:
                    complexity += 1

        # Recursively traverse children
        for child in node.children:
            traverse(child, node.type)

    # Start traversal from root
    traverse(tree.root_node)

    return complexity
