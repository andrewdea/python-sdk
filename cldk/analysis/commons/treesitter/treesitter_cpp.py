from cldk.analysis.commons.treesitter.base import TreeSitterBase
from orchard.helpers.perched import SupportedLanguages
from pathlib import Path

class TreeSitterCpp(TreeSitterBase):
    def __init__(self):
        super().__init__(language_name=SupportedLanguages.cpp.name)

    def parse_file(self, file_path: str | Path):
        with open(file_path, "r") as f:
            code = f.read()
        return self.parse(code)
