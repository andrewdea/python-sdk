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
from cldk.analysis.c.utils import compute_cyclomatic_complexity
from cldk.models.c.cpp_models import CppFunction

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

    logger.debug(
        f"variable names : {json.dumps([v.name for v in variables], indent=4)}"
    )
    assert variable_names == expected_variable_names, (
        f"Expected variable_names: \n{json.dumps(expected_variable_names, indent=4)}\ninstead got: \n{json.dumps(variable_names, indent=4)}"
    )

    test_enums_func = analysis.get_function("testEnums")
    assert isinstance(test_enums_func, CppFunction), (
        "testEnums should be a CppFunction object"
    )
    assert test_enums_func.cyclomatic_complexity == 6, (
        f"Expected cyclomatic_complexity of 6 for testEnums, got {test_enums_func.cyclomatic_complexity}"
    )


def test_cyclomatic_complexity():
    """Test cyclomatic complexity calculation for C++ code snippets"""

    # Complexity 1 - Simple statements (no decision points)
    snippet_1a = "int x = 0;"
    assert compute_cyclomatic_complexity(snippet_1a) == 1, (
        f"Expected complexity 1 for simple assignment, got {compute_cyclomatic_complexity(snippet_1a)}"
    )

    snippet_1b = """
    int main() {
        int a = 5;
        int b = 10;
        return a + b;
    }
    """
    assert compute_cyclomatic_complexity(snippet_1b) == 1, (
        f"Expected complexity 1 for simple function, got {compute_cyclomatic_complexity(snippet_1b)}"
    )

    # Complexity 2 - One decision point
    snippet_2a = """
    int main() {
        int x = 5;
        if (x > 0) {
            return 1;
        }
        return 0;
    }
    """
    assert compute_cyclomatic_complexity(snippet_2a) == 2, (
        f"Expected complexity 2 for single if, got {compute_cyclomatic_complexity(snippet_2a)}"
    )

    snippet_2b = """
    void process(int n) {
        for (int i = 0; i < n; i++) {
            printf("%d", i);
        }
    }
    """
    assert compute_cyclomatic_complexity(snippet_2b) == 2, (
        f"Expected complexity 2 for single for loop, got {compute_cyclomatic_complexity(snippet_2b)}"
    )

    # Complexity 3 - Two decision points
    snippet_3a = """
    int check(int x, int y) {
        if (x > 0) {
            if (y > 0) {
                return 1;
            }
        }
        return 0;
    }
    """
    assert compute_cyclomatic_complexity(snippet_3a) == 3, (
        f"Expected complexity 3 for nested ifs, got {compute_cyclomatic_complexity(snippet_3a)}"
    )

    snippet_3b = """
    void process(int x) {
        if (x > 0 && x < 100) {
            printf("valid");
        }
    }
    """
    assert compute_cyclomatic_complexity(snippet_3b) == 3, (
        f"Expected complexity 3 for if with &&, got {compute_cyclomatic_complexity(snippet_3b)}"
    )

    # Complexity 4 - Three decision points
    snippet_4a = """
    int classify(int x) {
        if (x < 0) {
            return -1;
        } else if (x == 0) {
            return 0;
        } else {
            return 1;
        }
    }
    """
    assert compute_cyclomatic_complexity(snippet_4a) == 4, (
        f"Expected complexity 4 for if-else-if chain, got {compute_cyclomatic_complexity(snippet_4a)}"
    )

    snippet_4b = """
    void process(int x, int y) {
        while (x > 0) {
            if (y > 0) {
                x--;
            } else {
                x -= 2;
            }
            y--;
        }
    }
    """
    assert compute_cyclomatic_complexity(snippet_4b) == 4, (
        f"Expected complexity 4 for while with nested if-else, got {compute_cyclomatic_complexity(snippet_4b)}"
    )

    # Complexity 5 - Four decision points
    snippet_5a = """
    int evaluate(int a, int b, int c, int d) {
        if (a > 0) {
            if (b > 0) {
                if (c > 0) {
                    if (d > 0) {
                        return 1;
                    }
                }
            }
        }
        return 0;
    }
    """
    assert compute_cyclomatic_complexity(snippet_5a) == 5, (
        f"Expected complexity 5 for quadruple nested ifs, got {compute_cyclomatic_complexity(snippet_5a)}"
    )

    snippet_5b = """
    void process(int x) {
        if (x > 0 && x < 10) {
            for (int i = 0; i < x; i++) {
                if (i % 2 == 0) {
                    printf("%d", i);
                }
            }
        }
    }
    """
    assert compute_cyclomatic_complexity(snippet_5b) == 5, (
        f"Expected complexity 5 for if with && and for loop, got {compute_cyclomatic_complexity(snippet_5b)}"
    )

    logger.info("All cyclomatic complexity tests passed!")


if __name__ == "__main__":
    logger.info("\n\n====================\n\ntesting\n\n====================")
    test_cyclomatic_complexity()
    test_cpp_application()
