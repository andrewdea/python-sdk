from pathlib import Path
from cldk.analysis.c.c_analysis import CAnalysis


class AnalysisRegistry:
    # TODO might be potentially good to include a hash commit as well, so we can be
    # really confident that we are looking at the right version of the code-base
    as_dict: dict[str, CAnalysis] = {}

    def create_analysis(self, project_dir: str | Path) -> CAnalysis:
        analysis = CAnalysis(Path(project_dir))
        self.as_dict[str(project_dir)] = analysis
        return analysis

    def get_analysis(self, project_dir: str | Path) -> CAnalysis:
        analysis = self.as_dict.get(str(project_dir))
        return analysis if analysis is not None else self.create_analysis(project_dir)


analysis_registry = AnalysisRegistry()
