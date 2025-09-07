from pathlib import Path
from cldk.analysis.commons.hammock_blocks.hb_definition import TSHammockBlock
from cldk.models.java.models import JHammockBlock
from pydantic import BaseModel
from typing import Optional, List, Dict, Union
import os

# from codeanalyzer.hb_tree_sitter.hbt_interface import HammockBlockTreeBuilder as hbt
from cldk.analysis.commons.hammock_blocks.hbt_interface import (
    HammockBlockTreeBuilder as hbt,
)

EXAMPLE_OUTPUTS_DIR = "example_outputs/"


def write_output(artifacts: BaseModel, output_dir: Path, filename: str):
    """Write artifacts to json"""
    output_file = output_dir / Path(filename)
    # Use Pydantic's json() with separators for compact output
    json_str = artifacts.model_dump_json(indent=4)
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
    hammock_block: Optional[JHammockBlock] = None
    module_hammock_blocks: List[Union[JHammockBlock, TSHammockBlock]] = []


def build_generic_file(
    file: Path, project_dir: Path, language: str
) -> Optional[GenericFile]:
    source = file.read_text(encoding="utf-8")
    module_hb, converted_hbt_map, ts_hbt_map = hbt.parse(
        source, filename=str(file), project_base=str(project_dir), language=language
    )

    # if module_hb is not None:
    return GenericFile(
        file_path=str(file),
        hammock_block=module_hb,
        module_hammock_blocks=converted_hbt_map["hammock_blocks"]
        if converted_hbt_map is not None
        else ts_hbt_map["hammock_blocks"],
    )


class GenericApplication(BaseModel):
    """Represents a generic application."""

    symbol_table: dict[Path, GenericFile]


def list_java_files(project_dir: Path) -> list[Path]:
    java_files = [j_file for j_file in project_dir.rglob("*.java")]
    return java_files


def list_python_files(project_dir: Path) -> list[Path]:
    py_files = [
        py_file
        for py_file in project_dir.rglob("*.py")
        if "site-packages" not in py_file.resolve().__str__()  # exclude site-packages
        and ".venv" not in py_file.resolve().__str__()  # exclude virtual environments
        and ".codeanalyzer"
        not in py_file.resolve().__str__()  # exclude internal cache directories
    ]
    return py_files


def build_symbol_table(project_dir: Path, language: str) -> dict[Path, GenericFile]:
    """Builds the symbol table for the project.

    This method scans the project directory, identifies Python files,
    and constructs a symbol table containing information about classes,
    functions, and variables defined in those files.
    """
    symbol_table: Dict[Path, GenericFile] = {}
    # Get all Java files first to show accurate progress
    # TODO obviously this would need to be altered depending on the language
    match language.lower():
        case "java":
            files = list_java_files(project_dir)
        case "python":
            files = list_python_files(project_dir)
        case _:
            raise NotImplementedError(f"This language is not supported yet: {language}")

    # with ProgressBar(len(py_files), "Building symbol table") as progress:
    for file in files:
        try:
            processed_file = build_generic_file(file, project_dir, language)
            if processed_file is not None:
                symbol_table[file] = processed_file
        except Exception as e:
            print(f"Failed to process {file}: {e}")
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
    # test_applications_dir = Path(
    #     # "../../codeanalyzer-java/src/test/resources/test-applications/"
    #     "../../opentelemetry-demo/src/ad/src/main/"
    # )
    project_name = "opentelemetry-demo"
    project_dir = Path("../../opentelemetry-demo/src/ad/src/main/")
    language = "java"
    sym_table = build_symbol_table(project_dir, language)
    gen_app = build_generic_application(symbol_table=sym_table)
    this_dir = Path(os.path.dirname(os.path.realpath(__file__)))
    write_output(
        gen_app,
        output_dir=this_dir / "example_outputs",
        filename=f"{project_name}.json",
    )
