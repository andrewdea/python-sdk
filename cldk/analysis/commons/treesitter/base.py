from orchard.data_types import SupportedLanguages
from orchard.helpers.perched import parser_registry
from tree_sitter import Parser, Tree, Language, Query, Node
from typing import Optional
from cldk.analysis.commons.treesitter.models import Captures


class TreeSitterBase:
    language_name: str
    ts_language: Language
    parser: Parser

    def __init__(
        self,
        language_name: str,
        ts_language: Optional[Language] = None,
        parser: Optional[Parser] = None,
    ) -> None:
        self.language_name = language_name
        self.ts_language = ts_language or Language(
            getattr(SupportedLanguages, language_name).value.ts_language()
        )
        self.parser = parser or parser_registry.get_parser(language_name)

    def parse(self, code: str) -> Tree:
        return self.parser.parse(bytes(code, "utf-8"))

    def get_raw_ast(self, code: str) -> Tree:
        return self.parse(code)

    def frame_query_and_capture_output(
        self, query: str, code_to_process: str
    ) -> Captures:
        """Run a query and return captures from the AST.

        Args:
            query (str): S-expression query string.
            code_to_process (str): Java source.

        Returns:
            Captures: Query captures for the AST root.
        """
        framed_query: Query = self.ts_language.query(query)
        tree = self.parse(code_to_process)
        return Captures(framed_query.captures(tree.root_node))

    def safe_ascend(self, node: Node, ascend_count: int) -> Node:
        """Ascend parent pointers safely in the AST.

        Args:
            node (Node): Starting node.
            ascend_count (int): Levels to ascend.

        Returns:
            Node: Ancestor node after ascending.

        Raises:
            ValueError: If node is None or has no parent.
        """
        if node is None:
            raise ValueError("Node does not exist.")
        if node.parent is None:
            raise ValueError("Node has no parent.")
        if ascend_count == 0:
            return node
        else:
            return self.safe_ascend(node.parent, ascend_count - 1)

    def remove_all_comments(self, source_code: str) -> str:
        # TODO leverage OrchardLanguage.comment_syntax
        raise NotImplementedError()
