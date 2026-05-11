from pathlib import Path
from cldk.models.python.models import PyHammockBlock
from cldk.analysis.commons.hammock_blocks.core import hb_graph_to_file
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
    # imports: List[JsImport] = []
    # comments: List[JsComment] = []
    # classes: Dict[str, JsClass] = {}
    # functions: Dict[str, JsCallable] = {}
    # variables: List[JsVariableDeclaration] = []
    hammock_block: Optional[PyHammockBlock] = None
    module_hammock_blocks: List[PyHammockBlock] = []


def build_generic_file(file: Path, project_dir: Path) -> Optional[GenericFile]:
    source = file.read_text(encoding="utf-8")
    module_hb, converted_hbt_map, ts_hbt_map = hbt.parse(
        source, filename=str(file), project_base=str(project_dir), language="javascript"
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

    This method scans the project directory, identifies JavaScript files,
    and constructs a symbol table containing information about classes,
    functions, and variables defined in those files.
    """
    symbol_table: Dict[Path, GenericFile] = {}
    # Get all JavaScript files first to show accurate progress
    js_files = [
        js_file
        for js_file in project_dir.rglob("*.js")
        if "node_modules" not in js_file.resolve().__str__()  # exclude node_modules
        and ".git" not in js_file.resolve().__str__()  # exclude git directories
        and "dist" not in js_file.resolve().__str__()  # exclude build directories
        and "build" not in js_file.resolve().__str__()  # exclude build directories
        and ".codeanalyzer"
        not in js_file.resolve().__str__()  # exclude internal cache directories
    ]

    # with ProgressBar(len(js_files), "Building symbol table") as progress:
    for js_file in js_files:
        try:
            processed_file = build_generic_file(js_file, project_dir)
            if processed_file is not None:
                symbol_table[js_file] = processed_file
        except Exception as e:
            print(f"Failed to process {js_file}: {e}")
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
    project_name = "robot-shop"
    project_dir = Path("../../robot-shop/catalogue")
    language = "javascript"
    # sym_table = build_symbol_table(project_dir, language)
    # gen_app = build_generic_application(symbol_table=sym_table)
    # this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    # write_output(
    #     gen_app,
    #     output_dir=this_dir / "example_outputs",
    #     filename=f"{project_name}.json",
    # )
    this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    # hb_graph_to_file(project_name, project_dir, language, this_dir / "example_outputs")
    hb_graph_to_file(
        project_dir, language, this_dir / "example_outputs" / f"new_{project_name}.json"
    )
