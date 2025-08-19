from pathlib import Path
from cldk.models.python.models import PyHammockBlock
from pydantic import BaseModel
from typing import Optional, List, Dict
import os

# from codeanalyzer.hb_tree_sitter.hbt_interface import HammockBlockTreeBuilder as hbt
from cldk.analysis.commons.hammock_blocks.hbt_interface import (
    HammockBlockTreeBuilder as hbt,
)


def write_output(artifacts: BaseModel, output_dir: Path, filename: str):
    """Write artifacts to json"""
    output_file = output_dir / Path(filename)
    # Use Pydantic's json() with separators for compact output
    json_str = artifacts.model_dump_json(indent=None)
    with output_file.open("w") as f:
        f.write(json_str)
    print(f"Analysis saved to {output_file}")


class GenericFile(BaseModel):
    """Represents a generic file."""

    file_path: str
    # module_name: str
    # imports: List[PyImport] = []
    # comments: List[PyComment] = []
    # classes: Dict[str, PyClass] = {}
    # functions: Dict[str, PyCallable] = {}
    # variables: List[PyVariableDeclaration] = []
    hammock_block: Optional[PyHammockBlock] = None
    module_hammock_blocks: List[PyHammockBlock] = []


def build_generic_file(file: Path, project_dir: Path) -> Optional[GenericFile]:
    source = file.read_text(encoding="utf-8")
    module_hb, converted_hbt_map, ts_hbt_map = hbt.parse(
        source, filename=str(file), project_base=str(project_dir)
    )

    print(f"type(module_hb) : {type(module_hb)}")
    print(f"type(converted_hbt_map) : {type(converted_hbt_map)}")
    print(f"type(ts_hbt_map) : {type(ts_hbt_map)}")

    if module_hb is not None:
        return GenericFile(
            file_path=str(file),
            hammock_block=module_hb,
            module_hammock_blocks=converted_hbt_map["hammock_blocks"],
        )


class GenericApplication(BaseModel):
    """Represents a generic application."""

    symbol_table: dict[Path, GenericFile]


def build_symbol_table(project_dir: Path) -> dict[Path, GenericFile]:
    """Builds the symbol table for the project.

    This method scans the project directory, identifies Python files,
    and constructs a symbol table containing information about classes,
    functions, and variables defined in those files.
    """
    symbol_table: Dict[Path, GenericFile] = {}
    # Get all Python files first to show accurate progress
    # TODO obviously this would need to be altered depending on the language
    py_files = [
        py_file
        for py_file in project_dir.rglob("*.py")
        if "site-packages" not in py_file.resolve().__str__()  # exclude site-packages
        and ".venv" not in py_file.resolve().__str__()  # exclude virtual environments
        and ".codeanalyzer"
        not in py_file.resolve().__str__()  # exclude internal cache directories
    ]

    # with ProgressBar(len(py_files), "Building symbol table") as progress:
    for py_file in py_files:
        try:
            processed_file = build_generic_file(py_file, project_dir)
            if processed_file is not None:
                symbol_table[py_file] = processed_file
        except Exception as e:
            print(f"Failed to process {py_file}: {e}")
            raise e
    # NOTE not sure I understand what the purpose of this method is
    # it doesn't return anything, and doesn't seem to affect the symbol_table?
    # actually it might be used to add call_sites, local_variables, accessed_variables,
    # and relations
    # self._hb_call_relations(symbol_table)

    return symbol_table


def build_generic_application(
    symbol_table: dict[Path, GenericFile],
) -> GenericApplication:
    return GenericApplication(symbol_table=symbol_table)


if __name__ == "__main__":
    project_dir = Path("../../codeanalyzer-python/test_examples/simple_repo/")
    sym_table = build_symbol_table(project_dir)
    gen_app = build_generic_application(symbol_table=sym_table)
    this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    write_output(
        gen_app, output_dir=this_dir / "example_outputs", filename="simple_repo.json"
    )
