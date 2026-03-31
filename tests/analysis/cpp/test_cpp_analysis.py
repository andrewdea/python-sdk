################################################################################
# Copyright IBM Corporation 2024, 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

"""
C/C++ Tests
"""

from cldk.analysis.c.cpp_analysis import CppAnalysis
from pathlib import Path
import json
import sys
import logging

logging.basicConfig()
logger = logging.getLogger(__package__)
logger.setLevel(logging.DEBUG)

EXAMPLE_PROJECT_DIR = Path("../../data/test_cpp_project")

if sys.platform == "darwin":
    includes_library = Path(
        "/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/include/"
    )
else:
    # TODO implement this for other platforms
    pass


def test_cpp_application(project_dir: Path = EXAMPLE_PROJECT_DIR):
    """Should return a CAnalysis object"""
    project_dir = project_dir.resolve()
    logger.info(f"testing with path: {project_dir}")
    analysis = CppAnalysis(project_dir)
    assert isinstance(analysis, CppAnalysis), (
        "get_c_application should return a CppAnalysis object"
    )

    imports = sorted(analysis.get_imports())
    expected_imports = sorted(
        [
            str(includes_library / "c++/v1/cmath"),
            str(includes_library / "c++/v1/concepts"),
            str(includes_library / "c++/v1/functional"),
            str(includes_library / "c++/v1/iostream"),
            str(includes_library / "c++/v1/memory"),
            str(includes_library / "c++/v1/string"),
            str(includes_library / "c++/v1/type_traits"),
            str(includes_library / "c++/v1/vector"),
            str(project_dir / "base.h"),
            str(project_dir / "derived.h"),
            str(project_dir / "edge_cases.h"),
            str(project_dir / "function_pointers.h"),
            str(project_dir / "macros.h"),
            str(project_dir / "operators.h"),
            str(project_dir / "std_function.h"),
            str(project_dir / "templates.h"),
        ]
    )
    logger.debug(f"imports : {json.dumps(imports, indent=4)}")
    assert imports == expected_imports, (
        f"Expected imports: \n{json.dumps(expected_imports, indent=4)}\ninstead got: \n{json.dumps(imports, indent=4)}"
    )

    variables = analysis.get_variables()

    expected_variable_names = [
        "constexprVariable",
        "nestedInstance",
        "anonymousVariable",
        "ptrContainer",
        "intContainer",
        "doubleContainer",
    ]

    variable_names = [v.name for v in variables]

    logger.debug(f"variable names : {json.dumps([v.name for v in variables], indent=4)}")
    assert variable_names == expected_variable_names, (
        f"Expected variable_names: \n{json.dumps(expected_variable_names, indent=4)}\ninstead got: \n{json.dumps(variable_names, indent=4)}"
    )

if __name__ == "__main__":
    logger.info("\n\n====================\n\ntesting\n\n====================")
    test_cpp_application()
