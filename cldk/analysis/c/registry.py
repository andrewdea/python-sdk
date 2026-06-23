from pathlib import Path
from cldk.analysis import AnalysisLevel
from cldk.analysis.c.c_analysis import CAnalysis
from typing import Optional, Union, List
from dataclasses import dataclass

from cldk.analysis.c.cpp_analysis import CppAnalysis
from cldk.analysis import AnalysisLevel
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


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
    def analysis(self) -> CppAnalysis:
        """
        Uses the analysis_registry to create or retrieve the analyzed codebase
        """
        return analysis_registry.get(self.root)


class AnalysisRegistry:
    """
    Handy class to keep track of analyzed codebases.

    Uses a dictionary to map codebase paths to their analysis.
    """

    as_dict: dict[str, CppAnalysis] = {}

    def create_analysis(
        self,
        project_dir: str | Path,
        compilation_db_path: Optional[Union[Path, str]] = None,
        extra_compiler_args: Optional[List[str]] = None,
        analysis_level: AnalysisLevel = AnalysisLevel.symbol_table,
        skip_fatal_errors: Optional[bool] = True,
    ) -> CppAnalysis:
        """
        Analyze the codebase at project_dir, store its analysis within this class,
        and return it.

        :param project_dir: str|Path where the codebase is stored
        """
        analysis = CppAnalysis(
            project_dir=Path(project_dir),
            compilation_db_path=compilation_db_path,
            extra_compiler_args=extra_compiler_args,
            analysis_level=analysis_level,
            skip_fatal_errors=skip_fatal_errors,
        )
        self.as_dict[str(project_dir)] = analysis
        return analysis

    # TODO: not the best way of doing this since we're caching at project
    # root level, but we're not taking into consideration the extra config
    def get(
        self,
        project_dir: str | Path,
        compilation_db_path: Optional[Union[Path, str]] = None,
        extra_compiler_args: Optional[List[str]] = None,
        analysis_level: AnalysisLevel = AnalysisLevel.symbol_table,
        skip_fatal_errors: Optional[bool] = True,
    ) -> CppAnalysis:
        """
        Retrieve the analysis for the codebase at project_dir.
        If it has already been analyzed, simply retrieve it from our dictionary.
        Else, analyze it. Then return it.
        """
        analysis = self.as_dict.get(str(project_dir))
        # check if this analysis has been created already,
        # and verify that the same config was used.
        # if not, create the analysis first
        if analysis is None or not compare_configs(
            analysis, compilation_db_path, extra_compiler_args, analysis_level
        ):
            analysis = self.create_analysis(
                project_dir,
                compilation_db_path,
                extra_compiler_args,
                analysis_level,
                skip_fatal_errors,
            )
        return analysis


# this registry can be used by callers to analyze their codebases.
# this ensures that we don't analyze the same codebase more than once per-thread; CLDK
# is responsible for managing its own state and will return the proper analysis
analysis_registry = AnalysisRegistry()
