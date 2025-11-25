import asyncio
from dataclasses import is_dataclass
from multilspy.multilspy_types import SymbolKind
from multilspy.multilspy_logger import MultilspyLogger
from orchard.core import find_symbol, find_symbol_in_file
from orchard.helpers.utils import get_server, call_lsp_action
from orchard.data_types import LspActions, SymbolInfo
from orchard.helpers.constants import PROJECT_ROOT
import logging


logging.basicConfig()
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)


lsp_logger = MultilspyLogger()
lsp_logger.logger.setLevel(logging.WARNING)


async def get_definition(repo_base: str, rel_path: str, symbol_name: str):
    found_symbols: list[SymbolInfo] = await find_symbol_in_file(
        repo_base,
        relative_path=rel_path,
        symbol_name=symbol_name,
    )
    print(f"found_symbols : {found_symbols}")
    server = get_server(repo_base, rel_path, lsp_logger)
    logger.debug("initialized the lsp")
    assert not server.server_started
    async with server.start_server():
        assert server.server_started
        defs = await call_lsp_action(
            LspActions.DEFINITION,
            [symbol.range for symbol in found_symbols],
            rel_path,
            server,
        )
        print(f"defs : {defs}")


async def get_references(repo_base: str, rel_path: str, symbol_name: str):
    found_symbols: list[SymbolInfo] = await find_symbol_in_file(
        repo_base,
        relative_path=rel_path,
        symbol_name=symbol_name,
    )
    print(f"found_symbols : {found_symbols}")
    server = get_server(repo_base, rel_path, lsp_logger)
    logger.debug("initialized the lsp")
    assert not server.server_started
    async with server.start_server():
        assert server.server_started
        refs = await call_lsp_action(
            LspActions.REFERENCES,
            [symbol.range for symbol in found_symbols],
            rel_path,
            server,
        )
        print(f"refs : {refs}")


def test_find_symbol():
    repo_base = "/Users/andrewjda/LLMs/python-sdk/"
    res = asyncio.run(
        find_symbol_in_file(
            repo_base,
            relative_path="cldk/analysis/commons/treesitter/treesitter_java.py",
            symbol_name="is_parsable",
        )
    )
    # res = asyncio.run(find_symbol("is_parsable", "python", repo_base))
    print(f"res : {res}")
    # assert res is not None and len(res) == 1
    symbol = res[0]
    print(f"symbol : {symbol}")
    print(f"symbol.name : {symbol.name}")
    print(f"symbol.kind : {symbol.kind}")
    # assert symbol.name == "Chunker"
    # assert symbol.kind == SymbolKind.Class
    # print("PASSED test_find_symbol")


if __name__ == "__main__":
    repo_base = PROJECT_ROOT
    # rel_path = "src/code_analysis_agent/code_mini_agent.py"
    symbol_name = "Chunker"

    res = asyncio.run(
        find_symbol(query=symbol_name, language="python", repo_base=repo_base)
    )
    print(f"res : {res}")
