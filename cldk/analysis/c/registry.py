from pathlib import Path
from cldk.analysis.c.c_analysis import CAnalysis
from typing import Optional, Union
from dataclasses import dataclass


@dataclass
class CCodebase:
    """
    All relevant information for a C/C++ codebase

    :param root: Path, base directory of the codebase
    :param name: str, defaults to the name of the root directory
    :param hash: str, optional hash to identify the codebase version, defaults to None
    """
    root: Path
    name: str
    hash: Optional[str] = None

    def __init__(
        self,
        root: Union[Path, str],
        name: Optional[str] = None,
        hash: Optional[str] = None,
    ):
        if isinstance(root, str):
            root = Path(root)
        self.root = Path(root)
        self.name = name if name is not None else root.name
        self.hash = hash

    @property
    def analysis(self) -> CAnalysis:
        """
        Uses the analysis_registry to create or retrieve the analyzed codebase
        """
        return analysis_registry.get(self.root)


class AnalysisRegistry:
    """
    Handy class to keep track of analyzed codebases.

    Uses a dictionary to map codebase paths to their analysis.
    """
    as_dict: dict[str, CAnalysis] = {}

    def create_analysis(self, project_dir: str | Path) -> CAnalysis:
        """
        Analyze the codebase at project_dir, store its analysis within this class,
        and return it.

        :param project_dir: str|Path where the codebase is stored
        """
        analysis = CAnalysis(Path(project_dir))
        self.as_dict[str(project_dir)] = analysis
        return analysis

    def get(self, project_dir: str | Path) -> CAnalysis:
        """
        Retrieve the analysis for the codebase at project_dir.
        If it has already been analyzed, simply retrieve it from our dictionary.
        Else, analyze it. Then return it.
        """
        analysis = self.as_dict.get(str(project_dir))
        return analysis if analysis is not None else self.create_analysis(project_dir)


# this registry can be used by callers to analyze their codebases.
# this ensures that we don't analyze the same codebase more than once per-thread; CLDK
# is responsible for managing its own state and will return the proper analysis
analysis_registry = AnalysisRegistry()
